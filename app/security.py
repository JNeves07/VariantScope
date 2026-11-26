"""Autenticação JWT para os endpoints administrativos."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from .config import Settings
from .config import settings as settings_global

try:
    import jwt
except ImportError as exc:  # pragma: no cover - dependência obrigatória
    raise RuntimeError("PyJWT não instalado. Execute pip install -r requirements.txt") from exc

portador = HTTPBearer(auto_error=False, description="Token Bearer obtido em POST /api/admin/token")


def criar_token(sub: str = "admin", minutos: int = 60, config: Settings | None = None) -> str:
    cfg = config or settings_global
    agora = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": sub,
            "iat": agora,
            "exp": agora + timedelta(minutes=minutos),
            "iss": "variantscope",
        },
        cfg.jwt_secret,
        algorithm="HS256",
    )


def validar_token(token: str, config: Settings | None = None) -> dict:
    cfg = config or settings_global
    try:
        dados = jwt.decode(token, cfg.jwt_secret, algorithms=["HS256"], issuer="variantscope")
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    return dados


def exigir_admin(
    credenciais: HTTPAuthorizationCredentials | None = Depends(portador),
    config: Settings | None = None,
) -> dict:
    if not credenciais:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Informe o token Bearer.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return validar_token(credenciais.credentials, config)
