"""
Schemas Pydantic do ingestion_service.
"""
from typing import List

from pydantic import BaseModel


class ColunasParticaoRequest(BaseModel):
    colunas: List[str] = []


class DicionarioRequest(BaseModel):
    tabela: str = "TABELA"
    colunas: List[str] = []
