"""
Cliente HTTP para comunicação com o metadata_service.
O approval_service NÃO acessa o banco diretamente.
"""
import os
from typing import Any, Dict, List, Optional

import httpx
from fastapi import HTTPException

METADATA_SERVICE_URL = os.getenv(
    "METADATA_SERVICE_URL", "http://metadata_service:8002"
)


def _handle_response(response: httpx.Response) -> Any:
    """Levanta HTTPException se a resposta não for 2xx."""
    if response.status_code == 404:
        raise HTTPException(status_code=404, detail=response.json().get("detail", "Não encontrado."))
    if not response.is_success:
        raise HTTPException(
            status_code=response.status_code,
            detail=response.json().get("detail", "Erro no metadata_service."),
        )
    return response.json()


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------

def get_ingestion_for_approval(ingestion_id: int) -> dict:
    """Busca dados completos de uma ingestão para o fluxo de aprovação."""
    with httpx.Client() as client:
        resp = client.get(f"{METADATA_SERVICE_URL}/ingestions/{ingestion_id}/approval-detail")
    return _handle_response(resp)


def get_pending_ingestions_for_owner(owner_username: str) -> dict:
    """Lista ingestões pendentes de aprovação para o owner autenticado."""
    with httpx.Client() as client:
        resp = client.get(
            f"{METADATA_SERVICE_URL}/ingestions/pending-approval",
            params={"owner": owner_username},
        )
    return _handle_response(resp)


# ---------------------------------------------------------------------------
# Write (delega ao metadata_service)
# ---------------------------------------------------------------------------

def approve_ingestion(ingestion_id: int, approved_by_username: str) -> dict:
    """Chama o metadata_service para aprovar uma ingestão."""
    with httpx.Client() as client:
        resp = client.post(
            f"{METADATA_SERVICE_URL}/ingestions/{ingestion_id}/approve",
            json={"approved_by_username": approved_by_username},
        )
    return _handle_response(resp)


def reject_ingestion(ingestion_id: int, rejected_by_username: str) -> dict:
    """Chama o metadata_service para rejeitar uma ingestão."""
    with httpx.Client() as client:
        resp = client.post(
            f"{METADATA_SERVICE_URL}/ingestions/{ingestion_id}/reject",
            json={"approved_by_username": rejected_by_username},
        )
    return _handle_response(resp)


def cancel_ingestion(ingestion_id: int, cancelled_by_username: str) -> dict:
    """Chama o metadata_service para cancelar uma ingestão específica."""
    with httpx.Client() as client:
        resp = client.post(
            f"{METADATA_SERVICE_URL}/ingestions/{ingestion_id}/cancel",
            json={"approved_by_username": cancelled_by_username},
        )
    return _handle_response(resp)


def cancel_expired_ingestions() -> dict:
    """Chama o metadata_service para cancelar em lote as ingestões expiradas."""
    with httpx.Client() as client:
        resp = client.post(f"{METADATA_SERVICE_URL}/ingestions/cancel-expired")
    return _handle_response(resp)
