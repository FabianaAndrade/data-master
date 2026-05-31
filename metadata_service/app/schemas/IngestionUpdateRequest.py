from pydantic import BaseModel
from .TableMetadata import TableMetadata
from .ColumnMetadata import ColumnMetadata
from typing import List

class IngestionUpdateRequest(BaseModel):
    table_metadata: TableMetadata
    columns: List[ColumnMetadata]
