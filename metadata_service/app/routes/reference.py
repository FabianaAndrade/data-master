"""
Rotas de dados de referência — fontes, tabelas, PII types, quality rules.
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..crud import reference as crud

router = APIRouter()


@router.get("/ingestions/fontes", response_model=Dict[str, Any], status_code=200)
def get_fontes_list():
    """Retorna a lista de fontes disponíveis para ingestão."""
    try:
        fontes = crud.get_fontes_list()
        return {"fontes": fontes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.get("/ingestions/tabelas/{fonte}", response_model=Dict[str, Any], status_code=200)
def get_tabelas_list(fonte: str):
    """Retorna a lista de tabelas disponíveis para uma fonte específica."""
    try:
        tabelas = crud.get_tabelas_list(fonte)
        return {"fonte": fonte, "tabelas": tabelas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.get("/ingestions/pii_types", response_model=Dict[str, Any], status_code=200)
def get_pii_types():
    """Retorna a lista de tipos de PII disponíveis."""
    try:
        pii_types = crud.get_pii_types_list()
        return {"piiTypes": pii_types}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")


@router.get("/ingestions/quality_rules", response_model=Dict[str, Any], status_code=200)
def get_quality_rules():
    """Retorna a lista de regras de qualidade disponíveis."""
    try:
        regras = crud.get_quality_rules_list()
        return {"colunas": [], "regras": regras}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
