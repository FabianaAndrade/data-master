from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from database import get_db_connection
from schemas import FullIngestionRequest, IngestionRequest

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

def start_ingestion_db(username: str, body: IngestionRequest) -> int:
    conn = get_db_connection()
    try:
        with conn:
            creator_id = get_or_create_user(conn, username)
            sigla_id = get_or_create_sigla(conn, body.sigla, username)
            
            with conn.cursor() as cur:
                cur.execute('SELECT "sys_id" FROM "origins" WHERE "sys_name" = %s AND "sys_table_name" = %s;', (body.fonte, body.tabela))
                origin_row = cur.fetchone()
                if origin_row:
                    origin_id = origin_row[0]
                else:
                    cur.execute(
                        'INSERT INTO "origins" ("sys_name", "sys_table_name") VALUES (%s, %s) RETURNING "sys_id";',
                        (body.fonte, body.tabela)
                    )
                    origin_id = cur.fetchone()[0]
                
                cur.execute(
                    """
                    INSERT INTO "ingestions" (
                        "sigla_id", "created_at", "status", "should_be_approved_until", 
                        "created_by", "last_updated_by", "active_version", "last_operation"
                    )
                    VALUES (%s, CURRENT_DATE, 'PENDING_APPROVAL', CURRENT_DATE + INTERVAL '7 days', %s, %s, NULL, 'CREATE')
                    RETURNING "ingestion_id";
                    """,
                    (sigla_id, creator_id, creator_id)
                )
                ingestion_id = cur.fetchone()[0]
                
                cur.execute(
                    """
                    INSERT INTO "ingestions_table_metadata" (
                        "ingestion_id", "version", "created_at", "is_active", 
                        "table_name", "table_description", "origin", "layer"
                    )
                    VALUES (%s, 1, CURRENT_DATE, TRUE, %s, %s, %s, 'RAW');
                    """,
                    (ingestion_id, body.tabela, body.descricao, origin_id)
                )
                
                cur.execute(
                    """
                    UPDATE "ingestions" SET "active_version" = 1 WHERE "ingestion_id" = %s;
                    """,
                    (ingestion_id,)
                )
        return ingestion_id
    finally:
        if conn:
            conn.close()

