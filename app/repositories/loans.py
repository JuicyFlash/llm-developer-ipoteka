import psycopg
from psycopg.rows import dict_row


def get_loan(conn: psycopg.Connection, loan_id: int) -> dict | None:
    with conn.cursor(row_factory=dict_row) as cur:
        cur.execute(
            """
            SELECT id, client_id, principal, rate_bp, term_months, issued_on, payment_day
            FROM loans
            WHERE id = %s
            """,
            (loan_id,),
        )
        return cur.fetchone()
