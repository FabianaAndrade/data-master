import os

class Config:
    # Kafka
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    CDC_TOPIC = os.getenv("CDC_TOPIC", "ingestion.events")
    CONSUMER_GROUP_ID = os.getenv("CONSUMER_GROUP_ID", "cdc-approved-ingestions")

    # GitHub
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "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") # Ideal is to provide it via env var
    GITHUB_ORG = os.getenv("GITHUB_ORG", "satus-org")

    # Misc
    DATA_CONTRACT_OUTPUT_DIR = os.getenv("DATA_CONTRACT_OUTPUT_DIR", ".")
