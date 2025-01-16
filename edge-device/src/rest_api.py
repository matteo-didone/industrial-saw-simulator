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
                self.logger.error(f"Error reading state: {e}")
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
                self.logger.error(f"Error getting metrics: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/command")
        async def execute_command(request: CommandRequest):
            """Esegue un comando sulla segatrice"""
            try:
                success = False
                
                # Log del comando ricevuto
                self.logger.info(f"Received command: {request.command} with parameters: {request.parameters}")
                
                if request.command == "start":
                    success = await self.opcua_client.start_saw()
                elif request.command == "stop":
                    success = await self.opcua_client.stop_saw()
                elif request.command == "pause":
                    success = await self.opcua_client.pause_saw()
                elif request.command == "reset":
                    success = await self.opcua_client.reset_saw()
                elif request.command == "toggle_barrier":
                    success = await self.opcua_client.toggle_barrier()
                elif request.command == "set_material":
                    if not request.parameters or "material" not in request.parameters:
                        self.logger.error("Missing material parameter")
                        raise HTTPException(
                            status_code=400,
                            detail="Material parameter is required"
                        )
                    
                    material = request.parameters["material"]
                    valid_materials = ["Steel", "Aluminum", "Wood"]
                    material_name = material.title()  # Capitalizza la prima lettera

                    if material_name not in valid_materials:
                        self.logger.error(f"Invalid material: {material}")
                        raise HTTPException(
                            status_code=400,
                            detail=f"Invalid material. Must be one of: {valid_materials}"
                        )
                    
                    self.logger.info(f"Setting material to: {material_name}")
                    success = await self.opcua_client.set_material(material_name)
                    self.logger.info(f"Set material result: {success}")
                    
                    if success:
                        self.mqtt_handler.publish_state({
                            "material_changed": material_name,
                            "timestamp": datetime.now().isoformat()
                        })
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unknown command: {request.command}"
                    )

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
                    raise HTTPException(
                        status_code=500,
                        detail=f"Command {request.command} failed to execute"
                    )

            except HTTPException:
                raise
            except Exception as e:
                self.logger.error(f"Error executing command: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/material")
        async def set_material(material_update: MaterialUpdate):
            """Imposta il materiale da tagliare"""
            try:
                material_name = material_update.material.title()
                success = await self.opcua_client.set_material(material_name)
                if success:
                    self.mqtt_handler.publish_state({
                        "material_changed": material_name,
                        "timestamp": datetime.now().isoformat()
                    })
                    return {
                        "status": "success",
                        "message": f"Material set to {material_name}"
                    }
                else:
                    raise HTTPException(
                        status_code=500,
                        detail="Failed to set material"
                    )
            except Exception as e:
                self.logger.error(f"Error setting material: {e}")
                raise HTTPException(status_code=500, detail=str(e))

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
                self.logger.error(f"Error getting alerts: {e}")
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
                self.logger.error(f"Error getting alert history: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def get_app(self):
        """Restituisce l'applicazione FastAPI"""
        return self.app