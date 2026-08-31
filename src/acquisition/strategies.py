"""
Strategy: cada método de captura implementa la misma interfaz
(fetch_new_images), así el resto del sistema no sabe ni le importa si las
imágenes vienen por Bluetooth, una carpeta compartida o una webcam.
"""
from abc import ABC, abstractmethod
from pathlib import Path
import shutil
import cv2

from PIL import Image, UnidentifiedImageError

from src.utils.config_loader import ConfigManager
from src.utils.logger import get_logger

log = get_logger(__name__)


class ImageAcquisitionStrategy(ABC):
    @abstractmethod
    def fetch_new_images(self) -> list[Path]:
        """Devuelve rutas a imágenes nuevas y válidas, listas para procesar."""
        raise NotImplementedError


class _ValidationMixin:
    """Lógica de validación compartida entre estrategias basadas en archivos."""

    def _is_valid_image(self, path: Path) -> bool:
        if path.stat().st_size == 0:
            log.warning(f"Imagen vacía descartada: {path.name}")
            return False
        try:
            with Image.open(path) as img:
                img.verify()
            return True
        except (UnidentifiedImageError, OSError) as e:
            log.warning(f"Imagen corrupta descartada: {path.name} ({e})")
            return False

    def _quarantine(self, path: Path, root: Path):
        q = root / "data" / "quarantine"
        q.mkdir(parents=True, exist_ok=True)
        shutil.move(str(path), str(q / path.name))


class BluetoothAcquisition(ImageAcquisitionStrategy, _ValidationMixin):
    """El SO deja las fotos transferidas por Bluetooth en una carpeta local;
    esta estrategia solo la vigila y valida lo que llega."""

    def fetch_new_images(self) -> list[Path]:
        config = ConfigManager()
        raw_dir = config.root / config.get("paths", "raw_images")
        raw_dir.mkdir(parents=True, exist_ok=True)
        allowed = set(config.get("acquisition", "allowed_extensions"))

        valid = []
        for path in raw_dir.iterdir():
            if path.suffix.lower() not in allowed:
                continue
            if self._is_valid_image(path):
                valid.append(path)
            else:
                self._quarantine(path, config.root)
        return valid


class FolderWatchAcquisition(BluetoothAcquisition):
    """Idéntica lógica a Bluetooth (vigilar carpeta); se separa como clase
    propia porque a futuro podría vigilar una carpeta de red o Drive."""
    pass


class WebcamAcquisition(ImageAcquisitionStrategy):
    """Para la fase de prueba (Semana 8): captura un frame directo de la
    webcam en vez de esperar que llegue un archivo."""

    def fetch_new_images(self) -> list[Path]:
        config = ConfigManager()
        raw_dir = config.root / config.get("paths", "raw_images")
        raw_dir.mkdir(parents=True, exist_ok=True)

        cam = cv2.VideoCapture(0)
        ok, frame = cam.read()
        cam.release()

        if not ok:
            log.error("No se pudo capturar frame de la webcam")
            return []

        from datetime import datetime
        filename = raw_dir / f"webcam_{datetime.now():%Y%m%d_%H%M%S}.jpg"
        cv2.imwrite(str(filename), frame)
        return [filename]


class AcquisitionFactory:
    """Factory Method: crea la estrategia correcta según config.yaml,
    sin que el código cliente conozca las clases concretas."""

    _strategies = {
        "bluetooth": BluetoothAcquisition,
        "folder_watch": FolderWatchAcquisition,
        "webcam": WebcamAcquisition,
    }

    @classmethod
    def create(cls) -> ImageAcquisitionStrategy:
        config = ConfigManager()
        method = config.get("acquisition", "method")
        strategy_cls = cls._strategies.get(method)
        if strategy_cls is None:
            raise ValueError(
                f"Método de adquisición desconocido: '{method}'. "
                f"Opciones válidas: {list(cls._strategies)}"
            )
        return strategy_cls()


# Uso:
# acquisition = AcquisitionFactory.create()   # lee config.yaml y decide
# images = acquisition.fetch_new_images()