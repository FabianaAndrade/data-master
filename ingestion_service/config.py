import os

JWT_SECRET = "secret_key"
JWT_ALGORITHM = "HS256"
AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth_service:8000")
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres_db:5432/data_catalog")
