"""Sistema de autenticación de EarHero AI (RF-01).

Implementa registro, login, logout y verificación de sesión usando un token
firmado (HMAC-SHA256) al estilo JWT, pero con solo la librería estándar para
mantener el proyecto liviano y reproducible en CI.

Mapea la clase `Usuario` del diagrama UML de la Unidad 4:
    +registrar(email, pass) bool
    +login(email, pass) TokenJWT
    +logout() void
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass, field

# Clave de firma. En producción vendría de una variable de entorno / secret.
_SECRET = os.environ.get("EARHERO_SECRET", "dev-secret-no-usar-en-prod").encode()

# Parámetros de hashing PBKDF2.
_PBKDF2_ITERATIONS = 120_000
_TOKEN_TTL_SECONDS = 3600  # RF-01: sesión de 1 hora.


class AuthError(Exception):
    """Error genérico de autenticación."""


class EmailInvalidoError(AuthError):
    """El email no tiene un formato mínimamente válido."""


class PasswordDebilError(AuthError):
    """La contraseña no cumple la política mínima."""


class UsuarioYaExisteError(AuthError):
    """Ya hay un usuario registrado con ese email."""


class CredencialesInvalidasError(AuthError):
    """Email o contraseña incorrectos."""


class TokenInvalidoError(AuthError):
    """El token está mal formado, expiró o la firma no coincide."""


def _b64u_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64u_decode(data: str) -> bytes:
    pad = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + pad)


def email_valido(email: str) -> bool:
    """Validación deliberadamente simple (no pretende ser RFC 5322)."""
    if not isinstance(email, str):
        return False
    email = email.strip()
    if email.count("@") != 1:
        return False
    local, _, dominio = email.partition("@")
    if not local or not dominio or "." not in dominio:
        return False
    if dominio.startswith(".") or dominio.endswith("."):
        return False
    return " " not in email


def password_segura(password: str) -> bool:
    """Política mínima: 8+ caracteres, al menos una letra y un dígito."""
    if not isinstance(password, str) or len(password) < 8:
        return False
    tiene_letra = any(c.isalpha() for c in password)
    tiene_digito = any(c.isdigit() for c in password)
    return tiene_letra and tiene_digito


def hash_password(password: str, salt: bytes | None = None) -> str:
    """Devuelve 'salt_hex$hash_hex' usando PBKDF2-HMAC-SHA256."""
    if salt is None:
        salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, _PBKDF2_ITERATIONS)
    return f"{salt.hex()}${dk.hex()}"


def verificar_password(password: str, almacenado: str) -> bool:
    """Comparación en tiempo constante contra el hash almacenado."""
    try:
        salt_hex, _ = almacenado.split("$", 1)
    except ValueError:
        return False
    salt = bytes.fromhex(salt_hex)
    calculado = hash_password(password, salt)
    return hmac.compare_digest(calculado, almacenado)


def generar_token(user_id: str, ttl: int = _TOKEN_TTL_SECONDS) -> str:
    """Genera un token firmado (header.payload.signature)."""
    header = {"alg": "HS256", "typ": "JWT"}
    ahora = int(time.time())
    payload = {"sub": user_id, "iat": ahora, "exp": ahora + ttl}
    h = _b64u_encode(json.dumps(header, separators=(",", ":")).encode())
    p = _b64u_encode(json.dumps(payload, separators=(",", ":")).encode())
    firma = hmac.new(_SECRET, f"{h}.{p}".encode(), hashlib.sha256).digest()
    return f"{h}.{p}.{_b64u_encode(firma)}"


def verificar_token(token: str) -> str:
    """Valida firma y expiración. Devuelve el user_id (sub) o lanza error."""
    if not isinstance(token, str) or token.count(".") != 2:
        raise TokenInvalidoError("Formato de token inválido")
    h, p, s = token.split(".")
    esperada = hmac.new(_SECRET, f"{h}.{p}".encode(), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64u_encode(esperada), s):
        raise TokenInvalidoError("Firma inválida")
    try:
        payload = json.loads(_b64u_decode(p))
    except (ValueError, json.JSONDecodeError) as exc:
        raise TokenInvalidoError("Payload corrupto") from exc
    if int(time.time()) >= payload.get("exp", 0):
        raise TokenInvalidoError("Token expirado")
    return payload["sub"]


@dataclass
class Usuario:
    id: str
    email: str
    password_hash: str
    creado_en: float = field(default_factory=time.time)


class RepositorioMemoria:
    """Repositorio de usuarios en memoria (default, usado por los tests)."""

    def __init__(self) -> None:
        self._por_email: dict[str, Usuario] = {}

    def buscar_por_email(self, email: str) -> Usuario | None:
        return self._por_email.get(email)

    def buscar_por_id(self, user_id: str) -> Usuario | None:
        for u in self._por_email.values():
            if u.id == user_id:
                return u
        return None

    def agregar(self, usuario: Usuario) -> None:
        self._por_email[usuario.email] = usuario


class ServicioAuth:
    """Casos de uso de autenticación sobre un repositorio intercambiable.

    Por defecto usa un repositorio en memoria, de modo que los tests son
    deterministas y no dependen de una base de datos. La API inyecta un
    repositorio respaldado por SQLAlchemy (ver repos.RepositorioUsuariosSQL).
    """

    def __init__(self, repo=None) -> None:
        self._repo = repo or RepositorioMemoria()

    def registrar(self, email: str, password: str) -> Usuario:
        email_norm = (email or "").strip().lower()
        if not email_valido(email_norm):
            raise EmailInvalidoError(email)
        if not password_segura(password):
            raise PasswordDebilError("La contraseña no cumple la política mínima")
        if self._repo.buscar_por_email(email_norm) is not None:
            raise UsuarioYaExisteError(email_norm)
        usuario = Usuario(
            id=secrets.token_hex(8),
            email=email_norm,
            password_hash=hash_password(password),
        )
        self._repo.agregar(usuario)
        return usuario

    def login(self, email: str, password: str) -> str:
        email_norm = (email or "").strip().lower()
        usuario = self._repo.buscar_por_email(email_norm)
        if usuario is None or not verificar_password(password, usuario.password_hash):
            raise CredencialesInvalidasError("Email o contraseña incorrectos")
        return generar_token(usuario.id)

    def usuario_actual(self, token: str) -> Usuario:
        user_id = verificar_token(token)
        usuario = self._repo.buscar_por_id(user_id)
        if usuario is None:
            raise TokenInvalidoError("Usuario no encontrado para el token")
        return usuario
