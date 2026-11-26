"""Testes de emissão/validação de JWT e das rotas administrativas."""
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.security import criar_token, validar_token


def test_token_roundtrip():
    token = criar_token()
    assert validar_token(token)["sub"] == "admin"


def test_token_expirado():
    agora = datetime.now(UTC)
    token = jwt.encode(
        {"sub": "admin", "exp": agora - timedelta(minutes=1), "iss": "variantscope"},
        settings.jwt_secret,
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as erro:
        validar_token(token)
    assert erro.value.status_code == 401


def test_token_assinatura_invalida():
    token = jwt.encode(
        {"sub": "admin", "exp": datetime.now(UTC) + timedelta(minutes=5), "iss": "variantscope"},
        "outro-segredo-com-32-bytes-no-minimo-ok",
        algorithm="HS256",
    )
    with pytest.raises(HTTPException) as erro:
        validar_token(token)
    assert erro.value.status_code == 401


def test_admin_sem_token_negado():
    with TestClient(app) as cliente:
        assert cliente.get("/api/admin/stats").status_code == 401


def test_admin_com_token_valido():
    with TestClient(app) as cliente:
        resposta = cliente.post("/api/admin/token", json={"password": settings.admin_password})
        assert resposta.status_code == 200
        token = resposta.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        stats = cliente.get("/api/admin/stats", headers=headers)
        assert stats.status_code == 200
        assert stats.json()["backend"] == "memory"
        limpeza = cliente.delete("/api/admin/cache", headers=headers)
        assert limpeza.status_code == 200 and "removidas" in limpeza.json()


def test_admin_senha_errada():
    with TestClient(app) as cliente:
        resposta = cliente.post("/api/admin/token", json={"password": "errada"})
        assert resposta.status_code == 401
