"""
Schemas Pydantic do approval_service.
"""
from pydantic import BaseModel


class RejectBody(BaseModel):
    motivo: str
