"""
Configurações do ingestion_service.
"""
import os

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000")
METADATA_SERVICE_URL = os.getenv("METADATA_SERVICE_URL", "http://metadata_service:8002")