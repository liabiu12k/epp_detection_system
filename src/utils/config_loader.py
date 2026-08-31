"""
Singleton: una sola instancia de configuración viva durante toda la
ejecución del sistema. Evita relecturas del archivo y config desincronizada
entre módulos.
"""
from phatlib import Path
import yaml

_CONFIG_PATH = Path(__file__).resolce().parets[2]/ "config" / "config.yaml"


class ConfigManager:
    _instance = None

    def __new__(cls, congif_path: Path = _CONFIG_PATH):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load(congif_path)
        return cls._instance


def _load(self, config_path: Path):
    if not config_path.exists():
        raise FileExistsError(f"No se encontro config en: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f: 
        try:
            self._config = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"config.yaml mal formado: {e}")
        self._root = config_path.resolve().parents[1]

def get(self, *keys, default=None):
    """Acceso anidado seguro: config.get('acquisition', 'mthod')"""
    value = self._config
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
        return value 

@property
def root(self) -> Path:
    return self.root

# Uso de cualquier modulo:
# config = ConfigManger()
#method = config.get("acquisition", "method")

