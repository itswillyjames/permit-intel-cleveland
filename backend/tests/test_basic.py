from fastapi.testclient import TestClient
from app.main import app

def test_root():
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "Permit Arbitrage" in r.json()["message"]


def test_ingest_and_score():
    client = TestClient(app)
    sample = {
        "permit_id": "X1",
        "city": "City",
        "address": "Addr",
        "valuation": 100000,
    }
    r = client.post("/permits/ingest", json=sample)
    assert r.status_code == 200
    pid = r.json()["id"]
    r2 = client.post(f"/permits/{pid}/score")
    assert r2.status_code == 200
    assert "win_score" in r2.json()
