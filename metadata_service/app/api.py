from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

import psycopg2

from . import crud
from .schemas import  FullIngestionRequest
#from .schemas.IngestionUpdateRequest import IngestionRequestUpdate
from .database import get_db_connection

from typing import Optional, Union

class ColumnMetadata(BaseModel):
    column_name: str
    data_type: str
    column_description: str
    pii: bool
    pii_type_id: Optional[Union[int, str]] = None
    partition_column: bool

class TableMetadata(BaseModel):
    table_name: str
    table_description: str
    layer: str
    origin_id: int
    origin_format: str
    periodicity: str
    ingestion_type: str
    inicio_atualizacao: str
    tipo_atualizacao: str
    data_criacao: Optional[str] = None
    horario: Optional[str] = None

class IngestionRequestUpdate(BaseModel):
    table_metadata: TableMetadata
    columns: List[ColumnMetadata]


router = APIRouter()

# =====================================================================
# STATIC ROUTES MUST come BEFORE dynamic /{ingestion_id} routes,
# otherwise FastAPI treats "fontes", "list", etc. as an ingestion_id.
# =====================================================================

@router.get("/ingestions/list", response_model=Dict[str, Any], status_code=200)
def list_ingestions(username: str = None):
    """
    Lista ingestões.
    Se ?username=X for passado, filtra pelas ingestões viíveis ao usuário
    (criadas por ele OU de siglas das quais ele é owner).
    Sem parâmetro retorna todas (uso interno/admin).
    """
    try:
        if username:
            ingestions = crud.get_ingestions_list_for_user(username)
        else:
            ingestions = crud.get_ingestions_list()
        return {"ingestions": ingestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.get("/ingestions/fontes", response_model=Dict[str, Any], status_code=200)
def get_fontes_list():
    """
    Retorna a lista de fontes disponíveis para ingestão.
    """
    try:
        fontes = crud.get_fontes_list()
        print("Fontes retrieved from database:", fontes)  # Debug log
        return {"fontes": fontes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.get("/ingestions/pii_types", response_model=Dict[str, Any], status_code=200)
def get_pii_types():
    """Retorna a lista de tipos de PII disponíveis.
    """
    try:
        pii_types = crud.get_pii_types_list()
        return {
            "piiTypes": pii_types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.get("/ingestions/quality_rules", response_model=Dict[str, Any], status_code=200)
def get_quality_rules():
    """Retorna a lista de regras de qualidade disponíveis.
    """
    try:
        regras = crud.get_quality_rules_list()
        return {
            "colunas": [],
            "regras": regras
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.get("/ingestions/tabelas/{fonte}", response_model=Dict[str, Any], status_code=200)
def get_tabelas_list(fonte: str):
    """Retorna a lista de tabelas disponíveis para uma fonte específica.
    """
    try:
        tabelas = crud.get_tabelas_list(fonte)
        return {"fonte": fonte, "tabelas": tabelas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

# =====================================================================
# DYNAMIC ROUTES (with path parameters) come AFTER static routes.
# =====================================================================

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

@router.get("/ingestions/{ingestion_id}/versions/{version}", response_model=Dict)
def get_ingestion_version(ingestion_id: str, version: int):
    """
    Busca uma versão específica de uma ingestão, incluindo metadados da tabela e colunas.
    """
    db_ingestion = crud.get_ingestion_version(ingestion_id=ingestion_id, version=version)
    if db_ingestion is None:
        raise HTTPException(status_code=404, detail="Ingestion version not found")
    return db_ingestion

@router.get("/ingestions/{ingestion_id}", response_model=Dict)
def get_active_ingestion(ingestion_id: str):
    """
    Busca a versão ativa de uma ingestão.
    """
    db_ingestion = crud.get_ingestion_detail_db(ingestion_id=ingestion_id)
    if db_ingestion is None:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    return db_ingestion

@router.post("/ingestions", status_code=201, response_model=Dict[str, Any])
def create_ingestion(request: FullIngestionRequest, username: str = "system"):
    """
    Cria uma nova solicitação de ingestão (versão 1).
    O parâmetro ?username= deve ser enviado pelo ingestion_service com o usuário autenticado.
    """
    try:
        result = crud.submit_ingestion_db(username=username, body=request)
        return {"ingestion_id": result, "message": "Ingestion created successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.put("/ingestions/{ingestion_id}", status_code=200, response_model=Dict[str, Any])
def update_ingestion(ingestion_id: int, request: IngestionRequestUpdate, username: str = None):
    """
    Cria uma nova versão para uma ingestão existente a partir de uma solicitação de edição.
    Parâmetro opcional: ?username= para registrar quem editou.
    Consumido pelo ingestion_service (middleware).
    """
    conn = get_db_connection()
    try:
        with conn:
            result = crud.create_new_version_for_ingestion(conn, ingestion_id=ingestion_id, request=request)
            if username:
                user = crud.get_user_by_username(username)
                if user:
                    with conn.cursor() as cur:
                        cur.execute(
                            'UPDATE "ingestions" SET "last_updated_by" = %s WHERE "ingestion_id" = %s;',
                            (user["user_id"], ingestion_id)
                        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    finally:
        if conn:
            conn.close()

@router.post("/ingestions/{ingestion_id}/request-delete", status_code=200, response_model=Dict[str, str])
def request_ingestion_deletion(ingestion_id: str):
    """
    Cria uma nova versão para uma ingestão com a marcação de 'solicitação de deleção'.
    """
    try:
        conn = next(get_db_connection())
        crud.request_ingestion_deletion(conn, ingestion_id=ingestion_id)
        conn.commit()
        return {"ingestion_id": ingestion_id, "message": "Deletion requested successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.delete("/ingestions/{ingestion_id}", status_code=200, response_model=Dict[str, str])
def delete_ingestion(ingestion_id: int, username: str = None):
    """
    Solicita a exclusão de uma ingestão (soft delete).
    Marca como PENDING_DELETE para aprovação — os dados NÃO são removidos do banco.
    Parâmetro opcional: ?username= para verificação de permissão.
    Consumido pelo ingestion_service (middleware).
    """
    result = crud.delete_ingestion_db(ingestion_id=ingestion_id, username=username)
    if "error" in result:
        if result["error"] == "not_found":
            raise HTTPException(status_code=404, detail=result["message"])
        if result["error"] == "already_deleted":
            raise HTTPException(status_code=409, detail=result["message"])
        if result["error"] == "forbidden":
            raise HTTPException(status_code=403, detail=result["message"])
    return {"ingestion_id": str(ingestion_id), "message": result["message"]}


# =====================================================================
# APPROVAL WORKFLOW ENDPOINTS
# Consumidos pelo approval_service via HTTP.
# =====================================================================

class ApproveRejectBody(BaseModel):
    approved_by_username: str


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
        user = crud.get_user_by_username(body.approved_by_username)
        user_id = user["user_id"] if user else None
        crud.approve_ingestion_db(ingestion_id=ingestion_id, approved_by=user_id)
        return {"ingestion_id": ingestion_id, "status": "APPROVED", "message": "Aprovada com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/ingestions/{ingestion_id}/reject", response_model=Dict[str, Any], status_code=200)
def reject_ingestion(ingestion_id: int, body: ApproveRejectBody):
    """
    Rejeita uma solicitação de ingestão.
    """
    try:
        user = crud.get_user_by_username(body.approved_by_username)
        user_id = user["user_id"] if user else None
        crud.reject_ingestion_db(ingestion_id=ingestion_id, rejected_by=user_id)
        return {"ingestion_id": ingestion_id, "status": "REJECTED", "message": "Rejeitada com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.post("/ingestions/{ingestion_id}/cancel", response_model=Dict[str, Any], status_code=200)
def cancel_ingestion(ingestion_id: int, body: ApproveRejectBody):
    """
    Cancela uma ingestão específica por prazo expirado.
    """
    try:
        user = crud.get_user_by_username(body.approved_by_username)
        user_id = user["user_id"] if user else None
        crud.cancel_ingestion_db(ingestion_id=ingestion_id, cancelled_by=user_id)
        return {"ingestion_id": ingestion_id, "status": "CANCELLED", "message": "Cancelada por prazo expirado."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


class CancelByUserBody(BaseModel):
    username: str

@router.post("/ingestions/{ingestion_id}/cancel-by-user", response_model=Dict[str, Any], status_code=200)
def cancel_ingestion_by_user(ingestion_id: int, body: CancelByUserBody):
    """
    Cancela uma ingestão pelo próprio solicitante.
    Regras: apenas o criador pode cancelar, e o status não pode ser APPROVED.
    """
    result = crud.cancel_ingestion_by_user(ingestion_id=ingestion_id, username=body.username)
    if "error" in result:
        if result["error"] == "not_found":
            raise HTTPException(status_code=404, detail=result["message"])
        if result["error"] == "already_approved":
            raise HTTPException(status_code=409, detail=result["message"])
        if result["error"] == "forbidden":
            raise HTTPException(status_code=403, detail=result["message"])
    return {"ingestion_id": ingestion_id, "status": "CANCELLED", "message": result["message"]}


@router.post("/ingestions/cancel-expired", response_model=Dict[str, Any], status_code=200)
def cancel_expired():
    """
    Cancela em lote todas as ingestões PENDING_APPROVAL com prazo expirado.
    """
    try:
        cancelled = crud.cancel_expired_ingestions()
        return {
            "canceladas": cancelled,
            "total": len(cancelled),
            "message": f"{len(cancelled)} ingestão(ões) cancelada(s) por prazo expirado.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
