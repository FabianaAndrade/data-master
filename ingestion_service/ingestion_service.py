from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx
from config import AUTH_SERVICE_URL
from database import startup_db_seed, get_db_connection
from auth import get_current_user
from schemas import IngestionRequest, FullIngestionRequest
import crud

app = FastAPI(title="Ingestion Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    startup_db_seed()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ingestion")
def ingestion_status():
    return {"message": "Ingestion service is running"}

@app.get("/ingestion/siglas")
async def get_siglas(username: str = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{AUTH_SERVICE_URL}/auth/siglas/{username}",
                timeout=10.0,
            )
            response.raise_for_status()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Erro do auth_service: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Auth service indisponível: {e}",
            )

    siglas_data = response.json()
    
    # Sync in Postgres
    try:
        conn = get_db_connection()
        with conn:
            crud.get_or_create_user(conn, username)
            for s in siglas_data:
                sigla_name = s.get("id")
                owner_username = s.get("owner")
                if sigla_name:
                    crud.get_or_create_sigla(conn, sigla_name, owner_username)
        conn.close()
    except Exception as e:
        print(f"Error syncing siglas: {e}")

    return {"user": username, "siglas": siglas_data}

@app.post("/ingestion/start")
async def start_ingestion(
    body: IngestionRequest,
    username: str = Depends(get_current_user),
):
    try:
        ingestion_id = crud.start_ingestion_db(username, body)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao iniciar fluxo de ingestão no banco: {e}"
        )

    return {
        "status": "started",
        "user": username,
        "ingestion_id": ingestion_id,
        "sigla": body.sigla,
        "fonte": body.fonte,
        "tabela": body.tabela,
        "descricao": body.descricao,
        "proximo_passo": "metadata",
    }

@app.post("/ingestion/submit")
async def submit_ingestion(
    body: FullIngestionRequest,
    username: str = Depends(get_current_user),
):
    try:
        ingestion_id = crud.submit_ingestion_db(username, body)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao salvar ingestão completa: {e}"
        )
        
    return {
        "status": "success",
        "ingestion_id": ingestion_id,
        "message": "Ingestão salva com sucesso no banco de dados."
    }

@app.get("/ingestion/list")
async def list_ingestions(username: str = Depends(get_current_user)):
    try:
        return crud.get_ingestions_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingestion/detail/{ingestion_id}")
async def get_ingestion_detail(ingestion_id: int, username: str = Depends(get_current_user)):
    try:
        detail = crud.get_ingestion_detail_db(ingestion_id)
        if not detail:
            raise HTTPException(status_code=404, detail="Ingestão não encontrada")
        return detail
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingestion/fontes")
async def get_ingestion_fontes(username: str = Depends(get_current_user)):
    try:
        return {"fontes": crud.get_fontes_list()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingestion/tabelas/{fonte}")
async def get_ingestion_tabelas(fonte: str, username: str = Depends(get_current_user)):
    try:
        return {
            "fonte": fonte,
            "tabelas": crud.get_tabelas_list(fonte)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingestion/tabelas/formato/{fonte}")
async def get_formato_arquivo_origem(fonte: str, username: str = Depends(get_current_user)):
    mock_formatos = {
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
    return mock_formatos

@app.get("/ingestion/metadados/{tabela}")
async def get_ingestion_metadados(tabela: str, username: str = Depends(get_current_user)):
    return {
        "opcoes": {
            "periodicidade": ["Diária", "Semanal", "Mensal", "Tempo Real", "Unica"],
            "tipoIngestao": ["Batch", "Micro-Batch", "Streaming"],
            "atualizacao": ["Batch", "Append", "Overwrite", "Merge"],
            "incluirColunaDataRef": ["Sim", "Não"]
        }
    }

@app.get("/ingestion/colunas/{tabela}")
async def get_table_columns(tabela: str, username: str = Depends(get_current_user)):
    try:
        pii_types = crud.get_pii_types_list()
        return {
            "colunas": [],
            "opcoes": {
                "dataTypes": ["STRING", "INTEGER", "BIGINT", "FLOAT", "DATE", "TIMESTAMP", "BOOLEAN"],
                "chavePrimaria": ["Sim", "Não"],
                "pii": ["Sim", "Não"],
                "piiTypes": pii_types
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingestion/coluna/particao/{tabela}")
async def get_coluna_particao(tabela: str, body: dict, username: str = Depends(get_current_user)):
    colunas = body.get("colunas", [])
    opcoes = ["Nenhuma"] + colunas
    return {
        "opcoes": {
            "colunas": opcoes
        }
    }

@app.post("/ingestion/dicionario/sugerir")
async def gerar_dicionario_ia(body: dict, username: str = Depends(get_current_user)):
    tabela = body.get("tabela", "TABELA")
    colunas = body.get("colunas", [])
    colunas_desc = []
    for col in colunas:
        colunas_desc.append({"nome": col, "descricao": f"Descrição gerada via IA para a coluna {col}"})
        
    return {
        "descricaoTabela": f"Tabela {tabela} otimizada para análise de dados e transações.",
        "colunas": colunas_desc
    }

@app.get("/ingestion/quality_rules/{tabela}")
async def quality_rules(tabela: str, username: str = Depends(get_current_user)):
    try:
        return {
            "colunas": [],
            "regras": crud.get_quality_rules_list()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingestion/approve/{ingestion_id}")
async def approve_ingestion(ingestion_id: int, username: str = Depends(get_current_user)):
    try:
        crud.approve_ingestion_db(ingestion_id)
        return {"status": "approved", "ingestion_id": ingestion_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/ingestion/reject/{ingestion_id}")
async def reject_ingestion(ingestion_id: int, username: str = Depends(get_current_user)):
    try:
        crud.reject_ingestion_db(ingestion_id)
        return {"status": "rejected", "ingestion_id": ingestion_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/ingestion/{ingestion_id}")
async def delete_ingestion(ingestion_id: int, username: str = Depends(get_current_user)):
    try:
        crud.delete_ingestion_db(ingestion_id)
        return {"status": "deleted", "ingestion_id": ingestion_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))