# Arquitectura del Sistema de Detección de EPP

Sistema de visión artificial para detectar el uso de Equipo de Protección
Personal (EPP) —casco, chaleco, arnés— en tiempo casi real dentro de una obra.

## 1. Visión general

El flujo es una cadena de procesamiento por lotes, no un streaming continuo:

1. Adquisición de imágenes (Bluetooth / carpeta / webcam).
2. Preprocesamiento (letterbox + CLAHE).
3. Inferencia con un detector (YOLOv8 al final; dummy durante desarrollo).
4. Reporte por notificaciones (Excel y guardado de evidencia).

Cada etapa recibe y devuelve un contexto común (dict), lo que desacopla los
módulos entre sí y permite probar el sistema end-to-end sin el modelo real.

## 2. Estructura de directorios

```
epp_detection_system/
├── main.py                    # Punto de entrada; conecta los módulos (composición raíz)
├── config/
│   └── config.yaml            # Única fuente de verdad de configuración
├── data/
│   ├── raw/                   # Imágenes de llegada (Bluetooth / carpeta)
│   ├── processed/             # Imágenes ya procesadas (idempotencia)
│   ├── quarantine/            # Archivos inválidos movidos aparte
│   └── dataset/               # Dataset para entrenamiento (Módulo 4)
├── models/                    # Pesos del modelo entrenado (.pt)
├── reports/                   # Alertas (.xlsx) y evidencia (imágenes)
│   └── evidencia/
├── logs/                      # Logs con rotación
├── src/
│   ├── acquisition/           # Módulo 1 — Adquisición
│   │   ├── strategies.py      #   Patrón Strategy + Factory Method
│   │   └── capture.py         #   Utilerías de validación/cuarentena (legacy)
│   ├── preprocessing/         # Módulo 2 — Preprocesamiento
│   │   └── preprocess.py      #   load → CLAHE → letterbox (funciones puras)
│   ├── inference/             # Módulo 3 — Inferencia (interfaz del detector)
│   │   └── detector.py        #   Detector (ABC), DummyDetector, YOLOv8Detector
│   ├── reporting/             # Módulo 5 — Reporte
│   │   └── observers.py       #   Patrón Observer (subject + observers)
│   ├── utils/
│   │   ├── config_loader.py   #   ConfigManager (Singleton)
│   │   └── logger.py          #   Logging centralizado con rotación
│   └── pipeline.py            #   Patrón Pipeline (etapas encadenadas)
└── tests/
    └── test_architecture.py   # Pruebas que validan el diseño (no el modelo)
```

## 3. Descomposición en módulos

| Módulo | Responsabilidad | Arquitectura |
|---|---|---|
| 1. Adquisición (`src/acquisition`) | Obtener fotos nuevas, validarlas, aislar las inválidas | Strategy + Factory Method |
| 2. Preprocesamiento (`src/preprocessing`) | Redimensionar a 640×640 (letterbox), corregir iluminación (CLAHE), normalizar | Funciones puras + PipelineStage |
| 3. Inferencia (`src/inference`) | Recibir imagen procesada → devolver detecciones `{class_name, confidence, bbox}` | Interfaz `Detector` (ABC) |
| 4. Entrenamiento (futuro) | Entrenar YOLOv8 con dataset propio de EPP | Fuera de scope actual |
| 5. Reporte (`src/reporting`) | Reaccionar a cada detección sin acoplarse a inferencia | Observer |
| 6. Config/Logging (`src/utils`) | Config única en memoria; logs con rotación | Singleton / módulo centralizado |

## 4. Patrones de diseño

### 4.1 Singleton — `ConfigManager` (`src/utils/config_loader.py`)
Una sola instancia de configuración viva durante toda la ejecución.

- Evita relectura del YAML y config desincronizada entre módulos.
- Acceso anidado seguro: `config.get('acquisition', 'poll_interval_seconds', default=30)`.
- Toda ruta se resuelve siempre contra la raíz del proyecto, nunca con rutas
  relativas al cwd.
- Uso: `config = ConfigManager()` desde cualquier módulo.

### 4.2 Strategy + Factory Method — `ImageAcquisitionStrategy` / `AcquisitionFactory`
(`src/acquisition/strategies.py`)

- `ImageAcquisitionStrategy` (ABC) define la interfaz `fetch_new_images() -> list[Path]`.
- Estrategias concretas: `BluetoothAcquisition`, `FolderWatchAcquisition`,
  `WebcamAcquisition` (misma interfaz; el resto del sistema no sabe de dónde salen las fotos).
- `_ValidationMixin` comparte la lógica de validación y cuarentena.
- `AcquisitionFactory.create()` lee `acquisition.method` del config y devuelve la
  estrategia correcta; el código cliente nunca instancia clases concretas.
- Agregar una cámara nueva = agregar una clase + entrada en `_strategies`.

### 4.3 Pipeline — `DetectionPipeline` (`src/pipeline.py`)
Encadena etapas en orden fijo; cada una recibe el contexto y lo devuelve
enriquecido.

