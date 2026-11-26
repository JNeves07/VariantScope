"""O entry point serverless precisa funcionar mesmo sem eventos de lifespan."""
import httpx

from api.index import app, handler


def test_entry_point_vercel():
    assert app.title == "VariantScope"
    assert callable(handler)


async def test_brief_sem_lifespan():
    """Mangum usa lifespan='off': o estado da app já deve estar pronto na importação."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as cliente:
        resposta = await cliente.get("/api/brief", params={"q": "rs113488022"})
    assert resposta.status_code == 200
    assert resposta.json()["variant"]["gene"] == "BRAF"
