from fastapi import APIRouter

from .ingestions import router as ingestions_router
from .reference import router as reference_router

router = APIRouter(prefix="/ingestion")
router.include_router(ingestions_router)
router.include_router(reference_router)
