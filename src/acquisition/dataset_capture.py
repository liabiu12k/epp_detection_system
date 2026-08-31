"""
Módulo de captura para el dataset inicial (S2).
Soporta dos modos: fotos individuales (tecla 'c') y clips de video cortos
(tecla 'v' inicia/detiene grabación) — la tarea pide "imágenes y videos".
"""
from datetime import datetime
from pathlib import Path

import cv2

from src.utils.config_loader import ConfigManager
from src.utils.logger import get_logger

log = get_logger(__name__)

CONDITIONS = [
    "luz_natural",
    "luz_artificial",
    "con_oclusion",
    "en_movimiento",
    "sin_epp",
    "epp_incorrecto",
]


class DatasetCaptureSession:
    def __init__(self, camera_index: int = 0):
        self.config = ConfigManager()
        self.camera_index = camera_index
        self.current_condition_idx = 0
        self.counts = {c: {"fotos": 0, "videos": 0} for c in CONDITIONS}

        self.output_dir = self.config.root / "data" / "raw" / "dataset_capture"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.recording = False
        self.video_writer = None

    def _current_condition(self) -> str:
        return CONDITIONS[self.current_condition_idx]

    def _save_frame(self, frame) -> Path:
        condition = self._current_condition()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        filename = self.output_dir / f"{condition}_{timestamp}.jpg"
        cv2.imwrite(str(filename), frame)
        self.counts[condition]["fotos"] += 1
        log.info(f"Foto capturada: {filename.name}")
        return filename

    def _toggle_video(self, frame):
        condition = self._current_condition()
        if not self.recording:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = self.output_dir / f"{condition}_{timestamp}.mp4"
            h, w = frame.shape[:2]
            fourcc = cv2.VideoWriter_fourcc(*"mp4v")
            self.video_writer = cv2.VideoWriter(str(filename), fourcc, 20.0, (w, h))
            self.recording = True
            self._current_video_name = filename.name
            log.info(f"Grabación iniciada: {filename.name}")
        else:
            self.video_writer.release()
            self.video_writer = None
            self.recording = False
            self.counts[condition]["videos"] += 1
            log.info(f"Grabación detenida: {self._current_video_name}")

    def run(self):
        cam = cv2.VideoCapture(self.camera_index)
        if not cam.isOpened():
            raise RuntimeError(f"No se pudo abrir la cámara (índice {self.camera_index})")

        print("\nControles: [c] foto | [v] iniciar/detener video | [n] cambiar condición | [q] salir\n")

        try:
            while True:
                ok, frame = cam.read()
                if not ok:
                    log.error("No se pudo leer frame de la cámara")
                    break

                if self.recording and self.video_writer is not None:
                    self.video_writer.write(frame)

                self._draw_overlay(frame)
                cv2.imshow("Captura de dataset - EPP", frame)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("c"):
                    self._save_frame(frame)
                elif key == ord("v"):
                    self._toggle_video(frame)
                elif key == ord("n"):
                    if not self.recording:  # evita cambiar de condición a mitad de un video
                        self.current_condition_idx = (self.current_condition_idx + 1) % len(CONDITIONS)
                elif key == ord("q"):
                    if self.recording:
                        self._toggle_video(frame)  # cierra el video abierto antes de salir
                    break
        finally:
            cam.release()
            cv2.destroyAllWindows()
            self._print_summary()

    def _draw_overlay(self, frame):
        condition = self._current_condition()
        rec_indicator = " [GRABANDO]" if self.recording else ""
        text = f"Condicion: {condition}{rec_indicator}"
        color = (0, 0, 255) if self.recording else (0, 255, 0)
        cv2.putText(frame, text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, "[c] foto  [v] video  [n] cambiar  [q] salir", (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

    def _print_summary(self):
        print("\n--- Resumen de la sesión ---")
        total_fotos = sum(c["fotos"] for c in self.counts.values())
        total_videos = sum(c["videos"] for c in self.counts.values())
        for condition, c in self.counts.items():
            print(f"  {condition:20s}: {c['fotos']:4d} fotos, {c['videos']:3d} videos")
        print(f"  {'TOTAL':20s}: {total_fotos:4d} fotos, {total_videos:3d} videos")
        log.info(f"Sesión finalizada. {total_fotos} fotos, {total_videos} videos")


if __name__ == "__main__":
    session = DatasetCaptureSession(camera_index=0)
    session.run()