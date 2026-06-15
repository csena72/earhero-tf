```python
import pytest
from gestor_dificultad_adaptativa import GestorDificultadAdaptativa, Ajuste

# Fixtures para el contexto de los tests
@pytest.fixture(scope='module')
def gestionador():
    return GestorDificultadAdaptativa(ventana=5, umbral_subida=0.8, umbral_bajada=0.4)

@pytest.fixture(scope='function')
def empty_gestionador():
    return GestorDificultadAdaptativa()

# Pruebas para __init__
@pytest.mark.parametrize("ventana, umbral_subida, umbral_bajada", [
    (5, 0.8, 0.4)
])
def test_init_valid(ventana, umbral_subida, umbral_bajada):
    gestor = GestorDificultadAdaptativa(ventana=ventana, umbral_subida=umbral_subida, umbral_bajada=umbral_bajada)
    assert gestor.ventana == ventana
    assert gestor.umbral_subida == umbral_subida
    assert gestor.umbral_bajada == umbral_bajada

@pytest.mark.parametrize("ventana", [0])
def test_init_invalid_ventana(ventana):
    with pytest.raises(ValueError, match="La ventana debe ser positiva"):
        GestorDificultadAdaptativa(ventana=ventana)

@pytest.mark.parametrize("umbral_subida, umbral_bajada", [(-0.2, 0.4), (0.8, -0.4)])
def test_init_invalid_umbrales(umbral_subida, umbral_bajada):
    with pytest.raises(ValueError, match="Los umbrales deben estar en el rango [0, 1]"):
        GestorDificultadAdaptativa(ventana=5, umbral_subida=umbral_subida, umbral_bajada=umbral_bajada)

# Pruebas para registrar
@pytest.mark.parametrize("correcto", [True])
def test_registrar_valid(correcto):
    gestor = gestionador()
    gestor.registrar(correcto)
    assert gestor.historial == [True]

@pytest.mark.parametrize("correcto", [None])
def test_registrar_invalid(correcto):
    gestor = gestionador()
    with pytest.raises(TypeError, match="El parámetro 'correcto' debe ser booleano"):
        gestor.registrar(correcto)

# Pruebas para evaluar
@pytest.mark.parametrize("nivel_actual, historial", [
    (5, [True, True, True])
])
def test_evaluar_valid(nivel_actual, historial):
    gestor = gestionador(historial=historial)
    result = gestor.evaluar(nivel_actual)
    assert result == Ajuste.SUBIR

@pytest.mark.parametrize("nivel_actual, historial", [
    (5, [])
])
def test_evaluar_invalid(nivel_actual, historial):
    gestor = empty_gestionador(historial=historial)
    result = gestor.evaluar(nivel_actual)
    assert result == Ajuste.MANTENER

# Pruebas para aplicar
@pytest.mark.parametrize("nivel_actual, historial", [
    (5, [True, True, True])
])
def test_aplicar_valid(nivel_actual, historial):
    gestor = gestionador(historial=historial)
    new_level = gestor.aplicar(nivel_actual)
    assert new_level == nivel_actual + 1

@pytest.mark.parametrize("nivel_actual, historial", [
    (5, [])
])
def test_aplicar_invalid(nivel_actual, historial):
    gestor = empty_gestionador(historial=historial)
    new_level = gestor.aplicar(nivel_actual)
    assert new_level == nivel_actual

# Pruebas para cantidad_notas
@pytest.mark.parametrize("nivel", [
    (5)
])
def test_cantidad_notas_valid(nivel):
    gestor = gestionador()
    result = gestor.cantidad_notas(nivel)
    assert result == 6

@pytest.mark.parametrize("nivel", [
    (-5)
])
def test_cantidad_notas_invalid(nivel):
    gestor = gestionador()
    new_level = gestor.cantidad_notas(nivel)
    assert new_level == 1
```