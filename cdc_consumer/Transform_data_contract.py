"""
Transform Data Contract
-----------------------
Transforma o payload enriquecido recebido via CDC/Outbox em um
Data Contract estruturado (dict) e persiste como YAML.

Padrões aplicados:
  - SRP: cada método constrói uma seção isolada do contrato.
  - Dataclass: representação tipada de colunas.
  - Builder interno: a montagem do contrato é feita em etapas claras.
"""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuração
# ---------------------------------------------------------------------------

API_VERSION = "v3.1.0"
CONTRACT_KIND = "DataContract"
DEFAULT_OUTPUT_DIR = os.getenv("DATA_CONTRACT_OUTPUT_DIR", ".")


# ---------------------------------------------------------------------------
# Modelo de domínio
# ---------------------------------------------------------------------------

@dataclass
class ColumnSpec:
    """Representação tipada de uma coluna do payload."""

    name: str
    description: str
    physical_type: str
    is_partition: bool = False
    is_primary_key: bool = False
    pii_type: str = ""
    quality_rules: list[str] = field(default_factory=list)

    # -- factory ----------------------------------------------------------

    @classmethod
    def from_payload(cls, raw: dict[str, Any]) -> ColumnSpec:
        """Cria um ColumnSpec a partir do dict cru de uma coluna."""
        return cls(
            name=raw.get("column_name", ""),
            description=raw.get("column_description", ""),
            physical_type=raw.get("data_type", "STRING"),
            is_partition=raw.get("partition_column", "Não") == "Sim",
            is_primary_key=False,
            pii_type=raw.get("pii_type", ""),
            quality_rules=raw.get("quality_rules", []),
        )

    # -- serialização para o contrato -------------------------------------

    def to_contract_dict(self) -> dict[str, Any]:
        """Converte para o formato esperado pelo schema do Data Contract."""
        return {
            "name": self.name,
            "description": self.description,
            "physicalType": self.physical_type,
            "primaryKey": self.is_primary_key,
            "partitioned": self.is_partition,
            "tags": [f"pii:{self.pii_type}"],
            "quality": [
                {
                    "id": rule,
                    "type": "library",
                    "metric": "rowCount",
                    "mustBe": "0",
                    "description": "",
                }
                for rule in self.quality_rules
            ],
        }


# ---------------------------------------------------------------------------
# Gerador do Data Contract
# ---------------------------------------------------------------------------

