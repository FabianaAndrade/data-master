"""
Configurações do metadata_service.
"""
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres_db:5432/data_catalog")
