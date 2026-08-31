"""
Módulo 2 — Preprocesamiento de imágenes.

Redimensiona, normaliza y corrige iluminación antes de pasar la imagen al
modelo YOLOv8. Cada función es pura (no modifica archivos en disco), para
que sea fácil de testear de forma aislada.
"""

import cv2
import numpy as np
from pathlib import Path

from src.config_loader import ConfigManager
from src.utils.logger import get_logger

log = get_logger(__name__)

class ImagePreprocessingError(Exception):
    """ Error especifico del modulo, para distinguirlo de errores genericos de OpenCV/IO
    mas abajo en el stack"""
    pass

def load_image(image_path: Path) -> np.ndarray:
    """ Carga la imagen desde disco. Ya llega validada por el Módulo 1, pero igual
        se verifica aqui por si el archivo se corrumpio entre que se valido y se proceso
    """
    image = cv2.imread(str(image_path))
    if image is None:
        raise ImagePreprocessingError(
            f"No se puede leer la imagen (formato o archivo dañado): {image_path.name}"
        )
    return image

def resize_image(image: np.ndarray, target_size: int) -> np.ndarray:
    """
    Redimensiona manteniendo proporción y rellenando con padding gris
    (letterbox), que es el enfoque estándar para YOLOv8 — evita distorsionar
    la imagen y así no deforma el tamaño real de casco/chaleco/arnés.
    """
    h, w = image.shape[:2]
    scale = target_size / max(h, w)
    new_w, new_h = int(w * scale), int(h* scale)

    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    canvas = np.full((target_size, target_size, 3), 114, dtype=np.uint8)
    top = (target_size - new_h) // 2
    left = (target_size - new_w) //2
    canvas[top:top + new_h, left:left + new_w] = resized

    return canvas

def correct_lighting(image: np.ndarray) -> np.ndarray:
    """
    Ecualización adaptativa de histograma (CLAHE) sobre el canal de
    luminosidad. Ayuda en obra, donde la iluminación varía mucho entre
    zonas con sol directo y zonas en sombra — justo la condición que la
    propia tesis identifica como crítica.
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_corrected = clahe.apply(l)

    corrected = cv2.merge((l_corrected, a, b))
    return cv2.cvtColor(corrected, cv2.COLOR_LAB2BGR)

def preprocess_image(image_path: Path) -> np.ndarray:
    """
    Pipeline de preprocesamiento completo para una sola imagen.
    Punto de entrada usado por PreprocessingStage.
    """
    try:
        config = ConfigManager()
        img_size = config.get("training", "img_size", default=640)
        image = load_image(image_path)
        image = correct_lighting(image)
        return resize_image(image, img_size)
    except ImagePreprocessingError as e:
        log.error(f"Preprocesamiento fallo para {image_path.name}: {e}")
        raise
    except Exception as e:
        log.error(f"Error inesperado preprocesando {image_path.name}: {e}")
        raise ImagePreprocessingError(str(e)) from e