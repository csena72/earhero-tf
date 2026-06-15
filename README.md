# EarHero AI — Trabajo Final: Suite de pruebas automatizadas asistida por IA

Continuación de la actividad **M1-U4 (EarHero AI)**. Este repo implementa el
módulo de software (autenticación + lógica de entrenamiento adaptativo) y una
**suite completa de pruebas automatizadas** —unitarias y funcionales— optimizada
y asistida por **modelos de IA locales (Ollama)**, con cobertura y CI/CD.

## Estructura

```
src/earhero/        # Módulo bajo prueba
  auth.py           #   Registro, login, tokens firmados (RF-01)
  progreso.py       #   XP, niveles por categoría, racha (RF-02, Perfil)
  dificultad.py     #   Gestor de dificultad adaptativa (RF-04)
  tutor.py          #   TutorIA: valida respuestas y genera ejercicios
  api.py            #   API REST FastAPI + sirve el frontend
frontend/           # Frontend (HTML/CSS/JS, sin build) con audio Web Audio API
  index.html
  styles.css
  app.js
Dockerfile          # Imagen de la app (API + frontend)
docker-compose.yml  # Levanta la app con un comando
tests/
  unit/             # Pruebas unitarias (pytest)
  functional/       # Pruebas funcionales: API (TestClient) y UI (Playwright)
tools/agents.py     # Pipeline multi-agente Ollama (la "herramienta de IA")
.github/workflows/  # Pipeline CI/CD (GitHub Actions)
docs/               # Reportes de cobertura + salidas de los agentes + informe
```

## Cómo correr la aplicación

### Opción A — Docker (recomendada para la entrega)

```bash
docker compose up --build
```

Abrí http://localhost:8000 — vas a poder registrarte, iniciar sesión y hacer
el entrenamiento auditivo (la app reproduce una secuencia de notas y tenés que
reproducirla con los botones). Para frenar: `docker compose down`.

### Opción B — Sin Docker

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn earhero.api:app --host 0.0.0.0 --port 8000
```


## Cómo correr (tests)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[test]"
python -m playwright install chromium     # solo para los tests de UI

# Toda la suite con cobertura
pytest --cov --cov-report=term-missing --cov-report=html:docs/coverage_html

# Solo unitarias / solo funcionales
pytest tests/unit
pytest tests/functional

# Levantar la API
uvicorn earhero.api:app --reload    # http://localhost:8000
```

## Asistencia con IA (Ollama, local)

Hay dos pipelines de agentes en `tools/`, ambos sobre modelos locales de Ollama
(un modelo por rol, ejecución secuencial). Los specs en `tools/spec/` —derivados
del documento de diseño— son la verdad que los agentes respetan.

### `tools/agents.py` — genera/optimiza los TESTS

| Rol | Modelo | Tarea |
|-----|--------|-------|
| Arquitecto | `llama3.1:8b` | Mapea escenarios de prueba |
| Tester | `qwen2.5-coder:3b` | Escribe los tests pytest |
| Revisor | `phi4-mini` | Redundancias y casos borde |
| Redactor | `llama3.1:8b` | Reflexión crítica del informe |

```bash
ollama serve
python tools/agents.py --modulo src/earhero/dificultad.py --fase todo
```

### `tools/build_app.py` — genera la APLICACIÓN

| Rol | Modelo | Tarea |
|-----|--------|-------|
| Arquitecto | `llama3.1:8b` | Consolida arquitectura y estructura |
| Backend | `qwen2.5-coder:3b` | API FastAPI + ORM + Swagger |
| Frontend | `qwen2.5-coder:3b` | HTML/CSS/JS con la paleta del documento |
| DevOps | `phi4-mini` | Dockerfile + docker-compose (Postgres) |
| QA | `llama3.1:8b` | Corre la suite real y reporta |

```bash
python tools/build_app.py --fase todo        # borradores en docs/generado/
python tools/build_app.py --fase qa          # corre pytest y resume
python tools/build_app.py --fase backend --apply   # escribe en el proyecto
```

Por defecto los agentes escriben **borradores** en `docs/generado/` y no pisan
el código validado del repo (que es el andamiaje que garantiza que la app
funciona). Con `--apply` además copian su salida a la ruta real; en ese caso
hay que correr `pytest` antes de commitear. **Ollama no corre en CI**: se usa
localmente para generar/optimizar; al repo viajan los archivos ya validados.

## Base de datos y documentación

- Persistencia con **SQLAlchemy**: PostgreSQL en `docker-compose`, SQLite en
  tests. Tablas: `usuarios`, `perfiles`, `progreso`, `sesiones_ejercicio`.
- **Swagger UI** autogenerada en `/docs` (y ReDoc en `/redoc`).

## Cobertura

| Momento  | Cobertura |
|----------|-----------|
| Antes (solo happy-path) | **70 %** |
| Después (con casos borde sugeridos por los agentes) | **98 %** |

Reporte navegable: `docs/coverage_html/index.html`.
