"""
CRUD de dados de referência — fontes, tabelas, PII types, quality rules.
"""
from ..database import get_db_connection


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
