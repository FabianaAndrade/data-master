"""
CRUD do workflow de aprovação — approve, reject, cancel, outbox, listagem de pendentes.
"""
import json

from psycopg2.extras import RealDictCursor

from ..database import get_db_connection


def _insert_approval_outbox(cur, ingestion_id: int) -> None:
    """
    Monta o payload enriquecido (metadados + colunas + PII + DQ) e insere
    na tabela outbox. Deve ser chamada DENTRO da mesma transação de aprovação.
    """
    # 1. Dados da ingestão + metadados da tabela
    cur.execute("""
        SELECT
            i.ingestion_id,
            i.status,
            i.active_version,
            i.last_operation,
            u_approver.full_name  AS approved_by,
            s.name                AS sigla,
            itm.table_name,
            itm.table_description,
            itm.layer,
            itm.origin_format,
            itm.periodicity,
            itm.ingestion_type,
            itm.version,
            itm.created_at        AS table_created_at,
            itm.usage,
            itm.limitations,
            itm.security_classification,
            itm.retention_months,
            o.sys_name            AS origin
        FROM "ingestions" i
        LEFT JOIN "ingestions_table_metadata" itm
               ON i.ingestion_id = itm.ingestion_id AND i.active_version = itm.version
        LEFT JOIN "siglas" s      ON i.sigla_id = s.sigla_id
        LEFT JOIN "users" u_approver ON i.last_updated_by = u_approver.user_id
        LEFT JOIN "origins" o     ON itm.origin = o.sys_id
        WHERE i.ingestion_id = %s;
    """, (ingestion_id,))
    ing = cur.fetchone()
    if not ing:
        return

    # 2. Colunas + PII + DQ rules
    cur.execute("""
        SELECT
            icm.column_name,
            icm.column_description,
            icm.data_type,
            icm.partition_column,
            icm.pii,
            pt.pii_name   AS pii_type,
            (
                SELECT string_agg(qr.rule_name, ', ')
                FROM "columns_quality_rules" cqr
                JOIN "quality_rules" qr ON cqr.rule_id = qr.rule_id
                WHERE cqr.ingestion_id = icm.ingestion_id
                  AND cqr.version_id   = icm.version
                  AND cqr.column_name  = icm.column_name
            ) AS quality_rules
        FROM "ingestions_columns_metadata" icm
        LEFT JOIN "pii_types" pt ON icm.pii_id = pt.pii_id
        WHERE icm.ingestion_id = %s
          AND icm.version = %s;
    """, (ingestion_id, ing["active_version"]))
    columns = cur.fetchall()

    # 3. Montar payload
    payload = {
        "ingestion_id": ing["ingestion_id"],
        "status": ing["status"],
        "operation_name": ing["last_operation"],
        "approved_by": ing["approved_by"],
        "sigla": ing["sigla"],
        "table_metadata": {
            "table_name": ing["table_name"],
            "table_description": ing["table_description"],
            "origin": ing["origin"],
            "layer": ing["layer"],
            "origin_format": ing["origin_format"],
            "periodicity": ing["periodicity"],
            "ingestion_type": ing["ingestion_type"],
            "version": ing["version"],
            "created_at": ing["table_created_at"].isoformat() if ing["table_created_at"] else None,
            "usage": ing["usage"],
            "limitations": ing["limitations"],
            "security_classification": ing["security_classification"],
            "retention_months": ing["retention_months"],
        },
        "columns": [
            {
                "column_name": col["column_name"],
                "column_description": col["column_description"],
                "data_type": col["data_type"],
                "partition_column": col["partition_column"],
                "pii": col["pii"],
                "pii_type": col["pii_type"],
                "quality_rules": [r.strip() for r in col["quality_rules"].split(",")]
                    if col["quality_rules"] else [],
            }
            for col in columns
        ],
    }

    # 4. Inserir na outbox (mesma transação)
    cur.execute(
        """
        INSERT INTO "outbox" ("aggregatetype", "aggregateid", "type", "payload")
        VALUES (%s, %s, %s, %s);
        """,
        ("ingestion", str(ingestion_id), "APPROVED", json.dumps(payload))
    )


