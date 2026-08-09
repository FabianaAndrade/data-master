"""
Cliente HTTP assíncrono para comunicação com metadata_service e auth_service.
Centraliza o tratamento de erros HTTP, eliminando o boilerplate dos endpoints.
"""
from typing import Any

import httpx
from fastapi import HTTPException

from .config import AUTH_SERVICE_URL, METADATA_SERVICE_URL


async def _request(method: str, url: str, service_name: str, **kwargs) -> Any:
    """Executa uma requisição HTTP com tratamento de erros padronizado."""
    async with httpx.AsyncClient() as client:
        try:
            response = await getattr(client, method)(url, timeout=10.0, **kwargs)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            try:
                detail = e.response.json().get("detail", e.response.text)
            except Exception:
                detail = e.response.text
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Erro do {service_name}: {detail}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"{service_name} indisponível: {e}",
            )


# ---------------------------------------------------------------------------
# Metadata service
# ---------------------------------------------------------------------------

async def metadata_get(path: str, **kwargs) -> Any:
    """GET no metadata_service."""
    return await _request("get", f"{METADATA_SERVICE_URL}{path}", "metadata_service", **kwargs)


async def metadata_post(path: str, **kwargs) -> Any:
    """POST no metadata_service."""
    return await _request("post", f"{METADATA_SERVICE_URL}{path}", "metadata_service", **kwargs)


async def metadata_put(path: str, **kwargs) -> Any:
    """PUT no metadata_service."""
    return await _request("put", f"{METADATA_SERVICE_URL}{path}", "metadata_service", **kwargs)


async def metadata_delete(path: str, **kwargs) -> Any:
    """DELETE no metadata_service."""
    return await _request("delete", f"{METADATA_SERVICE_URL}{path}", "metadata_service", **kwargs)


# ---------------------------------------------------------------------------
# Auth service
# ---------------------------------------------------------------------------

async def auth_get(path: str, **kwargs) -> Any:
    """GET no auth_service."""
    return await _request("get", f"{AUTH_SERVICE_URL}{path}", "auth_service", **kwargs)
