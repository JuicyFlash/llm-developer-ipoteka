from app.core import db
from app.domain.schedule import add_months, build_schedule
from app.repositories import loans as repo
from app.schemas.loans import Loan, ScheduleRow


def get_loan(loan_id: int) -> Loan | None:
    with db.connection() as conn:
        row = repo.get_loan(conn, loan_id)
    return Loan(**row) if row else None


def get_schedule(loan_id: int) -> list[ScheduleRow] | None:
    loan = get_loan(loan_id)
    if loan is None:
        return None
    rows = build_schedule(loan.principal, loan.rate_bp, loan.term_months)
    return [
        ScheduleRow(
            n=r.n,
            date=add_months(loan.issued_on, r.n, loan.payment_day),
            payment=r.payment,
            interest=r.interest,
            principal=r.principal,
            balance=r.balance,
        )
        for r in rows
    ]
