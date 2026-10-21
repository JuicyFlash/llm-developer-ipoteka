from datetime import date

import pytest

from app.domain.schedule import (
    add_months,
    annuity_payment,
    build_schedule,
    change_payment_day,
    early_repayment,
    round_div,
    total_interest,
)

P, RATE, N = 500_000_000, 1200, 240


def test_round_div_half_up():
    assert round_div(5, 2) == 3
    assert round_div(7, 3) == 2
    assert round_div(10_000, 3) == 3333


def test_annuity_payment():
    assert annuity_payment(P, RATE, N) == 5_505_431


def test_schedule_closes_to_kopeck():
    rows = build_schedule(P, RATE, N)
    assert len(rows) == N
    assert rows[0].interest == 5_000_000
    assert sum(r.principal for r in rows) == P
    assert rows[-1].balance == 0
    assert rows[-1].payment == 5_505_095
    assert total_interest(rows) == 821_303_104


def test_early_repayment_reduce_term():
    r = early_repayment(P, RATE, N, after_month=12, amount=50_000_000, mode="term")
    assert r.payment == 5_505_431
    assert r.months_total == 177
    assert r.saved == 298_656_620


def test_early_repayment_reduce_payment():
    r = early_repayment(P, RATE, N, after_month=12, amount=50_000_000, mode="payment")
    assert r.payment == 4_947_738
    assert r.months_total == 240
    assert r.saved == 77_153_825


def test_early_repayment_rejects_full_payoff():
    with pytest.raises(ValueError):
        early_repayment(P, RATE, N, after_month=12, amount=P, mode="term")


def test_change_payment_day_same_month():
    c = change_payment_day(100_000_000, RATE, date(2026, 10, 15), 20)
    assert (c.new_date, c.days) == (date(2026, 10, 20), 5)
    assert c.transition_interest == 164_384


def test_change_payment_day_next_month():
    c = change_payment_day(100_000_000, RATE, date(2026, 12, 15), 10)
    assert (c.new_date, c.days) == (date(2027, 1, 10), 26)


@pytest.mark.parametrize("day", [0, 29, 31])
def test_change_payment_day_rule(day):
    with pytest.raises(ValueError):
        change_payment_day(100_000_000, RATE, date(2026, 10, 15), day)


def test_add_months_crosses_year():
    assert add_months(date(2025, 11, 1), 2, 15) == date(2026, 1, 15)
