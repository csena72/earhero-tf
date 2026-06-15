"""Pruebas unitarias del Gestor de Dificultad Adaptativa."""

import pytest

from earhero.dificultad import Ajuste, GestorDificultadAdaptativa


def _alimentar(g, secuencia):
    for c in secuencia:
        g.registrar(c)


def test_construccion_invalida_ventana():
    with pytest.raises(ValueError):
        GestorDificultadAdaptativa(ventana=0)


@pytest.mark.parametrize("subida,bajada", [(0.4, 0.4), (0.3, 0.8), (1.1, 0.5)])
def test_construccion_umbrales_invalidos(subida, bajada):
    with pytest.raises(ValueError):
        GestorDificultadAdaptativa(umbral_subida=subida, umbral_bajada=bajada)


def test_no_ajusta_sin_ventana_completa():
    g = GestorDificultadAdaptativa(ventana=5)
    _alimentar(g, [True, True])
    assert g.evaluar(3) is Ajuste.MANTENER


def test_sube_con_buena_tasa():
    g = GestorDificultadAdaptativa(ventana=5, umbral_subida=0.8)
    _alimentar(g, [True, True, True, True, True])
    assert g.evaluar(3) is Ajuste.SUBIR


def test_no_sube_en_nivel_maximo():
    g = GestorDificultadAdaptativa(ventana=5, nivel_max=10)
    _alimentar(g, [True] * 5)
    assert g.evaluar(10) is Ajuste.MANTENER


def test_baja_con_mala_tasa():
    g = GestorDificultadAdaptativa(ventana=5, umbral_bajada=0.4)
    _alimentar(g, [False, False, False, False, True])
    assert g.evaluar(5) is Ajuste.BAJAR


def test_no_baja_en_nivel_minimo():
    g = GestorDificultadAdaptativa(ventana=5, nivel_min=1)
    _alimentar(g, [False] * 5)
    assert g.evaluar(1) is Ajuste.MANTENER


def test_mantiene_en_zona_media():
    g = GestorDificultadAdaptativa(ventana=5, umbral_subida=0.8, umbral_bajada=0.4)
    _alimentar(g, [True, True, True, False, False])  # 0.6
    assert g.evaluar(5) is Ajuste.MANTENER


def test_aplicar_sube_y_limpia_historial():
    g = GestorDificultadAdaptativa(ventana=5)
    _alimentar(g, [True] * 5)
    assert g.aplicar(3) == 4
    assert g.tasa_acierto == 0.0  # historial reiniciado


def test_aplicar_baja():
    g = GestorDificultadAdaptativa(ventana=5)
    _alimentar(g, [False] * 5)
    assert g.aplicar(5) == 4


def test_aplicar_mantiene():
    g = GestorDificultadAdaptativa(ventana=5)
    _alimentar(g, [True, True, True, False, False])
    assert g.aplicar(5) == 5


def test_tasa_acierto_sin_datos():
    assert GestorDificultadAdaptativa().tasa_acierto == 0.0


@pytest.mark.parametrize("nivel,esperado", [(1, 1), (2, 1), (3, 2), (5, 3), (10, 5)])
def test_cantidad_notas_crece_con_nivel(nivel, esperado):
    assert GestorDificultadAdaptativa().cantidad_notas(nivel) == esperado


def test_cantidad_notas_satura_fuera_de_rango():
    g = GestorDificultadAdaptativa(nivel_min=1, nivel_max=10)
    assert g.cantidad_notas(99) == g.cantidad_notas(10)
    assert g.cantidad_notas(-5) == g.cantidad_notas(1)
