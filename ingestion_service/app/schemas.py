"""
Schemas Pydantic do ingestion_service.
"""
from typing import List, Literal

from pydantic import BaseModel


class ExecutionStatusBody(BaseModel):
    status: Literal["success", "failed"]


class ColunasParticaoRequest(BaseModel):
    colunas: List[str] = []


class DicionarioRequest(BaseModel):
    tabela: str = "TABELA"
    colunas: List[str] = []
