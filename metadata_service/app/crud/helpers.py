"""
Funções utilitárias compartilhadas entre os módulos de CRUD.
"""
from datetime import datetime

from psycopg2.extras import RealDictCursor

from ..database import get_db_connection


def get_or_create_user(conn, username: str) -> int:
    with conn.cursor() as cur:
        cur.execute('SELECT "user_id" FROM "users" WHERE "email" = %s OR "full_name" = %s;', (username, username))
        row = cur.fetchone()
        if row:
            return row[0]
        email = f"{username}@empresa.com"
        cur.execute(
            'INSERT INTO "users" ("email", "full_name") VALUES (%s, %s) RETURNING "user_id";',
            (email, username)
        )
        return cur.fetchone()[0]

def get_or_create_sigla(conn, sigla_name: str, owner_username: str = None) -> int:
    with conn.cursor() as cur:
        cur.execute('SELECT "sigla_id" FROM "siglas" WHERE "name" = %s;', (sigla_name,))
        row = cur.fetchone()
        if row:
            return row[0]
        
        owner_id = None
        if owner_username:
            owner_id = get_or_create_user(conn, owner_username)
            
        cur.execute(
            'INSERT INTO "siglas" ("name", "owner_id") VALUES (%s, %s) RETURNING "sigla_id";',
            (sigla_name, owner_id)
        )
        return cur.fetchone()[0]

def parse_date(date_str: str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except Exception:
        try:
            return datetime.strptime(date_str, "%d/%m/%Y").date()
        except Exception:
            return None

def get_user_by_username(username: str):
    """Busca um usuário por full_name ou email."""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT user_id, full_name, email
                FROM "users"
                WHERE full_name = %s OR email = %s
                LIMIT 1;
                """,
                (username, username),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        if conn:
            conn.close()
