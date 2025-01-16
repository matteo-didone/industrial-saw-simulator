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
            await self.client.connect()
            self.connected = True
            await self._init_nodes()
            self.logger.info(f"Connected to OPC UA server at {self.server_url}")
        except Exception as e:
            self.logger.error(f"Failed to connect to OPC UA server: {e}")
            raise

    async def disconnect(self) -> None:
        """Disconnette dal server OPC UA"""
        if self.connected:
            await self.client.disconnect()
            self.connected = False
            self.logger.info("Disconnected from OPC UA server")

    async def _init_nodes(self) -> None:
        """Inizializza i riferimenti ai nodi"""
        try:
            # Ottieni il namespace index
            nsidx = await self.client.get_namespace_index("http://saw.simulator")

            # Ottieni il nodo principale della segatrice
            objects = self.client.nodes.objects
            saw = await objects.get_child(f"{nsidx}:IndustrialSaw")

            # Inizializza i riferimenti ai nodi per tutte le variabili
            node_names = [
                "State", "CuttingSpeed", "PiecesCut", "PowerConsumption",
                "Temperature", "SafetyBarrier", "BladeWear", "CurrentMaterial"
            ]

            for name in node_names:
                # Mantiene i nomi delle variabili in minuscolo senza underscore
                lowercase_name = name.lower()
                self.nodes[lowercase_name] = await saw.get_child(f"{nsidx}:{name}")

            self.logger.info("OPC UA nodes initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize nodes: {e}")
            raise
        
    async def read_values(self) -> Dict[str, Any]:
        """Legge tutti i valori dal server"""
        if not self.connected:
            raise ConnectionError("Not connected to OPC UA server")

        try:
            values = {}
            for node_name, node in self.nodes.items():
                value = await node.read_value()
                # Usa il nome del nodo così com'è, senza mappatura
                values[node_name] = value
            return values
        except Exception as e:
            self.logger.error(f"Error reading values: {e}")
            raise

    async def _call_method(self, method_name: str, *args) -> bool:
        """Helper function per chiamare i metodi del server"""
        try:
            if not self.connected:
                raise ConnectionError("Not connected to OPC UA server")
            
            nsidx = await self.client.get_namespace_index("http://saw.simulator")
            objects = self.client.nodes.objects
            saw = await objects.get_child(f"{nsidx}:IndustrialSaw")
            method = await saw.get_child(f"{nsidx}:{method_name}")
            
            await saw.call_method(method, *args)
            return True
        except Exception as e:
            self.logger.error(f"Error calling method {method_name}: {e}")
            return False

    async def start_saw(self) -> bool:
        """Avvia la segatrice"""
        return await self._call_method("Start")

    async def stop_saw(self) -> bool:
        """Ferma la segatrice"""
        return await self._call_method("Stop")

    async def pause_saw(self) -> bool:
        """Mette in pausa la segatrice"""
        return await self._call_method("Pause")

    async def reset_saw(self) -> bool:
        """Resetta la segatrice dallo stato di allarme"""
        return await self._call_method("Reset")

    async def toggle_barrier(self) -> bool:
        """Attiva/disattiva la barriera di sicurezza"""
        return await self._call_method("ToggleBarrier")

    async def set_material(self, material: str) -> bool:
        """Imposta il materiale da tagliare"""
        try:
            self.logger.info(f"Setting material to: {material}")
            
            # Mapping dei materiali (gestisce case-sensitivity)
            material_map = {
                "steel": "Steel",
                "aluminum": "Aluminum", 
                "wood": "Wood"
            }
            
            # Converti il materiale nel formato corretto
            material_name = material_map.get(material.lower())
            if not material_name:
                self.logger.error(f"Invalid material: {material}")
                return False
                
            # Chiama il metodo del server
            result = await self._call_method("SetMaterial", material_name)
            
            if result:
                self.logger.info(f"Successfully set material to: {material_name}")
                return True
            else:
                self.logger.error(f"Failed to set material to: {material_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error setting material: {e}")
            return False