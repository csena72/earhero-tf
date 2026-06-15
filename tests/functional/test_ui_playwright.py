"""Prueba funcional de UI con Playwright (navegador headless).

Levanta la app FastAPI en un hilo y verifica el flujo de login desde el
navegador, tal como lo haría un usuario real. Se salta automáticamente si
Playwright no está instalado, para no romper la suite en entornos sin browser.
"""

import socket
import threading
import time

import pytest

playwright_sync = pytest.importorskip(
    "playwright.sync_api", reason="Playwright no instalado"
)
import uvicorn  # noqa: E402

from earhero import api  # noqa: E402


def _puerto_libre() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    puerto = s.getsockname()[1]
    s.close()
    return puerto


@pytest.fixture(scope="module")
def servidor():
    api._auth = api.ServicioAuth()
    api._auth.registrar("demo@earhero.com", "Segura99")
    puerto = _puerto_libre()
    config = uvicorn.Config(api.app, host="127.0.0.1", port=puerto, log_level="warning")
    server = uvicorn.Server(config)
    hilo = threading.Thread(target=server.run, daemon=True)
    hilo.start()
    for _ in range(50):
        if server.started:
            break
        time.sleep(0.1)
    yield f"http://127.0.0.1:{puerto}"
    server.should_exit = True


def test_login_exitoso_en_navegador(servidor):
    with playwright_sync.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(servidor)
        page.fill("#email", "demo@earhero.com")
        page.fill("#password", "Segura99")
        page.click("#btn-login")
        page.wait_for_function(
            "document.getElementById('status').textContent.length > 0"
        )
        assert page.inner_text("#status") == "Sesión iniciada"
        browser.close()


def test_login_fallido_en_navegador(servidor):
    with playwright_sync.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(servidor)
        page.fill("#email", "demo@earhero.com")
        page.fill("#password", "incorrecta1")
        page.click("#btn-login")
        page.wait_for_function(
            "document.getElementById('status').textContent.length > 0"
        )
        assert page.inner_text("#status") == "Credenciales inválidas"
        browser.close()
