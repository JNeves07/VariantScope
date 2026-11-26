"""Configuração centralizada via variáveis de ambiente.

Nenhum segredo fica no código. Em desenvolvimento valores seguros são usados como
padrão; em produção defina VTS_JWT_SECRET e VTS_ADMIN_PASSWORD.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

VERSAO = "1.0.0"


def _booleano(nome: str, padrao: bool = False) -> bool:
    return os.getenv(nome, "1" if padrao else "0").strip().lower() in {
        "1", "true", "yes", "on"
    }


def _inteiro(nome: str, padrao: int, minimo: int = 1) -> int:
    try:
        return max(minimo, int(os.getenv(nome, str(padrao))))
    except (TypeError, ValueError):
        return padrao


@dataclass(frozen=True)
class Settings:
    """Valores lidos uma vez na inicialização do processo."""

    demo: bool
    cache_backend: str
    db_path: Path
    cache_ttl: int
    rate_limit: int
    rate_window: int
    jwt_secret: str
    admin_password: str
    ncbi_api_key: str | None
    ncbi_email: str | None
    cors_origins: tuple[str, ...]
    versao: str = VERSAO

    @property
    def secrets_padrao(self) -> bool:
        return self.jwt_secret.startswith("dev-only-") or self.admin_password == "admin"

    @classmethod
    def from_env(cls) -> Settings:
        # Na Vercel o filesystem é efêmero/somente leitura: cache em memória por padrão.
        padrao_backend = "memory" if os.getenv("VERCEL") else "sqlite"
        backend = os.getenv("VTS_CACHE_BACKEND", padrao_backend).strip().lower()
        if backend not in {"sqlite", "memory"}:
            backend = "sqlite"
        caminho = os.getenv("VTS_DB_PATH", "data/variantscope.sqlite3")
        origens = tuple(
            item.strip()
            for item in os.getenv("VTS_CORS_ORIGINS", "").split(",")
            if item.strip()
        )
        return cls(
            demo=_booleano("VTS_DEMO"),
            cache_backend=backend,
            db_path=Path(caminho),
            cache_ttl=_inteiro("VTS_CACHE_TTL", 6 * 3600, 60),
            rate_limit=_inteiro("VTS_RATE_LIMIT", 20, 1),
            rate_window=_inteiro("VTS_RATE_WINDOW", 60, 10),
            jwt_secret=os.getenv("VTS_JWT_SECRET", "dev-only-change-me-rotate-this-in-production"),
            admin_password=os.getenv("VTS_ADMIN_PASSWORD", "admin"),
            ncbi_api_key=os.getenv("NCBI_API_KEY") or None,
            ncbi_email=os.getenv("NCBI_EMAIL") or None,
            cors_origins=origens,
        )


settings = Settings.from_env()
