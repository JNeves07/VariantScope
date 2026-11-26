"""Aplicação FastAPI: fábrica, middleware de segurança e registro dos roteadores."""
from __future__ import annotations

import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .cache import criar_cache
from .config import settings
from .http import Http
from .routers import admin, brief, health

STATIC = Path(__file__).resolve().parent.parent / "frontend"
_hits: dict[str, deque] = defaultdict(deque)


def criar_app() -> FastAPI:
    """Cria a aplicação. Mantido como fábrica para testes e para o handler da Vercel."""

    transport = None
    if settings.demo:  # dados sintéticos, sem rede
        from .demo_data import demo_transport

        transport = demo_transport()

    def preparar_estado(app: FastAPI) -> None:
        app.state.http = Http(transport=transport)
        app.state.cache = criar_cache()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # Recria os recursos a cada ciclo de vida (TestClient, uvicorn). No
        # serverless (Mangum com lifespan="off") o estado já existe desde a criação.
        antigo = getattr(app.state, "http", None)
        if antigo is not None:
            await antigo.aclose()
        preparar_estado(app)
        try:
            yield
        finally:
            await app.state.http.aclose()

    aplicacao = FastAPI(
        title="VariantScope",
        description=(
            "Busca de evidências e ensaios clínicos para variants genômicas. "
            "Cada informação é rastreável a dbSNP/ClinVar, PubMed ou ClinicalTrials.gov."
        ),
        version=settings.versao,
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )
    preparar_estado(aplicacao)
    aplicacao.state.http_transport = transport

    if settings.cors_origins:
        aplicacao.add_middleware(
            CORSMiddleware,
            allow_origins=list(settings.cors_origins),
            allow_credentials=False,
            allow_methods=["GET", "POST", "DELETE"],
            allow_headers=["Authorization", "Content-Type"],
        )

    @aplicacao.middleware("http")
    async def seguranca_e_limites(request: Request, call_next):
        if request.url.path.startswith("/api/brief"):
            ip = (
                request.headers.get("x-forwarded-for")
                or (request.client.host if request.client else "?")
            ).split(",")[0].strip()
            janela, agora = _hits[ip], time.monotonic()
            while janela and janela[0] < agora - settings.rate_window:
                janela.popleft()
            if len(janela) >= settings.rate_limit:
                return JSONResponse(
                    {
                        "error": "rate_limited",
                        "message": "Muitas requisições. Aguarde um minuto.",
                    },
                    status_code=429,
                )
            janela.append(agora)

        resposta = await call_next(request)
        resposta.headers["X-Content-Type-Options"] = "nosniff"
        resposta.headers["X-Frame-Options"] = "DENY"
        resposta.headers["Referrer-Policy"] = "no-referrer"
        resposta.headers["Cache-Control"] = (
            "no-store" if request.url.path.startswith("/api/") else "public, max-age=300"
        )
        resposta.headers["Content-Security-Policy"] = (
            "default-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; img-src 'self' data:; script-src 'self'; "
            "connect-src 'self'"
        )
        return resposta

    aplicacao.include_router(health.router)
    aplicacao.include_router(brief.router)
    aplicacao.include_router(admin.router)

    @aplicacao.get("/", include_in_schema=False)
    async def indice():
        return FileResponse(STATIC / "index.html")

    @aplicacao.get("/favicon.svg", include_in_schema=False)
    async def favicon():
        return FileResponse(STATIC / "assets" / "favicon.svg")

    aplicacao.mount("/static", StaticFiles(directory=STATIC), name="static")

    return aplicacao


app = criar_app()
