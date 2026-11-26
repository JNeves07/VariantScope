"""Modelos de request/response da API."""
from __future__ import annotations

from pydantic import BaseModel, Field


class TokenRequest(BaseModel):
    password: str = Field(min_length=1, max_length=200)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
