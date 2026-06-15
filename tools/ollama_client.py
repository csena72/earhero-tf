"""Cliente mínimo para Ollama (HTTP local), compartido por los pipelines.

Sólo usa la librería estándar para no agregar dependencias.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

OLLAMA_URL = "http://localhost:11434/api/generate"


def ollama_generar(modelo: str, prompt: str, timeout: int = 1200) -> str:
    """Llama a /api/generate de Ollama (stream=False). Lanza RuntimeError si falla."""
    payload = json.dumps({"model": modelo, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read())["response"].strip()
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"No se pudo contactar a Ollama en {OLLAMA_URL}. "
            f"¿Está corriendo `ollama serve` y bajaste el modelo '{modelo}'?\n{exc}"
        ) from exc


def leer_specs(spec_dir: Path, nombres: list[str]) -> str:
    """Concatena varios archivos de spec en un solo bloque de contexto."""
    partes = []
    for n in nombres:
        ruta = spec_dir / n
        if ruta.exists():
            partes.append(f"===== {n} =====\n{ruta.read_text(encoding='utf-8')}")
    return "\n\n".join(partes)


def guardar(destino: Path, contenido: str) -> Path:
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(contenido, encoding="utf-8")
    print(f"  -> {destino}", file=sys.stderr)
    return destino


def extraer_codigo(texto: str) -> str:
    """Si el modelo devolvió ```bloques```, extrae el contenido del primero."""
    if "```" not in texto:
        return texto
    partes = texto.split("```")
    # partes[1] suele ser 'lenguaje\ncodigo...'
    bloque = partes[1] if len(partes) > 1 else texto
    lineas = bloque.split("\n")
    if lineas and lineas[0].strip().isalpha():
        lineas = lineas[1:]  # descarta el 'python'/'html' inicial
    return "\n".join(lineas).strip()
