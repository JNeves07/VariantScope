"""Testes dos backends de cache e da chave de consulta (sem dados em claro)."""
import asyncio
import time

from app.cache import MemoryCache, SQLiteCache, chave_consulta, criar_cache
from app.config import Settings


def executar(coro):
    return asyncio.run(coro)


def test_chave_consulta_e_deterministica_e_anonima():
    a = chave_consulta("BRAF V600E", "melanoma", "Brazil", True)
    b = chave_consulta("  braf v600e  ", " melanoma ", " brazil ", True)
    assert a == b
    assert "BRAF" not in a and "melanoma" not in a
    assert len(a) == 64


def test_chave_muda_com_filtros():
    base = chave_consulta("BRAF V600E", None, None, True)
    assert base != chave_consulta("BRAF V600E", "melanoma", None, True)
    assert base != chave_consulta("BRAF V600E", None, "Brazil", True)
    assert base != chave_consulta("BRAF V600E", None, None, False)


def test_cache_memoria_guarda_e_expira():
    async def cena():
        cache = MemoryCache()
        await cache.set("chave", {"valor": 1}, ttl=60)
        assert await cache.get("chave") == {"valor": 1}
        await cache.set("curta", {"valor": 2}, ttl=0)
        assert await cache.get("curta") is None

    executar(cena())


def test_cache_memoria_estatisticas_e_limpeza():
    async def cena():
        cache = MemoryCache()
        await cache.set("a", {"n": 1}, 60)
        await cache.get("a")
        await cache.get("falta")
        stats = await cache.stats()
        assert stats["backend"] == "memory"
        assert stats["acertos"] == 1 and stats["erros"] == 1
        assert await cache.clear() == 1
        assert await cache.get("a") is None

    executar(cena())


def test_cache_sqlite_persiste_e_nao_guarda_texto(tmp_path):
    async def cena():
        caminho = tmp_path / "subdir" / "cache.sqlite3"
        cache = SQLiteCache(caminho)
        chave = chave_consulta("rs113488022", None, None, True)
        await cache.set(chave, {"valor": " BRAF V600E "}, 60)
        assert (await cache.get(chave))["valor"] == " BRAF V600E "
        stats = await cache.stats()
        assert stats["backend"] == "sqlite" and stats["entradas"] == 1
        conteudo = caminho.read_bytes()
        assert b"rs113488022" not in conteudo and b"V600E" not in conteudo
        assert await cache.clear() == 1
        assert await cache.get(chave) is None

    executar(cena())


def test_cache_sqlite_respeita_ttl(tmp_path):
    async def cena():
        cache = SQLiteCache(tmp_path / "ttl.sqlite3")
        await cache.set("vencida", {"x": 1}, ttl=60)
        import sqlite3

        with sqlite3.connect(tmp_path / "ttl.sqlite3") as conn:
            conn.execute("UPDATE respostas SET expira = ? WHERE chave = ?", (time.time() - 1, "vencida"))
        assert await cache.get("vencida") is None

    executar(cena())


def test_fabrica_respeita_backend():
    memory = Settings.from_env()
    assert isinstance(
        criar_cache(
            Settings(
                demo=True, cache_backend="memory", db_path=memory.db_path,
                cache_ttl=60, rate_limit=20, rate_window=60, jwt_secret="s",
                admin_password="p", ncbi_api_key=None, ncbi_email=None, cors_origins=(),
            )
        ),
        MemoryCache,
    )
