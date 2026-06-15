"""Configuración de base de datos (SQLAlchemy).

La URL se toma de la variable de entorno DATABASE_URL:
  - Producción / docker-compose:  postgresql://earhero:earhero@db:5432/earhero
  - Desarrollo / tests (default):  sqlite (en memoria o archivo)

Esto permite correr los tests con SQLite (rápido, sin servicios) y la app real
con PostgreSQL, sin cambiar el código.
"""

from __future__ import annotations

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./earhero.db")

# SQLite necesita ajustes para usarse desde varios hilos (uvicorn / tests).
_es_sqlite = DATABASE_URL.startswith("sqlite")
_es_memoria = _es_sqlite and (":memory:" in DATABASE_URL or DATABASE_URL == "sqlite://")

_connect_args = {"check_same_thread": False} if _es_sqlite else {}
_kwargs = {"connect_args": _connect_args}
if _es_memoria:
    # Una única conexión compartida para que la BD en memoria persista
    # entre hilos durante los tests.
    _kwargs["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
Base = declarative_base()


def init_db() -> None:
    """Crea las tablas si no existen."""
    from . import models  # noqa: F401  (registra los modelos en Base.metadata)

    Base.metadata.create_all(bind=engine)


def reset_db() -> None:
    """Borra y recrea todas las tablas. Usado por los tests."""
    from . import models  # noqa: F401

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
