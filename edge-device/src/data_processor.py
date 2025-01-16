from collections import deque
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import logging
from dataclasses import dataclass
from enum import Enum
import statistics

class AlertSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

@dataclass
class Alert:
    type: str
    message: str
    severity: AlertSeverity
    timestamp: datetime
    active: bool = True

class DataProcessor:
    def __init__(self, window_size: int = 60):
        """
        Inizializza il processore dati
        :param window_size: Dimensione della finestra per le metriche in secondi
        """
        self.window_size = window_size
        self.logger = logging.getLogger(__name__)
        
        # Code circolari per dati storici (ultimi 60 secondi)
        self.power_history = deque(maxlen=window_size)
        self.speed_history = deque(maxlen=window_size)
        self.temperature_history = deque(maxlen=window_size)
        
        # Metriche aggregate
        self.hourly_pieces = 0
        self.last_hour_reset = datetime.now()
        
        # Soglie per allarmi
        self.thresholds = {
            "temperature": {
                "warning": 40.0,
                "critical": 50.0
            },
            "blade_wear": {
                "warning": 70.0,
                "critical": 90.0
            },
            "power_consumption": {
                "warning": 8.0,  # kW
                "critical": 10.0  # kW
            }
        }
        
        # Alert attivi e storico
        self.active_alerts: List[Alert] = []
        self.alert_history: List[Alert] = []

    def process_state(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Processa lo stato corrente e calcola le metriche
        """
        try:
            current_time = datetime.now()

            # Debug log
            self.logger.debug(f"Processing state: {state}")
            
            # Aggiorna lo storico con i nomi delle variabili del simulatore
            self.power_history.append((current_time, state["powerconsumption"]))
            self.speed_history.append((current_time, state["cuttingspeed"]))
            self.temperature_history.append((current_time, state["temperature"]))
            
            # Resetta contatore pezzi orario se necessario
            if current_time - self.last_hour_reset > timedelta(hours=1):
                self.hourly_pieces = 0
                self.last_hour_reset = current_time
            
            # Aggiorna il conteggio orario
            self.hourly_pieces = state["piecescut"]
            
            # Controlla le condizioni di allarme
            self._check_alerts(state)
            
            # Calcola le metriche
            return self._calculate_metrics()
            
        except Exception as e:
            self.logger.error(f"Error processing state: {e}")
            self.logger.error(f"Available state keys: {list(state.keys())}")
            raise

    def _calculate_metrics(self) -> Dict[str, Any]:
        """
        Calcola le metriche aggregate
        """
        current_time = datetime.now()
        window_start = current_time - timedelta(seconds=self.window_size)
        
        # Filtra i dati nella finestra temporale
        recent_power = [p[1] for p in self.power_history 
                       if p[0] > window_start]
        recent_speed = [s[1] for s in self.speed_history 
                       if s[0] > window_start]
        recent_temp = [t[1] for t in self.temperature_history 
                      if t[0] > window_start]
        
        metrics = {
            "powerconsumption": {
                "current": recent_power[-1] if recent_power else 0,
                "avg_1min": statistics.mean(recent_power) if recent_power else 0,
                "max_1min": max(recent_power) if recent_power else 0,
                "min_1min": min(recent_power) if recent_power else 0
            },
            "cuttingspeed": {
                "current": recent_speed[-1] if recent_speed else 0,
                "avg_1min": statistics.mean(recent_speed) if recent_speed else 0,
                "max_1min": max(recent_speed) if recent_speed else 0,
                "min_1min": min(recent_speed) if recent_speed else 0
            },
            "temperature": {
                "current": recent_temp[-1] if recent_temp else 0,
                "avg_1min": statistics.mean(recent_temp) if recent_temp else 0,
                "max_1min": max(recent_temp) if recent_temp else 0,
                "min_1min": min(recent_temp) if recent_temp else 0
            },
            "production": {
                "hourly_rate": self.hourly_pieces
            }
        }
        
        return metrics

    def _check_alerts(self, state: Dict[str, Any]):
        """
        Controlla le condizioni per generare alert
        """
        # Controllo temperatura
        temp = state["temperature"]
        if temp > self.thresholds["temperature"]["critical"]:
            self._add_alert(
                "high_temperature",
                f"Temperature critically high: {temp:.1f}°C",
                AlertSeverity.CRITICAL
            )
        elif temp > self.thresholds["temperature"]["warning"]:
            self._add_alert(
                "elevated_temperature",
                f"Temperature elevated: {temp:.1f}°C",
                AlertSeverity.WARNING
            )
        else:
            self._clear_alert("high_temperature")
            self._clear_alert("elevated_temperature")
        
        # Controllo usura lama
        wear = state["bladewear"]
        if wear > self.thresholds["blade_wear"]["critical"]:
            self._add_alert(
                "blade_critical",
                "Blade wear critical, replacement needed",
                AlertSeverity.CRITICAL
            )
        elif wear > self.thresholds["blade_wear"]["warning"]:
            self._add_alert(
                "blade_warning",
                "Blade wear high, plan replacement",
                AlertSeverity.WARNING
            )
        
        # Controllo consumo energetico
        power = state["powerconsumption"]
        if power > self.thresholds["power_consumption"]["critical"]:
            self._add_alert(
                "high_power_consumption",
                f"Critical power consumption: {power:.1f} kW",
                AlertSeverity.CRITICAL
            )
        elif power > self.thresholds["power_consumption"]["warning"]:
            self._add_alert(
                "elevated_power_consumption",
                f"High power consumption: {power:.1f} kW",
                AlertSeverity.WARNING
            )
        
        # Controllo stato sicurezza
        if not state["safetybarrier"] and state["state"] == "running":
            self._add_alert(
                "safety_violation",
                "Machine running with safety barrier open",
                AlertSeverity.CRITICAL
            )

    def _add_alert(self, alert_type: str, message: str, severity: AlertSeverity):
        """Aggiunge un nuovo alert se non ne esiste già uno attivo dello stesso tipo"""
        existing = next((a for a in self.active_alerts if a.type == alert_type), None)
        
        if not existing:
            alert = Alert(
                type=alert_type,
                message=message,
                severity=severity,
                timestamp=datetime.now()
            )
            self.active_alerts.append(alert)
            self.alert_history.append(alert)
            self.logger.warning(f"New alert: {message}")

    def _clear_alert(self, alert_type: str):
        """Disattiva un alert specifico"""
        for alert in self.active_alerts:
            if alert.type == alert_type:
                alert.active = False
                self.active_alerts.remove(alert)
                self.logger.info(f"Alert cleared: {alert.type}")

    def get_active_alerts(self) -> List[Alert]:
        """Restituisce gli alert attivi"""
        return self.active_alerts

    def get_alert_history(self, hours: int = 24) -> List[Alert]:
        """Restituisce lo storico degli alert"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [a for a in self.alert_history if a.timestamp > cutoff]

    def get_metrics(self) -> Dict[str, Any]:
        """Restituisce tutte le metriche correnti"""
        return self._calculate_metrics()