from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from pydantic import BaseModel

import psycopg2

from . import crud
from .schemas import  FullIngestionRequest
#from .schemas.IngestionUpdateRequest import IngestionRequestUpdate
from .database import get_db_connection

class ColumnMetadata(BaseModel):
    column_name: str
    data_type: str
    column_description: str
    data_type: str
    pii: bool
    pii_type_id: int
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

class IngestionRequestUpdate(BaseModel):
    table_metadata: TableMetadata
    columns: List[ColumnMetadata]


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
    db_ingestion = crud.get_ingestion_detail_db(ingestion_id=ingestion_id)
    if db_ingestion is None:
        raise HTTPException(status_code=404, detail="Ingestion not found")
    return db_ingestion

@router.post("/ingestions", status_code=201, response_model=Dict[str, Any])
def create_ingestion(request: FullIngestionRequest, conn: psycopg2.extensions.connection = Depends(get_db_connection)):
    """
    Cria uma nova solicitação de ingestão (versão 1).
    """
    try:
        result = crud.start_ingestion_db(conn, request=request)
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

@router.get("/ingestions/list", response_model=Dict[str, Any], status_code=200)
def list_ingestions(conn: psycopg2.extensions.connection = Depends(get_db_connection)):
    """
    Lista todas as ingestões, incluindo suas versões e status.
    """
    try:
        ingestions = crud.get_ingestions_list(conn)
        return {"ingestions": ingestions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    


@router.get("/ingestions/fontes", response_model=Dict[str, Any], status_code=200)
def get_fontes_list(conn: psycopg2.extensions.connection = Depends(get_db_connection)):
    """
    Retorna a lista de fontes disponíveis para ingestão.
    """
    try:
        fontes = crud.get_fontes_list(conn)
        print("Fontes retrieved from database:", fontes)  # Debug log
        return {"fontes": fontes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.get("/ingestions/tabelas/{fonte}", response_model=Dict[str, Any], status_code=200)
def get_tabelas_list(fonte: str, conn: psycopg2.extensions.connection = Depends(get_db_connection)):
    """Retorna a lista de tabelas disponíveis para uma fonte específica.
    """   
    try:
        tabelas = crud.get_tabelas_list(conn, fonte)
        return {"fonte": fonte, "tabelas": tabelas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.get("ingestions/quality_rules", response_model=Dict[str, Any], status_code=200)
def get_quality_rules(tabela: str, conn: psycopg2.extensions.connection = Depends(get_db_connection)):
    """Retorna a lista de regras de qualidade disponíveis para uma tabela específica.
    """  
    try:
        regras = crud.get_quality_rules_list(conn)
        return {
            "colunas": [],
            "regras": regras
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

@router.get("/ingestions/pii_types", response_model=Dict[str, Any], status_code=200)
def get_pii_types(conn: psycopg2.extensions.connection = Depends(get_db_connection)):
    """Retorna a lista de tipos de PII disponíveis.
    """  
    try:
        pii_types = crud.get_pii_types_list(conn)
        return {
            "piiTypes": pii_types
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

