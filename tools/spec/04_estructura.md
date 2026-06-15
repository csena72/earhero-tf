# Spec 04 — Estructura del proyecto (objetivo)

> Estructura que los agentes deben respetar al generar/regenerar la app.
> Refleja la arquitectura monolítica modular.

```
earhero-tf/
├── src/earhero/            # Monolito modular (un proceso)
│   ├── __init__.py
│   ├── db.py               # engine/session SQLAlchemy (DATABASE_URL)
│   ├── models.py           # ORM: usuarios, perfiles, progreso, sesiones
│   ├── repos.py            # repositorios SQL (puente dominio <-> ORM)
│   ├── auth.py             # módulo Autenticación JWT (RF-01)
│   ├── progreso.py         # XP, niveles por categoría, racha (RF-02)
│   ├── dificultad.py       # GestorDificultadAdaptativa (RF-04)
│   ├── tutor.py            # TutorIA (RF-03)
│   └── api.py              # FastAPI: endpoints + Swagger + monta frontend
├── frontend/               # Cliente web (Cyber-Arcade, modo oscuro)
│   ├── index.html
│   ├── styles.css          # usa los tokens del Spec 03
│   └── app.js              # fetch a la API + Web Audio API
├── tests/
│   ├── unit/               # pytest sobre la lógica
│   └── functional/         # API (TestClient) + UI (Playwright)
├── tools/                  # pipelines de agentes (este directorio)
│   ├── spec/               # specs derivados del documento (esta carpeta)
│   ├── ollama_client.py    # cliente Ollama compartido
│   ├── agents.py           # agentes que generan/optimizan TESTS
│   └── build_app.py        # agentes que generan la APLICACIÓN
├── .github/workflows/ci.yml
├── Dockerfile
├── docker-compose.yml      # servicios: db (postgres) + earhero
├── requirements.txt
└── pyproject.toml
```

## Reglas
- Todo el dominio vive en `src/earhero/` (monolito).
- La API documenta cada endpoint para Swagger (`/docs`).
- La persistencia es PostgreSQL en docker-compose, SQLite en tests.
- El frontend NO tiene build step (HTML/CSS/JS plano) para que Docker sea trivial.
