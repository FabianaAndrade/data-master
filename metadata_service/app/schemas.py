"""
Schemas Pydantic do metadata_service.
Todos os modelos de request/response ficam neste único arquivo.
"""
from typing import List, Optional, Union, Literal

from pydantic import BaseModel


class ExecutionStatusBody(BaseModel):
    status: Literal["success", "failed"]

# ---------------------------------------------------------------------------
# Modelos de criação de ingestão (FullIngestionRequest)
# ---------------------------------------------------------------------------

class ColumnInfo(BaseModel):
    nome: str
    dataType: str
    chavePrimaria: str
    pii: str
    piiType: str


class IngestionColumnDesc(BaseModel):
    coluna: str
    descricao: str


class IngestionColumnQuality(BaseModel):
    coluna: str
    regras: list[str]


class SiglaData(BaseModel):
    sigla: str
    gestorAprovador: str


class FonteData(BaseModel):
    sistemaOrigem: str
    formatoArquivo: str


class MetadadosData(BaseModel):
    nomeTabela: str
    periodicidade: str
    tipoIngestao: str
    horario: str = ""
    dataCriacao: str = ""
    dataAtualizacao: str = ""
    atualizacao: str = ""
    incluirColunaDataRef: str = ""
    camada: str = ""
    usage: str = ""
    limitacoes: str = ""
    classificacaoSeguranca: str = "Internal"
    retencao: str = "Não se aplica"


class ColunasData(BaseModel):
    numColunas: str
    colunas: list[ColumnInfo]
    colunaParticao: str


class DicionarizacaoData(BaseModel):
    descricaoTabela: str
    colunas: list[IngestionColumnDesc]


class QualidadeData(BaseModel):
    configurar: str
    colunas: list[IngestionColumnQuality]


class FullIngestionRequest(BaseModel):
    sigla: SiglaData
    fonte: FonteData
    metadados: MetadadosData
    colunas: ColunasData
    dicionarizacao: DicionarizacaoData
    qualidade: QualidadeData


# ---------------------------------------------------------------------------
# Modelo legado de criação simples (start_ingestion_db)
# ---------------------------------------------------------------------------

class IngestionRequest(BaseModel):
    sigla: str
    fonte: str
    tabela: str
    descricao: str = ""


# ---------------------------------------------------------------------------
# Modelos de edição / versionamento (update ingestion)
# ---------------------------------------------------------------------------

class ColumnMetadata(BaseModel):
    column_name: str
    data_type: str
    column_description: str
    pii: bool
    pii_type_id: Optional[Union[int, str]] = None
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
    data_criacao: Optional[str] = None
    horario: Optional[str] = None
    usage: Optional[str] = None
    limitations: Optional[str] = None
    security_classification: Optional[str] = "Internal"
    retention_months: Optional[str] = "Não se aplica"


class IngestionRequestUpdate(BaseModel):
    table_metadata: TableMetadata
    columns: List[ColumnMetadata]


# ---------------------------------------------------------------------------
# Modelos de workflow de aprovação
# ---------------------------------------------------------------------------

class ApproveRejectBody(BaseModel):
    approved_by_username: str


class CancelByUserBody(BaseModel):
    username: str
