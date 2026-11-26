"""Saúde da aplicação e metadados de deploy."""
from __future__ import annotations

from fastapi import APIRouter, Request

from ..config import settings

router = APIRouter(tags=["saúde"])


@router.get("/api/health", summary="Status da API")
async def health(request: Request) -> dict:
    return {
        "ok": True,
        "demo": settings.demo,
        "versao": settings.versao,
        "cache": settings.cache_backend,
        "aviso_segredos_padrao": settings.secrets_padrao,
        "configurado": bool(request.app.state.http.ncbi_key),
    }


@router.get("/healthz", include_in_schema=False, summary="Healthcheck para orquestradores")
async def healthz() -> dict:
    return {"status": "ok"}
