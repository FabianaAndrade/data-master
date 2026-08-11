"""
Rotas do workflow de aprovação — approve, reject, cancel, pendentes.
Consumidas pelo approval_service via HTTP.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..crud import approval as crud
from ..crud import helpers as crud_helpers
from ..schemas import ApproveRejectBody

router = APIRouter()


@router.get("/ingestions/pending-approval", response_model=Dict[str, Any], status_code=200)
def list_pending_for_owner(owner: str):
    """
    Lista ingestões PENDING_APPROVAL cujo owner da sigla é o usuário informado.
    Parâmetro: ?owner=<username>
    Consumido pelo approval_service.
    """
    ingestions = crud.get_pending_ingestions_for_owner(owner)
    for ing in ingestions:
        for key, value in ing.items():
            if hasattr(value, "isoformat"):
                ing[key] = value.isoformat()
    return {"owner": owner, "total": len(ingestions), "pendentes": ingestions}


@router.get("/ingestions/{ingestion_id}/approval-detail", response_model=Dict[str, Any], status_code=200)
def get_ingestion_approval_detail(ingestion_id: int):
    """
    Retorna dados completos de uma ingestão para o fluxo de aprovação:
    status, prazo, criador, owner da sigla.
    """
    data = crud.get_ingestion_for_approval(ingestion_id)
    if not data:
        raise HTTPException(status_code=404, detail="Ingestão não encontrada.")
    # Serializar datas para string (ISO format)
    for key, value in data.items():
        if hasattr(value, "isoformat"):
            data[key] = value.isoformat()
    return data


@router.post("/ingestions/{ingestion_id}/approve", response_model=Dict[str, Any], status_code=200)
def approve_ingestion(ingestion_id: int, body: ApproveRejectBody):
    """
    Aprova uma solicitação de ingestão. O caller (approval_service) deve
    passar o username do aprovador para registrar last_updated_by.
    """
    try:
        user = crud_helpers.get_user_by_username(body.approved_by_username)
        user_id = user["user_id"] if user else None
        crud.approve_ingestion_db(ingestion_id=ingestion_id, approved_by=user_id)
        return {"ingestion_id": ingestion_id, "status": "APPROVED", "message": "Aprovada com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/ingestions/{ingestion_id}/reject", response_model=Dict[str, Any], status_code=200)
def reject_ingestion(ingestion_id: int, body: ApproveRejectBody):
    """Rejeita uma solicitação de ingestão."""
    try:
        user = crud_helpers.get_user_by_username(body.approved_by_username)
        user_id = user["user_id"] if user else None
        crud.reject_ingestion_db(ingestion_id=ingestion_id, rejected_by=user_id)
        return {"ingestion_id": ingestion_id, "status": "REJECTED", "message": "Rejeitada com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/ingestions/{ingestion_id}/cancel", response_model=Dict[str, Any], status_code=200)
def cancel_ingestion(ingestion_id: int, body: ApproveRejectBody):
    """Cancela uma ingestão específica por prazo expirado."""
    try:
        user = crud_helpers.get_user_by_username(body.approved_by_username)
        user_id = user["user_id"] if user else None
        crud.cancel_ingestion_db(ingestion_id=ingestion_id, cancelled_by=user_id)
        return {"ingestion_id": ingestion_id, "status": "CANCELLED", "message": "Cancelada por prazo expirado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/ingestions/cancel-expired", response_model=Dict[str, Any], status_code=200)
def cancel_expired():
    """Cancela em lote todas as ingestões PENDING_APPROVAL com prazo expirado."""
    try:
        cancelled = crud.cancel_expired_ingestions()
        return {
            "canceladas": cancelled,
            "total": len(cancelled),
            "message": f"{len(cancelled)} ingestão(ões) cancelada(s) por prazo expirado.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
