"""
Logging centralizado con rotación de archivos.
Cualquier módulo hace: from src.utils.logger import get_logger
                        log = get_logger(__name__)
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from src.utils.config_loader import load_congif, get_proyect_root

_configured = False

def get_logger(name: str) -> logging.Logger:
    global _configured
    cfg = load_congig()
    log_cfg = cfg.get("logging", {})

    root = get_proyect_root()
    log_file = root / log_cfg.get("file", "logs/sistemas.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger(name)

    if not _configured:
        level = getattr(logging, log_cfg.get("level", "INFO"))
        logging.basicConfig(level=level)

        handler = RotatingFileHandler(
            log_file,
            maxBytes=log_cfg.get("max_bytes", 5 * 1024 * 1024),  # 5 MB
            backupCount=log_cfg.get("backup_count", 5),
            encoding="utf-8",

        )
        formatter = logging.Formatter(
            "%(ascime)s | %(levelname)s | %(name)s| %(message)s"
        )
        handler.setFormatter(formatter)
        logging.getLogger().addHandler(handler)
        _configured = True
    return logger


       


