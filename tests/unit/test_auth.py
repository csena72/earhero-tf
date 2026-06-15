"""Pruebas unitarias del sistema de autenticación."""

import time

import pytest

from earhero import auth


@pytest.fixture
def servicio():
    return auth.ServicioAuth()


# ---------- Validaciones puras ----------

@pytest.mark.parametrize("email,esperado", [
    ("user@dominio.com", True),
    ("a.b@sub.dominio.com", True),
    ("sinarroba.com", False),
    ("dos@@arroba.com", False),
    ("@sindominio.com", False),
    ("local@", False),
    ("local@sinpunto", False),
    ("con espacio@dominio.com", False),
    ("", False),
    (None, False),
])
def test_email_valido(email, esperado):
    assert auth.email_valido(email) is esperado


@pytest.mark.parametrize("password,esperado", [
    ("abcd1234", True),
    ("Segura99", True),
    ("corta1", False),       # menos de 8
    ("sololetras", False),   # sin dígito
    ("12345678", False),     # sin letra
    ("", False),
    (None, False),
])
def test_password_segura(password, esperado):
    assert auth.password_segura(password) is esperado


# ---------- Hashing ----------

def test_hash_password_es_verificable():
    h = auth.hash_password("Segura99")
    assert auth.verificar_password("Segura99", h)
    assert not auth.verificar_password("otra", h)


def test_hash_password_usa_salt_distinto():
    assert auth.hash_password("Segura99") != auth.hash_password("Segura99")


def test_verificar_password_con_formato_invalido():
    assert auth.verificar_password("x", "sin-separador") is False


# ---------- Tokens ----------

def test_token_ida_y_vuelta():
    token = auth.generar_token("user-1")
    assert auth.verificar_token(token) == "user-1"


def test_token_expirado(monkeypatch):
    token = auth.generar_token("user-1", ttl=1)
    futuro = time.time() + 5
    monkeypatch.setattr(auth.time, "time", lambda: futuro)
    with pytest.raises(auth.TokenInvalidoError):
        auth.verificar_token(token)


def test_token_firma_alterada():
    token = auth.generar_token("user-1")
    h, p, _ = token.split(".")
    falso = f"{h}.{p}.firmafalsa"
    with pytest.raises(auth.TokenInvalidoError):
        auth.verificar_token(falso)


@pytest.mark.parametrize("malo", ["", "a.b", "a.b.c.d", 123, "sinpuntos"])
def test_token_formato_invalido(malo):
    with pytest.raises(auth.TokenInvalidoError):
        auth.verificar_token(malo)


# ---------- Casos de uso ----------

def test_registrar_ok(servicio):
    u = servicio.registrar("Nuevo@Dominio.com", "Segura99")
    assert u.email == "nuevo@dominio.com"  # normalizado a minúsculas
    assert u.id


def test_registrar_email_invalido(servicio):
    with pytest.raises(auth.EmailInvalidoError):
        servicio.registrar("malo", "Segura99")


def test_registrar_password_debil(servicio):
    with pytest.raises(auth.PasswordDebilError):
        servicio.registrar("user@dominio.com", "123")


def test_registrar_duplicado(servicio):
    servicio.registrar("user@dominio.com", "Segura99")
    with pytest.raises(auth.UsuarioYaExisteError):
        servicio.registrar("USER@dominio.com", "Segura99")


def test_login_ok_devuelve_token(servicio):
    servicio.registrar("user@dominio.com", "Segura99")
    token = servicio.login("user@dominio.com", "Segura99")
    assert servicio.usuario_actual(token).email == "user@dominio.com"


def test_login_password_incorrecta(servicio):
    servicio.registrar("user@dominio.com", "Segura99")
    with pytest.raises(auth.CredencialesInvalidasError):
        servicio.login("user@dominio.com", "incorrecta1")


def test_login_usuario_inexistente(servicio):
    with pytest.raises(auth.CredencialesInvalidasError):
        servicio.login("fantasma@dominio.com", "Segura99")


def test_usuario_actual_con_token_de_otro_servicio(servicio):
    # token válido en firma pero sin usuario en este repositorio
    token = auth.generar_token("id-inexistente")
    with pytest.raises(auth.TokenInvalidoError):
        servicio.usuario_actual(token)
