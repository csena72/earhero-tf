# Spec 01 — Arquitectura

## Modelo: Monolítica Modular
Justificación (RNF-01 < 2s): el flujo crítico
`TutorIA.validarRespuesta() → GestorDificultadAdaptativa.ajustar() →
generarSiguienteEjercicio()` ocurre en el mismo proceso, en memoria, sin
overhead de red entre módulos. Por eso NO se usan microservicios.

## Implementación elegida
El documento describe el monolito en Node.js/Express. El Trabajo Final permite
elegir lenguaje (Python/JS/Java); se implementa el **mismo patrón monolítico
modular en Python con FastAPI**. Se respetan arquitectura, entidades, estilos y
persistencia; sólo cambia el lenguaje del servidor (decisión justificada en el
informe).

## Módulos del monolito (un solo proceso)
- **Autenticación JWT** → `auth.py` (registro, login, tokens firmados).
- **TutorIA** → `tutor.py` (valida respuesta, genera siguiente ejercicio).
- **GestorDificultadAdaptativa** → `dificultad.py` (sube/baja nivel por ventana).
- **Progreso** → `progreso.py` (XP, niveles por categoría, racha).
- **MotorAudioIA** → en el MVP el audio se sintetiza en el cliente (Web Audio
  API). En el diseño era server-side con caché Redis.
- **LaboratorioSpotify** → extensión futura (Spotify Web API vía OAuth 2.0).

## Capas de despliegue (diagrama del documento)
- **Cliente:** app móvil (React Native) + Dashboard web (React). En el MVP:
  frontend web servido por la misma app.
- **Red:** Cloudflare (CDN/DDoS) + Nginx (load balancer). Fuera del MVP.
- **Servidor de Aplicación:** monolito modular (FastAPI/uvicorn).
- **Persistencia:** **PostgreSQL** (usuarios, perfiles, progreso, sesiones de
  ejercicio) + **Redis** (caché de AudioBuffers). En el MVP se implementa
  PostgreSQL; Redis queda documentado (el audio es client-side, no requiere caché).
- **Servicio externo:** Spotify Web API (OAuth 2.0). Extensión futura.

## Contenedores (Docker)
- `db`: postgres:16-alpine con volumen persistente y healthcheck.
- `earhero`: la app (FastAPI + frontend), `depends_on: db (healthy)`,
  `DATABASE_URL=postgresql://...`.
