from pydantic import BaseModel
from metadata_service.app.schemas.TableMetadata import TableMetadata
from metadata_service.app.schemas.ColumnMetadata import ColumnMetadata
from typing import List

class IngestionUpdateRequest(BaseModel):
    table_metadata: TableMetadata
    columns: List[ColumnMetadata]
