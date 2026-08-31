"""
Módulo 1 — Adquisición de imágenes.

Modo de operación: captura por lotes (no streaming continuo).
Vigila una carpeta donde llegan las fotos transferidas por Bluetooth desde la
cámara, valida cada imagen y la deja lista para el resto del pipeline.
"""

import shutil
import time
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from src.utils.config_loader import load_config, get_proyect_root
from src.utils.logger import get_logger

log = get_logger(__name__)

def is_valid_image(path: Path) -> bool:
    """
    Verifica que el archivo sea una imagen legible y no esté corrupto/vacío.
    Una foto mala nunca debe tumbar el resto del pipeline.
    """
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


def fetch_new_images() -> list[Path]:
    """
    Revisa la carpeta de llegada (data/raw) y devuelve las imágenes nuevas y
    válidas, con extensión permitida según config.yaml.
    """
    cfg = load_config()
    root = get_project_root()
    raw_dir = root / cfg["paths"]["raw_images"]
    raw_dir.mkdir(parents=True, exist_ok=True)

    allowed_ext = set(cfg["acquisition"]["allowed_extensions"])
    candidates = [p for p in raw_dir.iterdir() if p.suffix.lower() in allowed_ext]

    valid_images = []
    for path in candidates:
        if is_valid_image(path):
            valid_images.append(path)
        else:
            _quarantine(path, root)

    if valid_images:
        log.info(f"{len(valid_images)} imagen(es) nueva(s) lista(s) para procesar")

    return valid_images


def _quarantine(path: Path, root: Path):
    """Mueve archivos inválidos a una carpeta aparte en vez de borrarlos,
    por si se necesita revisar después por qué fallaron."""
    quarantine_dir = root / "data" / "quarantine"
    quarantine_dir.mkdir(parents=True, exist_ok=True)
    try:
        shutil.move(str(path), str(quarantine_dir / path.name))
    except OSError as e:
        log.error(f"No se pudo poner en cuarentena {path.name}: {e}")


def mark_as_processed(path: Path):
    """Mueve una imagen ya procesada, para no volver a analizarla si el
    sistema se reinicia (idempotencia)."""
    cfg = load_config()
    root = get_project_root()
    processed_dir = root / cfg["paths"]["processed_images"]
    processed_dir.mkdir(parents=True, exist_ok=True)
    shutil.move(str(path), str(processed_dir / path.name))


def watch_loop(on_new_images):
    """
    Bucle principal: revisa periódicamente si llegaron fotos nuevas.
    on_new_images: función callback que recibe la lista de rutas válidas.
    """
    cfg = load_config()
    interval = cfg["acquisition"]["poll_interval_seconds"]
    max_retries = cfg["acquisition"]["max_retries"]
    backoff = cfg["acquisition"]["retry_backoff_seconds"]

    log.info(f"Vigilando carpeta de llegada cada {interval}s...")
    while True:
        for attempt in range(1, max_retries + 1):
            try:
                images = fetch_new_images()
                if images:
                    on_new_images(images)
                break
            except Exception as e:
                log.error(f"Error en intento {attempt}/{max_retries}: {e}")
                if attempt < max_retries:
                    time.sleep(backoff)
                else:
                    log.error("Se agotaron los reintentos; se sigue en el próximo ciclo.")
        time.sleep(interval)
        