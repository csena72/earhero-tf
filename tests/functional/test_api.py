"""Pruebas funcionales de la API REST (end-to-end con TestClient).

No usan mocks: ejercitan la aplicación completa (routing, auth, dominio) tal
como la vería un cliente HTTP real.
"""

import pytest
from fastapi.testclient import TestClient

from earhero import api
from earhero.db import reset_db


@pytest.fixture
def client():
    # Base de datos limpia entre tests (SQLite en memoria).
    reset_db()
    return TestClient(api.app)


def _registrar_y_login(client, email="user@dominio.com", pw="Segura99"):
    client.post("/api/register", json={"email": email, "password": pw})
    r = client.post("/api/login", json={"email": email, "password": pw})
    return r.json()["token"]


def test_register_devuelve_id_y_email(client):
    r = client.post("/api/register", json={"email": "a@b.com", "password": "Segura99"})
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.com"


def test_register_rechaza_password_debil(client):
    r = client.post("/api/register", json={"email": "a@b.com", "password": "123"})
    assert r.status_code == 400
    assert r.json()["detail"] == "PasswordDebilError"


def test_login_ok(client):
    client.post("/api/register", json={"email": "a@b.com", "password": "Segura99"})
    r = client.post("/api/login", json={"email": "a@b.com", "password": "Segura99"})
    assert r.status_code == 200
    assert "token" in r.json()


def test_login_credenciales_invalidas(client):
    r = client.post("/api/login", json={"email": "x@y.com", "password": "Segura99"})
    assert r.status_code == 401


def test_me_requiere_token(client):
    assert client.get("/api/me").status_code == 401


def test_me_con_token_valido(client):
    token = _registrar_y_login(client)
    r = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["nivel"] == 1


def test_me_con_token_basura(client):
    r = client.get("/api/me", headers={"Authorization": "Bearer xxx"})
    assert r.status_code == 401


def test_siguiente_genera_ejercicio(client):
    token = _registrar_y_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post("/api/ejercicio/siguiente", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["longitud"] == len(body["secuencia"])
    assert body["nivel"] >= 1


def test_responder_correcto_suma_xp(client):
    token = _registrar_y_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    secuencia = client.post("/api/ejercicio/siguiente", headers=headers).json()["secuencia"]
    r = client.post(
        "/api/ejercicio/responder",
        headers=headers,
        json={"respuesta": ",".join(secuencia)},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["correcto"] is True
    assert body["xp_ganado"] >= 10


def test_responder_incorrecto(client):
    token = _registrar_y_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    client.post("/api/ejercicio/siguiente", headers=headers)
    r = client.post(
        "/api/ejercicio/responder",
        headers=headers,
        json={"respuesta": "RespuestaMala"},
    )
    assert r.status_code == 200
    assert r.json()["correcto"] is False


def test_responder_sin_ejercicio_pendiente(client):
    token = _registrar_y_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    r = client.post(
        "/api/ejercicio/responder", headers=headers, json={"respuesta": "Do"}
    )
    assert r.status_code == 400


def test_home_sirve_frontend(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "EarHero" in r.text
