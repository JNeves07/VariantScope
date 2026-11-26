"""Entry point da Vercel (serverless).

O runtime @vercel/python reconhece a variável ASGI `app`. O `handler` Mangum é
mantido para executar a mesma aplicação em outros ambientes Lambda-like.
"""
from __future__ import annotations

from mangum import Mangum

from app.main import app

handler = Mangum(app, lifespan="off")

__all__ = ["app", "handler"]
