"""
Interfaz del detector — se define ahora (arquitectura), se implementa con
el modelo real más adelante (Módulo 6, semanas 5-8).

Definir la interfaz aquí permite que InferenceStage y el resto del pipeline
se construyan y prueben YA, sin depender de tener un modelo entrenado.
"""
from abc import ABC, abstractmethod
import numpy as np


class Detector(ABC):
    @abstractmethod
    def predict(self, image: np.ndarray) -> list[dict]:
        """
        Debe devolver una lista de detecciones, cada una como:
        {"class_name": str, "confidence": float, "bbox": [x1, y1, x2, y2]}
        """
        raise NotImplementedError


class DummyDetector(Detector):
    """Implementación falsa para poder correr y probar todo el pipeline
    (adquisición → preprocesamiento → inferencia → reporte) antes de tener
    el modelo YOLOv8 entrenado. Se reemplaza por YOLOv8Detector en S5-S8."""

    def predict(self, image: np.ndarray) -> list[dict]:
        return [{"class_name": "casco_ausente", "confidence": 0.87, "bbox": [10, 10, 100, 100]}]


class YOLOv8Detector(Detector):
    """Implementación real — se activa cuando exista el modelo entrenado
    (models/yolov8_epp_latest.pt). Placeholder por ahora."""

    def __init__(self, weights_path=None):
        from src.utils.config_loader import ConfigManager
        config = ConfigManager()
        self.weights_path = weights_path or (config.root / config.get("model", "weights_file"))
        self.threshold = config.get("model", "confidence_threshold", default=0.5)
        self._model = None  # carga perezosa (lazy load) — no carga el modelo hasta el primer uso

    def _load(self):
        if self._model is None:
            from ultralytics import YOLO
            if not self.weights_path.exists():
                raise FileNotFoundError(
                    f"Modelo no encontrado en {self.weights_path}. "
                    f"Entrena primero (Módulo 4) o usa DummyDetector mientras tanto."
                )
            self._model = YOLO(str(self.weights_path))

    def predict(self, image: np.ndarray) -> list[dict]:
        self._load()
        results = self._model.predict(image, conf=self.threshold, verbose=False)
        detections = []
        for r in results:
            for box in r.boxes:
                detections.append({
                    "class_name": self._model.names[int(box.cls)],
                    "confidence": float(box.conf),
                    "bbox": box.xyxy[0].tolist(),
                })
        return detections