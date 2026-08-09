"""
Dependencies do FastAPI para o approval_service.
"""
from typing import Optional

import jwt
from fastapi import Header, HTTPException

from .config import JWT_SECRET, JWT_ALGORITHM


def get_current_user(authorization: Optional[str] = Header(default=None)) -> str:
    """
    Decodifica o Bearer token e retorna o username (sub).
    Utilizado como Depends() nos endpoints protegidos.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Token de autenticação ausente ou inválido. Use o header Authorization: Bearer <token>.",
        )
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expirado.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Token inválido.")
