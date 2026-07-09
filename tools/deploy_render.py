#!/usr/bin/env python3
"""deploy_render.py — Automatiza el deploy de EarHero AI en Render.com

Hace todo lo que harías a mano en el navegador:
  1. Crea (o reutiliza) la base de datos PostgreSQL en Render
  2. Crea (o reutiliza) el Web Service apuntando al repo de GitHub
  3. Conecta DATABASE_URL y EARHERO_SECRET como variables de entorno
  4. Dispara el primer deploy
  5. Espera a que el servicio esté live y muestra la URL pública

Uso:
  python tools/deploy_render.py --token <RENDER_API_KEY> --repo csena72/earhero-tf

Obtené tu API key en: https://dashboard.render.com/u/settings → API Keys → Create API Key

También puede correr desde GitHub Actions (ver abajo). En ese caso el token
viene de un secret y no lo escribís en ningún archivo.

Requisitos: solo stdlib de Python 3.10+. Sin dependencias externas.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from typing import Any

BASE = "https://api.render.com/v1"
HEADERS_BASE = {"Accept": "application/json", "Content-Type": "application/json"}


# ── helpers HTTP ──────────────────────────────────────────────────────────────

def _req(method: str, path: str, token: str, body: dict | None = None) -> Any:
    url = f"{BASE}{path}"
    data = json.dumps(body).encode() if body else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={**HEADERS_BASE, "Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as exc:
        detalle = exc.read().decode(errors="replace")
        raise RuntimeError(f"Render API {method} {path} → {exc.code}: {detalle}") from exc


def get(path, token): return _req("GET", path, token)
def post(path, token, body): return _req("POST", path, token, body)
def patch(path, token, body): return _req("PATCH", path, token, body)


# ── helpers de negocio ────────────────────────────────────────────────────────

def listar_servicios(token: str) -> list[dict]:
    resp = get("/services?limit=100", token)
    # La API devuelve [{service: {...}}, ...]
    return [item["service"] for item in (resp if isinstance(resp, list) else [])]


def listar_postgres(token: str) -> list[dict]:
    resp = get("/postgres?limit=100", token)
    return [item["postgres"] for item in (resp if isinstance(resp, list) else [])]


def buscar_por_nombre(lista: list[dict], nombre: str) -> dict | None:
    return next((s for s in lista if s.get("name") == nombre), None)


def crear_postgres(token: str, nombre: str, region: str) -> dict:
    print(f"  Creando PostgreSQL '{nombre}' en {region}...")
    body = {"databaseName": "earhero", "databaseUser": "earhero",
            "name": nombre, "plan": "free", "region": region, "version": "16"}
    return post("/postgres", token, body)


def obtener_internal_url(token: str, pg_id: str, reintentos: int = 20) -> str:
    """Espera hasta que Render provisione la DB y devuelve la Internal URL."""
    for i in range(reintentos):
        info = get(f"/postgres/{pg_id}", token)
        conn = info.get("connectionInfo", {})
        url = conn.get("internalConnectionString") or conn.get("externalConnectionString")
        if url:
            return url
        print(f"    DB provisionando... ({i+1}/{reintentos})", end="\r")
        time.sleep(10)
    raise RuntimeError("La base de datos no se provisionó a tiempo.")


def crear_web_service(token: str, nombre: str, repo: str, rama: str, region: str) -> dict:
    print(f"  Creando Web Service '{nombre}'...")
    # Render necesita el repo en formato "owner/name"
    owner, _, repo_name = repo.partition("/")
    body = {
        "type": "web_service",
        "name": nombre,
        "region": region,
        "plan": "free",
        "runtime": "docker",
        "branch": rama,
        "repo": f"https://github.com/{repo}",
        "autoDeploy": "yes",
        "dockerCommand": "",
        # Render detecta el Dockerfile en la raíz automáticamente
    }
    resp = post("/services", token, body)
    return resp.get("service", resp)


def set_env_vars(token: str, service_id: str, vars_dict: dict) -> None:
    """Sobreescribe las variables de entorno del servicio."""
    env_vars = [{"key": k, "value": v} for k, v in vars_dict.items()]
    put_body = env_vars
    req = urllib.request.Request(
        f"{BASE}/services/{service_id}/env-vars",
        data=json.dumps(put_body).encode(),
        method="PUT",
        headers={**HEADERS_BASE, "Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        r.read()
    print(f"  Variables de entorno configuradas: {list(vars_dict.keys())}")


def disparar_deploy(token: str, service_id: str) -> str:
    print("  Disparando deploy...")
    resp = post(f"/services/{service_id}/deploys", token, {"clearCache": "do_not_clear"})
    return resp.get("deploy", resp).get("id", "")


def esperar_deploy(token: str, service_id: str, deploy_id: str,
                   timeout: int = 600) -> str:
    print("  Esperando que el deploy finalice", end="", flush=True)
    t0 = time.time()
    while time.time() - t0 < timeout:
        info = get(f"/services/{service_id}/deploys/{deploy_id}", token)
        status = info.get("deploy", info).get("status", "")
        if status == "live":
            print(" ✓")
            return "live"
        if status in ("failed", "canceled", "deactivated"):
            print(f" ✗ ({status})")
            return status
        print(".", end="", flush=True)
        time.sleep(15)
    print(" timeout")
    return "timeout"


def obtener_url(token: str, service_id: str) -> str:
    info = get(f"/services/{service_id}", token)
    svc = info.get("service", info)
    return svc.get("serviceDetails", {}).get("url", "")


# ── flujo principal ───────────────────────────────────────────────────────────

def deploy(
    token: str,
    repo: str,
    nombre_app: str = "earhero-tf",
    nombre_db: str = "earhero-db",
    rama: str = "main",
    region: str = "oregon",
    secret: str = "earhero-secret-cambiame",
    solo_url: bool = False,
) -> int:

    print("\n=== EarHero AI — Deploy automático en Render ===\n")

    # 1. Base de datos
    print("▶ 1/4  Base de datos PostgreSQL")
    pgs = listar_postgres(token)
    pg = buscar_por_nombre(pgs, nombre_db)
    if pg:
        print(f"  Reutilizando PostgreSQL existente '{nombre_db}' (id={pg['id']})")
        pg_id = pg["id"]
    else:
        pg = crear_postgres(token, nombre_db, region)
        pg_id = pg.get("postgres", pg).get("id") or pg.get("id")

    internal_url = obtener_internal_url(token, pg_id)
    print(f"  DATABASE_URL lista ({'*' * 20}...)")

    # 2. Web Service
    print("\n▶ 2/4  Web Service")
    servicios = listar_servicios(token)
    svc = buscar_por_nombre(servicios, nombre_app)
    if svc:
        print(f"  Reutilizando servicio existente '{nombre_app}' (id={svc['id']})")
        svc_id = svc["id"]
    else:
        svc = crear_web_service(token, nombre_app, repo, rama, region)
        svc_id = svc.get("id") or svc.get("service", {}).get("id")

    # 3. Variables de entorno
    print("\n▶ 3/4  Variables de entorno")
    set_env_vars(token, svc_id, {
        "DATABASE_URL": internal_url,
        "EARHERO_SECRET": secret,
        "PYTHONUNBUFFERED": "1",
    })

    if solo_url:
        url = obtener_url(token, svc_id)
        print(f"\n  URL: {url}")
        return 0

    # 4. Deploy
    print("\n▶ 4/4  Deploy")
    deploy_id = disparar_deploy(token, svc_id)
    estado = esperar_deploy(token, svc_id, deploy_id)

    url = obtener_url(token, svc_id)

    print("\n" + "=" * 50)
    if estado == "live":
        print(f"✅ Deploy exitoso!")
        print(f"   App:    {url}")
        print(f"   Docs:   {url}/docs")
        print(f"   GitHub: https://github.com/{repo}")
    else:
        print(f"❌ Deploy terminó con estado: {estado}")
        print(f"   Revisá los logs en: https://dashboard.render.com/web/{svc_id}/logs")
        return 1

    return 0


# ── integración con el pipeline de agentes ───────────────────────────────────
# Esto lo llama build_app.py cuando se agrega la fase "deploy":
#
#   python tools/deploy_render.py --token $RENDER_API_KEY --repo csena72/earhero-tf
#
# O desde GitHub Actions (el token viene de secrets):
#
#   - name: Deploy a Render
#     if: github.ref == 'refs/heads/main' && success()
#     run: python tools/deploy_render.py --token ${{ secrets.RENDER_API_KEY }} --repo csena72/earhero-tf


def main() -> int:
    ap = argparse.ArgumentParser(description="Deploy automático de EarHero AI en Render")
    ap.add_argument("--token", required=True, help="Render API Key")
    ap.add_argument("--repo", default="csena72/earhero-tf", help="owner/repo de GitHub")
    ap.add_argument("--app", default="earhero-tf", help="Nombre del Web Service en Render")
    ap.add_argument("--db", default="earhero-db", help="Nombre de la DB en Render")
    ap.add_argument("--rama", default="main")
    ap.add_argument("--region", default="oregon",
                    choices=["oregon", "ohio", "virginia", "frankfurt", "singapore"])
    ap.add_argument("--secret", default="earhero-secret-cambiame",
                    help="Valor de EARHERO_SECRET (tokens JWT)")
    ap.add_argument("--solo-url", action="store_true",
                    help="No hacer deploy, solo mostrar la URL actual")
    args = ap.parse_args()

    try:
        return deploy(
            token=args.token,
            repo=args.repo,
            nombre_app=args.app,
            nombre_db=args.db,
            rama=args.rama,
            region=args.region,
            secret=args.secret,
            solo_url=args.solo_url,
        )
    except RuntimeError as exc:
        print(f"\nERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())