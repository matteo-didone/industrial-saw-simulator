# edge-device/src/rest_api.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

class MaterialUpdate(BaseModel):
    material: str

class CommandRequest(BaseModel):
    command: str
    parameters: Optional[Dict[str, Any]] = None

class AlertResponse(BaseModel):
    type: str
    message: str
    severity: str
    timestamp: datetime
    active: bool

class APIServer:
    def __init__(self, opcua_client, mqtt_handler, data_processor):
        self.app = FastAPI(title="Saw Edge Device API")
        self.opcua_client = opcua_client
        self.mqtt_handler = mqtt_handler
        self.data_processor = data_processor
        self.logger = logging.getLogger(__name__)
        
        self._setup_cors()
        self._setup_routes()

    def _setup_cors(self):
        """Configura CORS per l'API"""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Configura le route dell'API"""
        @self.app.get("/")
        async def root():
            return {
                "message": "Saw Edge Device API",
                "status": "running",
                "timestamp": datetime.now()
            }

        @self.app.get("/state")
        async def get_state():
            """Ottiene lo stato corrente della segatrice"""
            try:
                state = await self.opcua_client.read_values()
                self.mqtt_handler.publish_state(state)
                return {
                    "status": "success",
                    "data": state,
                    "timestamp": datetime.now()
                }
            except Exception as e:
                self.logger.error(f"Error reading state: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/metrics")
        async def get_metrics():
            """Ottiene le metriche elaborate"""
            try:
                metrics = self.data_processor.get_metrics()
                self.mqtt_handler.publish_metrics(metrics)
                return {
                    "status": "success",
                    "data": metrics,
                    "timestamp": datetime.now()
                }
            except Exception as e:
                self.logger.error(f"Error getting metrics: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/command")
        async def execute_command(request: CommandRequest):
            """Esegue un comando sulla segatrice"""
            try:
                # Log del comando ricevuto
                self.logger.info(f"Received command request: {request.command} with parameters: {request.parameters}")
                
                success = False
                command_executed = False
                
                if request.command == "start":
                    self.logger.info("Attempting start command...")
                    success = await self.opcua_client.start_saw()
                    command_executed = True
                    
                elif request.command == "stop":
                    self.logger.info("Attempting stop command...")
                    success = await self.opcua_client.stop_saw()
                    command_executed = True
                    
                elif request.command == "pause":
                    self.logger.info("Attempting pause command...")
                    success = await self.opcua_client.pause_saw()
                    command_executed = True
                    
                elif request.command == "reset":
                    self.logger.info("Attempting reset command...")
                    success = await self.opcua_client.reset_saw()
                    command_executed = True
                    
                elif request.command == "toggle_barrier":
                    self.logger.info("Attempting toggle barrier command...")
                    success = await self.opcua_client.toggle_barrier()
                    command_executed = True
                    
                elif request.command == "set_material":
                    if not request.parameters or "material" not in request.parameters:
                        error_msg = "Material parameter is required"
                        self.logger.error(error_msg)
                        raise HTTPException(status_code=400, detail=error_msg)
                    
                    material = request.parameters["material"]
                    valid_materials = ["steel", "aluminum", "wood"]
                    material_name = material.lower()

                    if material_name not in valid_materials:
                        error_msg = f"Invalid material. Must be one of: {valid_materials}"
                        self.logger.error(error_msg)
                        raise HTTPException(status_code=400, detail=error_msg)
                    
                    self.logger.info(f"Attempting to set material to: {material_name}")
                    success = await self.opcua_client.set_material(material_name)
                    command_executed = True
                    
                else:
                    error_msg = f"Unknown command: {request.command}"
                    self.logger.error(error_msg)
                    raise HTTPException(status_code=400, detail=error_msg)

                if not command_executed:
                    error_msg = f"Command {request.command} was not executed"
                    self.logger.error(error_msg)
                    raise HTTPException(status_code=500, detail=error_msg)

                self.logger.info(f"Command {request.command} execution result: {success}")

                if success:
                    # Pubblica l'esecuzione del comando su MQTT
                    self.mqtt_handler.publish_state({
                        "command_executed": request.command,
                        "timestamp": datetime.now().isoformat()
                    })
                    return {
                        "status": "success",
                        "message": f"Command {request.command} executed successfully"
                    }
                else:
                    error_msg = f"Command {request.command} failed to execute"
                    self.logger.error(error_msg)
                    raise HTTPException(status_code=500, detail=error_msg)

            except HTTPException:
                raise
            except Exception as e:
                error_msg = f"Error executing command {request.command}: {str(e)}"
                self.logger.error(error_msg, exc_info=True)
                raise HTTPException(status_code=500, detail=error_msg)

        @self.app.get("/alerts")
        async def get_alerts():
            """Ottiene gli alert attivi"""
            try:
                alerts = self.data_processor.get_active_alerts()
                return {
                    "status": "success",
                    "data": [
                        AlertResponse(
                            type=alert.type,
                            message=alert.message,
                            severity=alert.severity.value,
                            timestamp=alert.timestamp,
                            active=alert.active
                        ) for alert in alerts
                    ],
                    "timestamp": datetime.now()
                }
            except Exception as e:
                self.logger.error(f"Error getting alerts: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/alerts/history")
        async def get_alert_history(hours: int = 24):
            """Ottiene lo storico degli alert"""
            try:
                alerts = self.data_processor.get_alert_history(hours)
                return {
                    "status": "success",
                    "data": [
                        AlertResponse(
                            type=alert.type,
                            message=alert.message,
                            severity=alert.severity.value,
                            timestamp=alert.timestamp,
                            active=alert.active
                        ) for alert in alerts
                    ],
                    "timestamp": datetime.now()
                }
            except Exception as e:
                self.logger.error(f"Error getting alert history: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

    def get_app(self):
        """Restituisce l'applicazione FastAPI"""
        return self.app