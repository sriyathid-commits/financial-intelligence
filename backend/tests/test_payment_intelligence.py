def create_unknown(client, user="recon-user"):
    tx=client.post("/api/v1/transactions",json={"user_id":user,"amount":"5000.00","merchant_id":"merchant-a"}).json()
    for state in ("AUTHORIZED","PROCESSING","DEBITED","UNKNOWN"):
        response=client.post(f"/api/v1/transactions/{tx['transaction_id']}/transitions",json={"target_status":state})
        assert response.status_code==200
    return tx["transaction_id"]

def test_unknown_reconciliation_requires_evidence_and_settles(client):
    transaction_id=create_unknown(client)
    started=client.post(f"/api/v1/reconciliation/{transaction_id}/start")
    assert started.status_code==200
    assert started.json()["status"]=="OPEN"
    assert client.get(f"/api/v1/reconciliation/{transaction_id}").json()["status"]=="OPEN"
    investigation=client.get(f"/api/v1/investigations/{transaction_id}").json()
    assert investigation["transaction"]["status"]=="RECONCILING"
    assert [e["to_status"] for e in investigation["timeline"]][-1]=="RECONCILING"
    evidence={"evidence_type":"MERCHANT_CONFIRMED","evidence_reference":"sandbox-event-001","details":"Synthetic sandbox merchant confirmation received","source":"SANDBOX"}
    resolved=client.post(f"/api/v1/reconciliation/{transaction_id}/evidence",json=evidence)
    assert resolved.status_code==200
    assert resolved.json()["status"]=="SETTLED"
    assert resolved.json()["evidence"]["reference"]=="sandbox-event-001"
    detail=client.get(f"/api/v1/investigations/{transaction_id}").json()
    assert detail["transaction"]["status"]=="SETTLED"
    assert [e["to_status"] for e in detail["timeline"]][-2:]==["RECONCILING","SETTLED"]
    assert detail["reconciliation"]["status"]=="SETTLED"
    assert client.post(f"/api/v1/reconciliation/{transaction_id}/evidence",json=evidence).status_code==409

def test_reversal_and_invalid_reconciliation_state(client):
    tx=client.post("/api/v1/transactions",json={"user_id":"u","amount":"1.00"}).json()
    assert client.post(f"/api/v1/reconciliation/{tx['transaction_id']}/start").status_code==409
    txid=create_unknown(client,user="reverse-user")
    assert client.post(f"/api/v1/reconciliation/{txid}/start").status_code==200
    body={"evidence_type":"REVERSAL_RECEIVED","evidence_reference":"rev-001","details":"Sandbox reversal record received"}
    result=client.post(f"/api/v1/reconciliation/{txid}/evidence",json=body)
    assert result.status_code==200
    assert result.json()["status"]=="REVERSED"

def test_mandate_assessment_uses_recorded_transaction(client):
    client.post("/api/v1/mandates",json={"mandate_id":"m-assess","user_id":"u-assess","expected_amount":"649.00","frequency":"MONTHLY","tolerance_percent":"5"})
    tx=client.post("/api/v1/transactions",json={"user_id":"u-assess","amount":"699.00","mandate_id":"m-assess"}).json()
    result=client.get(f"/api/v1/mandates/m-assess/assessment?transaction_id={tx['transaction_id']}")
    assert result.status_code==200
    assert result.json()["transaction_comparison"]["within_tolerance"] is False
    assert result.json()["recorded_mandate_transaction_count"]==1
    assert client.get(f"/api/v1/mandates/m-assess/assessment?transaction_id=missing").status_code==404