class DataContractGenerator:
    """
    Constrói um Data Contract a partir de um payload enriquecido e
    persiste o resultado como arquivo YAML.

    Uso:
        generator = DataContractGenerator(payload)
        contract  = generator.build()
        generator.write_yaml("output/my_contract.yaml")
    """

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload
        self._metadata: dict[str, Any] = payload.get("table_metadata", {})
        self._contract: dict[str, Any] | None = None

    # -- propriedades de conveniência ------------------------------------

    @property
    def table_name(self) -> str:
        return self._metadata.get("table_name", "unknown")

    @property
    def table_description(self) -> str:
        return self._metadata.get("table_description", "")

    # -- builders de cada seção ------------------------------------------

    def _build_header(self) -> dict[str, Any]:
        """Seção de cabeçalho: apiVersion, kind, id, name, version, status."""
        return {
            "apiVersion": API_VERSION,
            "kind": CONTRACT_KIND,
            "id": self.table_name,
            "name": self.table_name,
            "version": str(self._metadata.get("version", "1")),
            "status": self._payload.get("status", ""),
        }

    def _build_description(self) -> dict[str, str]:
        """Seção description (purpose / usage / limitations)."""
        desc = self.table_description
        return {
            "purpose": desc,
            "usage": desc,
            "limitations": desc,
        }

    def _build_columns(self) -> list[dict[str, Any]]:
        """Converte a lista de colunas do payload em dicts do contrato."""
        raw_columns = self._payload.get("columns", [])
        return [
            ColumnSpec.from_payload(col).to_contract_dict()
            for col in raw_columns
        ]

    def _build_schema(self) -> list[dict[str, Any]]:
        """Seção schema (lista de objetos de tabela com propriedades)."""
        return [
            {
                "name": self.table_name,
                "physicalType": "table",
                "description": self.table_description,
                "properties": self._build_columns(),
            }
        ]

    def _build_servers(self) -> list[dict[str, str]]:
        """Seção servers."""
        return [
            {
                "server": "databricks",
                "type": "azure",
                "format": "delta",
                "location": "sc:dd",
            }
        ]

    def _build_team(self) -> dict[str, Any]:
        """Seção team."""
        approved_by = self._payload.get("approved_by", "")
        return {
            "name": self._payload.get("sigla", ""),
            "members": [
                {
                    "username": approved_by,
                    "name": approved_by,
                    "role": "Owner",
                }
            ],
        }

    def _build_sla_properties(self) -> list[dict[str, str]]:
        """Seção slaProperties."""
        return [
            {
                "property": "periodicity",
                "value": self._metadata.get("periodicity", ""),
                "description": "Periodicity of data updates",
            },
            {
                "property": "ingestion_type",
                "value": self._metadata.get("ingestion_type", ""),
                "description": "Type of data ingestion",
            },
            {
                "property": "data_contract_execution_timestamp",
                "value": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "description": "Timestamp de execucao do data contract no databricks",
            }
        ]

    def _build_custom_properties(self) -> list[dict[str, Any]]:
        """Seção customProperties."""
        return [
            {"property": "aprovado_por", "value": self._payload.get("approved_by", "")},
            {"property": "ingestion_id", "value": self._payload.get("ingestion_id", "")},
            {"property": "sistema_origem", "value": self._metadata.get("origin", "")},
            {"property": "formato_origem", "value": self._metadata.get("origin_format", "")},
            {"property": "medallion_layer", "value": self._metadata.get("layer", "")},
        ]

    # -- orquestração ----------------------------------------------------

    def build(self) -> dict[str, Any]:
        """Monta o Data Contract completo a partir do payload."""
        self._contract = {
            **self._build_header(),
            "description": self._build_description(),
            "schema": self._build_schema(),
            "servers": self._build_servers(),
            "team": self._build_team(),
            "slaProperties": self._build_sla_properties(),
            "customProperties": self._build_custom_properties(),
            "contractCreatedTs": datetime.now(timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            ),
        }
        return self._contract

    # -- persistência YAML -----------------------------------------------

    def write_yaml(self) -> str:
        """
        Escreve o contrato em um arquivo YAML.

        Args:
            filepath: caminho completo do arquivo de saída.
                      Se omitido, gera automaticamente baseado no table_name.

        Returns:
            O caminho do arquivo escrito.
        """
        if self._contract is None:
            self.build()

        dc_yaml= yaml.dump(
                self._contract,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
                encoding='utf-8'
            )

    
        return dc_yaml

    # -- representação ---------------------------------------------------

    def __repr__(self) -> str:
        status = "built" if self._contract else "pending"
        return f"<DataContractGenerator table={self.table_name!r} status={status}>"


# ---------------------------------------------------------------------------
# Execução direta (teste / demonstração)
# ---------------------------------------------------------------------------

"""if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    sample_payload = {
        "sigla": "MKTI - Marketing e Tecnologia",
        "status": "APPROVED",
        "columns": [
            {
                "pii": "Sim",
                "pii_type": "CNPJ",
                "data_type": "STRING",
                "column_name": "cpf",
                "quality_rules": ["VALIDA_NULOS", "VALIDA_CPF"],
                "partition_column": "Não",
                "column_description": "Descrição gerada via IA para a coluna cpf",
            },
            {
                "pii": "Não",
                "pii_type": "",
                "data_type": "DATE",
                "column_name": "dat_ref_carga",
                "quality_rules": ["VALIDA_NULOS", "VALIDA_CPF"],
                "partition_column": "Sim",
                "column_description": "Descrição gerada via IA para a coluna dat_ref_carga",
            },
        ],
        "approved_by": "jsilva",
        "ingestion_id": 107,
        "table_metadata": {
            "layer": "RAW",
            "origin": "mysql",
            "version": 1,
            "table_name": "teste1",
            "periodicity": "Diária",
            "origin_format": "csv",
            "ingestion_type": "Micro-Batch",
            "table_description": "Tabela teste1 otimizada para análise de dados e transações.",
        },
    }

    generator = DataContractGenerator(sample_payload)
    contract = generator.build()

    print(generator.write_yaml())"""