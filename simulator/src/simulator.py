# simulator/src/simulator.py
from dataclasses import dataclass
from enum import Enum
import random
import time
from typing import Optional

class MachineState(Enum):
    INACTIVE = "inactive"
    RUNNING = "running"
    PAUSED = "paused"
    ALARM = "alarm"
    ERROR = "error"

@dataclass
class MaterialType:
    name: str
    max_cutting_speed: float
    power_consumption_factor: float

class IndustrialSawSimulator:
    def __init__(self):
        self.state = MachineState.INACTIVE
        self.cutting_speed = 0.0
        self.pieces_cut = 0
        self.power_consumption = 0.0
        self.temperature = 20.0
        self.safety_barrier = True
        self.blade_wear = 0.0
        
        self.materials = {
            "steel": MaterialType("Steel", 30.0, 1.5),
            "aluminum": MaterialType("Aluminum", 50.0, 1.0),
            "wood": MaterialType("Wood", 80.0, 0.8)
        }
        self.current_material = self.materials["steel"]
        
        self.anomaly_chance = 0.01
        self.last_update = time.time()

    def start(self):
        if self.state in [MachineState.INACTIVE, MachineState.PAUSED] and self.safety_barrier:
            self.state = MachineState.RUNNING
            self._update_cutting_speed()
            return True
        return False

    def stop(self):
        if self.state in [MachineState.RUNNING, MachineState.PAUSED]:
            self.state = MachineState.INACTIVE
            self.cutting_speed = 0
            self.power_consumption = 0.1
            return True
        return False

    def pause(self):
        if self.state == MachineState.RUNNING:
            self.state = MachineState.PAUSED
            self.cutting_speed = 0
            self.power_consumption *= 0.2
            return True
        return False

    def reset(self):
        """Resetta la macchina dallo stato di allarme o errore"""
        if self.state in [MachineState.ALARM, MachineState.ERROR]:
            self.state = MachineState.INACTIVE
            self.cutting_speed = 0
            self.power_consumption = 0.1
            self.temperature = 20.0
            return True
        return False

    def set_material(self, material_name: str) -> bool:
        """Imposta il materiale da tagliare"""
        material_key = material_name.lower()
        if material_key in self.materials:
            self.current_material = self.materials[material_key]
            if self.state == MachineState.RUNNING:
                self._update_cutting_speed()
            return True
        return False

    def toggle_safety_barrier(self) -> bool:
        """Attiva/disattiva la barriera di sicurezza"""
        try:
            # Controlla lo stato corrente
            current_state = self.state
            
            # Cambia lo stato della barriera
            self.safety_barrier = not self.safety_barrier
            
            # Se la macchina è in funzione e la barriera viene aperta
            if not self.safety_barrier and current_state == MachineState.RUNNING:
                self.state = MachineState.ALARM
                self.cutting_speed = 0
                self.power_consumption = 0.1
            
            return True
            
        except Exception:
            return False

    def _update_cutting_speed(self):
        if self.state == MachineState.RUNNING:
            max_speed = self.current_material.max_cutting_speed
            self.cutting_speed = max_speed * (0.9 + random.random() * 0.2)
            self._update_power_consumption()

    def _update_power_consumption(self):
        base_power = 2.0
        if self.state == MachineState.RUNNING:
            speed_factor = self.cutting_speed / self.current_material.max_cutting_speed
            material_factor = self.current_material.power_consumption_factor
            wear_factor = 1 + (self.blade_wear / 100) * 0.5
            
            self.power_consumption = (
                base_power + 
                (speed_factor * 5) * 
                material_factor * 
                wear_factor
            )

    def simulate_step(self, dt: float):
        """Simula un passo temporale"""
        if self.state == MachineState.RUNNING:
            pieces_probability = (self.cutting_speed * dt) / 60
            if random.random() < pieces_probability:
                self.pieces_cut += 1
            
            self.blade_wear += (self.cutting_speed * dt) / 1000
            self.temperature = 20 + (self.power_consumption * 2) + random.uniform(-0.5, 0.5)
            
            if random.random() < self.anomaly_chance:
                self._simulate_anomaly()

    def _simulate_anomaly(self):
        anomaly_type = random.choice([
            'temperature_spike',
            'power_surge',
            'speed_fluctuation',
            'error_state'
        ])
        
        if anomaly_type == 'temperature_spike':
            self.temperature += random.uniform(10, 20)
        elif anomaly_type == 'power_surge':
            self.power_consumption *= random.uniform(1.5, 2.0)
        elif anomaly_type == 'speed_fluctuation':
            self.cutting_speed *= random.uniform(0.5, 1.5)
        elif anomaly_type == 'error_state':
            self.state = MachineState.ERROR

    def get_state(self):
        return {
            "state": self.state.value,
            "cutting_speed": self.cutting_speed,
            "pieces_cut": self.pieces_cut,
            "power_consumption": self.power_consumption,
            "temperature": self.temperature,
            "safety_barrier": self.safety_barrier,
            "blade_wear": self.blade_wear,
            "current_material": self.current_material.name
        }