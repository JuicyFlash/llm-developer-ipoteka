from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_live():
    assert client.get("/health/live").json() == {"status": "ok"}


def test_ready_reports_vector():
    resp = client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["vector"]


def test_loan():
    loan = client.get("/loans/1").json()
    assert loan["principal"] == 500_000_000
    assert loan["rate_bp"] == 1200


def test_schedule():
    rows = client.get("/loans/1/schedule").json()
    assert len(rows) == 240
    assert rows[0] == {"n": 1, "date": "2025-11-15", "payment": 5_505_431, "interest": 5_000_000,
                       "principal": 505_431, "balance": 499_494_569}
    assert rows[-1]["balance"] == 0


def test_missing_loan():
    assert client.get("/loans/999999").status_code == 404
    assert client.get("/loans/999999/schedule").status_code == 404
