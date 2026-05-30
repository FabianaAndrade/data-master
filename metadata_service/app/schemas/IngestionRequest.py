from pydantic import BaseModel
from .TableMetadata import TableMetadata
from .ColumnMetadata import ColumnMetadata
from typing import List

class IngestionRequest(BaseModel):
    sigla_id: int
    created_by: int
    table_metadata: TableMetadata
    columns: List[ColumnMetadata]