# EPP Detection System

Sistema de visión artificial para detectar el uso de Equipo de Protección Personal (EPP) en entornos de obra, con enfoque en casco, chaleco y arnés. El proyecto está diseñado como una arquitectura modular para recopilar imágenes, preprocessarlas, ejecutar inferencia y generar reportes de alertas con evidencia visual.

## Descripción general

Este sistema permite:

- Capturar imágenes desde distintas fuentes de entrada.
- Validar y clasificar archivos para evitar datos corruptos o no útiles.
- Preprocesar imágenes con técnicas como letterbox y CLAHE.
- Ejecutar inferencia con un detector configurable.
- Generar reportes y guardar evidencia visual de cada detección.
- Diseñar la solución con patrones de arquitectura reutilizables y pruebas de estructura.

La solución está pensada para evolucionar desde un detector dummy en fase de desarrollo hasta una integración con YOLOv8 real cuando el dataset y los pesos estén listos.

## Objetivo del proyecto

Detectar automáticamente si los trabajadores usan o no el equipo de protección personal requerido en una obra o zona de riesgo, y registrar las incidencias para auditoría y seguimiento.

## Stack y enfoque

- Python
- OpenCV
- NumPy
- PyYAML
- Arquitectura modular basada en patrones:
  - Singleton
  - Strategy + Factory Method
  - Pipeline
  - Observer
- Preparado para integración con modelos de detección como YOLOv8

## Estructura del repositorio

```text
.
├── ARCHITECTURE.md
├── README.md
├── main.py
├── config/
│   └── config.yaml
├── data/
│   ├── dataset/
│   ├── processed/
│   ├── quarantine/
│   └── raw/
├── logs/
├── models/
├── reports/
├── src/
│   ├── acquisition/
│   │   ├── capture.py
│   │   ├── dataset_capture.py
│   │   └── strategies.py
│   ├── dataset/
│   │   └── coverage_check.py
│   ├── inference/
│   │   └── detector.py
│   ├── pipeline.py
│   ├── preprocessing/
│   │   └── preprocess.py
│   ├── reporting/
│   │   └── observers.py
│   ├── utils/
│   │   ├── config_loader.py
│   │   └── logger.py
│   └── ...
├── tests/
│   └── test_architecture.py
└── .gitignore
```

## Módulos principales

### 1. Adquisición
Encargado de obtener nuevas imágenes desde la fuente configurada. Permite integrar distintos métodos de captura sin acoplar el resto del sistema.

### 2. Preprocesamiento
Se encarga de preparar cada imagen para la inferencia, incluyendo normalización, escalado y corrección de iluminación.

### 3. Inferencia
Define la interfaz para el detector y permite alternar entre versiones simuladas o reales del modelo.

### 4. Reporte
Notifica detecciones y genera registros o evidencia visual para análisis posterior.

### 5. Configuración y logging
Proporciona acceso centralizado a la configuración del proyecto y un sistema de logs con rotación.

## Configuración

La configuración base está en:

```text
config/config.yaml
```

Se definen rutas de entrada/salida, umbral de confianza, rutas de modelos, método de adquisición y parámetros de logging.

## Requisitos

- Python 3.10+
- pip
- Dependencias de visión por computadora y YAML

## Instalación

1. Clona el repositorio.
2. Crea un entorno virtual.
3. Instala las dependencias.

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Si aún no existe un archivo `requirements.txt`, puedes instalar las dependencias necesarias manualmente:

```bash
pip install numpy opencv-python pyyaml
```

## Ejecución

Desde la raíz del proyecto:

```bash
python main.py
```

Esto inicia la cadena del pipeline con el detector configurado en el archivo de configuración.

## Estado actual

El proyecto ya tiene:

- Estructura modular definida
- Configuración centralizada
- Patrón de pipeline
- Observadores para reporte
- Detector base y detector dummy
- Pruebas de arquitectura iniciales

Todavía está en una fase de desarrollo donde la parte de entrenamiento y detección real con YOLOv8 se completará en etapas posteriores.

## Roadmap sugerido

- Completar el pipeline funcional end-to-end
- Implementar validación real de detecciones por clase
- Integrar YOLOv8 entrenado para EPP
- Añadir almacenamiento de alertas en Excel o CSV
- Mejorar la evidencia visual y la inspección humana
- Añadir pruebas automáticas más completas sobre imagen, configuración y detección

## Notas

Este repositorio está orientado a un sistema real de monitoreo industrial, por lo que la modularidad y la trazabilidad de datos son prioritarias. La estructura intenta facilitar la integración de nuevas fuentes de captura, nuevos modelos y canales de notificación sin romper el flujo principal.

## Siguiente paso recomendado

Antes de usarlo en producción, conviene:

- revisar las rutas absolutas y de entorno,
- ajustar `config/config.yaml`,
- añadir el archivo `requirements.txt`,
- y completar la parte de inferencia real con el modelo de detección final.

