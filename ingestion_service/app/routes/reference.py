"""
Rotas de dados de referência para formulários de ingestão.
"""
from fastapi import APIRouter, Depends

from ..dependencies import get_current_user
from ..schemas import ColunasParticaoRequest, DicionarioRequest
from .. import metadata_client
from .llm_client import generate_dictionary

router = APIRouter()


@router.get("/siglas")
async def get_siglas(username: str = Depends(get_current_user)):
    """Retorna as siglas do usuário autenticado."""
    siglas_data = await metadata_client.auth_get(f"/auth/siglas/{username}")
    return {"user": username, "siglas": siglas_data}


@router.get("/fontes")
async def get_ingestion_fontes(username: str = Depends(get_current_user)):
    """Retorna a lista de fontes disponíveis."""
    return await metadata_client.metadata_get("/ingestions/fontes")


@router.get("/tabelas/{fonte}")
async def get_ingestion_tabelas(fonte: str, username: str = Depends(get_current_user)):
    """Retorna as tabelas disponíveis para uma fonte."""
    return await metadata_client.metadata_get(f"/ingestions/tabelas/{fonte}")


@router.get("/tabelas/formato/{fonte}")
async def get_formato_arquivo_origem(fonte: str, username: str = Depends(get_current_user)):
    """Retorna os formatos de arquivo disponíveis."""
    return {
        "opcoes": [
            {"value": "csv", "label": "CSV"},
            {"value": "json", "label": "JSON"},
            {"value": "JSON API", "label": "JSON API"},
            {"value": "xml", "label": "XML"},
            {"value": "parquet", "label": "Parquet"},
            {"value": "orc", "label": "ORC"},
            {"value": "Tabela relacional", "label": "Tabela relacional"},
            {"value": "N/A", "label": "N/A"},
        ]
    }


@router.get("/metadados/{tabela}")
async def get_ingestion_metadados(tabela: str, username: str = Depends(get_current_user)):
    """Retorna opções de metadados para configuração de ingestão."""
    return {
        "opcoes": {
            "periodicidade": ["Diária", "Semanal", "Mensal", "Tempo Real", "Unica"],
            "tipoIngestao": ["Batch", "Micro-Batch", "Streaming"],
            "atualizacao": ["Batch", "Append", "Overwrite", "Merge"],
            "incluirColunaDataRef": ["Sim", "Não"],
        }
    }


@router.get("/colunas/{tabela}")
async def get_table_columns(tabela: str, username: str = Depends(get_current_user)):
    """Retorna opções de configuração de colunas (tipos, PII, etc.)."""
    data = await metadata_client.metadata_get("/ingestions/pii_types")
    pii_types = data.get("piiTypes", [])
    return {
        "colunas": [],
        "opcoes": {
            "dataTypes": ["STRING", "INTEGER", "BIGINT", "FLOAT", "DATE", "TIMESTAMP", "BOOLEAN"],
            "chavePrimaria": ["Sim", "Não"],
            "pii": ["Sim", "Não"],
            "piiTypes": pii_types,
        },
    }


@router.post("/coluna/particao/{tabela}")
async def get_coluna_particao(
    tabela: str,
    body: ColunasParticaoRequest,
    username: str = Depends(get_current_user),
):
    """Retorna opções de coluna de partição."""
    opcoes = ["Nenhuma"] + body.colunas
    return {"opcoes": {"colunas": opcoes}}


@router.post("/dicionario/sugerir")
async def gerar_dicionario_ia(
    body: DicionarioRequest,
    username: str = Depends(get_current_user),
):
    """Gera descricoes automaticas usando o modelo Ollama configurado."""
    return await generate_dictionary(body.tabela, body.colunas)


@router.get("/quality_rules/{tabela}")
async def quality_rules(tabela: str, username: str = Depends(get_current_user)):
    """Retorna regras de qualidade disponíveis."""
    return await metadata_client.metadata_get("/ingestions/quality_rules")
