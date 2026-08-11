"""
CRUD de ingestões — criação, listagem, detalhe, cancelamento, exclusão e versionamento.
"""
from psycopg2.extras import RealDictCursor

from ..database import get_db_connection
from ..schemas import FullIngestionRequest, IngestionRequest
from .helpers import get_or_create_user, get_or_create_sigla, parse_date


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
                    VALUES (%s, CURRENT_DATE, 'PENDING_APPROVAL', CURRENT_DATE + INTERVAL '10 days', %s, %s, NULL, 'CREATE')
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
                cur.execute('SELECT "sys_id" FROM "origins" WHERE "sys_name" = %s AND "sys_table_name" = %s;', (body.fonte.sistemaOrigem, body.metadados.nomeTabela))
                origin_row = cur.fetchone()
                if origin_row:
                    origin_id = origin_row[0]
                else:
                    cur.execute(
                        'INSERT INTO "origins" ("sys_name", "sys_table_name") VALUES (%s, %s) RETURNING "sys_id";',
                        (body.fonte.sistemaOrigem, body.metadados.nomeTabela)
                    )
                    origin_id = cur.fetchone()[0]
                
                cur.execute(
                    """
                    INSERT INTO "ingestions" (
                        "sigla_id", "created_at", "status", "should_be_approved_until", 
                        "created_by", "last_updated_by", "active_version", "last_operation"
                    )
                    VALUES (%s, CURRENT_DATE, 'PENDING_APPROVAL', CURRENT_DATE + INTERVAL '10 days', %s, %s, NULL, 'CREATE')
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
                        body.metadados.nomeTabela, 
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
                    u.full_name as responsavel,
                    s.name as sigla
                FROM "ingestions" i
                LEFT JOIN "ingestions_table_metadata" itm 
                    ON i.ingestion_id = itm.ingestion_id AND i.active_version = itm.version
                LEFT JOIN "users" u 
                    ON i.created_by = u.user_id
                LEFT JOIN "siglas" s
                    ON i.sigla_id = s.sigla_id;
            """)
            return cur.fetchall()
    finally:
        if conn:
            conn.close()

def get_ingestions_list_for_user(username: str):
    """
    Retorna ingestões visíveis ao usuário:
    - ingestões criadas por ele (created_by)
    - ingestões de siglas das quais ele é owner
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    i.ingestion_id as id,
                    itm.table_name as tabela,
                    i.status,
                    i.last_operation as detalhe,
                    cb.full_name as responsavel,
                    s.name as sigla
                FROM "ingestions" i
                LEFT JOIN "ingestions_table_metadata" itm 
                    ON i.ingestion_id = itm.ingestion_id AND i.active_version = itm.version
                LEFT JOIN "users" cb ON i.created_by = cb.user_id
                LEFT JOIN "siglas" s ON i.sigla_id = s.sigla_id
                LEFT JOIN "users" ow ON s.owner_id = ow.user_id
                WHERE 
                    cb.full_name = %s OR cb.email = %s
                    OR ow.full_name = %s OR ow.email = %s
                ORDER BY i.ingestion_id DESC;
            """, (username, username, username, username))
            return cur.fetchall()
    finally:
        if conn:
            conn.close()

def cancel_ingestion_by_user(ingestion_id: int, username: str):
    """
    Cancela uma ingestão desde que o solicitante seja o criador
    e o status NÃO seja APPROVED.
    Retorna dict com status e mensagem.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Busca a ingestão com dados do criador
            cur.execute("""
                SELECT i.ingestion_id, i.status, cb.full_name as creator_name, cb.email as creator_email
                FROM "ingestions" i
                LEFT JOIN "users" cb ON i.created_by = cb.user_id
                WHERE i.ingestion_id = %s;
            """, (ingestion_id,))
            row = cur.fetchone()
            if not row:
                return {"error": "not_found", "message": "Ingestão não encontrada."}

            if row["status"] == "APPROVED":
                return {"error": "already_approved", "message": "Não é possível cancelar uma ingestão já aprovada."}

            # Verifica se é o criador
            is_creator = username in (row["creator_name"] or "", row["creator_email"] or "")
            if not is_creator:
                return {"error": "forbidden", "message": "Apenas o solicitante pode cancelar esta ingestão."}

        with conn:
            with conn.cursor() as cur:
                user_id_row = None
                cur.execute('SELECT user_id FROM "users" WHERE full_name = %s OR email = %s;', (username, username))
                user_id_row = cur.fetchone()
                user_id = user_id_row[0] if user_id_row else None

                cur.execute("""
                    UPDATE "ingestions"
                    SET status = 'CANCELLED', last_operation = 'CANCEL', last_updated_by = %s
                    WHERE ingestion_id = %s;
                """, (user_id, ingestion_id))
        return {"ok": True, "message": "Ingestão cancelada com sucesso."}
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
                    icm.pii as pii,
                    pt.pii_name as pii_tipo,
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

def delete_ingestion_db(ingestion_id: int, username: str = None):
    """
    Solicita a exclusão de uma ingestão (soft delete).
    Marca a ingestão como PENDING_DELETE para que passe pelo fluxo de aprovação.
    Os dados NÃO são removidos do banco — apenas o status é alterado.
    Retorna dict com resultado da operação.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Verifica se a ingestão existe
            cur.execute('SELECT "ingestion_id", "status" FROM "ingestions" WHERE "ingestion_id" = %s;', (ingestion_id,))
            row = cur.fetchone()
            if not row:
                return {"error": "not_found", "message": "Ingestão não encontrada."}

            # Não permite solicitar exclusão de ingestão já marcada para exclusão
            if row["status"] in ("PENDING_DELETE", "DELETED"):
                return {"error": "already_deleted", "message": "Esta ingestão já está marcada para exclusão ou já foi excluída."}

            # Verifica permissão: se username informado, checar se é o criador ou owner da sigla
            if username:
                cur.execute("""
                    SELECT cb.full_name as creator_name, cb.email as creator_email,
                           ow.full_name as owner_name, ow.email as owner_email
                    FROM "ingestions" i
                    LEFT JOIN "users" cb ON i.created_by = cb.user_id
                    LEFT JOIN "siglas" s ON i.sigla_id = s.sigla_id
                    LEFT JOIN "users" ow ON s.owner_id = ow.user_id
                    WHERE i.ingestion_id = %s;
                """, (ingestion_id,))
                perm_row = cur.fetchone()
                if perm_row:
                    is_allowed = username in (
                        perm_row.get("creator_name") or "",
                        perm_row.get("creator_email") or "",
                        perm_row.get("owner_name") or "",
                        perm_row.get("owner_email") or "",
                    )
                    if not is_allowed:
                        return {"error": "forbidden", "message": "Você não tem permissão para solicitar exclusão desta ingestão."}

        # Soft delete: marcar como PENDING_DELETE para aprovação
        with conn:
            with conn.cursor() as cur:
                user_id = None
                if username:
                    cur.execute('SELECT user_id FROM "users" WHERE full_name = %s OR email = %s;', (username, username))
                    user_id_row = cur.fetchone()
                    user_id = user_id_row[0] if user_id_row else None

                cur.execute(
                    """
                    UPDATE "ingestions"
                    SET "status" = 'PENDING_DELETE',
                        "last_operation" = 'DELETE',
                        "last_updated_by" = %s,
                        "should_be_approved_until" = CURRENT_DATE + INTERVAL '10 days'
                    WHERE "ingestion_id" = %s;
                    """,
                    (user_id, ingestion_id)
                )

        return {"ok": True, "message": f"Solicitação de exclusão da ingestão {ingestion_id} enviada para aprovação."}
    finally:
        if conn:
            conn.close()

