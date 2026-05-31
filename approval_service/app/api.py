from datetime import date
from typing import Any, Dict, Optional

import jwt
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from . import database as metadata_client

router = APIRouter()

# Chave JWT compartilhada com o auth_service
JWT_SECRET = "secret_key"
JWT_ALGORITHM = "HS256"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decode_token(authorization: Optional[str]) -> str:
    """Decodifica o Bearer token e retorna o username (sub)."""
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


def _validate_approval_rules(ingestion: dict, approver_username: str) -> None:
    """
    Aplica as regras de negócio do workflow de aprovação.
    Lança HTTPException em caso de violação.
    """
    # 1. Ingestão deve estar PENDING_APPROVAL
    if ingestion.get("status") != "PENDING_APPROVAL":
        raise HTTPException(
            status_code=409,
            detail=f"A ingestão não está pendente de aprovação. Status atual: {ingestion.get('status')}.",
        )

    # 2. Prazo de aprovação não pode ter expirado (10 dias)
    deadline_str = ingestion.get("should_be_approved_until")
    if deadline_str:
        deadline = date.fromisoformat(deadline_str)
        if date.today() > deadline:
            # Notifica o metadata_service para cancelar
            metadata_client.cancel_ingestion(ingestion["ingestion_id"], approver_username)
            raise HTTPException(
                status_code=410,
                detail=(
                    f"O prazo de aprovação expirou em {deadline_str}. "
                    "A solicitação foi cancelada automaticamente."
                ),
            )

    # 3. Apenas o owner da sigla pode aprovar
    owner_name = ingestion.get("owner_name") or ""
    owner_email = ingestion.get("owner_email") or ""
    if approver_username not in (owner_name, owner_email):
        raise HTTPException(
            status_code=403,
            detail=(
                f"Apenas o owner da sigla '{ingestion.get('sigla_name')}' pode aprovar esta ingestão. "
                f"Owner responsável: {owner_name}."
            ),
        )

    # 4. Solicitante não pode aprovar a própria ingestão
    creator_name = ingestion.get("created_by_name") or ""
    creator_email = ingestion.get("created_by_email") or ""
    if approver_username in (creator_name, creator_email):
        raise HTTPException(
            status_code=403,
            detail="O solicitante não pode aprovar a própria ingestão.",
        )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

class RejectBody(BaseModel):
    motivo: Optional[str] = None


@router.get("/approvals/pending", response_model=Dict[str, Any], status_code=200)
def list_pending_approvals(authorization: Optional[str] = Header(default=None)):
    """
    Lista todas as ingestões pendentes de aprovação para o owner autenticado.
    Delega ao metadata_service via HTTP.
    """
    username = _decode_token(authorization)
    return metadata_client.get_pending_ingestions_for_owner(username)


@router.get("/approvals/{ingestion_id}", response_model=Dict[str, Any], status_code=200)
def get_approval_detail(ingestion_id: int, authorization: Optional[str] = Header(default=None)):
    """
    Retorna detalhes de uma ingestão para análise de aprovação.
    Delega ao metadata_service via HTTP.
    """
    _decode_token(authorization)  # valida autenticação
    return metadata_client.get_ingestion_for_approval(ingestion_id)


@router.post("/approvals/{ingestion_id}/approve", response_model=Dict[str, Any], status_code=200)
def approve_ingestion(ingestion_id: int, authorization: Optional[str] = Header(default=None)):
    """
    Aprova uma solicitação de ingestão.

    Regras de negócio validadas localmente antes de delegar ao metadata_service:
    - Apenas o owner da sigla pode aprovar
    - O solicitante não pode aprovar a própria solicitação
    - A aprovação deve ser feita dentro do prazo de 10 dias
    """
    username = _decode_token(authorization)

    # Busca dados da ingestão via metadata_service
    ingestion = metadata_client.get_ingestion_for_approval(ingestion_id)

    # Aplica as regras de negócio
    _validate_approval_rules(ingestion, username)

    # Delega a escrita ao metadata_service
    result = metadata_client.approve_ingestion(ingestion_id, username)
    return {
        **result,
        "aprovado_por": username,
    }


@router.post("/approvals/{ingestion_id}/reject", response_model=Dict[str, Any], status_code=200)
def reject_ingestion(
    ingestion_id: int,
    body: RejectBody = RejectBody(),
    authorization: Optional[str] = Header(default=None),
):
    """
    Rejeita uma solicitação de ingestão.

    Regras de negócio validadas localmente antes de delegar ao metadata_service:
    - Apenas o owner da sigla pode rejeitar
    - O solicitante não pode rejeitar a própria solicitação
    - A rejeição deve ser feita dentro do prazo de 10 dias
    """
    username = _decode_token(authorization)

    # Busca dados da ingestão via metadata_service
    ingestion = metadata_client.get_ingestion_for_approval(ingestion_id)

    # Aplica as regras de negócio
    _validate_approval_rules(ingestion, username)

    # Delega a escrita ao metadata_service
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
    Pode ser chamado por um job/cron externo — não requer autenticação.
    Delega ao metadata_service via HTTP.
    """
    return metadata_client.cancel_expired_ingestions()
