"""
Rotas de CRUD de ingestões.
"""
from fastapi import APIRouter, Depends, HTTPException
import httpx
import os
import time
import logging
from ..dependencies import get_current_user
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
DCM_API_KEY = os.getenv("DATA_CONTRACT_API_KEY", "ed_live_user_i619nOoJlcm8SKvJf43VRxeaus5h3zrHUSdnxBXXd4IeQxGL0KJ2GAPhbcnrGIlH")
# The DCM (Spring Boot) rejects requests where Host header != APPLICATION_HOST_WEB
DCM_HOST_HEADER = os.getenv("DATA_CONTRACT_MANAGER_HOST", "localhost:8081")


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

@router.get("/impact-analysis/{ingestion_id}")
async def get_impact_analysis(ingestion_id: int, username: str = Depends(get_current_user)):
    """
    Analisa o impacto de editar/excluir uma ingestão.
    """
    global DCM_PRODUCT_MAP, LAST_CACHE_UPDATE
    logger.info(f"--- DEBUG IMPACT ANALYSIS START (ID: {ingestion_id}) ---")
    product_id = None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"x-api-key": DCM_API_KEY, "Host": DCM_HOST_HEADER, "Accept": "application/json"}
            s_ingestion_id = str(ingestion_id)

            current_time = time.time()
            if s_ingestion_id in DCM_PRODUCT_MAP and (current_time - LAST_CACHE_UPDATE < CACHE_TTL):
                product_id = DCM_PRODUCT_MAP[s_ingestion_id]
                logger.info(f"DEBUG: Cache HIT -> {product_id}")
            else:
                logger.info(f"DEBUG: Cache MISS for {s_ingestion_id}, fetching products...")
                res = await client.get(f"{DCM_URL}/api/dataproducts", headers=headers)
                if res.status_code == 200:
                    data = res.json()
                    print(f"DEBUG: DCM response data: {data}")
                    prods = data.get("items", []) if isinstance(data, dict) else data
                    if not isinstance(prods, list):
                        prods = []
                    logger.info(f"DEBUG: Got {len(prods) if prods else 0} products")
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
                    LAST_CACHE_UPDATE = current_time
                    product_id = DCM_PRODUCT_MAP.get(s_ingestion_id)
                else:
                    logger.error(f"DEBUG: DCM failed {res.status_code}")
                logger.info(f"DEBUG: Final product_id: {product_id}")

            if not product_id:
                return {"consumers": [], "message": "No product found"}

            logger.info(f"DEBUG: Fetching details for product {product_id}")
            res_prod = await client.get(f"{DCM_URL}/api/dataproducts/{product_id}", headers=headers)
            if res_prod.status_code != 200:
                logger.error("DEBUG: DCM product failed %s: %s", res_prod.status_code, res_prod.text)
                return {"product_id": product_id, "consumers": [], "message": "Product details unavailable"}
            product_data = res_prod.json()
            team = product_data.get("team")
            team_name = team.get("name") if isinstance(team, dict) else team
            logger.info(f"DEBUG: Team: {team_name}")

            if not team_name:
                return {"consumers": [], "message": "No team found"}

            logger.info(f"DEBUG: Fetching team {team_name}")
            res_team = await client.get(f"{DCM_URL}/api/teams/{team_name}", headers=headers)
            if res_team.status_code != 200:
                logger.error("DEBUG: DCM team failed %s: %s", res_team.status_code, res_team.text)
                return {"product_id": product_id, "consumers": [], "message": "Team members unavailable"}
            team_data = res_team.json()
            members = team_data.get("members", []) if isinstance(team_data, dict) else team_data
            if not isinstance(members, list):
                members = []
            logger.info(f"DEBUG: Got {len(members)} members")

            consumers = []
            for member in members:
                if not isinstance(member, dict):
                    continue
                email = member.get("emailAddress") or member.get("email") or member.get("mail")
                name = member.get("name") or member.get("displayName") or email
                if email:
                    consumers.append({"name": name, "email": email})
            logger.info(f"DEBUG: Final consumers: {consumers}")
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
