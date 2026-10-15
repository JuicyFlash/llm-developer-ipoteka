from fastapi import APIRouter, HTTPException

from app.schemas.loans import Loan, ScheduleRow
from app.services import loans

router = APIRouter(prefix="/loans", tags=["loans"])


@router.get("/{loan_id}", response_model=Loan)
def get_loan(loan_id: int):
    loan = loans.get_loan(loan_id)
    if loan is None:
        raise HTTPException(404, "кредит не найден")
    return loan


@router.get("/{loan_id}/schedule", response_model=list[ScheduleRow])
def get_schedule(loan_id: int):
    schedule = loans.get_schedule(loan_id)
    if schedule is None:
        raise HTTPException(404, "кредит не найден")
    return schedule
