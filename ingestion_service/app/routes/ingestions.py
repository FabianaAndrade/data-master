"""
Rotas de CRUD de ingestões.
"""
from fastapi import APIRouter, Depends, HTTPException
import httpx
import os
import time
import logging
from typing import Any, Dict, Optional
from ..dependencies import get_current_user
from ..schemas import ExecutionStatusBody
from .. import metadata_client

logger = logging.getLogger("uvicorn")

router = APIRouter()

# Global cache for Contract ID -> Product ID mapping
# Format: { "contract_id": "product_id" }
DCM_PRODUCT_MAP = {}
LAST_CACHE_UPDATE = 0
CACHE_TTL = 3600  # Cache expires every hour (in seconds)

# Constants for Data Contract Manager
DCM_URL = os.getenv("DATA_CONTRACT_MANAGER_URL", "http://datacontract_manager:8080").rstrip("/")
DCM_API_KEY = os.getenv("DATA_CONTRACT_API_KEY", "")
# The DCM (Spring Boot) rejects requests where Host header != APPLICATION_HOST_WEB
DCM_HOST_HEADER = os.getenv("DATA_CONTRACT_MANAGER_HOST", "localhost:8081")

@router.post("/execution-status/{ingestion_id}", response_model=Dict[str, Any], status_code=200)
async def update_execution_status(ingestion_id: int, body: ExecutionStatusBody):
    """Atualiza o status de execução da ingestão (success/failed). Chamado pelo GitHub Actions."""
    return await metadata_client.metadata_post(
        f"/ingestions/{ingestion_id}/execution-status",
        json={"status": body.status},
    )

@router.get("/detail/{ingestion_id}")
async def get_ingestion_detail(ingestion_id: int, username: str = Depends(get_current_user)):
    """Obtém os detalhes de uma ingestão específica."""
    try:
        return await metadata_client.metadata_get(f"/ingestions/{ingestion_id}")
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Ingestão {ingestion_id} não encontrada ou erro na busca: {str(e)}")

@router.get("/detail/{ingestion_id}")
async def get_ingestion_detail(ingestion_id: int, username: str = Depends(get_current_user)):
    """Obtém os detalhes de uma ingestão específica."""
    try:
        # Chama o metadata_service para pegar os dados da ingestão
        result = await metadata_client.metadata_get(f"/ingestions/{ingestion_id}")
        if not result:
            raise HTTPException(status_code=404, detail="Ingestão não encontrada")
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Erro ao buscar detalhes da ingestão {ingestion_id}: {str(e)}")

def _build_dcm_headers() -> dict:
    """Headers padrão para as chamadas ao Data Contract Manager."""
    return {"x-api-key": DCM_API_KEY, "Host": DCM_HOST_HEADER, "Accept": "application/json"}


async def _load_product_map(client: httpx.AsyncClient, headers: dict) -> None:
    """Carrega o mapa contract_id -> product_id a partir dos data products."""
    global DCM_PRODUCT_MAP, LAST_CACHE_UPDATE
    res = await client.get(f"{DCM_URL}/api/dataproducts", headers=headers)
    if res.status_code != 200:
        logger.error("DEBUG: DCM dataproducts failed %s: %s", res.status_code, res.text)
        return

    data = res.json()
    prods = data.get("items", []) if isinstance(data, dict) else data
    if not isinstance(prods, list):
        prods = []

    DCM_PRODUCT_MAP.clear()
    for p in prods or []:
        pid = p.get("id") or p.get("dataProductId")
        ports = p.get("outputPorts") or p.get("output_ports") or []
        if not pid or not isinstance(ports, list):
            continue
        for port in ports:
            cid = port.get("contractId") or port.get("contract_id")
            if cid is not None:
                DCM_PRODUCT_MAP[str(cid)] = pid
    LAST_CACHE_UPDATE = time.time()
    logger.info(f"DEBUG: Product map updated with {len(DCM_PRODUCT_MAP)} entries")


