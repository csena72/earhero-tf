"""Gestor de Dificultad Adaptativa (RF-04).

Lógica pura, sin I/O, que decide si el usuario debe subir, bajar o mantener el
nivel según su ventana reciente de respuestas. Por ser determinista y con
varias ramas, es el mejor candidato para cobertura de ramas en los unit tests.

Mapea `GestorDificultadAdaptativa` del UML:
    +int ventanaDeRespuestas
    +float umbralSubida
    +float umbralBajada
"""

from __future__ import annotations

from collections import deque
from enum import Enum


class Ajuste(str, Enum):
    SUBIR = "subir"
    BAJAR = "bajar"
    MANTENER = "mantener"


class GestorDificultadAdaptativa:
    def __init__(
        self,
        ventana: int = 5,
        umbral_subida: float = 0.8,
        umbral_bajada: float = 0.4,
        nivel_min: int = 1,
        nivel_max: int = 10,
    ) -> None:
        if ventana <= 0:
            raise ValueError("La ventana debe ser positiva")
        if not 0.0 <= umbral_bajada < umbral_subida <= 1.0:
            raise ValueError("Umbrales inválidos: 0 <= bajada < subida <= 1")
        self.ventana = ventana
        self.umbral_subida = umbral_subida
        self.umbral_bajada = umbral_bajada
        self.nivel_min = nivel_min
        self.nivel_max = nivel_max
        self._historial: deque[bool] = deque(maxlen=ventana)

    def registrar(self, correcto: bool) -> None:
        self._historial.append(bool(correcto))

    @property
    def tasa_acierto(self) -> float:
        if not self._historial:
            return 0.0
        return sum(self._historial) / len(self._historial)

    def evaluar(self, nivel_actual: int) -> Ajuste:
        """Decide el ajuste. No ajusta hasta tener la ventana completa."""
        if len(self._historial) < self.ventana:
            return Ajuste.MANTENER
        tasa = self.tasa_acierto
        if tasa >= self.umbral_subida and nivel_actual < self.nivel_max:
            return Ajuste.SUBIR
        if tasa <= self.umbral_bajada and nivel_actual > self.nivel_min:
            return Ajuste.BAJAR
        return Ajuste.MANTENER

    def aplicar(self, nivel_actual: int) -> int:
        ajuste = self.evaluar(nivel_actual)
        if ajuste is Ajuste.SUBIR:
            self._historial.clear()
            return min(nivel_actual + 1, self.nivel_max)
        if ajuste is Ajuste.BAJAR:
            self._historial.clear()
            return max(nivel_actual - 1, self.nivel_min)
        return nivel_actual

    def cantidad_notas(self, nivel: int) -> int:
        """RF-04: a menor nivel, menos notas en el ejercicio."""
        nivel = max(self.nivel_min, min(nivel, self.nivel_max))
        return 1 + (nivel - 1) // 2

    def exportar_historial(self) -> list[bool]:
        """Devuelve la ventana reciente (para persistirla)."""
        return list(self._historial)

    def importar_historial(self, valores: list[bool]) -> None:
        """Reconstruye la ventana desde un estado persistido."""
        self._historial.clear()
        for v in valores[-self.ventana:]:
            self._historial.append(bool(v))
