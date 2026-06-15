"""TutorIA: orquesta la validación de respuestas y la generación de ejercicios.

Mapea `TutorIA` del UML:
    +validarRespuesta(String resp, Ejercicio ej) ResultadoEjercicio
    +generarSiguienteEjercicio(Perfil p) Ejercicio
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .dificultad import GestorDificultadAdaptativa
from .progreso import NivelCategoria, TipoModulo

NOTAS = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"]


@dataclass
class Ejercicio:
    tipo: TipoModulo
    nivel: int
    secuencia: list[str]

    @property
    def respuesta_correcta(self) -> str:
        return ",".join(self.secuencia)


@dataclass
class ResultadoEjercicio:
    correcto: bool
    xp_ganado: int
    nivel_categoria: int


class TutorIA:
    def __init__(self, gestor: GestorDificultadAdaptativa | None = None, rng=None) -> None:
        self.gestor = gestor or GestorDificultadAdaptativa()
        self._rng = rng or random.Random()

    def generar_siguiente_ejercicio(self, categoria: NivelCategoria) -> Ejercicio:
        n = self.gestor.cantidad_notas(categoria.nivel)
        secuencia = [self._rng.choice(NOTAS) for _ in range(n)]
        return Ejercicio(tipo=categoria.tipo, nivel=categoria.nivel, secuencia=secuencia)

    def validar_respuesta(
        self, respuesta: str, ejercicio: Ejercicio, categoria: NivelCategoria
    ) -> ResultadoEjercicio:
        correcto = (respuesta or "").strip() == ejercicio.respuesta_correcta
        xp = categoria.calcular_xp(correcto)
        categoria.subir_nivel()
        self.gestor.registrar(correcto)
        categoria.nivel = self.gestor.aplicar(categoria.nivel)
        return ResultadoEjercicio(
            correcto=correcto,
            xp_ganado=xp,
            nivel_categoria=categoria.nivel,
        )
