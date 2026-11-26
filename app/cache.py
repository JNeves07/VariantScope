"""Cache TTL em memória ou SQLite.

Privacidade: a chave é um hash da consulta; o texto digitado pelo usuário nunca é
gravado. A tabela `consultas` guarda apenas contadores agregados por chave.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Protocol

from .config import Settings
from .config import settings as settings_global


class CacheBackend(Protocol):
    async def get(self, chave: str) -> dict[str, Any] | None: ...
    async def set(self, chave: str, valor: dict[str, Any], ttl: int) -> None: ...
    async def stats(self) -> dict[str, Any]: ...
    async def clear(self) -> int: ...


def chave_consulta(
    termo: str, condicao: str | None = None, pais: str | None = None, demo: bool = False
) -> str:
    """Chave estável e sem informações em claro sobre a busca do usuário."""
    bruto = json.dumps(
        {
            "q": (termo or "").strip().lower(),
            "condition": (condicao or "").strip().lower(),
            "country": (pais or "").strip().lower(),
            "demo": bool(demo),
        },
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()


class MemoryCache:
    """Cache em processo; ideal para Vercel (filesystem somente leitura)."""

    def __init__(self) -> None:
        self._dados: dict[str, tuple[float, str]] = {}
        self._acertos = 0
        self._erros = 0

    async def get(self, chave: str) -> dict[str, Any] | None:
        item = self._dados.get(chave)
        if not item:
            self._erros += 1
            return None
        expira, payload = item
        if expira <= time.time():
            self._dados.pop(chave, None)
            self._erros += 1
            return None
        self._acertos += 1
        return json.loads(payload)

    async def set(self, chave: str, valor: dict[str, Any], ttl: int) -> None:
        self._dados[chave] = (time.time() + ttl, json.dumps(valor, ensure_ascii=False))
        if len(self._dados) > 500:
            mais_antigo = min(self._dados, key=lambda k: self._dados[k][0])
            self._dados.pop(mais_antigo, None)

    async def stats(self) -> dict[str, Any]:
        return {
            "backend": "memory",
            "entradas": len(self._dados),
            "acertos": self._acertos,
            "erros": self._erros,
            "expiradas": sum(1 for expira, _ in self._dados.values() if expira <= time.time()),
        }

    async def clear(self) -> int:
        total = len(self._dados)
        self._dados.clear()
        return total


class SQLiteCache:
    """Cache persistente em SQLite; usado pelo Docker e por execuções locais."""

    def __init__(self, caminho: Path) -> None:
        self.caminho = caminho
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        self._inicializar()

    def _conectar(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.caminho, timeout=10)
        conn.row_factory = sqlite3.Row
        return conn

    def _inicializar(self) -> None:
        with self._conectar() as conn:
            conn.executescript(
                """
                PRAGMA journal_mode = WAL;
                CREATE TABLE IF NOT EXISTS respostas (
                    chave TEXT PRIMARY KEY,
                    payload TEXT NOT NULL,
                    expira REAL NOT NULL,
                    criado_em REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_respostas_expira ON respostas(expira);
                CREATE TABLE IF NOT EXISTS consultas (
                    chave TEXT PRIMARY KEY,
                    total INTEGER NOT NULL DEFAULT 0,
                    ultima_em REAL NOT NULL
                );
                """
            )

    async def get(self, chave: str) -> dict[str, Any] | None:
        def consultar() -> dict[str, Any] | None:
            agora = time.time()
            with self._conectar() as conn:
                linha = conn.execute(
                    "SELECT payload FROM respostas WHERE chave = ? AND expira > ?",
                    (chave, agora),
                ).fetchone()
                if linha:
                    conn.execute(
                        "INSERT INTO consultas (chave, total, ultima_em) VALUES (?, 1, ?) "
                        "ON CONFLICT(chave) DO UPDATE SET total = total + 1, ultima_em = excluded.ultima_em",
                        (chave, agora),
                    )
                    return json.loads(linha["payload"])
                conn.execute("DELETE FROM respostas WHERE chave = ?", (chave,))
            return None

        return await asyncio.to_thread(consultar)

    async def set(self, chave: str, valor: dict[str, Any], ttl: int) -> None:
        def gravar() -> None:
            agora = time.time()
            with self._conectar() as conn:
                conn.execute(
                    "INSERT INTO respostas (chave, payload, expira, criado_em) VALUES (?, ?, ?, ?) "
                    "ON CONFLICT(chave) DO UPDATE SET payload = excluded.payload, "
                    "expira = excluded.expira, criado_em = excluded.criado_em",
                    (chave, json.dumps(valor, ensure_ascii=False), agora + ttl, agora),
                )
                conn.execute("DELETE FROM respostas WHERE expira <= ?", (agora,))

        await asyncio.to_thread(gravar)

    async def stats(self) -> dict[str, Any]:
        def consultar() -> dict[str, Any]:
            with self._conectar() as conn:
                respostas = conn.execute("SELECT COUNT(*) AS n FROM respostas").fetchone()["n"]
                expiradas = conn.execute(
                    "SELECT COUNT(*) AS n FROM respostas WHERE expira <= ?", (time.time(),)
                ).fetchone()["n"]
                consultas = conn.execute(
                    "SELECT COALESCE(SUM(total), 0) AS n FROM consultas"
                ).fetchone()["n"]
            return {
                "backend": "sqlite",
                "arquivo": str(self.caminho),
                "entradas": respostas,
                "expiradas": expiradas,
                "acertos": consultas,
            }

        return await asyncio.to_thread(consultar)

    async def clear(self) -> int:
        def limpar() -> int:
            with self._conectar() as conn:
                total = conn.execute("SELECT COUNT(*) AS n FROM respostas").fetchone()["n"]
                conn.execute("DELETE FROM respostas")
            return total

        return await asyncio.to_thread(limpar)


def criar_cache(config: Settings | None = None) -> CacheBackend:
    cfg = config or settings_global
    if cfg.cache_backend == "memory":
        return MemoryCache()
    return SQLiteCache(cfg.db_path)
