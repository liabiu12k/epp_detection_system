"""
Punto de entrada del sistema. Conecta todos los módulos usando los
patrones definidos en la arquitectura:
  - ConfigManager (Singleton)
  - AcquisitionFactory (Strategy + Factory Method)
  - DetectionPipeline (Pipeline)
  - DetectionSubject (Observer)
  - Inyección de dependencias en cada etapa

Mientras no exista el modelo entrenado, usa DummyDetector para poder
correr y probar el sistema completo end-to-end.
"""
from src.acquisition.strategies import AcquisitionFactory
from src.pipeline import DectectionPipeline, PreprocessingStage, InferenceStage, ReportingStage
from src.reporting.observers import DectecionSubject, ExcelReportObserver, EvidenceImageObserver
from src.inference.detector import DummyDetector, YOLOv8Detector
from src.utils.config_loader import ConfigManager
from src.utils.logger import get_logger 

log = get_logger(__name__)

def build_pipeline(use_real_model: bool = False) -> DetectionPipeline:
    subject = DeteectionSubject()
    subject.subscribe(ExcelReportObserver())
    subject.subscribe(EvidenceImageObserver())

    detector = YOLOv8Detector() if use_real_model else DummyDetector()

    return DetectionPipeline([
        PreprocessingStage(),
        InferenceStage(detector=detector),
        ReportingStage(subject=subject),
    ])

def main():
    config = ConfigManager()
    log.info("Sistema de detección de EPP iniciado")

    # Aún sin modelo entrenado (eso es S5-S8) -> use_real_model=False
    pipeline = build_pipeline(use_real_model=False)
    acquisition = AcquisitionFactory.create()

    images = acquisition.fetch_new_images()
    if not images:
        log.info("Sin images nuevas por procesar")
        return

    for image_path in images:
        try:
            pipeline.run(image_path)
        except Exception as e:
            log.error(f"Error al procesar imagen {image_path}: {e}")

if __name__ == "__main__":
    main()

