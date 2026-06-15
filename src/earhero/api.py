"""API REST + UI mínima de EarHero AI (FastAPI).

Expone los casos de uso para las pruebas funcionales:
    POST /api/register
    POST /api/login
    GET  /api/me
    POST /api/ejercicio/responder
    GET  /            -> página HTML de login (para Playwright/Selenium)
"""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from .auth import AuthError, ServicioAuth, TokenInvalidoError
from .progreso import NivelCategoria, TipoModulo
from .tutor import Ejercicio, TutorIA

app = FastAPI(title="EarHero AI", version="1.0.0")

# Estado en memoria (suficiente para el MVP y los tests).
_auth = ServicioAuth()
_tutor = TutorIA()
_categorias: dict[str, NivelCategoria] = {}


class Credenciales(BaseModel):
    email: str
    password: str


class Respuesta(BaseModel):
    respuesta: str
    esperada: str


def _categoria_de(user_id: str) -> NivelCategoria:
    if user_id not in _categorias:
        _categorias[user_id] = NivelCategoria(tipo=TipoModulo.NOTAS)
    return _categorias[user_id]


def _usuario_desde_header(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta token Bearer")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return _auth.usuario_actual(token).id
    except TokenInvalidoError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


@app.post("/api/register")
def register(cred: Credenciales):
    try:
        usuario = _auth.registrar(cred.email, cred.password)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=type(exc).__name__) from exc
    return {"id": usuario.id, "email": usuario.email}


@app.post("/api/login")
def login(cred: Credenciales):
    try:
        token = _auth.login(cred.email, cred.password)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail="Credenciales inválidas") from exc
    return {"token": token}


@app.get("/api/me")
def me(user_id: str = Depends(_usuario_desde_header)):
    cat = _categoria_de(user_id)
    return {"id": user_id, "nivel": cat.nivel, "xp": cat.puntos_acumulados}


@app.post("/api/ejercicio/responder")
def responder(payload: Respuesta, user_id: str = Depends(_usuario_desde_header)):
    cat = _categoria_de(user_id)
    ej = Ejercicio(tipo=cat.tipo, nivel=cat.nivel, secuencia=payload.esperada.split(","))
    resultado = _tutor.validar_respuesta(payload.respuesta, ej, cat)
    return {
        "correcto": resultado.correcto,
        "xp_ganado": resultado.xp_ganado,
        "nivel": resultado.nivel_categoria,
    }


_PAGINA_LOGIN = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>EarHero AI</title></head>
<body>
  <h1>EarHero AI</h1>
  <form id="login-form" onsubmit="return false;">
    <input id="email" type="email" placeholder="email" />
    <input id="password" type="password" placeholder="contraseña" />
    <button id="btn-login" type="button">Ingresar</button>
  </form>
  <p id="status"></p>
  <script>
    document.getElementById('btn-login').addEventListener('click', async () => {
      const email = document.getElementById('email').value;
      const password = document.getElementById('password').value;
      const r = await fetch('/api/login', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({email, password})
      });
      document.getElementById('status').textContent =
        r.ok ? 'Sesión iniciada' : 'Credenciales inválidas';
    });
  </script>
</body></html>"""


@app.get("/", response_class=HTMLResponse)
def home():
    return _PAGINA_LOGIN
