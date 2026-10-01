from decimal import Decimal
from fastapi.testclient import TestClient
from app.engines.state_engine import TransactionStatus, validate_transition
from app.db.session import get_db
from app.main import app
from app.models.transaction import Transaction
from app.services.transaction_service import transition_transaction
from app.schemas.transactions import TransactionCreate
from conftest import TestingSession, engine
import pytest

def test_create_and_read_transaction(client: TestClient):
    response = client.post("/api/v1/transactions", json={"user_id":"user-1", "amount":"649.00", "merchant_id":"merchant-netflix"})
    assert response.status_code == 201
    tx = response.json()
    assert tx["amount"] == "649.00"
    assert tx["environment"] == "SYNTHETIC"
    assert client.get(f"/api/v1/transactions/{tx['transaction_id']}").status_code == 200
    timeline = client.get(f"/api/v1/transactions/{tx['transaction_id']}/timeline").json()
    assert timeline[0]["to_status"] == "INITIATED"

def test_invalid_amount_rejected(client: TestClient):
    assert client.post("/api/v1/transactions", json={"user_id":"u", "amount":"0"}).status_code == 422

def test_state_machine_and_audited_transition(client: TestClient):
    tx = client.post("/api/v1/transactions", json={"user_id":"u", "amount":"10.25"}).json()
    response = client.post(f"/api/v1/transactions/{tx['transaction_id']}/transitions", json={"target_status":"AUTHORIZED"})
    assert response.status_code == 200
    timeline = client.get(f"/api/v1/transactions/{tx['transaction_id']}/timeline").json()
    assert [e["to_status"] for e in timeline] == ["INITIATED", "AUTHORIZED"]
    invalid = client.post(f"/api/v1/transactions/{tx['transaction_id']}/transitions", json={"target_status":"SETTLED"})
    assert invalid.status_code == 409
    assert invalid.json()["detail"].startswith("Invalid transaction transition")

def test_decimal_and_transition_rules():
    assert Decimal("0.10") + Decimal("0.20") == Decimal("0.30")
    validate_transition("UNKNOWN", "RECONCILING")
    with pytest.raises(ValueError):
        validate_transition("INITIATED", "SETTLED")
