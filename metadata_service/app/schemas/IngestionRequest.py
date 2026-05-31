from pydantic import BaseModel
from .TableMetadata import TableMetadata
from .ColumnMetadata import ColumnMetadata
from typing import List

class IngestionRequest(BaseModel):
    sigla: str
    fonte: str
    tabela: str
    descricao: str = ""