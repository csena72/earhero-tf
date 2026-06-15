"""Pruebas unitarias del TutorIA (usando un RNG sembrado para determinismo)."""

import random

from earhero.dificultad import GestorDificultadAdaptativa
from earhero.progreso import NivelCategoria, TipoModulo
from earhero.tutor import TutorIA


def _tutor():
    return TutorIA(gestor=GestorDificultadAdaptativa(ventana=3), rng=random.Random(42))


def test_genera_ejercicio_con_cantidad_segun_nivel():
    tutor = _tutor()
    cat = NivelCategoria(tipo=TipoModulo.NOTAS, nivel=1)
    ej = tutor.generar_siguiente_ejercicio(cat)
    assert ej.tipo is TipoModulo.NOTAS
    assert len(ej.secuencia) == 1


def test_respuesta_correcta_otorga_xp():
    tutor = _tutor()
    cat = NivelCategoria(tipo=TipoModulo.NOTAS, nivel=2)
    ej = tutor.generar_siguiente_ejercicio(cat)
    res = tutor.validar_respuesta(ej.respuesta_correcta, ej, cat)
    assert res.correcto is True
    assert res.xp_ganado == 20


def test_respuesta_incorrecta_no_otorga_xp():
    tutor = _tutor()
    cat = NivelCategoria(tipo=TipoModulo.NOTAS, nivel=2)
    ej = tutor.generar_siguiente_ejercicio(cat)
    res = tutor.validar_respuesta("RespuestaMala", ej, cat)
    assert res.correcto is False
    assert res.xp_ganado == 0


def test_tres_aciertos_suben_de_nivel():
    tutor = _tutor()  # ventana=3
    cat = NivelCategoria(tipo=TipoModulo.NOTAS, nivel=1)
    for _ in range(3):
        ej = tutor.generar_siguiente_ejercicio(cat)
        res = tutor.validar_respuesta(ej.respuesta_correcta, ej, cat)
    assert res.nivel_categoria == 2
