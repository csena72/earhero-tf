"""API REST + frontend de EarHero AI (FastAPI) con persistencia en base de datos.

La documentación interactiva (Swagger UI) queda disponible en /docs y la
alternativa ReDoc en /redoc. La persistencia (usuarios, perfiles, progreso y
sesiones de ejercicio) se hace vía SQLAlchemy; la URL se toma de DATABASE_URL
(PostgreSQL en docker-compose, SQLite en tests/dev).
"""

from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .auth import AuthError, ServicioAuth, TokenInvalidoError
from .db import SessionLocal, init_db
from .repos import RepositorioProgresoSQL, RepositorioUsuariosSQL
from .tutor import TutorIA

DESCRIPCION = """
**EarHero AI** — API de la app de entrenamiento auditivo.

Cubre el ciclo del documento de diseño: autenticación (JWT), generación de
ejercicios por el *TutorIA*, ajuste de dificultad adaptativa y persistencia de
progreso. La validación de cada respuesta se hace **del lado del servidor**.
"""

TAGS = [
    {"name": "Autenticación", "description": "Registro, login y sesión (RF-01)."},
    {"name": "Entrenamiento", "description": "Ejercicios, respuestas y progreso (RF-02/04)."},
]

app = FastAPI(
    title="EarHero AI",
    version="1.0.0",
    description=DESCRIPCION,
    openapi_tags=TAGS,
    contact={"name": "Cristian Sena — TF IA para Programadores"},
)

# Servicios respaldados por la base de datos.
_auth = ServicioAuth(RepositorioUsuariosSQL(SessionLocal))
_progreso = RepositorioProgresoSQL(SessionLocal)


# ---------- Esquemas (documentados en Swagger) ----------

class Credenciales(BaseModel):
    email: str = Field(..., examples=["demo@earhero.com"])
    password: str = Field(..., examples=["Segura99"], description="8+ caracteres, con letras y números")


class Respuesta(BaseModel):
    respuesta: str = Field(..., examples=["Do,Re,Mi"], description="Notas separadas por coma")


class UsuarioOut(BaseModel):
    id: str
    email: str


class TokenOut(BaseModel):
    token: str


class MeOut(BaseModel):
    id: str
    nivel: int
    xp: int


class EjercicioOut(BaseModel):
    nivel: int
    longitud: int
    secuencia: list[str] = Field(..., examples=[["Do", "Mi", "Sol"]])


class ResultadoOut(BaseModel):
    correcto: bool
    xp_ganado: int
    nivel: int


# ---------- Dependencias ----------

def _usuario_desde_header(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Falta token Bearer")
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return _auth.usuario_actual(token).id
    except TokenInvalidoError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


# ---------- Autenticación ----------

@app.post("/api/register", tags=["Autenticación"], response_model=UsuarioOut,
          summary="Registrar un nuevo usuario")
def register(cred: Credenciales):
    """Crea un usuario validando email y política de contraseña."""
    try:
        usuario = _auth.registrar(cred.email, cred.password)
    except AuthError as exc:
        raise HTTPException(status_code=400, detail=type(exc).__name__) from exc
    return {"id": usuario.id, "email": usuario.email}


@app.post("/api/login", tags=["Autenticación"], response_model=TokenOut,
          summary="Iniciar sesión y obtener token")
def login(cred: Credenciales):
    """Devuelve un token firmado (Bearer) válido por una hora."""
    try:
        token = _auth.login(cred.email, cred.password)
    except AuthError as exc:
        raise HTTPException(status_code=401, detail="Credenciales inválidas") from exc
    return {"token": token}


@app.get("/api/me", tags=["Autenticación"], response_model=MeOut,
         summary="Datos del usuario autenticado")
def me(user_id: str = Depends(_usuario_desde_header)):
    """Devuelve nivel y XP actuales. Requiere header `Authorization: Bearer <token>`."""
    cat, _ = _progreso.cargar_categoria(user_id)
    return {"id": user_id, "nivel": cat.nivel, "xp": cat.puntos_acumulados}


# ---------- Entrenamiento ----------

@app.post("/api/ejercicio/siguiente", tags=["Entrenamiento"], response_model=EjercicioOut,
          summary="Generar el próximo ejercicio")
def siguiente(user_id: str = Depends(_usuario_desde_header)):
    """Genera un ejercicio según el nivel del usuario y lo deja como pendiente."""
    cat, gestor = _progreso.cargar_categoria(user_id)
    ejercicio = TutorIA(gestor).generar_siguiente_ejercicio(cat)
    _progreso.guardar_pendiente(user_id, ejercicio)
    return {
        "nivel": ejercicio.nivel,
        "longitud": len(ejercicio.secuencia),
        "secuencia": ejercicio.secuencia,
    }


@app.post("/api/ejercicio/responder", tags=["Entrenamiento"], response_model=ResultadoOut,
          summary="Responder el ejercicio pendiente")
def responder(payload: Respuesta, user_id: str = Depends(_usuario_desde_header)):
    """Valida la respuesta contra el ejercicio pendiente, otorga XP y ajusta dificultad."""
    ejercicio = _progreso.cargar_pendiente(user_id)
    if ejercicio is None:
        raise HTTPException(status_code=400, detail="No hay ejercicio pendiente")
    cat, gestor = _progreso.cargar_categoria(user_id)
    resultado = TutorIA(gestor).validar_respuesta(payload.respuesta, ejercicio, cat)
    _progreso.guardar_categoria(user_id, cat, gestor)
    _progreso.actualizar_racha(user_id)
    _progreso.resolver_pendiente(user_id)
    return {
        "correcto": resultado.correcto,
        "xp_ganado": resultado.xp_ganado,
        "nivel": resultado.nivel_categoria,
    }


# Crea las tablas al importar (en Docker la BD ya está disponible por depends_on).
init_db()

# --- Frontend estático (se monta DESPUÉS de las rutas /api) ---
_FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"
if _FRONTEND_DIR.is_dir():
    app.mount("/", StaticFiles(directory=str(_FRONTEND_DIR), html=True), name="frontend")
