# EarHero AI — imagen de la aplicación (API + frontend)
FROM python:3.12-slim

# Evita .pyc y fuerza logs sin buffer.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

# Dependencias primero (mejor cacheo de capas).
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código y frontend.
COPY src/ ./src/
COPY frontend/ ./frontend/

EXPOSE 8000

# Healthcheck simple contra la home del frontend.
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/')" || exit 1

CMD ["uvicorn", "earhero.api:app", "--host", "0.0.0.0", "--port", "8000"]
