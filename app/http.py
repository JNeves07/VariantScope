"""Shared async HTTP: retries, NCBI rate limiting, TTL cache. Never logs query strings (privacy)."""
from __future__ import annotations

import asyncio
import os
import time
from typing import Any

import httpx

from .config import settings


class SourceError(RuntimeError):
    def __init__(self, source: str, message: str, status: int | None = None):
        super().__init__(f"{source}: {message}")
        self.source, self.message, self.status = source, message, status


class Http:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None, ttl: int | None = None):
        self._client = httpx.AsyncClient(
            transport=transport,
            timeout=httpx.Timeout(20.0, connect=8.0),
            headers={"User-Agent": f"VariantScope/{settings.versao} (research tool; contact via repo)"},
            follow_redirects=True,
        )
        self._cache: dict[str, tuple[float, Any]] = {}
        self._ttl = ttl or settings.cache_ttl
        self._locks: dict[str, asyncio.Lock] = {}
        self._last: dict[str, float] = {}
        self.ncbi_key = settings.ncbi_api_key or os.getenv("NCBI_API_KEY")
        self.ncbi_email = settings.ncbi_email or os.getenv("NCBI_EMAIL")

    @property
    def fechado(self) -> bool:
        """Permite recriar o cliente quando o ciclo de vida anterior foi encerrado."""
        return self._client.is_closed

    async def aclose(self) -> None:
        await self._client.aclose()

    async def _throttle(self, host: str) -> None:
        # NCBI: 3 req/s without key, 10 with key.
        interval = 0.11 if (self.ncbi_key and "ncbi" in host) else (0.36 if "ncbi" in host else 0.0)
        if not interval:
            return
        lock = self._locks.setdefault(host, asyncio.Lock())
        async with lock:
            wait = self._last.get(host, 0) + interval - time.monotonic()
            if wait > 0:
                await asyncio.sleep(wait)
            self._last[host] = time.monotonic()

    async def get_json(self, source: str, url: str, params: dict | None = None) -> Any:
        params = dict(params or {})
        if "ncbi.nlm.nih.gov" in url:
            params.setdefault("tool", "variantscope")
            if self.ncbi_email:
                params.setdefault("email", self.ncbi_email)
            if self.ncbi_key:
                params.setdefault("api_key", self.ncbi_key)
        key = url + "?" + "&".join(f"{k}={params[k]}" for k in sorted(params) if k != "api_key")
        hit = self._cache.get(key)
        if hit and hit[0] > time.monotonic():
            return hit[1]
        host = httpx.URL(url).host
        last: Exception | None = None
        for attempt in range(3):
            await self._throttle(host)
            try:
                r = await self._client.get(url, params=params)
                if r.status_code in (429, 500, 502, 503, 504):
                    last = SourceError(source, f"HTTP {r.status_code}", r.status_code)
                    await asyncio.sleep(0.6 * 2**attempt)
                    continue
                if r.status_code == 404:
                    raise SourceError(source, "not found", 404)
                r.raise_for_status()
                data = r.json()
                self._cache[key] = (time.monotonic() + self._ttl, data)
                if len(self._cache) > 500:  # crude bound
                    self._cache.pop(next(iter(self._cache)))
                return data
            except SourceError:
                raise
            except (httpx.TimeoutException, httpx.TransportError, ValueError) as e:
                last = SourceError(source, f"{type(e).__name__}")
                await asyncio.sleep(0.6 * 2**attempt)
            except httpx.HTTPStatusError as e:
                raise SourceError(source, f"HTTP {e.response.status_code}", e.response.status_code) from e
        raise last or SourceError(source, "failed")
