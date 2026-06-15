#!/usr/bin/env python3
"""Pipeline multi-agente local (Ollama) que GENERA la aplicación EarHero AI.

Mismo enfoque que tools/agents.py (que generaba los tests), pero acá los agentes
generan la APLICACIÓN COMPLETA siguiendo el documento de diseño: backend con API
documentada en Swagger, base de datos, frontend con la estética del documento y
Docker. Los specs en tools/spec/ (derivados del documento) son la verdad que los
agentes deben respetar.

Roles (un modelo por rol, ejecución SECUENCIAL para no saturar la RAM):
  ARQUITECTO (llama3.1:8b)      -> consolida arquitectura y estructura
  BACKEND    (qwen2.5-coder:3b) -> API FastAPI + modelos ORM + Swagger
  FRONTEND   (qwen2.5-coder:3b) -> HTML/CSS/JS con la paleta del documento
  DEVOPS     (phi4-mini)        -> Dockerfile + docker-compose (Postgres)
  QA         (llama3.1:8b)      -> corre la suite de tests y reporta

Por defecto los agentes escriben BORRADORES en docs/generado/ (no pisan el
código validado del repo). Con --apply, además copian su salida a la ruta real
del proyecto; en ese caso DEBÉS correr pytest después, porque la salida de un
modelo chico puede no compilar. El andamiaje del repo es la referencia que
garantiza que la app funciona.

Uso:
  ollama serve                                   # en otra terminal
  python tools/build_app.py --fase todo
  python tools/build_app.py --fase frontend
  python tools/build_app.py --fase qa            # corre los tests reales
  python tools/build_app.py --fase backend --apply   # escribe en el proyecto
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ollama_client import extraer_codigo, guardar, leer_specs, ollama_generar  # noqa: E402

RAIZ = Path(__file__).resolve().parents[1]
SPEC_DIR = Path(__file__).resolve().parent / "spec"
OUT = RAIZ / "docs" / "generado"

AGENTES = {
    "arquitecto": "llama3.1:8b",
    "backend": "qwen2.5-coder:3b",
    "frontend": "qwen2.5-coder:3b",
    "devops": "phi4-mini:latest",
    "qa": "llama3.1:8b",
}

# Cada fase: (specs que lee, prompt, archivos de salida que intenta producir)
REGLA_COMUN = (
    "Respetá EXACTAMENTE los specs: arquitectura monolítica modular, las "
    "entidades del UML, la paleta de colores y la estructura de carpetas. "
    "No inventes librerías ni endpoints que no estén en los specs."
)


def correr(rol: str, prompt: str, salida: Path, solo_codigo: bool = False) -> str:
    modelo = AGENTES[rol]
    print(f"\n[{rol.upper()}] modelo '{modelo}' ...", file=sys.stderr)
    texto = ollama_generar(modelo, prompt)
    if solo_codigo:
        texto = extraer_codigo(texto)
    guardar(salida, texto)
    return texto


def fase_arquitecto():
    ctx = leer_specs(SPEC_DIR, ["00_proyecto.md", "01_arquitectura.md", "04_estructura.md"])
    prompt = (
        f"Sos arquitecto de software. {REGLA_COMUN}\n"
        "A partir de estos specs, redactá docs/generado/ARQUITECTURA.md: describí "
        "las capas, los módulos del monolito, la estructura de carpetas y las "
        "decisiones clave (por qué monolítico modular para RNF-01).\n\n" + ctx
    )
    correr("arquitecto", prompt, OUT / "ARQUITECTURA.md")


def fase_backend():
    ctx = leer_specs(SPEC_DIR, ["01_arquitectura.md", "02_entidades.md"])
    prompt = (
        f"Sos desarrollador backend Python. {REGLA_COMUN}\n"
        "Generá el archivo FastAPI 'api.py' del monolito: endpoints de registro, "
        "login (token), /api/me, /api/ejercicio/siguiente y /api/ejercicio/responder. "
        "Cada endpoint con summary/description y response_model para que Swagger "
        "(/docs) quede documentado. La persistencia es vía SQLAlchemy. Devolvé SOLO "
        "código Python.\n\n" + ctx
    )
    correr("backend", prompt, OUT / "backend" / "api.py", solo_codigo=True)

    prompt_models = (
        f"Sos desarrollador backend Python. {REGLA_COMUN}\n"
        "Generá 'models.py' con los modelos SQLAlchemy para las tablas usuarios, "
        "perfiles, progreso y sesiones_ejercicio descriptas en el spec de entidades. "
        "Devolvé SOLO código Python.\n\n" + ctx
    )
    correr("backend", prompt_models, OUT / "backend" / "models.py", solo_codigo=True)


def fase_frontend():
    ctx = leer_specs(SPEC_DIR, ["03_estilo.md", "00_proyecto.md"])
    for archivo, que in [
        ("index.html", "el HTML de la pantalla de Inicio (login/registro) y la de "
                        "Entrenamiento (botón Reproducir, grilla de notas, Responder)"),
        ("styles.css", "el CSS usando EXACTAMENTE los tokens de color del spec "
                        "(modo oscuro, glassmorphism, cards, botones grandes)"),
        ("app.js", "el JS: fetch a la API y reproducción de las notas con Web Audio API"),
    ]:
        prompt = (
            f"Sos desarrollador frontend. {REGLA_COMUN}\n"
            f"Generá {que}. Sin frameworks ni build. Devolvé SOLO el contenido del "
            f"archivo {archivo}.\n\n" + ctx
        )
        correr("frontend", prompt, OUT / "frontend" / archivo, solo_codigo=True)


def fase_devops():
    ctx = leer_specs(SPEC_DIR, ["01_arquitectura.md", "04_estructura.md"])
    correr("devops",
           f"Sos DevOps. {REGLA_COMUN}\nGenerá un Dockerfile (python:3.12-slim, "
           "uvicorn) para la app. Devolvé SOLO el Dockerfile.\n\n" + ctx,
           OUT / "devops" / "Dockerfile", solo_codigo=True)
    correr("devops",
           f"Sos DevOps. {REGLA_COMUN}\nGenerá docker-compose.yml con dos servicios: "
           "db (postgres:16-alpine con volumen y healthcheck) y earhero "
           "(depends_on db healthy, DATABASE_URL a postgres, puerto 8000). "
           "Devolvé SOLO el YAML.\n\n" + ctx,
           OUT / "devops" / "docker-compose.yml", solo_codigo=True)


def fase_qa():
    print("\n[QA] corriendo la suite real (pytest) ...", file=sys.stderr)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--cov", "--cov-report=term-missing", "-q"],
        cwd=RAIZ, capture_output=True, text=True,
    )
    reporte = (proc.stdout or "") + "\n" + (proc.stderr or "")
    ctx = "Salida de pytest:\n" + reporte[-4000:]
    resumen = ollama_generar(
        AGENTES["qa"],
        "Sos QA. Resumí en 5 bullets el resultado de esta corrida de tests "
        "(cantidad de tests, cobertura, módulos flojos) y dá una recomendación.\n\n"
        + ctx,
    )
    guardar(OUT / "QA.md", f"# Reporte QA\n\n## Salida pytest\n```\n{reporte}\n```\n\n## Resumen del agente\n{resumen}")


FASES = {
    "arquitectura": fase_arquitecto,
    "backend": fase_backend,
    "frontend": fase_frontend,
    "devops": fase_devops,
    "qa": fase_qa,
}


def aplicar_al_proyecto():
    """Copia los borradores generados a su ruta real (uso bajo tu responsabilidad)."""
    mapa = {
        OUT / "backend" / "api.py": RAIZ / "src" / "earhero" / "api.py",
        OUT / "backend" / "models.py": RAIZ / "src" / "earhero" / "models.py",
        OUT / "frontend" / "index.html": RAIZ / "frontend" / "index.html",
        OUT / "frontend" / "styles.css": RAIZ / "frontend" / "styles.css",
        OUT / "frontend" / "app.js": RAIZ / "frontend" / "app.js",
        OUT / "devops" / "Dockerfile": RAIZ / "Dockerfile",
        OUT / "devops" / "docker-compose.yml": RAIZ / "docker-compose.yml",
    }
    for origen, destino in mapa.items():
        if origen.exists():
            destino.write_text(origen.read_text(encoding="utf-8"), encoding="utf-8")
            print(f"  aplicado: {destino}", file=sys.stderr)
    print("\nAHORA CORRÉ: pytest   (verificá que siga verde antes de commitear)",
          file=sys.stderr)


def main() -> int:
    ap = argparse.ArgumentParser(description="Generador de la app EarHero con agentes Ollama")
    ap.add_argument("--fase", default="todo",
                    choices=[*FASES.keys(), "todo"])
    ap.add_argument("--apply", action="store_true",
                    help="Copia los borradores al proyecto (luego corré pytest)")
    ap.add_argument("--map", action="append", default=[],
                    help="Reasigna rol=modelo, ej: --map backend=qwen2.5-coder:1.5b")
    args = ap.parse_args()

    for m in args.map:
        rol, _, modelo = m.partition("=")
        if rol in AGENTES and modelo:
            AGENTES[rol] = modelo

    fases = list(FASES) if args.fase == "todo" else [args.fase]
    try:
        for f in fases:
            FASES[f]()
        if args.apply:
            aplicar_al_proyecto()
    except RuntimeError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    print(f"\nListo. Revisá los borradores en {OUT}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
