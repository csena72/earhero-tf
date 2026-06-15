"""Progreso del usuario: XP, niveles por categoría y racha (RF-02, Perfil).

Mapea `NivelCategoria` y `Perfil` del UML:
    NivelCategoria.calcularXP(bool correcto) int
    NivelCategoria.subirNivel() void
    Perfil.actualizarRacha() void
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum


class TipoModulo(str, Enum):
    NOTAS = "notas"
    INTERVALOS = "intervalos"
    ACORDES = "acordes"


_XP_BASE_ACIERTO = 10
_XP_FALLO = 0
_XP_POR_NIVEL = 100


@dataclass
class NivelCategoria:
    tipo: TipoModulo
    nivel: int = 1
    puntos_acumulados: int = 0
    aciertos: int = 0
    intentos: int = 0

    def calcular_xp(self, correcto: bool) -> int:
        """XP escalado por nivel: niveles altos otorgan más XP por acierto."""
        self.intentos += 1
        if not correcto:
            return _XP_FALLO
        self.aciertos += 1
        ganado = _XP_BASE_ACIERTO * self.nivel
        self.puntos_acumulados += ganado
        return ganado

    @property
    def tasa_acierto(self) -> float:
        if self.intentos == 0:
            return 0.0
        return self.aciertos / self.intentos

    def subir_nivel(self) -> bool:
        """Sube de nivel si hay XP suficiente. Devuelve True si subió."""
        if self.puntos_acumulados >= self.nivel * _XP_POR_NIVEL:
            self.puntos_acumulados -= self.nivel * _XP_POR_NIVEL
            self.nivel += 1
            return True
        return False


@dataclass
class Perfil:
    nivel_global: int = 1
    racha: int = 0
    ultima_sesion: date | None = None
    niveles: dict[TipoModulo, NivelCategoria] = field(default_factory=dict)

    def nivel_de(self, tipo: TipoModulo) -> NivelCategoria:
        if tipo not in self.niveles:
            self.niveles[tipo] = NivelCategoria(tipo=tipo)
        return self.niveles[tipo]

    def actualizar_racha(self, hoy: date | None = None) -> int:
        """Suma a la racha si la sesión es del día siguiente; la reinicia si se
        salteó días. Sesiones del mismo día no alteran la racha."""
        hoy = hoy or date.today()
        if self.ultima_sesion is None:
            self.racha = 1
        elif hoy == self.ultima_sesion:
            pass  # misma jornada
        elif hoy == self.ultima_sesion + timedelta(days=1):
            self.racha += 1
        elif hoy > self.ultima_sesion:
            self.racha = 1  # se cortó la racha
        else:
            raise ValueError("La fecha no puede ser anterior a la última sesión")
        self.ultima_sesion = hoy
        return self.racha
