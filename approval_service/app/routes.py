"""
Endpoints do approval_service.
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends

from . import metadata_client
from .dependencies import get_current_user
from .schemas import RejectBody
from .validators import ApprovalValidator

router = APIRouter()


@router.get("/approvals/pending", response_model=Dict[str, Any], status_code=200)
def list_pending_approvals(username: str = Depends(get_current_user)):
    """
    Lista todas as ingestões pendentes de aprovação para o owner autenticado.
    Delega ao metadata_service via HTTP.
    """
    return metadata_client.get_pending_ingestions_for_owner(username)


@router.get("/approvals/{ingestion_id}", response_model=Dict[str, Any], status_code=200)
def get_approval_detail(ingestion_id: int, username: str = Depends(get_current_user)):
    """
    Retorna detalhes de uma ingestão para análise de aprovação.
    Delega ao metadata_service via HTTP.
    """
    return metadata_client.get_ingestion_for_approval(ingestion_id)


@router.post("/approvals/{ingestion_id}/approve", response_model=Dict[str, Any], status_code=200)
def approve_ingestion(ingestion_id: int, username: str = Depends(get_current_user)):
    """
    Aprova uma solicitação de ingestão.
    """
    ingestion = metadata_client.get_ingestion_for_approval(ingestion_id)

    ApprovalValidator(ingestion, username).validate()

    result = metadata_client.approve_ingestion(ingestion_id, username)
    return {
        **result,
        "aprovado_por": username,
    }


@router.post("/approvals/{ingestion_id}/reject", response_model=Dict[str, Any], status_code=200)
def reject_ingestion(
    ingestion_id: int,
    body: RejectBody = RejectBody(),
    username: str = Depends(get_current_user),
):
    """
    Rejeita uma solicitação de ingestão.

    Regras de negócio validadas localmente antes de delegar ao metadata_service:
    - Apenas o owner da sigla pode rejeitar
    - A rejeição deve ser feita dentro do prazo de 10 dias
    """
    ingestion = metadata_client.get_ingestion_for_approval(ingestion_id)

    ApprovalValidator(ingestion, username).validate()

    result = metadata_client.reject_ingestion(ingestion_id, username)
    return {
        **result,
        "rejeitado_por": username,
        "motivo": body.motivo,
    }


@router.post("/approvals/expire", response_model=Dict[str, Any], status_code=200)
def expire_pending_ingestions():
    """
    Cancela automaticamente todas as ingestões PENDING_APPROVAL com prazo expirado.
    """
    return metadata_client.cancel_expired_ingestions()