def create_new_version_for_ingestion(conn, ingestion_id: int, request) -> dict:
    """
    Cria uma nova versão para uma ingestão existente.
    - Incrementa version baseado na versão ativa atual
    - Marca a versão anterior como is_active = FALSE
    - Insere novos metadados de tabela e colunas
    - Atualiza active_version e status na tabela ingestions
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # 1. Buscar versão ativa atual
        cur.execute(
            'SELECT "active_version" FROM "ingestions" WHERE "ingestion_id" = %s;',
            (ingestion_id,)
        )
        row = cur.fetchone()
        if not row:
            raise Exception(f"Ingestão {ingestion_id} não encontrada.")

        current_version = row["active_version"] or 0
        new_version = current_version + 1

        # 2. A versão anterior CONTINUA ATIVA até que a nova seja aprovada.
        # Não marcamos is_active = FALSE aqui.

        # 3. Inserir novos metadados da tabela
        tm = request.table_metadata
        inicio_atualizacao = parse_date(tm.inicio_atualizacao) if tm.inicio_atualizacao else None
        data_criacao = parse_date(tm.data_criacao) if tm.data_criacao else None

        cur.execute(
            """
            INSERT INTO "ingestions_table_metadata" (
                "ingestion_id", "version", "created_at", "is_active",
                "table_name", "table_description", "origin", "layer",
                "origin_format", "periodicity", "ingestion_type", "inicial_date_update"
            )
            VALUES (%s, %s, COALESCE(%s, CURRENT_DATE), FALSE, %s, %s, %s, %s, %s, %s, %s, %s);
            """,
            (
                ingestion_id, new_version, data_criacao,
                tm.table_name, tm.table_description,
                tm.origin_id, tm.layer,
                tm.origin_format, tm.periodicity,
                tm.ingestion_type, inicio_atualizacao
            )
        )

        # 4. Buscar mapa de PII types
        cur.execute('SELECT "pii_name", "pii_id" FROM "pii_types";')
        pii_map = {r["pii_name"]: r["pii_id"] for r in cur.fetchall()}

        # 5. Inserir colunas da nova versão
        for col in request.columns:
            pii_id = pii_map.get(str(col.pii_type_id)) if col.pii else None
            # Se pii_type_id for numérico, usar diretamente
            if col.pii and isinstance(col.pii_type_id, int) and col.pii_type_id > 0:
                pii_id = col.pii_type_id

            cur.execute(
                """
                INSERT INTO "ingestions_columns_metadata" (
                    "ingestion_id", "version", "column_name", "column_description",
                    "data_type", "pii", "pii_id", "partition_column"
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                """,
                (
                    ingestion_id, new_version,
                    col.column_name, col.column_description,
                    col.data_type,
                    "Sim" if col.pii else "Não",
                    pii_id,
                    "Sim" if col.partition_column else "Não"
                )
            )

        # 6. Atualizar ingestion: status para PENDING_APPROVAL, operação = EDIT
        # NOTA: NÃO atualizamos active_version aqui! Ele só será atualizado quando for aprovado.
        cur.execute(
            """
            UPDATE "ingestions"
            SET "status" = 'PENDING_APPROVAL',
                "last_operation" = 'EDIT',
                "should_be_approved_until" = CURRENT_DATE + INTERVAL '10 days'
            WHERE "ingestion_id" = %s;
            """,
            (ingestion_id,)
        )

    return {
        "ingestion_id": ingestion_id,
        "new_version": new_version,
        "message": f"Nova versão {new_version} criada com sucesso."
    }
