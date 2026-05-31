import time
import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres_db:5432/data_catalog")

def get_db_connection():
    return psycopg2.connect(DATABASE_URL)

def startup_db_seed():
    seed_database_if_empty()

def seed_database_if_empty():
    conn = None
    retries = 5
    for i in range(retries):
        try:
            conn = get_db_connection()
            break
        except Exception as e:
            print(f"Database connection attempt {i+1} failed: {e}. Retrying in 2 seconds...")
            time.sleep(2)
    else:
        print("Could not connect to database for seeding after retries.")
        return

    try:
        with conn:
            with conn.cursor() as cur:
                # 1. Seed origins
                cur.execute('SELECT COUNT(*) FROM "origins";')
                if cur.fetchone()[0] == 0:
                    mock_tabelas = {
                        "postgres": ["TABE_XPTO", "TABE_CLIENTES", "TABE_VENDAS"],
                        "oracle": ["TABE_LANCAMENTOS", "TABE_PRODUTOS"],
                        "mysql": ["TABE_CONFIG"],
                        "sqlserver": ["TABE_PEDIDOS", "TABE_FORNECEDORES"]
                    }
                    for sys_name, tables in mock_tabelas.items():
                        for table in tables:
                            cur.execute(
                                'INSERT INTO "origins" ("sys_name", "sys_table_name") VALUES (%s, %s);',
                                (sys_name, table)
                            )
                
                # 2. Seed quality rules
                cur.execute('SELECT COUNT(*) FROM "quality_rules";')
                if cur.fetchone()[0] == 0:
                    rules = [
                        ("VALIDA_NULOS", "Valida nulos"),
                        ("VALIDA_BANDEIRA_CARTAO", "Valida bandeira do cartão"),
                        ("VALIDA_CPF", "Valida CPF"),
                        ("VALIDA_CNPJ", "Valida CNPJ"),
                        ("VALIDA_EMAIL", "Valida email"),
                        ("VALIDA_TELEFONE", "Valida telefone"),
                        ("VALIDA_CEP", "Valida endereço"),
                    ]
                    for name, desc in rules:
                        cur.execute(
                            'INSERT INTO "quality_rules" ("rule_name") VALUES (%s);',
                            (name,)
                        )
                
                # 3. Seed pii_types
                cur.execute('SELECT COUNT(*) FROM "pii_types";')
                if cur.fetchone()[0] == 0:
                    pii_names = ["N/A", "CPF", "CNPJ", "Email", "Telefone", "Endereço", "Nome", "Data Nascimento", "Outros"]
                    for pii_name in pii_names:
                        cur.execute(
                            'INSERT INTO "pii_types" ("pii_name") VALUES (%s);',
                            (pii_name,)
                        )

                # 4. Seed users (ensure required seed users are present)
                users = [
                    (1, "jsilva@empresa.com", "jsilva"),
                    (2, "rsantana@empresa.com", "rsantana"),
                    (3, "amoreira@empresa.com", "amoreira"),
                    (4, "cgarcia@empresa.com", "cgarcia")
                ]
                for uid, email, name in users:
                    cur.execute('SELECT COUNT(*) FROM "users" WHERE "user_id" = %s;', (uid,))
                    if cur.fetchone()[0] == 0:
                        cur.execute(
                            'INSERT INTO "users" ("user_id", "email", "full_name") VALUES (%s, %s, %s);',
                            (uid, email, name)
                        )

                # 5. Seed siglas (ensure required seed siglas are present)
                siglas = [
                    (1, "MKTI - Marketing e Tecnologia", 1),
                    (2, "FIN - Financeiro", 2),
                    (3, "TI - Tecnologia da Informação", 1)
                ]
                for sid, name, owner_id in siglas:
                    cur.execute('SELECT COUNT(*) FROM "siglas" WHERE "sigla_id" = %s;', (sid,))
                    if cur.fetchone()[0] == 0:
                        cur.execute(
                            'INSERT INTO "siglas" ("sigla_id", "name", "owner_id") VALUES (%s, %s, %s);',
                            (sid, name, owner_id)
                        )

                # 6. Default ingestions are not seeded to allow database to start with 0 records
                pass
        print("Database seeded successfully.")
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        if conn:
            conn.close()