- Etapas previstas: `PreprocessingStage` → `InferenceStage(detector)` →
  `ReportingStage(subject)`.
- `InferenceStage` y `ReportingStage` reciben sus dependencias por inyección
  (detector y subject), lo que permite probarlas con sustitutos.
- El pipeline se construye en `main.build_pipeline()` y es fácil de reordenar
  o instrumentar.

### 4.4 Observer — `DetectionSubject` / `DetectionObserver`
(`src/reporting/observers.py`)

- La inferencia no decide qué hacer con una detección: solo notifica.
- `DetectionSubject.notify(detection, image_path)` avisa a TODOS los suscriptores.
- Observadores previstos:
  - `ExcelReportObserver`: registra la alerta en `reports/alertas.xlsx`.
  - `EvidenceImageObserver`: guarda la imagen con detecciones en `reports/evidencia/`.
- Agregar un canal de alerta nuevo (WhatsApp, pantalla, correo) NO toca el código
  de inferencia: solo se registra un observer más en `build_pipeline`.

## 5. Flujo de datos

```
main.py
  │  ConfigManager()                         # 1 instancia global (Singleton)
  │
  ├─ acquisition = AcquisitionFactory.create()
  │        └─ fetch_new_images() → [Path...] # imágenes nuevas y VÁLIDAS
  │
  └─ por cada imagen:
       pipeline.run(image_path)
         │  Context = {"image_path": ...}
         ├─ PreprocessingStage → {image: np.ndarray(640×640, BGR)}
         ├─ InferenceStage(detector) → {detections: [{class_name, confidence, bbox}]}
         └─ ReportingStage(subject) → subject.notify(detection, image_path)
                ├─ ExcelReportObserver     (escribe el .xlsx)
                └─ EvidenceImageObserver   (guarda la evidencia)
```

Contrato del detector (`src/inference/detector.py`):

```python
class Detector(ABC):
    def predict(self, image: np.ndarray) -> list[dict]:
        """
        Devuelve una lista de detecciones:
        [{"class_name": str, "confidence": float, "bbox": [x1, y1, x2, y2]}]
        """
```

- `DummyDetector`: devuelve una detección falsa — permite probar el pipeline
  completo antes de tener el modelo.
- `YOLOv8Detector`: carga los pesos con lazy load (`models/…latest.pt`), filtra
  por umbral de confianza y traduce resultados a listas de dicts.
- Intercambiables: `build_pipeline(use_real_model=True)` conmuta entre ambos.

## 6. Configuración (`config/config.yaml`)

| Sección | Clave | Propósito |
|---|---|---|
| `paths` | `raw_images`, `processed_images`, `dataset_dir`, `models_dir`, `reports_dir`, `logs_dir` | Rutas absolutas siempre derivadas de la raíz del proyecto |
| `models` | `weights_file`, `variant`, `confidence_threshold`, `classes` | Detector y umbral |
| `training` | `epochs`, `batch_size`, `learning_rate`, `img_size` | Entrenamiento futuro |
| `acquisition` | `method`, `poll_interval_seconds`, `max_retries`, `retry_backoff_seconds`, `allowed_extensions` | Origen y política de captura |
| `reporting` | `output_file`, `save_evidence_images`, `evidence_dir` | Destino de alertas y evidencia |
| `logging` | `level`, `file`, `max_bytes`, `backup_count` | Logging con rotación |

Selección de método de adquisición: solo hay que cambiar `acquisition.method`
entre `bluetooth`, `folder_watch` o `webcam`; sin cambios de código.

## 7. Estado actual e implementación (S1–S5)

La arquitectura está **definida** e implementada parcialmente:

- Definidos y funcionales: `ConfigManager` (Singleton), `AcquisitionFactory`
  (Strategy/Factory), interfaz `Detector` + `DummyDetector`, modulo de
  preprocesamiento (CLAHE + letterbox).
- Pendientes como stubs/placeholder:
  - `src/pipeline.py` (etapas + `DetectionPipeline`) — esqueleto a completar.
  - Observadores concretos (`ExcelReportObserver`, `EvidenceImageObserver`).
  - `tests/test_architecture.py` es el contrato de diseño que los módulos deben satisfacer.
- `YOLOv8Detector` está definido pero requiere el entrenamiento (Módulo 4/S5–S8).

## 8. Decisiones clave

1. **Interfaz de detector primero**: permite construir y probar todo el
   pipeline sin depender del modelo entrenado.
2. **Captura por lotes, no streaming**: el SO deja las fotos Bluetooth en una
   carpeta; el sistema la vigila por polling (`poll_interval_seconds`).
3. **Idempotencia**: las imágenes procesadas se mueven a `data/processed` para
   no re-analizarlas tras un reinicio.
4. **Cuarentena, no borrado**: los archivos inválidos se mueven a
   `data/quarantine` para auditar por qué fallaron.
5. **Funciones puras en preprocesamiento**: testables de forma aislada sin
   tocar disco.
6. **Config única vía Singleton**: elimina rutas relativas y lecturas repetidas
   del YAML; cualquier cambio se hace en un solo archivo.