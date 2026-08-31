"""
Observer: el módulo de inferencia no decide qué hacer con una detección,
solo la notifica. Cada "suscriptor" reacciona a su manera, sin acoplarse
entre sí — así agregar una alerta nueva no toca el código de inferencia.
"""
from abc import ABC, abstractmethod
from datetime import datatime

import pandas as pd

from src.utils.config_loader import ConfigManager
from src.utils.logger import get_logger

log = get_logger(__name__)
