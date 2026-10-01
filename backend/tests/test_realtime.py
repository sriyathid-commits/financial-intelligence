from fastapi.testclient import TestClient
from app.main import app

def test_dashboard_and_synthetic_simulator_controls(client):
    created=client.post("/api/v1/transactions",json={"user_id":"dash-user","amount":"42.00"})
    assert created.status_code==201
    summary=client.get("/api/v1/dashboard/summary")
    assert summary.status_code==200
    assert summary.json()["environment"]=="SYNTHETIC"
    assert summary.json()["total_transactions"]==1
    assert summary.json()["transactions_today"]==1
    status=client.get("/api/v1/simulator/status").json()
    assert status["running"] is False
    assert client.post("/api/v1/simulator/start",json={"interval_seconds":0.4}).status_code==422

def test_websocket_receives_transaction_events():
    with TestClient(app) as ws_client:
        with ws_client.websocket_connect("/ws/transactions") as socket:
            assert socket.receive_json()["event_type"]=="CONNECTED"
            response=ws_client.post("/api/v1/transactions",json={"user_id":"ws-demo","amount":"99.00"})
            assert response.status_code==201
            event=socket.receive_json()
            assert event["event_type"]=="TRANSACTION_CREATED"
            assert event["transaction_id"]==response.json()["transaction_id"]
            assert event["environment"]=="SYNTHETIC"
