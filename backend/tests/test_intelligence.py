def test_normal_transaction_has_low_advisory_score(client):
    tx=client.post("/api/v1/transactions",json={"user_id":"regular-user","amount":"649.00","merchant_id":"streaming"}).json()
    risk=client.get(f"/api/v1/transactions/{tx['transaction_id']}/risk")
    assert risk.status_code==200
    body=risk.json()
    assert body["risk_band"]=="LOW"
    assert body["overall_score"] < 35
    assert body["rules"]==[]
    assert body["environment"]=="SYNTHETIC"
    assert "not scientifically validated" in body["methodology"]

def test_mandate_and_device_evidence_produce_high_advisory_score(client):
    client.post("/api/v1/transactions",json={"user_id":"u-risk","amount":"649.00","merchant_id":"m-risk","device_id":"old-device"})
    client.post("/api/v1/mandates",json={"mandate_id":"monthly","user_id":"u-risk","merchant_id":"m-risk","expected_amount":"649.00","frequency":"MONTHLY","tolerance_percent":"5"})
    tx=client.post("/api/v1/transactions",json={"user_id":"u-risk","amount":"49999.00","merchant_id":"m-risk","device_id":"new-device","mandate_id":"monthly"}).json()
    risk=client.get(f"/api/v1/transactions/{tx['transaction_id']}/risk").json()
    codes={rule["rule_id"] for rule in risk["rules"]}
    assert "AMOUNT_ABOVE_USER_BASELINE" in codes
    assert "MANDATE_AMOUNT_DEVIATION" in codes
    assert "NEW_DEVICE" in codes
    assert risk["risk_band"]=="HIGH"
    explanation=client.get(f"/api/v1/transactions/{tx['transaction_id']}/explanation").json()
    assert explanation["explanation"]
    assert any("mandate tolerance" in statement for statement in explanation["explanation"])

def test_duplicate_is_anomaly_not_automatic_fraud(client):
    body={"user_id":"u-dup","amount":"100.00","merchant_id":"m-dup","occurred_at":"2026-09-30T10:00:00Z"}
    client.post("/api/v1/transactions",json=body)
    second=client.post("/api/v1/transactions",json=body).json()
    risk=client.get(f"/api/v1/transactions/{second['transaction_id']}/risk").json()
    assert any(signal["type"]=="DUPLICATE_ANOMALY" for signal in risk["anomalies"])
    assert "Advisory" in risk["decision_authority"] and "allow/block" in risk["decision_authority"]
