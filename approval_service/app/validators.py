"""
Regras de negócio do workflow de aprovação.
"""
from datetime import date

from fastapi import HTTPException

from . import metadata_client


class ApprovalValidator:
    """
    Encapsula as regras de validação para aprovação/rejeição de ingestões.
    """

    def __init__(self, ingestion: dict, approver_username: str) -> None:
        self._ingestion = ingestion
        self._approver_username = approver_username


    def validate(self) -> None:
        """
        Executa todas as regras de negócio em sequência.
        """
        self._check_status()
        self._check_deadline()
        self._check_ownership()


    def _check_status(self) -> None:
        """
        A ingestão deve estar com status PENDING_APPROVAL.
        """
        status = self._ingestion.get("status")
        if status != "PENDING_APPROVAL":
            raise HTTPException(
                status_code=409,
                detail=f"A ingestão não está pendente de aprovação. Status atual: {status}.",
            )

    def _check_deadline(self) -> None:
        """
        O prazo de aprovação não pode ter expirado.
        """
        deadline_str = self._ingestion.get("should_be_approved_until")
        if not deadline_str:
            return

        deadline = date.fromisoformat(deadline_str)
        if date.today() > deadline:
            metadata_client.cancel_ingestion(
                self._ingestion["ingestion_id"], self._approver_username
            )
            raise HTTPException(
                status_code=410,
                detail=(
                    f"O prazo de aprovação expirou em {deadline_str}. "
                    "A solicitação foi cancelada automaticamente."
                ),
            )

    def _check_ownership(self) -> None:
        """
        Apenas o owner da sigla pode aprovar/rejeitar.
        """
        owner_name = self._ingestion.get("owner_name") or ""
        owner_email = self._ingestion.get("owner_email") or ""
        if self._approver_username not in (owner_name, owner_email):
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Apenas o owner da sigla '{self._ingestion.get('sigla_name')}' pode aprovar esta ingestão. "
                    f"Owner responsável: {owner_name}."
                ),
            )
