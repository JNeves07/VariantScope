"""Testes do endpoint de comparação (modo demo, sem rede)."""
from fastapi.testclient import TestClient

from app.main import app


def _post(cliente, corpo):
    return cliente.post("/api/compare", json=corpo)


def test_comparacao_happy_path_e_reuso_de_cache():
    with TestClient(app) as cliente:
        corpo = {"q1": "BRAF p.Val600Glu", "q2": "KRAS p.Gly12Cys", "country": "Brazil"}
        resposta = _post(cliente, corpo)
        assert resposta.status_code == 200
        dados = resposta.json()
        assert set(dados) == {"a", "b", "comparacao"}
        assert dados["a"]["variant"]["gene"] == "BRAF"
        assert dados["b"]["variant"]["gene"] == "KRAS"
        assert dados["a"]["query"]["country"] == "Brazil"
        assert dados["b"]["query"]["country"] == "Brazil"

        c = dados["comparacao"]
        assert set(c) == {"ensaios_comuns", "ensaios_unicos_a", "ensaios_unicos_b",
                          "tiers_a", "tiers_b", "divergencias"}
        for chave in ("ensaios_comuns", "ensaios_unicos_a", "ensaios_unicos_b", "tiers_a", "tiers_b"):
            assert isinstance(c[chave], list)
        assert c["divergencias"] and all(isinstance(x, str) for x in c["divergencias"])
        ncts = {x["nct"] for x in dados["a"]["trials"]["items"]}
        assert set(c["ensaios_unicos_a"]).isdisjoint(c["ensaios_comuns"])
        assert set(c["ensaios_comuns"]).issubset(ncts)

        segunda = _post(cliente, corpo).json()
        assert segunda["a"]["cached"] is True and segunda["b"]["cached"] is True


def test_comparacao_entrada_invalida():
    with TestClient(app) as cliente:
        assert _post(cliente, {"q1": "x" * 61, "q2": "BRAF V600E"}).status_code == 422
        assert _post(cliente, {"q1": "BRAF V600E", "q2": "nonsense!"}).status_code == 422
        assert _post(cliente, {"q1": "BRAF V600E"}).status_code == 422


def test_comparacao_variante_desconhecida():
    with TestClient(app) as cliente:
        resposta = _post(cliente, {"q1": "BRAF V600E", "q2": "rs999999999"})
        assert resposta.status_code == 404


def test_comparacao_variantes_iguais():
    with TestClient(app) as cliente:
        dados = _post(cliente, {"q1": "EGFR L858R", "q2": "egfr l858r"}).json()
        assert dados["a"] == dados["b"]
        c = dados["comparacao"]
        assert c["ensaios_unicos_a"] == [] and c["ensaios_unicos_b"] == []
        assert set(c["ensaios_comuns"]) == {x["nct"] for x in dados["a"]["trials"]["items"]}
        assert c["divergencias"] == ["Nenhuma divergência relevante entre os dois briefs."]