def submit_ingestion_db(username: str, body: FullIngestionRequest) -> int:
    conn = get_db_connection()
    try:
        with conn:
            creator_id = get_or_create_user(conn, username)
            sigla_id = get_or_create_sigla(conn, body.sigla.sigla, body.sigla.gestorAprovador)
            
            with conn.cursor() as cur:
                cur.execute('SELECT "sys_id" FROM "origins" WHERE "sys_name" = %s AND "sys_table_name" = %s;', (body.fonte.sistemaOrigem, body.fonte.tabela))
                origin_row = cur.fetchone()
                if origin_row:
                    origin_id = origin_row[0]
                else:
                    cur.execute(
                        'INSERT INTO "origins" ("sys_name", "sys_table_name") VALUES (%s, %s) RETURNING "sys_id";',
                        (body.fonte.sistemaOrigem, body.fonte.tabela)
                    )
                    origin_id = cur.fetchone()[0]
                
                cur.execute(
                    """
                    INSERT INTO "ingestions" (
                        "sigla_id", "created_at", "status", "should_be_approved_until", 
                        "created_by", "last_updated_by", "active_version", "last_operation"
                    )
                    VALUES (%s, CURRENT_DATE, 'PENDING_APPROVAL', CURRENT_DATE + INTERVAL '7 days', %s, %s, NULL, 'CREATE')
                    RETURNING "ingestion_id";
                    """,
                    (sigla_id, creator_id, creator_id)
                )
                ingestion_id = cur.fetchone()[0]
                
                data_criacao = parse_date(body.metadados.dataCriacao)
                data_atualizacao = parse_date(body.metadados.dataAtualizacao)
                
                cur.execute(
                    """
                    INSERT INTO "ingestions_table_metadata" (
                        "ingestion_id", "version", "created_at", "is_active", 
                        "table_name", "table_description", "origin", "layer", 
                        "origin_format", "periodicity", "ingestion_type", "inicial_date_update"
                    )
                    VALUES (%s, 1, %s, TRUE, %s, %s, %s, 'RAW', %s, %s, %s, %s);
                    """,
                    (
                        ingestion_id, 
                        data_criacao,
                        body.metadados.nomeTabela or body.fonte.tabela, 
                        body.dicionarizacao.descricaoTabela, 
                        origin_id,
                        body.fonte.formatoArquivo,
                        body.metadados.periodicidade,
                        body.metadados.tipoIngestao,
                        data_atualizacao
                    )
                )
                
                descriptions = {d.coluna: d.descricao for d in body.dicionarizacao.colunas}
                
                cur.execute('SELECT "pii_name", "pii_id" FROM "pii_types";')
                pii_map = {row[0]: row[1] for row in cur.fetchall()}
                
                cur.execute('SELECT "rule_name", "rule_id" FROM "quality_rules";')
                rules_map = {row[0]: row[1] for row in cur.fetchall()}
                
                for col in body.colunas.colunas:
                    if not col.nome:
                        continue
                    
                    col_desc = descriptions.get(col.nome, "")
                    pii_id = pii_map.get(col.piiType) if col.pii == "Sim" else None
                    is_partition = "Sim" if body.colunas.colunaParticao == col.nome else "Não"
                    
                    cur.execute(
                        """
                        INSERT INTO "ingestions_columns_metadata" (
                            "ingestion_id", "version", "column_name", "column_description", 
                            "data_type", "pii", "pii_id", "partition_column"
                        )
                        VALUES (%s, 1, %s, %s, %s, %s, %s, %s);
                        """,
                        (ingestion_id, col.nome, col_desc, col.dataType, col.pii, pii_id, is_partition)
                    )
                
                for col_rule in body.qualidade.colunas:
                    if not col_rule.coluna:
                        continue
                    for r_name in col_rule.regras:
                        r_id = rules_map.get(r_name)
                        if r_id:
                            cur.execute(
                                """
                                INSERT INTO "columns_quality_rules" ("rule_id", "ingestion_id", "version_id", "column_name")
                                VALUES (%s, %s, 1, %s);
                                """,
                                (r_id, ingestion_id, col_rule.coluna)
                            )
                
                cur.execute(
                    """
                    UPDATE "ingestions" SET "active_version" = 1 WHERE "ingestion_id" = %s;
                    """,
                    (ingestion_id,)
                )
        return ingestion_id
    finally:
        if conn:
            conn.close()

def get_ingestions_list():
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    i.ingestion_id as id,
                    itm.table_name as tabela,
                    i.status,
                    i.last_operation as detalhe,
                    u.full_name as responsavel
                FROM "ingestions" i
                LEFT JOIN "ingestions_table_metadata" itm 
                    ON i.ingestion_id = itm.ingestion_id AND i.active_version = itm.version
                LEFT JOIN "users" u 
                    ON i.created_by = u.user_id;
            """)
            return cur.fetchall()
    finally:
        if conn:
            conn.close()

def get_ingestion_detail_db(ingestion_id: int):
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    i.ingestion_id as id,
                    itm.table_name as tabela_nome,
                    i.created_at as criado_em,
                    s.name as sigla,
                    itm.inicial_date_update as inicio_ingestao,
                    itm.created_at as data_criacao,
                    itm.table_description as descricao,
                    itm.periodicity as periodicidade,
                    itm.origin_format as formato_origem,
                    itm.ingestion_type as tipo_atualizacao,
                    i.status,
                    u.full_name as aprovador,
                    itm.layer as camada,
                    o.sys_name as sistema_origem
                FROM "ingestions" i
                LEFT JOIN "ingestions_table_metadata" itm 
                    ON i.ingestion_id = itm.ingestion_id AND i.active_version = itm.version
                LEFT JOIN "siglas" s ON i.sigla_id = s.sigla_id
                LEFT JOIN "users" u ON s.owner_id = u.user_id
                LEFT JOIN "origins" o ON itm.origin = o.sys_id
                WHERE i.ingestion_id = %s;
            """, (ingestion_id,))
            ing_row = cur.fetchone()
            if not ing_row:
                return None
                
            cur.execute("""
                SELECT 
                    icm.column_name as nome,
                    icm.column_description as descricao,
                    icm.data_type as tipo_dado,
                    icm.partition_column as particao,
                    pt.pii_name as pii,
                    (
                        SELECT string_agg(qr.rule_name, ', ') 
                        FROM "columns_quality_rules" cqr
                        JOIN "quality_rules" qr ON cqr.rule_id = qr.rule_id
                        WHERE cqr.ingestion_id = icm.ingestion_id 
                          AND cqr.version_id = icm.version 
                          AND cqr.column_name = icm.column_name
                    ) as dq_rule
                FROM "ingestions_columns_metadata" icm
                LEFT JOIN "pii_types" pt ON icm.pii_id = pt.pii_id
                WHERE icm.ingestion_id = %s AND icm.version = (
                    SELECT active_version FROM "ingestions" WHERE ingestion_id = %s
                );
            """, (ingestion_id, ingestion_id))
            col_rows = cur.fetchall()
            
            ing_row["colunas"] = col_rows
            return ing_row
    finally:
        if conn:
            conn.close()

