from pydantic import BaseModel


class ColumnMetadata(BaseModel):
    column_name: str
    data_type: str
    column_description: str
    data_type: str
    pii: bool
    pii_type_id: int
    partition_column: bool
