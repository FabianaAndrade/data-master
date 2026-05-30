import psycopg2
from psycopg2.extras import RealDictCursor
from .schemas.IngestionRequest import IngestionRequest
from .schemas.IngestionUpdateRequest import IngestionRequestUpdate



def get_ingestion_version(conn: psycopg2.extensions.connection, ingestion_id: str, version: int):
    """
    Busca os metadados de uma versão específica de uma ingestão.
    """
    # Esta query precisa ser melhorada para retornar um JSON aninhado.
    # Frameworks como SQLAlchemy facilitariam isso.
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
            SELECT * FROM ingestions_table_metadata itm
            LEFT JOIN ingestions_columns_metadata icm ON itm.ingestion_id = icm.ingestion_id AND itm.version = icm.version
            WHERE itm.ingestion_id = %s AND itm.version = %s;
        """, (ingestion_id, version))
        return cur.fetchall()

def get_active_ingestion(conn: psycopg2.extensions.connection, ingestion_id: str):
    """
    Busca a versão ativa de uma ingestão.
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT active_version FROM ingestions WHERE ingestion_id = %s;", (ingestion_id,))
        active_version_row = cur.fetchone()
        if not active_version_row:
            return None
        
        active_version = active_version_row['active_version']
        return get_ingestion_version(conn, ingestion_id, active_version)

def create_new_ingestion(conn: psycopg2.extensions.connection, request: IngestionRequestCreate):
    """
    Cria uma nova ingestão (versão 1) no banco de dados.
    """
    with conn.cursor() as cur:
        # 1. Inserir na tabela principal `ingestions`
        cur.execute(
            """
            INSERT INTO ingestions (sigla_id, created_by, status, last_operation, active_version) 
            VALUES (%s, %s, 'PENDING_APPROVAL', 'CREATE', 1) 
            RETURNING ingestion_id;
            """,
            (request.sigla_id, request.created_by)
        )
        ingestion_id = cur.fetchone()[0]

        # 2. Inserir metadados da tabela
        table_meta = request.table_metadata
        cur.execute(
            """
            INSERT INTO ingestions_table_metadata (ingestion_id, version, table_name, table_description, layer, is_active)
            VALUES (%s, 1, %s, %s, %s, TRUE);
            """,
            (ingestion_id, table_meta.table_name, table_meta.table_description, table_meta.layer)
        )

        # 3. Inserir metadados das colunas
        for col in request.columns:
            cur.execute(
                """
                INSERT INTO ingestions_columns_metadata (ingestion_id, version, column_name, data_type, column_description)
                VALUES (%s, 1, %s, %s, %s);
                """,
                (ingestion_id, col.column_name, col.data_type, col.column_description)
            )
        
        return {"ingestion_id": ingestion_id, "version": 1}


def create_new_version_for_ingestion(conn: psycopg2.extensions.connection, ingestion_id: str, request: IngestionRequestUpdate):
    """
    Cria uma nova versão para uma ingestão existente.
    """
    with conn.cursor() as cur:
        # 1. Obter a versão ativa atual e travar a linha para evitar concorrência
        cur.execute("SELECT active_version FROM ingestions WHERE ingestion_id = %s FOR UPDATE;", (ingestion_id,))
        current_version = cur.fetchone()['active_version']
        new_version = current_version + 1

        # 2. Marcar a versão antiga como inativa
        cur.execute(
            "UPDATE ingestions_table_metadata SET is_active = FALSE WHERE ingestion_id = %s AND version = %s;",
            (ingestion_id, current_version)
        )

        # 3. Inserir os novos metadados da tabela para a nova versão
        table_meta = request.table_metadata
        cur.execute(
            """
            INSERT INTO ingestions_table_metadata (ingestion_id, version, table_name, table_description, layer, is_active)
            VALUES (%s, %s, %s, %s, %s, TRUE);
            """,
            (ingestion_id, new_version, table_meta.table_name, table_meta.table_description, table_meta.layer)
        )

        # 4. Inserir os novos metadados das colunas para a nova versão
        for col in request.columns:
            cur.execute(
                """
                INSERT INTO ingestions_columns_metadata (ingestion_id, version, column_name, data_type, column_description)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (ingestion_id, new_version, col.column_name, col.data_type, col.column_description)
            )

        # 5. Atualizar a tabela principal para apontar para a nova versão
        cur.execute(
            "UPDATE ingestions SET active_version = %s, last_operation = 'UPDATE' WHERE ingestion_id = %s;",
            (new_version, ingestion_id)
        )

        return {"ingestion_id": ingestion_id, "new_version": new_version}

def request_ingestion_deletion(conn: psycopg2.extensions.connection, ingestion_id: str):
    # Lógica para criar uma nova versão com status de deleção
    # Similar a `create_new_version_for_ingestion`, mas com `last_operation = 'DELETE_REQUESTED'`
    # e talvez um status diferente na `ingestions_table_metadata`.
    pass
