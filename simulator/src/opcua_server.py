# simulator/src/opcua_server.py
from asyncua import Server, ua
from asyncua.common.node import Node
import asyncio
import logging
from .simulator import IndustrialSawSimulator

class SawOPCUAServer:
    def __init__(self, simulator: IndustrialSawSimulator):
        self.simulator = simulator
        self.server = Server()
        self.nodes = {}
        self.running = False
        self.logger = logging.getLogger(__name__)

    async def init(self):
        """Inizializza il server OPC UA e crea la struttura dei nodi"""
        await self.server.init()

        # Configura l'endpoint
        self.server.set_endpoint("opc.tcp://0.0.0.0:4840/saw/")
        self.server.set_server_name("Industrial Saw Simulator")

        # Registra il namespace
        uri = "http://saw.simulator"
        idx = await self.server.register_namespace(uri)

        # Ottieni il nodo Objects
        objects = self.server.nodes.objects

        # Crea l'oggetto principale per la segatrice
        saw_object = await objects.add_object(idx, "IndustrialSaw")

        # Aggiungi tutte le variabili
        self.nodes["state"] = await saw_object.add_variable(
            idx, "State", "inactive",
            ua.VariantType.String
        )
        self.nodes["cutting_speed"] = await saw_object.add_variable(
            idx, "CuttingSpeed", 0.0,
            ua.VariantType.Float
        )
        self.nodes["pieces_cut"] = await saw_object.add_variable(
            idx, "PiecesCut", 0,
            ua.VariantType.UInt32
        )
        self.nodes["power_consumption"] = await saw_object.add_variable(
            idx, "PowerConsumption", 0.0,
            ua.VariantType.Float
        )
        self.nodes["temperature"] = await saw_object.add_variable(
            idx, "Temperature", 20.0,
            ua.VariantType.Float
        )
        self.nodes["safety_barrier"] = await saw_object.add_variable(
            idx, "SafetyBarrier", True,
            ua.VariantType.Boolean
        )
        self.nodes["blade_wear"] = await saw_object.add_variable(
            idx, "BladeWear", 0.0,
            ua.VariantType.Float
        )
        self.nodes["current_material"] = await saw_object.add_variable(
            idx, "CurrentMaterial", "Steel",
            ua.VariantType.String
        )

        # Aggiungi i metodi di controllo
        await saw_object.add_method(
            idx, "Start", self.start_saw, [], []
        )
        await saw_object.add_method(
            idx, "Stop", self.stop_saw, [], []
        )
        await saw_object.add_method(
            idx, "Pause", self.pause_saw, [], []
        )
        await saw_object.add_method(
            idx, "Reset", self.reset_saw, [], []
        )
        await saw_object.add_method(
            idx, "ToggleBarrier", self.toggle_barrier, [], []
        )
        await saw_object.add_method(
            idx, "SetMaterial", self.set_material,
            [ua.VariantType.String], [ua.VariantType.Boolean]
        )

        # Rendi i nodi scrivibili
        for node in self.nodes.values():
            await node.set_writable()
            
        self.logger.info("OPC UA Server initialized successfully")

    async def start(self):
        """Avvia il server e il loop di aggiornamento"""
        self.running = True
        await self.server.start()
        self.logger.info("OPC UA Server started")
        
        try:
            while self.running:
                await self._update_state()
                await asyncio.sleep(0.1)
        except Exception as e:
            self.logger.error(f"Error in server main loop: {e}")
            raise

    async def _update_state(self):
        """Aggiorna lo stato dei nodi OPC UA"""
        # Aggiorna il simulatore
        self.simulator.simulate_step(0.1)  # 100ms steps

        # Aggiorna i nodi OPC UA
        state = self.simulator.get_state()
        value_types = {
            "state": (str, ua.VariantType.String),
            "cutting_speed": (float, ua.VariantType.Float),
            "pieces_cut": (int, ua.VariantType.UInt32),
            "power_consumption": (float, ua.VariantType.Float),
            "temperature": (float, ua.VariantType.Float),
            "safety_barrier": (bool, ua.VariantType.Boolean),
            "blade_wear": (float, ua.VariantType.Float),
            "current_material": (str, ua.VariantType.String)
        }

        for key, value in state.items():
            if key in self.nodes:
                try:
                    # Converti il valore al tipo corretto
                    type_converter, variant_type = value_types[key]
                    converted_value = type_converter(value)
                    # Crea una variante con il tipo corretto
                    variant = ua.Variant(converted_value, variant_type)
                    await self.nodes[key].write_value(variant)
                except Exception as e:
                    self.logger.error(f"Error updating node {key}: {e}")

    async def stop(self):
        """Ferma il server"""
        self.running = False
        await self.server.stop()
        self.logger.info("OPC UA Server stopped")

    async def start_saw(self, parent: Node):
        """Avvia la segatrice"""
        self.logger.info("Start command received")
        success = self.simulator.start()
        self.logger.info(f"Start command result: {success}")
        return [ua.Variant(success, ua.VariantType.Boolean)]

    async def stop_saw(self, parent: Node):
        """Ferma la segatrice"""
        self.logger.info("Stop command received")
        success = self.simulator.stop()
        self.logger.info(f"Stop command result: {success}")
        return [ua.Variant(success, ua.VariantType.Boolean)]

    async def pause_saw(self, parent: Node):
        """Mette in pausa la segatrice"""
        self.logger.info("Pause command received")
        success = self.simulator.pause()
        self.logger.info(f"Pause command result: {success}")
        return [ua.Variant(success, ua.VariantType.Boolean)]

    async def reset_saw(self, parent: Node):
        """Resetta la segatrice"""
        self.logger.info("Reset command received")
        success = self.simulator.reset()
        self.logger.info(f"Reset command result: {success}")
        return [ua.Variant(success, ua.VariantType.Boolean)]

    async def toggle_barrier(self, parent: Node):
        """Attiva/disattiva la barriera di sicurezza"""
        self.logger.info("Toggle barrier command received")
        success = self.simulator.toggle_safety_barrier()
        return [ua.Variant(success, ua.VariantType.Boolean)]

    async def set_material(self, parent: Node, material: str):
        """Imposta il materiale da tagliare"""
        self.logger.info(f"Set material command received: {material}")
        success = self.simulator.set_material(material)
        if not success:
            self.logger.warning(f"Invalid material specified: {material}")
            return [ua.Variant(False, ua.VariantType.Boolean)]
        self.logger.info(f"Successfully set material to: {material}")
        return [ua.Variant(True, ua.VariantType.Boolean)]