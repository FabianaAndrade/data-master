"""
Configurações do approval_service.
"""
import os

JWT_SECRET = os.getenv("JWT_SECRET", "")
JWT_ALGORITHM = "HS256"
