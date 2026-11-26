"""Testes de integração da API (modo demo, sem rede)."""
import importlib
import os

from fastapi.testclient import TestClient

os.environ["VTS_DEMO"] = "1"
import app.main as modulo

importlib.reload(modulo)


def test_api_flow():
    with TestClient(modulo.app) as cliente:
        assert cliente.get("/api/health").json()["demo"] is True
        resposta = cliente.get("/api/brief", params={"q": "rs113488022"})
        assert resposta.status_code == 200 and resposta.json()["demo"] is True
        assert cliente.get("/api/brief", params={"q": "nonsense!"}).status_code == 422
        assert cliente.get("/api/brief", params={"q": "rs999999999"}).status_code == 404
        assert "default-src" in resposta.headers["content-security-policy"]
        assert resposta.headers["x-frame-options"] == "DENY"
        assert cliente.get("/").status_code == 200


def test_healthz_e_metadados():
    with TestClient(modulo.app) as cliente:
        assert cliente.get("/healthz").json() == {"status": "ok"}
        dados = cliente.get("/api/health").json()
        assert dados["versao"] == "1.0.0"
        assert dados["cache"] == "memory"
        assert "configurado" in dados


def test_segunda_busca_vem_do_cache():
    with TestClient(modulo.app) as cliente:
        primeira = cliente.get("/api/brief", params={"q": "BRAF V600E"}).json()
        segunda = cliente.get("/api/brief", params={"q": "BRAF V600E"}).json()
        assert primeira["cached"] is False
        assert segunda["cached"] is True
        assert segunda["variant"]["change"]["short"] == "V600E"


def test_filtro_de_pais_gera_chave_diferente():
    with TestClient(modulo.app) as cliente:
        cliente.get("/api/brief", params={"q": "BRAF V600E"})  # primeira chamada popula o cache
        sem_filtro = cliente.get("/api/brief", params={"q": "BRAF V600E"}).json()
        com_filtro = cliente.get("/api/brief", params={"q": "BRAF V600E", "country": "Brazil"}).json()
        assert sem_filtro["cached"] is True
        assert com_filtro["cached"] is False


def test_arquivos_estaticos():
    with TestClient(modulo.app) as cliente:
        assert cliente.get("/static/app.js").status_code == 200
        assert cliente.get("/static/style.css").status_code == 200
        assert cliente.get("/favicon.svg").status_code == 200


def test_documentacao_openapi():
    with TestClient(modulo.app) as cliente:
        esquema = cliente.get("/api/openapi.json").json()
        caminhos = esquema["paths"]
        assert "/api/brief" in caminhos
        assert "/api/admin/token" in caminhos
        assert "/api/health" in caminhos
