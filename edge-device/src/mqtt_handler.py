# edge-device/src/mqtt_handler.py
import paho.mqtt.client as mqtt
import json
import logging
from typing import Dict, Any, Optional, Callable
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

class MQTTHandler:
    def __init__(self):
        # Configurazione client MQTT
        self.client = mqtt.Client(
            client_id="saw_edge_device",
            protocol=mqtt.MQTTv5
        )
        self.connected = False
        self.logger = logging.getLogger(__name__)
        
        # Configurazione broker
        self.broker = os.getenv("MQTT_BROKER", "mosquitto")
        self.port = int(os.getenv("MQTT_PORT", "1883"))
        self.topic_prefix = "saw/"
        
        # Callback per i comandi ricevuti
        self.command_callbacks = {}
        
        # Configura callbacks
        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message
        self.client.on_publish = self._on_publish

    def connect(self) -> bool:
        """Connette al broker MQTT"""
        try:
            self.client.connect(self.broker, self.port)
            self.client.loop_start()
            return True
        except Exception as e:
            self.logger.error(f"Failed to connect to MQTT broker: {e}")
            return False

    def disconnect(self):
        """Disconnette dal broker MQTT"""
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            self.logger.error(f"Error disconnecting from MQTT broker: {e}")

    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback per la connessione"""
        if rc == 0:
            self.connected = True
            self.logger.info("Connected to MQTT broker")
            
            # Sottoscrivi ai topic dei comandi
            self.client.subscribe(f"{self.topic_prefix}commands/#")
        else:
            self.logger.error(f"Failed to connect to MQTT broker with code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback per la disconnessione"""
        self.connected = False
        self.logger.info("Disconnected from MQTT broker")

    def _on_message(self, client, userdata, msg):
        """Callback per i messaggi ricevuti"""
        try:
            topic = msg.topic
            payload = json.loads(msg.payload.decode())
            
            # Estrai il comando dal topic
            command = topic.split('/')[-1]
            
            if command in self.command_callbacks:
                self.command_callbacks[command](payload)
            else:
                self.logger.warning(f"Received message for unknown command: {command}")
                
        except json.JSONDecodeError:
            self.logger.error("Received invalid JSON payload")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")

    def _on_publish(self, client, userdata, mid):
        """Callback per la pubblicazione dei messaggi"""
        self.logger.debug(f"Message {mid} published successfully")

    def publish_state(self, state: Dict[str, Any]) -> bool:
        """Pubblica lo stato della segatrice"""
        if not self.connected:
            self.logger.warning("Not connected to MQTT broker")
            return False

        try:
            # Pubblica stato completo
            topic = f"{self.topic_prefix}state"
            payload = json.dumps({
                "timestamp": datetime.now().isoformat(),
                "data": state
            })
            self.client.publish(topic, payload, qos=1)
            
            # Pubblica singoli valori su topic separati
            for key, value in state.items():
                topic = f"{self.topic_prefix}state/{key}"
                payload = json.dumps({
                    "timestamp": datetime.now().isoformat(),
                    "value": value
                })
                self.client.publish(topic, payload, qos=1)
            
            return True
        except Exception as e:
            self.logger.error(f"Error publishing state: {e}")
            return False

    def publish_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Pubblica le metriche calcolate"""
        if not self.connected:
            return False

        try:
            topic = f"{self.topic_prefix}metrics"
            payload = json.dumps({
                "timestamp": datetime.now().isoformat(),
                "data": metrics
            })
            self.client.publish(topic, payload, qos=1)
            return True
        except Exception as e:
            self.logger.error(f"Error publishing metrics: {e}")
            return False

    def publish_alert(self, alert_type: str, message: str, severity: str = "info") -> bool:
        """Pubblica un alert"""
        if not self.connected:
            return False

        try:
            topic = f"{self.topic_prefix}alerts"
            payload = json.dumps({
                "type": alert_type,
                "message": message,
                "severity": severity,
                "timestamp": datetime.now().isoformat()
            })
            self.client.publish(topic, payload, qos=2)
            return True
        except Exception as e:
            self.logger.error(f"Error publishing alert: {e}")
            return False

    def register_command_callback(self, command: str, callback: Callable):
        """Registra una callback per un comando specifico"""
        self.command_callbacks[command] = callback
        self.logger.info(f"Registered callback for command: {command}")