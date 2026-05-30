from pydantic import BaseModel

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