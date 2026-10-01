import hashlib, hmac, json, time
from fastapi.testclient import TestClient
from app.main import app

def test_role_scoped_api_auth_and_metrics(monkeypatch,client):
    monkeypatch.setenv("AUTH_REQUIRED","true")
    monkeypatch.setenv("API_KEY_ANALYST","a"*48)
    monkeypatch.setenv("API_KEY_OPERATOR","b"*48)
    assert client.get("/api/v1/transactions").status_code==401
    analyst={"Authorization":"Bearer "+"a"*48}
    operator={"Authorization":"Bearer "+"b"*48}
    assert client.get("/api/v1/transactions",headers=analyst).status_code==200
    assert client.post("/api/v1/transactions",headers=analyst,json={"user_id":"secure","amount":"10.00"}).status_code==403
    created=client.post("/api/v1/transactions",headers=operator,json={"user_id":"secure","amount":"10.00"})
    assert created.status_code==201
    assert created.headers.get("x-request-id")
    assert "finintel_http_requests_total" in client.get("/metrics",headers=analyst).text
    assert client.get("/metrics").status_code==401

def test_signed_partner_event_is_authenticated_and_idempotent(monkeypatch,client):
    monkeypatch.setenv("AUTH_REQUIRED","true")
    monkeypatch.setenv("API_KEY_ANALYST","a"*48)
    monkeypatch.setenv("API_KEY_OPERATOR","b"*48)
    monkeypatch.setenv("SANDBOX_PARTNER_ID","test-sandbox")
    monkeypatch.setenv("SANDBOX_PARTNER_WEBHOOK_SECRET","c"*48)
    tx=client.post("/api/v1/transactions",headers={"Authorization":"Bearer "+"b"*48},json={"user_id":"partner-user","amount":"75.00"}).json()
    body=json.dumps({"transaction_id":tx["transaction_id"],"target_status":"AUTHORIZED","details":"Partner sandbox auth"},separators=(",",":" )).encode()
    timestamp=str(int(time.time()));event_id="evt-auth-1"
    signature=hmac.new(("c"*48).encode(),f"{timestamp}.{event_id}.".encode()+body,hashlib.sha256).hexdigest()
    headers={"X-Partner-Id":"test-sandbox","X-Event-Id":event_id,"X-Event-Timestamp":timestamp,"X-Event-Signature":signature}
    response=client.post("/api/v1/partner-events",content=body,headers=headers)
    assert response.status_code==200
    assert response.json()["status"]=="AUTHORIZED"
    assert client.post("/api/v1/partner-events",content=body,headers=headers).status_code==409
    bad={**headers,"X-Event-Id":"evt-auth-2","X-Event-Signature":"bad"}
    assert client.post("/api/v1/partner-events",content=body,headers=bad).status_code==401

def test_graph_and_outcome_feedback_are_bounded_and_do_not_train(client):
    first=client.post("/api/v1/transactions",json={"user_id":"graph-user","amount":"100.00","device_id":"shared-device"}).json()
    client.post("/api/v1/transactions",json={"user_id":"graph-user","amount":"200.00","device_id":"shared-device"})
    graph=client.get(f"/api/v1/graph/transactions/{first['transaction_id']}").json()
    assert graph["environment"]=="SYNTHETIC"
    assert any(node["kind"]=="DEVICE" for node in graph["nodes"])
    assert len([node for node in graph["nodes"] if node["kind"]=="TRANSACTION"])==2
    bounded=client.get(f"/api/v1/graph/transactions/{first['transaction_id']}?limit=1").json()
    assert [node["label"] for node in bounded["nodes"] if node["kind"]=="TRANSACTION"]==[first["transaction_id"]]
    feedback=client.post(f"/api/v1/investigations/{first['transaction_id']}/outcomes",json={"outcome_label":"CONFIRMED_LEGITIMATE","reviewer_id":"analyst-demo","evidence_reference":"review-1"})
    assert feedback.status_code==201
    assert feedback.json()["verification_status"]=="UNVERIFIED"
    assert feedback.json()["risk_snapshot"]["machine_learning_status"]=="NOT_CONFIGURED"
    summary=client.get("/api/v1/learning/summary").json()
    assert summary["model_training_enabled"] is False
    assert summary["feedback_counts"][0]["count"]==1
    feedback_id=feedback.json()["feedback_id"]
    verified=client.post(f"/api/v1/investigations/feedback/{feedback_id}/verify",json={"reviewer_id":"second-reviewer"})
    assert verified.status_code==200
    assert verified.json()["verification_status"]=="VERIFIED"
    assert client.post(f"/api/v1/investigations/feedback/{feedback_id}/verify",json={"reviewer_id":"second-reviewer"}).status_code==409
    evaluated=client.get("/api/v1/learning/summary").json()["verified_evaluations"]
    assert evaluated["sample_size"]==1
    assert evaluated["confusion_counts"]["true_negative"]==1
    history=client.get(f"/api/v1/investigations/{first['transaction_id']}/outcomes").json()
    assert len(history["feedback"])==1

def test_security_requires_distinct_strong_keys_when_enabled(monkeypatch):
    from app.core.security import validate_security_configuration
    monkeypatch.setenv("AUTH_REQUIRED","true")
    monkeypatch.setenv("API_KEY_ANALYST","short")
    monkeypatch.setenv("API_KEY_OPERATOR","short")
    import pytest
    with pytest.raises(RuntimeError): validate_security_configuration()
    monkeypatch.setenv("API_KEY_ANALYST","d"*48)
    monkeypatch.setenv("API_KEY_OPERATOR","e"*48)
    validate_security_configuration()

def test_secured_websocket_accepts_operator_bearer_subprotocol(monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRED","true")
    monkeypatch.setenv("API_KEY_ANALYST","a"*48)
    monkeypatch.setenv("API_KEY_OPERATOR","b"*48)
    with TestClient(app) as secured_client:
        with secured_client.websocket_connect("/ws/transactions",subprotocols=["finintel.events.v1","bearer."+"a"*48]) as socket:
            assert socket.accepted_subprotocol=="finintel.events.v1"
            assert socket.receive_json()["event_type"]=="CONNECTED"
