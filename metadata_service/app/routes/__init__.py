"""
Pacote de rotas do metadata_service.
Agrega os sub-routers mantendo a ordem correta:
rotas estáticas antes das dinâmicas (/{ingestion_id}).
"""
from fastapi import APIRouter

from .reference import router as reference_router
from .approval import router as approval_router
from .ingestions import router as ingestions_router

router = APIRouter()

# Ordem importa: rotas estáticas (/fontes, /list, /pii_types, /pending-approval, /cancel-expired)
# devem ser registradas ANTES das rotas dinâmicas (/{ingestion_id})
router.include_router(reference_router)
router.include_router(approval_router)
router.include_router(ingestions_router)
