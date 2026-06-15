from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from enum import Enum as BaseEnum

Base = declarative_base()

class TipoModulo(BaseEnum):
    Notas = 'Notas'
    Intervalos = 'Intervalos'
    Acordes = 'Acordes'

class Usuario(Base):
    __tablename__ = 'usuarios'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    passwordHash = Column(String(128), nullable=False)
    creadoEn = Column(DateTime, default=DateTime.utcnow)

    perfil_id = Column(Integer, ForeignKey('perfiles.id'), nullable=False)
    perfil = relationship("Perfil", back_populates="usuario")

    def registrar(self, email: str, password_hash: str) -> bool:
        # Implementación del registro
        pass

    def login(self, email: str, password_hash: str) -> 'TokenJWT':
        # Implementación del login y generación de token JWT
        pass

    def logout(self) -> None:
        # Implementación del logout
        pass

class Perfil(Base):
    __tablename__ = 'perfiles'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    nivelGlobal = Column(Integer, default=0)
    racha = Column(Integer, default=0)
    ultimaSesion = Column(DateTime)

    niveles = relationship("NivelCategoria", back_populates="perfil")
    logros = relationship("Logro")

    usuario = relationship("Usuario", back_populates="perfil")

    def verProgreso(self) -> 'ResumenProgreso':
        # Implementación para obtener el resumen del progreso
        pass

    def actualizarRacha(self) -> None:
        # Implementación para actualizar la racha del perfil
        pass

    def obtenerLogrosDesbloqueados(self) -> List['Logro']:
        # Implementación para obtener los logros desbloqueados
        pass

class NivelCategoria(Base):
    __tablename__ = 'niveles_categoria'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    tipoModulo = Column(Enum(TipoModulo), nullable=False)
    nivel = Column(Integer, nullable=False)
    puntosAcumulados = Column(Integer, default=0)
    tasaAcierto = Column(Float)

    perfil = relationship("Perfil", back_populates="niveles")

class SesionEjercicio(Base):
    __tablename__ = 'sesiones_ejercicio'
    
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey('usuarios.id'), nullable=False)
    tipoModulo = Column(Enum(TipoModulo), nullable=False)
    nivel = Column(Integer, nullable=False)
    secuencia = Column(String(100))
    estado = Column(String(50))  # Puede ser 'iniciada', 'finalizada'
    creadoEn = Column(DateTime)

    usuario = relationship("Usuario", back_populates="sesiones_ejercicio")