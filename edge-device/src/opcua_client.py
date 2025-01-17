# edge-device/src/opcua_client.py
from asyncua import Client, ua
import asyncio
import logging
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class OPCUAClient:
    def __init__(self):
        self.server_url = os.getenv("OPCUA_SERVER_URL", "opc.tcp://simulator:4840/saw/")
        self.client = Client(url=self.server_url)
        self.connected = False
        self.nodes = {}
        self.logger = logging.getLogger(__name__)

    async def connect(self) -> None:
        """Connette al server OPC UA"""
        try:
            self.logger.info(f"Attempting to connect to OPC UA server at {self.server_url}")
            await self.client.connect()
            self.connected = True
            await self._init_nodes()
            self.logger.info(f"Successfully connected to OPC UA server at {self.server_url}")
        except Exception as e:
            self.logger.error(f"Failed to connect to OPC UA server: {e}", exc_info=True)
            raise

    async def disconnect(self) -> None:
        """Disconnette dal server OPC UA"""
        if self.connected:
            try:
                await self.client.disconnect()
                self.connected = False
                self.logger.info("Disconnected from OPC UA server")
            except Exception as e:
                self.logger.error(f"Error during disconnect: {e}", exc_info=True)

    async def _init_nodes(self) -> None:
        """Inizializza i riferimenti ai nodi"""
        try:
            self.logger.info("Initializing OPC UA nodes...")
            # Ottieni il namespace index
            nsidx = await self.client.get_namespace_index("http://saw.simulator")
            self.logger.info(f"Got namespace index: {nsidx}")

            # Ottieni il nodo principale della segatrice
            objects = self.client.nodes.objects
            saw = await objects.get_child(f"{nsidx}:IndustrialSaw")
            self.logger.info("Found IndustrialSaw node")

            # Inizializza i riferimenti ai nodi per tutte le variabili
            node_names = [
                "State", "CuttingSpeed", "PiecesCut", "PowerConsumption",
                "Temperature", "SafetyBarrier", "BladeWear", "CurrentMaterial"
            ]

            for name in node_names:
                lowercase_name = name.lower()
                self.nodes[lowercase_name] = await saw.get_child(f"{nsidx}:{name}")
                self.logger.info(f"Initialized node: {name}")

            self.logger.info("Successfully initialized all OPC UA nodes")

        except Exception as e:
            self.logger.error(f"Failed to initialize nodes: {e}", exc_info=True)
            raise
    
    async def _call_method(self, method_name: str, *args) -> bool:
        """Helper function per chiamare i metodi del server"""
        try:
            if not self.connected:
                self.logger.error(f"Cannot call {method_name}: Not connected to OPC UA server")
                return False

            self.logger.info(f"Calling OPC UA method: {method_name} with args: {args}")

            nsidx = await self.client.get_namespace_index("http://saw.simulator")
            self.logger.info(f"Got namespace index: {nsidx}")

            objects = self.client.nodes.objects
            saw = await objects.get_child(f"{nsidx}:IndustrialSaw")
            self.logger.info(f"Got saw node: {saw}")

            method = await saw.get_child(f"{nsidx}:{method_name}")
            self.logger.info(f"Got method node: {method}")

            result = await saw.call_method(method, *args)
            self.logger.info(f"Raw method result: {result}")
            
            # Se il risultato è direttamente un booleano
            if isinstance(result, bool):
                return result
                
            # Se il risultato è una lista di un elemento
            if isinstance(result, list) and len(result) > 0:
                # Prendi il primo elemento
                success = result[0]
                # Se è un booleano usalo direttamente
                if isinstance(success, bool):
                    return success
                # Altrimenti converti in booleano
                return bool(success)
            
            # In caso di risultato inatteso, logga e ritorna True
            self.logger.info(f"Method {method_name} returned: {result}")
            return True if result else False

        except Exception as e:
            self.logger.error(f"Error calling method {method_name}: {e}", exc_info=True)
            return False

    async def read_values(self) -> Dict[str, Any]:
        """Legge tutti i valori dal server"""
        if not self.connected:
            self.logger.error("Cannot read values: Not connected to OPC UA server")
            raise ConnectionError("Not connected to OPC UA server")

        try:
            self.logger.debug("Reading values from OPC UA server")
            values = {}
            for node_name, node in self.nodes.items():
                try:
                    value = await node.read_value()
                    values[node_name] = value
                except Exception as e:
                    self.logger.error(f"Error reading node {node_name}: {e}")
                    values[node_name] = None
            return values
        except Exception as e:
            self.logger.error(f"Error reading values: {e}", exc_info=True)
            raise

    async def start_saw(self) -> bool:
        """Avvia la segatrice"""
        self.logger.info("Start command received")
        return await self._call_method("Start")

    async def stop_saw(self) -> bool:
        """Ferma la segatrice"""
        self.logger.info("Stop command received")
        return await self._call_method("Stop")

    async def pause_saw(self) -> bool:
        """Mette in pausa la segatrice"""
        self.logger.info("Pause command received")
        return await self._call_method("Pause")

    async def reset_saw(self) -> bool:
        """Resetta la segatrice"""
        self.logger.info("Reset command received")
        return await self._call_method("Reset")

    async def toggle_barrier(self) -> bool:
        """Attiva/disattiva la barriera di sicurezza"""
        self.logger.info("Toggle barrier command received")
        return await self._call_method("ToggleBarrier")

    async def set_material(self, material: str) -> bool:
        """Imposta il materiale da tagliare"""
        try:
            self.logger.info(f"Set material command received: {material}")
            result = await self._call_method("SetMaterial", material)
            
            if result:
                self.logger.info(f"Successfully set material to: {material}")
                return True
            else:
                self.logger.error(f"Failed to set material to: {material}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting material: {e}", exc_info=True)
            return False    