def approve_ingestion_db(ingestion_id: int, approved_by: int):
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # Check current status to determine what approval means
                cur.execute('SELECT "status" FROM "ingestions" WHERE "ingestion_id" = %s;', (ingestion_id,))
                row = cur.fetchone()
                if not row:
                    return

                if row["status"] == "PENDING_DELETE":
                    # Approving a deletion request: mark as DELETED (soft delete confirmed)
                    cur.execute(
                        """
                        UPDATE "ingestions"
                        SET "status" = 'DELETED', "last_updated_by" = %s
                        WHERE "ingestion_id" = %s;
                        """,
                        (approved_by, ingestion_id)
                    )
                else:
                    # Normal approval ( Creation or Edit )
                    # Find the latest version (which is pending)
                    cur.execute('SELECT MAX(version) as max_v FROM "ingestions_table_metadata" WHERE "ingestion_id" = %s;', (ingestion_id,))
                    max_row = cur.fetchone()
                    if max_row and max_row["max_v"]:
                        pending_version = max_row["max_v"]
                        
                        # Deactivate all versions
                        cur.execute(
                            'UPDATE "ingestions_table_metadata" SET "is_active" = FALSE WHERE "ingestion_id" = %s;',
                            (ingestion_id,)
                        )
                        # Activate the pending version
                        cur.execute(
                            'UPDATE "ingestions_table_metadata" SET "is_active" = TRUE WHERE "ingestion_id" = %s AND "version" = %s;',
                            (ingestion_id, pending_version)
                        )
                        
                        cur.execute(
                            """
                            UPDATE "ingestions"
                            SET "status" = 'APPROVED', "last_updated_by" = %s, "active_version" = %s
                            WHERE "ingestion_id" = %s;
                            """,
                            (approved_by, pending_version, ingestion_id)
                        )
                    else:
                        cur.execute(
                            """
                            UPDATE "ingestions"
                            SET "status" = 'APPROVED', "last_updated_by" = %s
                            WHERE "ingestion_id" = %s;
                            """,
                            (approved_by, ingestion_id)
                        )

                    # -------------------------------------------------------
                    # Outbox: montar payload enriquecido e inserir na outbox
                    # (na mesma transação para garantir atomicidade)
                    # -------------------------------------------------------
                    _insert_approval_outbox(cur, ingestion_id)

    finally:
        if conn:
            conn.close()

def reject_ingestion_db(ingestion_id: int, rejected_by: int):
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE "ingestions"
                    SET "status" = 'REJECTED', "last_updated_by" = %s
                    WHERE "ingestion_id" = %s;
                    """,
                    (rejected_by, ingestion_id)
                )
    finally:
        if conn:
            conn.close()

def get_ingestion_for_approval(ingestion_id: int):
    """
    Retorna dados completos de uma ingestão para o fluxo de aprovação:
    status, prazo, quem criou, owner da sigla.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    i.ingestion_id,
                    i.status,
                    i.created_at,
                    i.should_be_approved_until,
                    i.created_by,
                    cb.full_name  AS created_by_name,
                    cb.email      AS created_by_email,
                    s.sigla_id,
                    s.name        AS sigla_name,
                    s.owner_id,
                    ow.full_name  AS owner_name,
                    ow.email      AS owner_email,
                    itm.table_name
                FROM "ingestions" i
                LEFT JOIN "siglas"                    s   ON i.sigla_id    = s.sigla_id
                LEFT JOIN "users"                     ow  ON s.owner_id    = ow.user_id
                LEFT JOIN "users"                     cb  ON i.created_by  = cb.user_id
                LEFT JOIN "ingestions_table_metadata" itm
                       ON i.ingestion_id = itm.ingestion_id
                      AND i.active_version = itm.version
                WHERE i.ingestion_id = %s;
                """,
                (ingestion_id,),
            )
            row = cur.fetchone()
            return dict(row) if row else None
    finally:
        if conn:
            conn.close()

def get_pending_ingestions_for_owner(owner_username: str):
    """
    Lista ingestões PENDING_APPROVAL cujo owner da sigla é o usuário informado
    e o prazo ainda não expirou.
    """
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT
                    i.ingestion_id,
                    i.status,
                    i.created_at,
                    i.should_be_approved_until,
                    s.name        AS sigla_name,
                    cb.full_name  AS solicitante,
                    itm.table_name
                FROM "ingestions" i
                LEFT JOIN "siglas"                    s   ON i.sigla_id   = s.sigla_id
                LEFT JOIN "users"                     ow  ON s.owner_id   = ow.user_id
                LEFT JOIN "users"                     cb  ON i.created_by = cb.user_id
                LEFT JOIN "ingestions_table_metadata" itm
                       ON i.ingestion_id = itm.ingestion_id
                      AND i.active_version = itm.version
                WHERE i.status IN ('PENDING_APPROVAL', 'PENDING_DELETE')
                  AND (ow.full_name = %s OR ow.email = %s)
                ORDER BY i.should_be_approved_until ASC;
                """,
                (owner_username, owner_username),
            )
            return [dict(r) for r in cur.fetchall()]
    finally:
        if conn:
            conn.close()

def cancel_expired_ingestions():
    """
    Cancela ingestões PENDING_APPROVAL cujo prazo de 10 dias expirou.
    Retorna lista de IDs cancelados.
    """
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE "ingestions"
                    SET status         = 'CANCELLED',
                        last_operation = 'CANCEL'
                    WHERE status = 'PENDING_APPROVAL'
                      AND should_be_approved_until < CURRENT_DATE
                    RETURNING ingestion_id;
                    """
                )
                rows = cur.fetchall()
                return [r[0] for r in rows]
    finally:
        if conn:
            conn.close()

def cancel_ingestion_db(ingestion_id: int, cancelled_by: int):
    """Cancela uma ingestão específica por prazo expirado."""
    conn = get_db_connection()
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE "ingestions"
                    SET status          = 'CANCELLED',
                        last_operation  = 'CANCEL',
                        last_updated_by = %s
                    WHERE ingestion_id = %s;
                    """,
                    (cancelled_by, ingestion_id)
                )
    finally:
        if conn:
            conn.close()
