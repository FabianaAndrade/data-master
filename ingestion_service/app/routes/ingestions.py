"""
Rotas de CRUD de ingestões.
"""
from fastapi import APIRouter, Depends

from ..dependencies import get_current_user
from .. import metadata_client

router = APIRouter()


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
        "siglas": user_siglas,
        "ingestoes_cadastradas": cadastradas_por_mim,
        "ingestoes_total_siglas": total_das_minhas_siglas,
    }


@router.get("/detail/{ingestion_id}")
async def get_ingestion_detail(ingestion_id: int, username: str = Depends(get_current_user)):
    """Retorna detalhes de uma ingestão específica."""
    return await metadata_client.metadata_get(f"/ingestions/{ingestion_id}")


@router.post("/cancel/{ingestion_id}")
async def cancel_ingestion(ingestion_id: int, username: str = Depends(get_current_user)):
    """Cancela uma ingestão pelo próprio solicitante."""
    return await metadata_client.metadata_post(
        f"/ingestions/{ingestion_id}/cancel-by-user", json={"username": username},
    )


@router.delete("/delete/{ingestion_id}")
async def delete_ingestion(ingestion_id: int, username: str = Depends(get_current_user)):
    """Solicita exclusão de uma ingestão."""
    return await metadata_client.metadata_delete(
        f"/ingestions/{ingestion_id}", params={"username": username},
    )


@router.put("/edit/{ingestion_id}")
async def edit_ingestion(ingestion_id: int, body: dict, username: str = Depends(get_current_user)):
    """Edita uma ingestão existente (cria nova versão)."""
    return await metadata_client.metadata_put(
        f"/ingestions/{ingestion_id}", json=body, params={"username": username},
    )
