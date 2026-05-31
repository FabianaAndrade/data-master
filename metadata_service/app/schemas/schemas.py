from pydantic import BaseModel



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
    tabela: str
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

