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
  api.py            #   API REST FastAPI + página de login
tests/
  unit/             # Pruebas unitarias (pytest)
  functional/       # Pruebas funcionales: API (TestClient) y UI (Playwright)
tools/agents.py     # Pipeline multi-agente Ollama (la "herramienta de IA")
.github/workflows/  # Pipeline CI/CD (GitHub Actions)
docs/               # Reportes de cobertura + salidas de los agentes + informe
```

## Cómo correr (local)

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

El módulo `tools/agents.py` arma un pipeline de **4 agentes** (un modelo por rol):

| Rol         | Modelo             | Tarea                                      |
|-------------|--------------------|--------------------------------------------|
| Arquitecto  | `llama3.1:8b`      | Mapea escenarios de prueba del módulo      |
| Tester      | `qwen2.5-coder:3b` | Escribe los tests pytest                   |
| Revisor     | `phi4-mini`        | Detecta redundancias y casos borde faltantes |
| Redactor    | `llama3.1:8b`      | Redacta la reflexión crítica del informe   |

```bash
ollama serve   # en otra terminal
python tools/agents.py --modulo src/earhero/dificultad.py --fase todo
python tools/agents.py --fase redactar --cobertura-antes 70 --cobertura-despues 98
```

Las salidas quedan en `docs/agente_*.md`. **Ollama no corre en CI**: se usa
localmente para *generar/optimizar* tests; al repo viajan los tests ya escritos.

## Cobertura

| Momento  | Cobertura |
|----------|-----------|
| Antes (solo happy-path) | **70 %** |
| Después (con casos borde sugeridos por los agentes) | **98 %** |

Reporte navegable: `docs/coverage_html/index.html`.