def get_fontes_list():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT DISTINCT "sys_name" FROM "origins";')
            rows = cur.fetchall()
            fontes = [{"value": r[0], "label": f"{r[0].capitalize()} - DB"} for r in rows]
            if not fontes:
                fontes = [
                    {"value": "postgres", "label": "PostgreSQL - PGPRD03"},
                    {"value": "oracle", "label": "Oracle - ORAPRD01"},
                    {"value": "mysql", "label": "MySQL - MYSQLPRD01"},
                    {"value": "sqlserver", "label": "SQL Server - SQLSERVERPRD01"},
                ]
            return fontes
    finally:
        if conn:
            conn.close()

def get_tabelas_list(fonte: str):
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT "sys_table_name" FROM "origins" WHERE "sys_name" = %s;', (fonte,))
            rows = cur.fetchall()
            tabelas = [{"value": r[0], "label": r[0]} for r in rows]
            if not tabelas:
                mock_tabelas = {
                    "postgres": ["TABE_XPTO", "TABE_CLIENTES", "TABE_VENDAS"],
                    "oracle": ["TABE_LANCAMENTOS", "TABE_PRODUTOS"],
                    "mysql": ["TABE_CONFIG"],
                    "sqlserver": ["TABE_PEDIDOS", "TABE_FORNECEDORES"]
                }
                tabelas = [{"value": t, "label": t} for t in mock_tabelas.get(fonte, [])]
            return tabelas
    finally:
        if conn:
            conn.close()

def get_pii_types_list():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT "pii_name" FROM "pii_types";')
            rows = cur.fetchall()
            pii_types = [r[0] for r in rows]
            if not pii_types:
                pii_types = ["N/A", "CPF", "CNPJ", "Email", "Telefone", "Endereço", "Nome", "Data Nascimento", "Outros"]
            return pii_types
    finally:
        if conn:
            conn.close()

def get_quality_rules_list():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute('SELECT "rule_name" FROM "quality_rules";')
            rows = cur.fetchall()
            regras = [{"nome": r[0], "descricao": r[0].replace("_", " ").capitalize()} for r in rows]
            if not regras:
                regras = [
                    {"nome": "VALIDA_NULOS", "descricao": "Valida nulos"},
                    {"nome": "VALIDA_BANDEIRA_CARTAO", "descricao": "Valida bandeira do cartão"},
                    {"nome": "VALIDA_CPF", "descricao": "Valida CPF"},
                    {"nome": "VALIDA_CNPJ", "descricao": "Valida CNPJ"},
                    {"nome": "VALIDA_EMAIL", "descricao": "Valida email"},
                    {"nome": "VALIDA_TELEFONE", "descricao": "Valida telefone"},
                    {"nome": "VALIDA_CEP", "descricao": "Valida endereço"},
                ]
            return regras
    finally:
        if conn:
            conn.close()

def approve_ingestion_db(ingestion_id: int):
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE "ingestions" 
                    SET "status" = 'APPROVED', "last_operation" = 'APPROVE'
                    WHERE "ingestion_id" = %s;
                    """,
                    (ingestion_id,)
                )
    finally:
        if conn:
            conn.close()

def reject_ingestion_db(ingestion_id: int):
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE "ingestions" 
                    SET "status" = 'REJECTED', "last_operation" = 'REJECT'
                    WHERE "ingestion_id" = %s;
                    """,
                    (ingestion_id,)
                )
    finally:
        if conn:
            conn.close()

def delete_ingestion_db(ingestion_id: int):
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    DELETE FROM "ingestions" WHERE "ingestion_id" = %s;
                    """,
                    (ingestion_id,)
                )
    finally:
        if conn:
            conn.close()
