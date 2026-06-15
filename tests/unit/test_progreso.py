"""Pruebas unitarias de progreso: XP, niveles por categoría y racha."""

from datetime import date, timedelta

import pytest

from earhero.progreso import NivelCategoria, Perfil, TipoModulo


def test_calcular_xp_acierto_escala_con_nivel():
    cat = NivelCategoria(tipo=TipoModulo.NOTAS, nivel=3)
    assert cat.calcular_xp(True) == 30
    assert cat.puntos_acumulados == 30
    assert cat.aciertos == 1


def test_calcular_xp_fallo_no_suma():
    cat = NivelCategoria(tipo=TipoModulo.NOTAS, nivel=3)
    assert cat.calcular_xp(False) == 0
    assert cat.puntos_acumulados == 0
    assert cat.intentos == 1
    assert cat.aciertos == 0


def test_tasa_acierto():
    cat = NivelCategoria(tipo=TipoModulo.NOTAS)
    cat.calcular_xp(True)
    cat.calcular_xp(False)
    assert cat.tasa_acierto == 0.5


def test_tasa_acierto_sin_intentos():
    assert NivelCategoria(tipo=TipoModulo.NOTAS).tasa_acierto == 0.0


def test_subir_nivel_con_xp_suficiente():
    cat = NivelCategoria(tipo=TipoModulo.NOTAS, nivel=1, puntos_acumulados=100)
    assert cat.subir_nivel() is True
    assert cat.nivel == 2
    assert cat.puntos_acumulados == 0


def test_no_sube_sin_xp():
    cat = NivelCategoria(tipo=TipoModulo.NOTAS, nivel=1, puntos_acumulados=50)
    assert cat.subir_nivel() is False
    assert cat.nivel == 1


def test_perfil_crea_categoria_lazy():
    p = Perfil()
    cat = p.nivel_de(TipoModulo.ACORDES)
    assert isinstance(cat, NivelCategoria)
    assert p.nivel_de(TipoModulo.ACORDES) is cat  # misma instancia


def test_racha_primera_sesion():
    p = Perfil()
    assert p.actualizar_racha(date(2025, 1, 1)) == 1


def test_racha_dia_consecutivo():
    p = Perfil()
    p.actualizar_racha(date(2025, 1, 1))
    assert p.actualizar_racha(date(2025, 1, 2)) == 2


def test_racha_mismo_dia_no_cambia():
    p = Perfil()
    p.actualizar_racha(date(2025, 1, 1))
    assert p.actualizar_racha(date(2025, 1, 1)) == 1


def test_racha_se_corta():
    p = Perfil()
    p.actualizar_racha(date(2025, 1, 1))
    assert p.actualizar_racha(date(2025, 1, 5)) == 1


def test_racha_fecha_pasada_es_error():
    p = Perfil()
    p.actualizar_racha(date(2025, 1, 5))
    with pytest.raises(ValueError):
        p.actualizar_racha(date(2025, 1, 1))


def test_racha_usa_hoy_por_defecto():
    p = Perfil()
    assert p.actualizar_racha() == 1
    assert p.ultima_sesion == date.today()
