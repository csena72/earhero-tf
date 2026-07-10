import importlib.util
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[2] / "tools" / "deploy_render.py"
SPEC = importlib.util.spec_from_file_location("deploy_render", MODULE_PATH)
deploy_render = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(deploy_render)


def test_deploy_uses_sqlite_when_postgres_creation_fails(monkeypatch):
    captured = {}

    monkeypatch.setattr(deploy_render, "listar_postgres", lambda token: [])
    monkeypatch.setattr(
        deploy_render,
        "crear_postgres",
        lambda token, nombre, region: (_ for _ in ()).throw(
            RuntimeError("Render API POST /postgres → 404: not found")
        ),
    )
    monkeypatch.setattr(
        deploy_render,
        "obtener_internal_url",
        lambda token, pg_id, reintentos=20: (_ for _ in ()).throw(
            RuntimeError("La base de datos no se provisionó a tiempo")
        ),
    )
    monkeypatch.setattr(deploy_render, "listar_servicios", lambda token: [])
    monkeypatch.setattr(
        deploy_render,
        "crear_web_service",
        lambda token, nombre, repo, rama, region: {"id": "svc-123"},
    )
    monkeypatch.setattr(
        deploy_render,
        "set_env_vars",
        lambda token, service_id, vars_dict: captured.setdefault("env", vars_dict),
    )
    monkeypatch.setattr(deploy_render, "disparar_deploy", lambda token, service_id: "deploy-1")
    monkeypatch.setattr(deploy_render, "esperar_deploy", lambda token, service_id, deploy_id, timeout=600: "live")
    monkeypatch.setattr(deploy_render, "obtener_url", lambda token, service_id: "https://example.onrender.com")

    result = deploy_render.deploy(token="fake-token", repo="csena72/earhero-tf", secret="secret")

    assert result == 0
    assert captured["env"]["DATABASE_URL"] == "sqlite:///./earhero.db"
