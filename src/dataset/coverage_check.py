"""
Verifica cuánto se ha capturado por condición, comparando con las metas
mínimas definidas para el dataset (variedad de iluminación, oclusión,
ángulo, movimiento que exige la matriz de consistencia de la tesis).

Se corre cuantas veces se quiera durante S2, sin reabrir la cámara.
"""

from pathlib import Path
from collections import Counter
