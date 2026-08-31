"""
Pruebas de arquitectura: no validan el modelo (aún no existe), validan que
las piezas del diseño encajen correctamente entre sí.
"""
import numpy as np
from src.utils.config_loader import ConfigMnager
from src.pipeline import DetectionPipeline, PipelineStage
from src.reporting.observers import DetectionSubject, DetectionObserver
from src.inference.detector import DummyDetector


def test_config_is_singleton():
    """Dos instancias de ConfigManager deben ser el mismo objeto."""
    c1 = ConfigManager()
    c2 = ConfigManager()
    assert c1 is c2

def test_dummy_detector_returns_valid_format():
    detector = DummyDetector()
    fake_image = np.zeros((640, 640, 3), dtype=np.uint8)
    detections = detector.predict(fake_image)
    assert isinstance(detections, list)
    assert "class_name" in detections[0]
    assert "confidence" in detections[0]


def test_observer_notifies_all_subscribers():
    """Verifica que el patrón Observer llegue a TODOS los suscriptores,
    no solo al primero."""
    calls = []

    class SpyObserver(DetectionObserver):
        def on_detection(self, detection, image_path):
            calls.append(detection)

    subject = DetectionSubject()
    subject.subscribe(SpyObserver())
    subject.subscribe(SpyObserver())

    subject.notify({"class_name": "chaleco_ausente"}, image_path="fake.jpg")
    assert len(calls) == 2  # ambos observers recibieron la notificación


def test_pipeline_runs_stages_in_order():
    """Verifica que el Pipeline ejecute las etapas en el orden dado,
    acumulando el contexto correctamente."""
    order = []

    class StageA(PipelineStage):
        def process(self, context):
            order.append("A")
            context["a"] = True
            return context

    class StageB(PipelineStage):
        def process(self, context):
            order.append("B")
            assert context["a"] is True  # confirma que StageA corrió antes
            return context

    pipeline = DetectionPipeline([StageA(), StageB()])
    pipeline.run(image_path="fake.jpg")
    assert order == ["A", "B"]