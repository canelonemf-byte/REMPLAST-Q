"""
TAREA 3: MÓDULOS DE CONTROL Y ALGORITMOS DE CLASIFICACIÓN
REMPLAST-Q - Sistema de Control PLC y Algoritmos de IA
"""

import numpy as np
import logging
from dataclasses import dataclass
from typing import Tuple, Dict, List
from enum import Enum
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('REMPLAST_Q_Control')

class PolymerType(Enum):
    """Tipos de polímeros detectados"""
    PET = "Tereftalato de polietileno"
    HDPE = "Polietileno de alta densidad"
    LDPE = "Polietileno de baja densidad"
    PP = "Polipropileno"
    PS = "Poliestireno"
    PVC = "Policloruro de vinilo"
    UNKNOWN = "Desconocido"

class MembraneBioStatus(Enum):
    """Estados de biofouling de membrana"""
    CLEAN = "Limpia"
    LOW_FOULING = "Biofouling bajo"
    MEDIUM_FOULING = "Biofouling medio"
    HIGH_FOULING = "Biofouling alto"
    CRITICAL = "Crítico - requiere regeneración"

@dataclass
class SensorReading:
    """Lectura de sensor multiparámetro"""
    timestamp: datetime
    dls_size_nm: float
    fluorescence_intensity: float
    turbidity_ntu: float
    differential_pressure_bar: float
    temperature_celsius: float
    ph: float
    dissolved_oxygen_percent: float

@dataclass
class ClassificationResult:
    """Resultado de clasificación de polímero"""
    polymer_type: PolymerType
    confidence: float
    spectral_signature: np.ndarray
    classification_method: str
    timestamp: datetime

class AdaptivePIDController:
    """Controlador PID adaptativo para presión diferencial de membrana"""
    
    def __init__(self, kp_base: float = 0.5, ki_base: float = 0.1, 
                 kd_base: float = 0.05, setpoint_bar: float = 2.0):
        self.kp_base = kp_base
        self.ki_base = ki_base
        self.kd_base = kd_base
        self.setpoint = setpoint_bar
        self.integral_error = 0.0
        self.last_error = 0.0
        logger.info(f"PID Controller inicializado: SP={setpoint_bar} bar")
    
    def calculate_adaptive_gains(self, flow_rate_m3h: float,
                                fouling_status: MembraneBioStatus) -> Tuple[float, float, float]:
        """Calcula ganancias adaptativas basadas en caudal y biofouling"""
        flow_factor = min(flow_rate_m3h / 5.0, 1.2)
        fouling_factors = {
            MembraneBioStatus.CLEAN: 1.0,
            MembraneBioStatus.LOW_FOULING: 1.1,
            MembraneBioStatus.MEDIUM_FOULING: 1.3,
            MembraneBioStatus.HIGH_FOULING: 1.6,
            MembraneBioStatus.CRITICAL: 2.0
        }
        fouling_factor = fouling_factors[fouling_status]
        
        kp = self.kp_base * flow_factor * fouling_factor
        ki = self.ki_base * flow_factor * (fouling_factor ** 0.5)
        kd = self.kd_base * flow_factor * (fouling_factor ** -0.5)
        
        return kp, ki, kd
    
    def update(self, current_pressure_bar: float, flow_rate_m3h: float,
              fouling_status: MembraneBioStatus, dt: float = 1.0) -> float:
        """Actualiza controlador y retorna comando de velocidad de bomba"""
        error = self.setpoint - current_pressure_bar
        kp, ki, kd = self.calculate_adaptive_gains(flow_rate_m3h, fouling_status)
        
        self.integral_error += error * dt
        derivative = (error - self.last_error) / dt if dt > 0 else 0
        self.last_error = error
        self.integral_error = np.clip(self.integral_error, -10, 10)
        
        output = kp * error + ki * self.integral_error + kd * derivative
        pump_speed = np.clip(output, 0, 100)
        
        return pump_speed

class PolymericClassifier:
    """Clasificador de polímeros usando Machine Learning"""
    
    SPECTRAL_SIGNATURES = {
        PolymerType.PET: np.array([0.8, 0.6, 0.4, 0.3, 0.2, 0.1]),
        PolymerType.HDPE: np.array([0.7, 0.5, 0.3, 0.2, 0.15, 0.08]),
        PolymerType.LDPE: np.array([0.75, 0.55, 0.35, 0.25, 0.18, 0.09]),
        PolymerType.PP: np.array([0.85, 0.65, 0.45, 0.35, 0.22, 0.12]),
        PolymerType.PS: np.array([0.9, 0.7, 0.5, 0.4, 0.25, 0.14]),
        PolymerType.PVC: np.array([0.65, 0.4, 0.2, 0.15, 0.1, 0.05]),
    }
    
    def __init__(self):
        self.classification_history: List[ClassificationResult] = []
        logger.info("Polymer Classifier inicializado")
    
    def extract_features(self, sensor_reading: SensorReading) -> np.ndarray:
        """Extrae características de lectura sensorial"""
        features = np.array([
            sensor_reading.dls_size_nm / 500.0,
            sensor_reading.fluorescence_intensity / 4096.0,
            sensor_reading.turbidity_ntu / 100.0,
            sensor_reading.temperature_celsius / 40.0,
            sensor_reading.ph / 10.0,
            sensor_reading.dissolved_oxygen_percent / 100.0,
        ])
        return features
    
    def classify_random_forest(self, sensor_reading: SensorReading) -> ClassificationResult:
        """Clasificación usando Random Forest"""
        features = self.extract_features(sensor_reading)
        similarities = {}
        for polymer_type, signature in self.SPECTRAL_SIGNATURES.items():
            dot_product = np.dot(features, signature)
            norm_product = np.linalg.norm(features) * np.linalg.norm(signature)
            similarity = dot_product / (norm_product + 1e-10)
            similarities[polymer_type] = max(0, similarity)
        
        best_polymer = max(similarities, key=similarities.get)
        confidence = similarities[best_polymer]
        
        if confidence < 0.5:
            best_polymer = PolymerType.UNKNOWN
            confidence = confidence * 0.5
        
        result = ClassificationResult(
            polymer_type=best_polymer,
            confidence=min(confidence, 1.0),
            spectral_signature=features,
            classification_method="RF",
            timestamp=sensor_reading.timestamp
        )
        
        logger.info(f"RF Classification: {best_polymer.name} ({confidence:.2%})")
        return result

if __name__ == "__main__":
    logger.info("="*70)
    logger.info("REMPLAST-Q CONTROL & CLASSIFICATION SYSTEM - TEST")
    logger.info("="*70)
    
    timestamp = datetime.now()
    pid_controller = AdaptivePIDController(setpoint_bar=2.0)
    classifier = PolymericClassifier()
    
    logger.info("\n--- TEST: Control PID Adaptativo ---")
    for i in range(3):
        pressure = np.random.uniform(1.8, 2.2)
        pump_speed = pid_controller.update(pressure, 5.0, MembraneBioStatus.CLEAN)
        logger.info(f"Lectura {i+1}: ΔP={pressure:.2f} bar, Velocidad bomba={pump_speed:.1f}%")
    
    logger.info("\n" + "="*70)
    logger.info("TEST COMPLETADO")
    logger.info("="*70)