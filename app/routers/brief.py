"""Endpoints de brief e de comparação entre variantes."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, HTTPException, Query, Request

from ..brief import NotFound, UpstreamDown, build_brief
from ..compare import comparar_briefs
from ..config import settings
from ..http import Http
from ..normalize import InputError
from ..schemas import CompareRequest

router = APIRouter(tags=["brief"])


def _http_da_app(request: Request) -> Http:
    http = request.app.state.http
    if http.fechado:  # ciclo de vida encerrado (ex.: serverless ou TestClient reutilizado)
        http = Http(transport=request.app.state.http_transport)
        request.app.state.http = http
    return http


def _traduzir_erro(exc: Exception) -> HTTPException:
    if isinstance(exc, InputError):
        return HTTPException(422, str(exc))
    if isinstance(exc, NotFound):
        return HTTPException(404, str(exc))
    return HTTPException(502, str(exc))


@router.get("/api/brief", summary="Gera um brief de evidências e ensaios clínicos")
async def brief(
    request: Request,
    q: str = Query(..., min_length=1, max_length=60, description="rsID ou gene + alteração proteica"),
    condition: str | None = Query(None, max_length=80, description="Condição (filtro opcional)"),
    country: str | None = Query(None, max_length=60, description="País do centro de pesquisa"),
) -> dict:
    try:
        return await build_brief(
            _http_da_app(request),
            q,
            condition,
            country,
            demo=settings.demo,
            cache=request.app.state.cache,
            ttl=settings.cache_ttl,
        )
    except (InputError, NotFound, UpstreamDown) as exc:
        raise _traduzir_erro(exc) from exc


@router.post("/api/compare", summary="Compara dois briefs reaproveitando o cache")
async def comparar(request: Request, dados: CompareRequest) -> dict:
    """Resolve as duas variantes com o mesmo orquestrador e o mesmo cliente HTTP."""
    http = _http_da_app(request)
    comuns = dict(
        demo=settings.demo, cache=request.app.state.cache, ttl=settings.cache_ttl
    )
    args = (dados.condition, dados.country)
    try:
        if dados.q1.strip().lower() == dados.q2.strip().lower():
            unico = await build_brief(http, dados.q1, *args, **comuns)
            a, b = unico, unico
        else:
            a, b = await asyncio.gather(
                build_brief(http, dados.q1, *args, **comuns),
                build_brief(http, dados.q2, *args, **comuns),
            )
    except (InputError, NotFound, UpstreamDown) as exc:
        raise _traduzir_erro(exc) from exc
    return {"a": a, "b": b, "comparacao": comparar_briefs(a, b)}
