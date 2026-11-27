"""Modelos de request/response da API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class CompareRequest(BaseModel):
    """Duas variantes com os mesmos filtros opcionais (mesmos limites de /api/brief)."""

    q1: str = Field(min_length=1, max_length=60)
    q2: str = Field(min_length=1, max_length=60)
    condition: str | None = Field(default=None, max_length=80)
    country: str | None = Field(default=None, max_length=60)
