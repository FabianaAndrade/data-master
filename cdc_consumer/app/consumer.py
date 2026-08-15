"""
CDC Consumer — Lógica de consumo Kafka
"""

import json
import time
import logging

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

from .config import Config
from .services.transformer import DataContractGenerator
from .services.github import GithubPushRepos

logger = logging.getLogger("cdc_consumer")


def connect_kafka(retries: int = 30, delay: int = 5) -> KafkaConsumer:
    """Tenta conectar ao Kafka com retries."""
    for attempt in range(1, retries + 1):
        try:
            consumer = KafkaConsumer(
                Config.CDC_TOPIC,
                bootstrap_servers=Config.KAFKA_BOOTSTRAP_SERVERS,
                group_id=Config.CONSUMER_GROUP_ID,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
                key_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
            )
            logger.info("✅ Conectado ao Kafka em %s", Config.KAFKA_BOOTSTRAP_SERVERS)
            return consumer
        except NoBrokersAvailable:
            logger.warning(
                "⏳ Kafka não disponível (tentativa %d/%d). Retentando em %ds...",
                attempt, retries, delay,
            )
            time.sleep(delay)

    raise RuntimeError(f"Não foi possível conectar ao Kafka após {retries} tentativas.")


def process_approved_ingestion(payload: dict) -> None:
    """
    Processa o evento enriquecido de uma ingestão aprovada.
    """
    logger.info("Iniciando processamento da ingestão: %s", payload)
    
    generator = DataContractGenerator(payload)
    contract_yaml = generator.write_yaml()
    logger.info("Data Contract gerado com sucesso:\n%s", contract_yaml)

    table_name = payload.get("table_metadata", {}).get("table_name", "unknown")
    team_name = payload.get("sigla", "")

    # Cria o repo no GitHub já com o arquivo YAML do data contract
    github = GithubPushRepos()
    
    # Handle the fact that contract_yaml might be bytes (if yaml.dump returns bytes) or str
    if isinstance(contract_yaml, bytes):
        contract_yaml = contract_yaml.decode("utf-8")
        
    result = github.create_repo_with_contract(table_name, contract_yaml, team_name)
    logger.info("GitHub result: %s", result)


def start_consumer():
    """Inicia o loop principal de consumo do Kafka."""
    logger.info("🚀 CDC Consumer iniciando (Outbox Pattern)...")
    logger.info("   Tópico : %s", Config.CDC_TOPIC)
    logger.info("   Broker : %s", Config.KAFKA_BOOTSTRAP_SERVERS)
    logger.info("   Group  : %s", Config.CONSUMER_GROUP_ID)

    consumer = connect_kafka()

    logger.info("👂 Escutando eventos no tópico '%s'...", Config.CDC_TOPIC)

    try:
        for message in consumer:
            logger.info(
                "📨 Mensagem recebida — partition=%s offset=%s key=%s",
                message.partition, message.offset, message.key,
            )

            payload = message.value
            if payload is None:
                logger.info("Tombstone event ignorado (offset=%s)", message.offset)
                continue

            # O Debezium EventRouter pode entregar o payload como string JSON.
            if isinstance(payload, str):
                logger.info("Payload recebido como string, fazendo parse JSON...")
                try:
                    payload = json.loads(payload)
                except json.JSONDecodeError:
                    logger.error("❌ Falha ao parsear payload: %s", payload[:200])
                    continue

            logger.info("📬 Payload type: %s", type(payload).__name__)

            # Se o payload vier wrapped pelo Debezium (com campos 'before', 'after', etc.)
            if isinstance(payload, dict) and "payload" in payload:
                inner = payload["payload"]
                if isinstance(inner, str):
                    try:
                        payload = json.loads(inner)
                    except json.JSONDecodeError:
                        logger.error("❌ Falha ao parsear payload interno: %s", inner[:200])
                        continue
                else:
                    payload = inner

            # O EventRouter já filtra: só eventos da tabela outbox chegam aqui.
            logger.info(
                "📬 Evento recebido: ingestion_id=%s",
                payload.get("ingestion_id", "?") if isinstance(payload, dict) else "?",
            )

            if isinstance(payload, dict):
                process_approved_ingestion(payload)
            else:
                logger.warning("⚠️ Payload não é um dict após parsing: type=%s, valor=%s",
                               type(payload).__name__, str(payload)[:300])

    except KeyboardInterrupt:
        logger.info("🛑 Consumer encerrado pelo usuário.")
    finally:
        consumer.close()
        logger.info("🔌 Consumer desconectado do Kafka.")
