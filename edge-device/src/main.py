# edge-device/src/main.py
import asyncio
import logging
import uvicorn
from dotenv import load_dotenv
import os
from .opcua_client import OPCUAClient
from .mqtt_handler import MQTTHandler
from .data_processor import DataProcessor
from .rest_api import APIServer

class EdgeDevice:
    def __init__(self):
        # Configura logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Carica variabili d'ambiente
        load_dotenv()
        
        # Inizializza componenti
        self.opcua_client = OPCUAClient()
        self.mqtt_handler = MQTTHandler()
        self.data_processor = DataProcessor()
        
        # Crea API server
        self.api_server = APIServer(
            self.opcua_client,
            self.mqtt_handler,
            self.data_processor
        )
        
        # Flag per il controllo del loop principale
        self.running = False

    async def start(self):
        """Avvia tutti i componenti dell'edge device"""
        try:
            # Connetti al server OPC UA
            self.logger.info("Connecting to OPC UA server...")
            await self.opcua_client.connect()
            
            # Connetti al broker MQTT
            self.logger.info("Connecting to MQTT broker...")
            if not self.mqtt_handler.connect():
                raise Exception("Failed to connect to MQTT broker")
            
            # Registra i callback per i comandi MQTT
            self._setup_mqtt_callbacks()
            
            # Avvia il loop principale
            self.running = True
            await self._main_loop()
            
        except Exception as e:
            self.logger.error(f"Error starting edge device: {e}")
            raise

    async def stop(self):
        """Ferma tutti i componenti"""
        self.running = False
        
        # Disconnetti dall'OPC UA
        await self.opcua_client.disconnect()
        
        # Disconnetti dal broker MQTT
        self.mqtt_handler.disconnect()
        
        self.logger.info("Edge device stopped")

    def _setup_mqtt_callbacks(self):
        """Configura i callback per i comandi MQTT"""
        self.mqtt_handler.register_command_callback(
            "start", 
            lambda _: asyncio.create_task(self.opcua_client.start_saw())
        )
        
        self.mqtt_handler.register_command_callback(
            "stop", 
            lambda _: asyncio.create_task(self.opcua_client.stop_saw())
        )
        
        self.mqtt_handler.register_command_callback(
            "pause", 
            lambda _: asyncio.create_task(self.opcua_client.pause_saw())
        )
        
        self.mqtt_handler.register_command_callback(
            "toggle_barrier", 
            lambda _: asyncio.create_task(self.opcua_client.toggle_barrier())
        )

    async def _main_loop(self):
        """Loop principale che legge i dati e li processa"""
        while self.running:
            try:
                # Leggi lo stato corrente
                state = await self.opcua_client.read_values()
                
                # Processa i dati
                metrics = self.data_processor.process_state(state)
                
                # Pubblica su MQTT
                self.mqtt_handler.publish_state(state)
                self.mqtt_handler.publish_metrics(metrics)
                
                # Gestisci gli alert
                alerts = self.data_processor.get_active_alerts()
                for alert in alerts:
                    self.mqtt_handler.publish_alert(
                        alert.type,
                        alert.message,
                        alert.severity.value
                    )
                
                # Attendi prima del prossimo ciclo
                await asyncio.sleep(1)  # Aggiorna ogni secondo
                
            except Exception as e:
                self.logger.error(f"Error in main loop: {e}")
                await asyncio.sleep(5)  # Attendi prima di riprovare

async def main():
    # Crea l'istanza dell'edge device
    edge_device = EdgeDevice()
    
    try:
        # Avvia il server API in un task separato
        api = edge_device.api_server.get_app()
        config = uvicorn.Config(
            api,
            host="0.0.0.0",
            port=int(os.getenv("REST_API_PORT", "5000")),
            log_level="info"
        )
        server = uvicorn.Server(config)
        api_task = asyncio.create_task(server.serve())
        
        # Avvia l'edge device
        await edge_device.start()
        
        # Attendi che entrambi i task completino
        await asyncio.gather(api_task)
        
    except KeyboardInterrupt:
        await edge_device.stop()
    except Exception as e:
        logging.error(f"Fatal error: {e}")
        await edge_device.stop()
        raise

if __name__ == "__main__":
    asyncio.run(main())