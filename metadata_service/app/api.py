from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
import psycopg2

from . import crud
from .schemas.IngestionRequest import IngestionRequest
from schemas.IngestionUpdateRequest import IngestionRequestUpdate
from .database import get_db_connection

router = APIRouter()

@router.get("/ingestions/{ingestion_id}/versions/{version}", response_model=Dict)
def get_ingestion_version(ingestion_id: str, version: int, conn: psycopg2.extensions.connection = Depends(get_db_connection)):
    """
    Busca uma versão específica de uma ingestão, incluindo metadados da tabela e colunas.
    """
    db_ingestion = crud.get_ingestion_version(conn, ingestion_id=ingestion_id, version=version)
    if db_ingestion is None:
        raise HTTPException(status_code=404, detail="Ingestion version not found")
    return db_ingestion

@router.get("/ingestions/{ingestion_id}", response_model=Dict)
def get_active_ingestion(ingestion_id: str, conn: psycopg2.extensions.connection = Depends(get_db_connection)):
    """
    Busca a versão ativa de uma ingestão.
    """
    db_ingestion = crud.get_active_ingestion(conn, ingestion_id=ingestion_id)
    if db_ingestion is None:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    return db_ingestion

@router.post("/ingestions", status_code=201, response_model=Dict[str, Any])
def create_ingestion(request: IngestionRequestCreate, conn: psycopg2.extensions.connection = Depends(get_db_connection)):
    """
    Cria uma nova solicitação de ingestão (versão 1).
    """
    try:
        result = crud.create_new_ingestion(conn, request=request)
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.put("/ingestions/{ingestion_id}", status_code=200, response_model=Dict[str, Any])

def update_ingestion(ingestion_id: str, request: IngestionRequestUpdate, conn: psycopg2.extensions.connection = Depends(get_db_connection)):
    """
    Cria uma nova versão para uma ingestão existente a partir de uma solicitação de edição.
    """
    try:
        result = crud.create_new_version_for_ingestion(conn, ingestion_id=ingestion_id, request=request)
        conn.commit()
        return result
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.post("/ingestions/{ingestion_id}/request-delete", status_code=200, response_model=Dict[str, str])
def request_ingestion_deletion(ingestion_id: str, conn: psycopg2.extensions.connection = Depends(get_db_connection)):
    """
    Cria uma nova versão para uma ingestão com a marcação de 'solicitação de deleção'.
    """
    try:
        crud.request_ingestion_deletion(conn, ingestion_id=ingestion_id)
        conn.commit()
        return {"ingestion_id": ingestion_id, "message": "Deletion requested successfully."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
