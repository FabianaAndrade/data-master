"""
Rotas CRUD de ingestões — criar, listar, detalhar, editar, cancelar, excluir.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..crud import ingestions as crud
from ..crud import helpers as crud_helpers
from ..database import get_db_connection
from ..schemas import (
    FullIngestionRequest,
    IngestionRequestUpdate,
    CancelByUserBody,
    ExecutionStatusBody,
)

router = APIRouter()


@router.post("/ingestions/{ingestion_id}/execution-status", response_model=Dict[str, Any], status_code=200)
def update_execution_status(ingestion_id: int, body: ExecutionStatusBody):
    """Atualiza o status de execução da ingestão (SUCCESS/FAILED)."""
    result = crud.update_execution_status_db(ingestion_id=ingestion_id, status=body.status)
    if "error" in result:
        if result["error"] == "not_found":
            raise HTTPException(status_code=404, detail=result["message"])
        raise HTTPException(status_code=500, detail=result["message"])
    return {
        "ingestion_id": ingestion_id,
        "status": result["status"],
        "message": result["message"]
    }

@router.get("/ingestions/list", response_model=Dict[str, Any], status_code=200)

def list_ingestions(username: str = None):
    """
    Lista ingestões.
    Se ?username=X for passado, filtra pelas ingestões visíveis ao usuário
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


@router.get("/ingestions/{ingestion_id}/versions/{version}", response_model=Dict)
def get_ingestion_version(ingestion_id: str, version: int):
    """
    Busca uma versão específica de uma ingestão, incluindo metadados da tabela e colunas.
    """
    db_ingestion = crud.get_ingestion_detail_db(ingestion_id=ingestion_id)
    if db_ingestion is None:
        raise HTTPException(status_code=404, detail="Ingestion version not found")
    return db_ingestion


@router.get("/ingestions/{ingestion_id}", response_model=Dict)
def get_active_ingestion(ingestion_id: str):
    """Busca a versão ativa de uma ingestão."""
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
                user = crud_helpers.get_user_by_username(username)
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
    """Cria uma nova versão para uma ingestão com a marcação de 'solicitação de deleção'."""
    try:
        conn = next(get_db_connection())
        crud.delete_ingestion_db(ingestion_id=ingestion_id)
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