async def _find_product_by_contract_id(contract_id: str) -> Optional[str]:
    """Retorna o data product que possui o data contract (ingestion_id) informado."""
    global DCM_PRODUCT_MAP, LAST_CACHE_UPDATE

    current_time = time.time()
    if contract_id in DCM_PRODUCT_MAP and (current_time - LAST_CACHE_UPDATE < CACHE_TTL):
        product_id = DCM_PRODUCT_MAP[contract_id]
        logger.info(f"DEBUG: Cache HIT -> {product_id}")
        return product_id

    logger.info(f"DEBUG: Cache MISS for {contract_id}, fetching products...")
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = _build_dcm_headers()
        await _load_product_map(client, headers)
    logger.info(f"DEBUG: Final product_id: {DCM_PRODUCT_MAP.get(contract_id)}")
    return DCM_PRODUCT_MAP.get(contract_id)


async def _fetch_product_consumers(product_id: str) -> list:
    """Busca os acessos (consumerType=user) do data product e retorna os consumidores."""
    logger.info(f"DEBUG: Fetching access for product {product_id}")
    async with httpx.AsyncClient(timeout=10.0) as client:
        headers = _build_dcm_headers()
        params = {
            "pageSize": 1000,
            "providerDataProductId": product_id,
            "consumerType": "user",
        }
        res = await client.get(f"{DCM_URL}/api/access", headers=headers, params=params)
        if res.status_code != 200:
            logger.error("DEBUG: DCM access failed %s: %s", res.status_code, res.text)
            return []

        accesses = res.json()
        if not isinstance(accesses, list):
            accesses = []

        consumers = []
        for access in accesses:
            if not isinstance(access, dict):
                continue
            consumer = access.get("consumer") or {}
            if not isinstance(consumer, dict):
                continue
            user_id = consumer.get("userId")
            if user_id:
                consumers.append({"name": user_id, "email": user_id})
        logger.info(f"DEBUG: Final consumers: {consumers}")
        return consumers


@router.get("/impact-analysis/{ingestion_id}")
async def get_impact_analysis(ingestion_id: int, username: str = Depends(get_current_user)):
    """
    Analisa o impacto de editar/excluir uma ingestão.
    Fluxo: ingestion_id -> data contract -> data product -> acessos (usuários consumidores).
    """
    logger.info(f"--- DEBUG IMPACT ANALYSIS START (ID: {ingestion_id}) ---")
    try:
        product_id = await _find_product_by_contract_id(str(ingestion_id))
        if not product_id:
            return {"consumers": [], "message": "No product found"}

        consumers = await _fetch_product_consumers(product_id)
        return {"product_id": product_id, "consumers": consumers}
    except Exception as e:
        logger.exception(f"DEBUG FATAL: {str(e)}")
        return {"consumers": [], "error": str(e)}


@router.post("/submit")
async def submit_ingestion(
    body: dict = {},
    username: str = Depends(get_current_user),
):
    """Cria uma nova solicitação de ingestão."""
    result = await metadata_client.metadata_post(
        "/ingestions", json=body, params={"username": username},
    )
    return {
        "status": "success",
        "ingestion_id": result.get("ingestion_id"),
        "message": "Ingestão salva com sucesso no banco de dados.",
    }


@router.get("/list")
async def list_ingestions(username: str = Depends(get_current_user)):
    """Lista ingestões visíveis para o usuário autenticado."""
    return await metadata_client.metadata_get(
        "/ingestions/list", params={"username": username},
    )


@router.get("/account-stats")
async def get_account_stats(username: str = Depends(get_current_user)):
    """Retorna estatísticas de ingestão do usuário."""
    user_siglas = await metadata_client.auth_get(f"/auth/siglas/{username}")
    sigla_names = [s["id"] for s in user_siglas] if isinstance(user_siglas, list) else []

    all_data = await metadata_client.metadata_get("/ingestions/list")
    all_ingestions = all_data.get("ingestions", [])

    cadastradas_por_mim = sum(1 for i in all_ingestions if i.get("responsavel") == username)
    total_das_minhas_siglas = sum(1 for i in all_ingestions if i.get("sigla") in sigla_names)

    return {
        "username": username,
        "stats": {
            "cadastradas": cadastradas_por_mim,
            "total_siglas": total_das_minhas_siglas,
        }
    }
