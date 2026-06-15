# Dockerfile para el monolito modular de EarHero con FastAPI y Uvicorn
FROM python:3.12-slim

WORKDIR /app

COPY ./src/earhero/db.py ./
COPY ./src/earhero/models.py ./
COPY ./src/earhero/repos.py ./
COPY ./src/earhero/auth.py ./
COPY ./src/earhero/progreso.py ./
COPY ./src/earhero/dificultad.py ./
COPY ./src/earhero/tutor.py ./
COPY ./src/earhero/api.py ./

RUN pip install fastapi uvicorn psycopg2-binary requests SQLAlchemy python-dotenv

CMD ["uvicorn", "src:app.main:run"]