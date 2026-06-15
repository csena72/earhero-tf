#!/usr/bin/env python3
"""Pipeline multi-agente local con Ollama para asistir el diseño de pruebas.

Esta es la "herramienta de IA" del TF: en vez de GitHub Copilot (en la nube),
usamos varios modelos locales servidos por Ollama, cada uno con un rol distinto.
El pipeline es SECUENCIAL a propósito: Ollama carga/descarga un modelo por vez,
así no necesitás tener varios modelos de 5 GB en RAM/VRAM a la vez.

Roles y modelos (ajustables con --map):
  1. ARQUITECTO  (llama3.1:8b)      -> lee un módulo y mapea escenarios de prueba
  2. TESTER      (qwen2.5-coder:3b) -> escribe tests pytest para esos escenarios
  3. REVISOR     (phi4-mini)        -> detecta redundancias y casos borde faltantes
  4. REDACTOR    (llama3.1:8b)      -> redacta la reflexión crítica del informe

NO se ejecuta en CI: corre localmente, durante el desarrollo, para *generar*
y *optimizar* los tests. Lo que viaja al CI son los tests ya commiteados.

Uso:
    python tools/agents.py --modulo src/earhero/dificultad.py --fase mapear
    python tools/agents.py --modulo src/earhero/dificultad.py --fase todo
    python tools/agents.py --fase redactar --cobertura-antes 70 --cobertura-despues 98
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"

# Asignación rol -> modelo. Editá esto si querés probar otros agentes.
AGENTES = {
    "arquitecto": "llama3.1:8b",
    "tester": "qwen2.5-coder:3b",
    "revisor": "phi4-mini:latest",
    "redactor": "llama3.1:8b",
}

PROMPTS = {
    "arquitecto": (
        "Sos un QA senior. Analizá el siguiente módulo Python y devolvé una lista "
        "numerada de escenarios de prueba (happy path, casos borde, errores y ramas "
        "condicionales). Para cada uno indicá: entrada, acción y resultado esperado. "
        "Sé exhaustivo con los límites y las excepciones.\n\n=== MÓDULO ===\n{contenido}"
    ),
    "tester": (
        "Sos un desarrollador experto en pytest. A partir de estos escenarios, escribí "
        "un archivo de tests pytest COMPLETO y ejecutable. Usá parametrize donde aporte, "
        "fixtures cuando convenga y nombres descriptivos en español. Devolvé SOLO código "
        "Python, sin explicaciones.\n\n=== ESCENARIOS ===\n{contenido}"
    ),
    "revisor": (
        "Sos un revisor de código. Recibís una suite de tests pytest. Señalá: (1) tests "
        "redundantes que se pueden unificar con parametrize, (2) ramas o casos borde que "
        "FALTAN cubrir, (3) cualquier antipatrón. Devolvé un informe breve con bullets y "
        "una recomendación final.\n\n=== TESTS ===\n{contenido}"
    ),
    "redactor": (
        "Sos un estudiante de ingeniería redactando la reflexión crítica de un trabajo "
        "final sobre testing asistido por IA. La cobertura subió de {antes}% a {despues}%. "
        "Escribí 3 párrafos: (1) decisiones de diseño de pruebas y por qué, (2) cómo "
        "ayudaron (y dónde fallaron) los modelos locales de Ollama frente a Copilot, "
        "(3) cuándo conviene automatizar y cuándo no. Tono profesional, en español."
    ),
}


import sys as _sys
_sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parent))
from ollama_client import ollama_generar  # cliente compartido



def correr_agente(rol: str, **fmt) -> str:
    modelo = AGENTES[rol]
    prompt = PROMPTS[rol].format(**fmt)
    print(f"\n[{rol.upper()}] usando modelo '{modelo}'...", file=sys.stderr)
    salida = ollama_generar(modelo, prompt)
    destino = Path("docs") / f"agente_{rol}.md"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(salida, encoding="utf-8")
    print(f"  -> guardado en {destino}", file=sys.stderr)
    return salida


def main() -> int:
    ap = argparse.ArgumentParser(description="Pipeline multi-agente Ollama para el TF")
    ap.add_argument("--modulo", help="Ruta al módulo .py a analizar")
    ap.add_argument(
        "--fase",
        choices=["mapear", "escribir", "revisar", "redactar", "todo"],
        default="todo",
    )
    ap.add_argument("--cobertura-antes", type=int, default=70)
    ap.add_argument("--cobertura-despues", type=int, default=98)
    ap.add_argument(
        "--map", action="append", default=[],
        help="Sobrescribe rol=modelo, ej: --map tester=qwen2.5-coder:1.5b",
    )
    args = ap.parse_args()

    for m in args.map:
        rol, _, modelo = m.partition("=")
        if rol in AGENTES and modelo:
            AGENTES[rol] = modelo

    contenido = ""
    if args.modulo:
        contenido = Path(args.modulo).read_text(encoding="utf-8")

    try:
        if args.fase in ("mapear", "todo"):
            escenarios = correr_agente("arquitecto", contenido=contenido)
            contenido = escenarios
        if args.fase in ("escribir", "todo"):
            tests = correr_agente("tester", contenido=contenido)
            contenido = tests
        if args.fase in ("revisar", "todo"):
            correr_agente("revisor", contenido=contenido)
        if args.fase in ("redactar", "todo"):
            correr_agente(
                "redactor",
                antes=args.cobertura_antes,
                despues=args.cobertura_despues,
            )
    except RuntimeError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1

    print("\nListo. Revisá los archivos docs/agente_*.md", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
