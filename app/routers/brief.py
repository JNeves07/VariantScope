"""Endpoint principal: geração do brief a partir de uma variante."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from ..brief import NotFound, UpstreamDown, build_brief
from ..config import settings
from ..http import Http
from ..normalize import InputError

router = APIRouter(tags=["brief"])


@router.get("/api/brief", summary="Gera um brief de evidências e ensaios clínicos")
async def brief(
    request: Request,
    q: str = Query(..., min_length=1, max_length=80, description="rsID ou gene + alteração proteica"),
    condition: str | None = Query(None, max_length=80, description="Condição (filtro opcional)"),
    country: str | None = Query(None, max_length=60, description="País do centro de pesquisa"),
) -> dict:
    http = request.app.state.http
    if http.fechado:  # ciclo de vida encerrado (ex.: serverless ou TestClient reutilizado)
        http = Http(transport=request.app.state.http_transport)
        request.app.state.http = http

    try:
        return await build_brief(
            http,
            q,
            condition,
            country,
            demo=settings.demo,
            cache=request.app.state.cache,
            ttl=settings.cache_ttl,
        )
    except InputError as exc:
        raise HTTPException(422, str(exc)) from exc
    except NotFound as exc:
        raise HTTPException(404, str(exc)) from exc
    except UpstreamDown as exc:
        raise HTTPException(502, str(exc)) from exc
