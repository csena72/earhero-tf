"""Repositorios SQLAlchemy: puente entre el dominio y la base de datos.

Mantienen el dominio (auth.Usuario, progreso.NivelCategoria, tutor.Ejercicio)
desacoplado del ORM. La API usa estos repositorios; los tests unitarios usan
el repositorio en memoria de auth.py.
"""

from __future__ import annotations

from datetime import date

from .auth import Usuario
from .dificultad import GestorDificultadAdaptativa
from .models import PerfilORM, ProgresoORM, SesionEjercicioORM, UsuarioORM
from .progreso import NivelCategoria, Perfil, TipoModulo
from .tutor import Ejercicio


def _hist_a_str(valores: list[bool]) -> str:
    return "".join("1" if v else "0" for v in valores)


def _str_a_hist(s: str | None) -> list[bool]:
    return [c == "1" for c in (s or "")]


class RepositorioUsuariosSQL:
    """Implementa la interfaz que espera auth.ServicioAuth, sobre SQLAlchemy."""

    def __init__(self, session_factory) -> None:
        self._sf = session_factory

    def buscar_por_email(self, email: str) -> Usuario | None:
        with self._sf() as s:
            row = s.query(UsuarioORM).filter_by(email=email).one_or_none()
            return self._a_dominio(row)

    def buscar_por_id(self, user_id: str) -> Usuario | None:
        with self._sf() as s:
            row = s.get(UsuarioORM, user_id)
            return self._a_dominio(row)

    def agregar(self, usuario: Usuario) -> None:
        with self._sf() as s:
            s.add(UsuarioORM(
                id=usuario.id, email=usuario.email,
                password_hash=usuario.password_hash, creado_en=usuario.creado_en,
            ))
            s.add(PerfilORM(usuario_id=usuario.id))
            s.commit()

    @staticmethod
    def _a_dominio(row: UsuarioORM | None) -> Usuario | None:
        if row is None:
            return None
        return Usuario(id=row.id, email=row.email,
                       password_hash=row.password_hash, creado_en=row.creado_en)


class RepositorioProgresoSQL:
    """Carga/guarda progreso, perfil y la sesión de ejercicio pendiente."""

    def __init__(self, session_factory) -> None:
        self._sf = session_factory

    def cargar_categoria(self, user_id: str, tipo=TipoModulo.NOTAS):
        """Devuelve (NivelCategoria, GestorDificultadAdaptativa) con su estado."""
        with self._sf() as s:
            row = self._row_categoria(s, user_id, tipo)
            cat = NivelCategoria(
                tipo=TipoModulo(row.tipo), nivel=row.nivel,
                puntos_acumulados=row.puntos_acumulados,
                aciertos=row.aciertos, intentos=row.intentos,
            )
            gestor = GestorDificultadAdaptativa()
            gestor.importar_historial(_str_a_hist(row.historial))
            return cat, gestor

    def guardar_categoria(self, user_id: str, cat: NivelCategoria,
                          gestor: GestorDificultadAdaptativa) -> None:
        with self._sf() as s:
            row = self._row_categoria(s, user_id, cat.tipo)
            row.nivel = cat.nivel
            row.puntos_acumulados = cat.puntos_acumulados
            row.aciertos = cat.aciertos
            row.intentos = cat.intentos
            row.historial = _hist_a_str(gestor.exportar_historial())
            s.commit()

    def actualizar_racha(self, user_id: str, hoy: date | None = None) -> int:
        with self._sf() as s:
            perfil_row = s.get(PerfilORM, user_id)
            perfil = Perfil(
                racha=perfil_row.racha,
                ultima_sesion=perfil_row.ultima_sesion.date()
                if perfil_row.ultima_sesion else None,
            )
            racha = perfil.actualizar_racha(hoy)
            perfil_row.racha = racha
            from datetime import datetime
            perfil_row.ultima_sesion = datetime.combine(
                perfil.ultima_sesion, datetime.min.time())
            s.commit()
            return racha

    def guardar_pendiente(self, user_id: str, ejercicio: Ejercicio) -> None:
        with self._sf() as s:
            s.query(SesionEjercicioORM).filter_by(
                usuario_id=user_id, estado="pendiente").delete()
            s.add(SesionEjercicioORM(
                usuario_id=user_id, tipo=ejercicio.tipo.value,
                nivel=ejercicio.nivel, secuencia=",".join(ejercicio.secuencia),
                estado="pendiente",
            ))
            s.commit()

    def cargar_pendiente(self, user_id: str) -> Ejercicio | None:
        with self._sf() as s:
            row = s.query(SesionEjercicioORM).filter_by(
                usuario_id=user_id, estado="pendiente").first()
            if row is None:
                return None
            return Ejercicio(tipo=TipoModulo(row.tipo), nivel=row.nivel,
                             secuencia=row.secuencia.split(","))

    def resolver_pendiente(self, user_id: str) -> None:
        with self._sf() as s:
            s.query(SesionEjercicioORM).filter_by(
                usuario_id=user_id, estado="pendiente").update({"estado": "resuelto"})
            s.commit()

    @staticmethod
    def _row_categoria(s, user_id: str, tipo) -> ProgresoORM:
        tipo_val = tipo.value if hasattr(tipo, "value") else tipo
        row = s.query(ProgresoORM).filter_by(
            usuario_id=user_id, tipo=tipo_val).one_or_none()
        if row is None:
            row = ProgresoORM(usuario_id=user_id, tipo=tipo_val, historial="")
            s.add(row)
            s.commit()
        return row
