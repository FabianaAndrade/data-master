from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import httpx
from config import AUTH_SERVICE_URL, METADATA_SERVICE_URL
from auth import get_current_user

app = FastAPI(title="Ingestion Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



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
    

    return {"user": username, "siglas": siglas_data}


@app.post("/ingestion/submit")
async def submit_ingestion(
    username: str = Depends(get_current_user),
    body: dict = {}
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{METADATA_SERVICE_URL}/ingestions",
                json=body,
                params={"username": username},   # ← repassa o usuário autenticado
                timeout=10.0,
            )
            response.raise_for_status()
            ingestion_id = response.json().get("ingestion_id")
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Erro do metadata_service: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=503,
                detail=f"Metadata service indisponível: {e}",
            )
        
    return {
        "status": "success",
        "ingestion_id": ingestion_id,
        "message": "Ingestão salva com sucesso no banco de dados."
    }


@app.get("/ingestion/list")
async def list_ingestions(username: str = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{METADATA_SERVICE_URL}/ingestions/list",
                params={"username": username},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Erro do metadata_service: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Metadata service indisponível: {e}")

@app.get("/ingestion/account-stats")
async def get_account_stats(username: str = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        try:
            # 1. Obter siglas do usuário
            siglas_res = await client.get(f"{AUTH_SERVICE_URL}/auth/siglas/{username}", timeout=10.0)
            siglas_res.raise_for_status()
            user_siglas = siglas_res.json()
            sigla_names = [s["id"] for s in user_siglas] if isinstance(user_siglas, list) else []

            # 2. Obter TODAS as ingestões
            ing_res = await client.get(f"{METADATA_SERVICE_URL}/ingestions/list", timeout=10.0)
            ing_res.raise_for_status()
            all_ingestions = ing_res.json().get("ingestions", [])

            # 3. Calcular estatísticas
            cadastradas_por_mim = sum(1 for i in all_ingestions if i.get("responsavel") == username)
            total_das_minhas_siglas = sum(1 for i in all_ingestions if i.get("sigla") in sigla_names)


            return {
                "username": username,
                "siglas": user_siglas,
                "ingestoes_cadastradas": cadastradas_por_mim,
                "ingestoes_total_siglas": total_das_minhas_siglas
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/ingestion/detail/{ingestion_id}")
async def get_ingestion_detail(ingestion_id: int, username: str = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{METADATA_SERVICE_URL}/ingestions/{ingestion_id}", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Erro do metadata_service: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Metadata service indisponível: {e}")

@app.post("/ingestion/cancel/{ingestion_id}")
async def cancel_ingestion(ingestion_id: int, username: str = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{METADATA_SERVICE_URL}/ingestions/{ingestion_id}/cancel-by-user",
                json={"username": username},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.json().get("detail", e.response.text))
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Metadata service indisponível: {e}")

@app.delete("/ingestion/delete/{ingestion_id}")
async def delete_ingestion(ingestion_id: int, username: str = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{METADATA_SERVICE_URL}/ingestions/{ingestion_id}",
                params={"username": username},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.json().get("detail", e.response.text),
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Metadata service indisponível: {e}")

@app.put("/ingestion/edit/{ingestion_id}")
async def edit_ingestion(ingestion_id: int, body: dict, username: str = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.put(
                f"{METADATA_SERVICE_URL}/ingestions/{ingestion_id}",
                json=body,
                params={"username": username},
                timeout=10.0,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=e.response.json().get("detail", e.response.text),
            )
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Metadata service indisponível: {e}")

@app.get("/ingestion/fontes")
async def get_ingestion_fontes(username: str = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{METADATA_SERVICE_URL}/ingestions/fontes", timeout=10.0)
            print("Response from metadata_service:", response.status_code, response.text)  # Debug log
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Erro do metadata_service: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Metadata service indisponível: {e}")


#/ingestions/tabelas/{fonte}
@app.get("/ingestion/tabelas/{fonte}")
async def get_ingestion_tabelas(fonte: str, username: str = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{METADATA_SERVICE_URL}/ingestions/tabelas/{fonte}", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Erro do metadata_service: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Metadata service indisponível: {e}")

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

#ingestions/pii_types

@app.get("/ingestion/colunas/{tabela}")
async def get_table_columns(tabela: str, username: str = Depends(get_current_user)):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{METADATA_SERVICE_URL}/ingestions/pii_types", timeout=10.0)
            response.raise_for_status()
            pii_types = response.json().get("piiTypes", [])
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
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{METADATA_SERVICE_URL}/ingestions/quality_rules", timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=f"Erro do metadata_service: {e.response.text}")
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Metadata service indisponível: {e}")