"""Modelos ORM de EarHero AI.

Mapean las entidades de persistencia del documento de diseño:
usuarios, perfiles, progreso (NivelCategoria) y sesiones de ejercicio.
"""

from __future__ import annotations

import time

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint, func,
)
from sqlalchemy.orm import relationship

from .db import Base


class UsuarioORM(Base):
    __tablename__ = "usuarios"

    id = Column(String(32), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    creado_en = Column(Float, default=time.time)

    perfil = relationship("PerfilORM", uselist=False, back_populates="usuario",
                          cascade="all, delete-orphan")
    progreso = relationship("ProgresoORM", back_populates="usuario",
                            cascade="all, delete-orphan")
    sesiones = relationship("SesionEjercicioORM", back_populates="usuario",
                            cascade="all, delete-orphan")


class PerfilORM(Base):
    __tablename__ = "perfiles"

    usuario_id = Column(String(32), ForeignKey("usuarios.id"), primary_key=True)
    nivel_global = Column(Integer, default=1)
    racha = Column(Integer, default=0)
    ultima_sesion = Column(DateTime, nullable=True)

    usuario = relationship("UsuarioORM", back_populates="perfil")


class ProgresoORM(Base):
    __tablename__ = "progreso"
    __table_args__ = (UniqueConstraint("usuario_id", "tipo", name="uq_usuario_tipo"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(String(32), ForeignKey("usuarios.id"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)
    nivel = Column(Integer, default=1)
    puntos_acumulados = Column(Integer, default=0)
    aciertos = Column(Integer, default=0)
    intentos = Column(Integer, default=0)
    # Ventana reciente de respuestas para el gestor de dificultad ("1"/"0").
    historial = Column(String(64), default="")

    usuario = relationship("UsuarioORM", back_populates="progreso")


class SesionEjercicioORM(Base):
    __tablename__ = "sesiones_ejercicio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    usuario_id = Column(String(32), ForeignKey("usuarios.id"), nullable=False, index=True)
    tipo = Column(String(20), nullable=False)
    nivel = Column(Integer, nullable=False)
    secuencia = Column(String(255), nullable=False)  # "Do,Re,Mi"
    estado = Column(String(20), default="pendiente")  # pendiente | resuelto
    creado_en = Column(DateTime, server_default=func.now())

    usuario = relationship("UsuarioORM", back_populates="sesiones")
