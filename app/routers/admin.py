"""Endpoints administrativos protegidos por JWT."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from ..config import settings
from ..schemas import TokenRequest, TokenResponse
from ..security import criar_token, exigir_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/token", response_model=TokenResponse, summary="Emite um token JWT")
def token(dados: TokenRequest) -> TokenResponse:
    if dados.password != settings.admin_password:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Senha inválida.")
    return TokenResponse(access_token=criar_token(), expires_in=3600)


@router.get("/stats", summary="Estatísticas do cache (requer JWT)")
async def estatisticas(request: Request, _: dict = Depends(exigir_admin)) -> dict:
    return await request.app.state.cache.stats()


@router.delete("/cache", summary="Limpa o cache (requer JWT)")
async def limpar_cache(request: Request, _: dict = Depends(exigir_admin)) -> dict:
    removidas = await request.app.state.cache.clear()
    return {"removidas": removidas}
