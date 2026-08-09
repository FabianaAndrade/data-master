"""
CDC Consumer — Consome eventos enriquecidos do tópico Kafka
publicados via Outbox Pattern + Debezium EventRouter.

Quando uma ingestão é aprovada, o metadata_service insere um payload
completo na tabela outbox (na mesma transação). O Debezium captura
essa inserção e o EventRouter SMT roteia para o tópico `ingestion.events`.

Este consumer recebe o payload já enriquecido com:
- Metadados da tabela
- Metadados das colunas (tipos, descrições)
- Informações de PII
- Regras de Data Quality

Não há consulta direta ao banco de dados.
"""

from Transform_data_contract import DataContractGenerator
from Github_push_repos import GithubPushRepos
import json
import os
import time
import logging

from kafka import KafkaConsumer
from kafka.errors import NoBrokersAvailable

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
TOPIC = os.getenv("CDC_TOPIC", "ingestion.events")
GROUP_ID = os.getenv("CONSUMER_GROUP_ID", "cdc-approved-ingestions")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("cdc_consumer")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def connect_kafka(retries: int = 30, delay: int = 5) -> KafkaConsumer:
    """Tenta conectar ao Kafka com retries."""
    for attempt in range(1, retries + 1):
        try:
            consumer = KafkaConsumer(
                TOPIC,
                bootstrap_servers=KAFKA_BOOTSTRAP,
                group_id=GROUP_ID,
                auto_offset_reset="earliest",
                enable_auto_commit=True,
                value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
                key_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
            )
            logger.info("✅ Conectado ao Kafka em %s", KAFKA_BOOTSTRAP)
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

    table_name = payload["table_metadata"]["table_name"]

    # Cria o repo no GitHub já com o arquivo YAML do data contract
    github = GithubPushRepos()
    result = github.create_repo_with_contract(table_name, contract_yaml.decode("utf-8") if isinstance(contract_yaml, bytes) else contract_yaml)
    logger.info("GitHub result: %s", result)



# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    logger.info("🚀 CDC Consumer iniciando (Outbox Pattern)...")
    logger.info("   Tópico : %s", TOPIC)
    logger.info("   Broker : %s", KAFKA_BOOTSTRAP)
    logger.info("   Group  : %s", GROUP_ID)

    consumer = connect_kafka()

    logger.info("👂 Escutando eventos no tópico '%s'...", TOPIC)

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
            # Nesse caso, precisamos fazer o parse manual.
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
            # O payload é o JSON completo inserido na outbox.
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


if __name__ == "__main__":
    main()
