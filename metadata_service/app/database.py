import os
import psycopg2
from psycopg2.extras import RealDictCursor

DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """
    Cria e retorna uma nova conexão com o banco de dados.
    FastAPI usará isso como uma dependência.
    """
    try:
        conn = psycopg2.connect(DATABASE_URL)
        yield conn
    finally:
        conn.close()
