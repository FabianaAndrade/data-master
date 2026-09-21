import os

class Config:
    KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:29092")
    CDC_TOPIC = os.getenv("CDC_TOPIC", "ingestion.events")
    CONSUMER_GROUP_ID = os.getenv("CONSUMER_GROUP_ID", "cdc-approved-ingestions")

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
    GITHUB_ORG = os.getenv("GITHUB_ORG", "aggron-org")

    DATA_CONTRACT_OUTPUT_DIR = os.getenv("DATA_CONTRACT_OUTPUT_DIR", ".")
