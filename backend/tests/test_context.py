def test_mandate_and_context_evidence(client):
    user = client.post("/api/v1/users", json={"user_id":"user-demo", "display_name":"Synthetic User"})
    assert user.status_code == 201
    merchant = client.post("/api/v1/merchants", json={"merchant_id":"merchant-demo", "display_name":"Fictional StreamCo", "category":"SUBSCRIPTION"})
    assert merchant.status_code == 201
    client.post("/api/v1/transactions", json={"user_id":"user-demo", "amount":"649.00", "merchant_id":"merchant-demo"})
    current = client.post("/api/v1/transactions", json={"user_id":"user-demo", "amount":"49999.00", "merchant_id":"merchant-demo"}).json()
    mandate = client.post("/api/v1/mandates", json={"mandate_id":"mandate-demo", "user_id":"user-demo", "merchant_id":"merchant-demo", "expected_amount":"649.00", "frequency":"MONTHLY", "tolerance_percent":"5.00"})
    assert mandate.status_code == 201
    tx = client.post("/api/v1/transactions", json={"user_id":"user-demo", "amount":"49999.00", "merchant_id":"merchant-demo", "mandate_id":"mandate-demo"}).json()
    context = client.get(f"/api/v1/transactions/{tx['transaction_id']}/context")
    assert context.status_code == 200
    body = context.json()
    assert body["environment"] == "SYNTHETIC"
    assert body["merchant"]["seen_before_by_user"] is True
    assert body["mandate"]["active"] is True
    assert body["mandate"]["expected_amount"] == "649.00"
    assert body["evidence"][0]["sample_size"] == 2
    assert "not validated risk" in body["limitations"][0]
    assert client.get("/api/v1/mandates").status_code == 200

def test_mandate_validation_and_missing_context(client):
    bad = client.post("/api/v1/mandates", json={"mandate_id":"m", "user_id":"u", "expected_amount":"0", "frequency":"DAILY"})
    assert bad.status_code == 422
    assert client.get("/api/v1/transactions/missing/context").status_code == 404
