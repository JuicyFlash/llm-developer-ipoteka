from datetime import date

from pydantic import BaseModel


class Loan(BaseModel):
    id: int
    client_id: int
    principal: int
    rate_bp: int
    term_months: int
    issued_on: date
    payment_day: int


class ScheduleRow(BaseModel):
    n: int
    date: date
    payment: int
    interest: int
    principal: int
    balance: int
