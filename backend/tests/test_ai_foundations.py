from app.ml.feature_engineering import transaction_features
from app.ml.model_adapter import ModelAdapter, ScikitLearnRiskModel

def test_unconfigured_model_is_explicitly_inactive(client):
    tx=client.post("/api/v1/transactions",json={"user_id":"ml-user","amount":"649.00"}).json()
    risk=client.get(f"/api/v1/transactions/{tx['transaction_id']}/risk").json()
    assert risk["machine_learning"]=={"status":"NOT_CONFIGURED","score":None,"model_name":None,"explanation_type":"NOT_AVAILABLE","explanation":[]}

def test_model_adapter_uses_injected_estimator_and_distinguishes_explanation():
    class Estimator:
        classes_=[0,1]
        def predict_proba(self, matrix):
            assert len(matrix[0])==2
            return [[0.8,0.2]]
    model=ScikitLearnRiskModel(Estimator(),"test-estimator",lambda features:[{"feature":"amount","impact":0.3}])
    result=ModelAdapter(model).assess({"amount":10.0,"history":1.0})
    assert result["status"]=="AVAILABLE"
    assert result["score"]==0.2
    assert result["explanation_type"]=="MODEL_EXPLAINER"
    assert result["explanation"][0]["direction"]=="INCREASES"

def test_bounded_natural_language_query_and_evidence_summary(client):
    tx=client.post("/api/v1/transactions",json={"user_id":"query-user","amount":"7499.00","merchant_id":"fictional-market"}).json()
    response=client.post("/api/v1/queries/transactions",json={"query":"show unknown transactions over 5000"})
    assert response.status_code==200
    result=response.json()
    assert result["interpreted_filters"]=={"status":"UNKNOWN","amount_gt":"5000"}
    assert result["results"]==[]
    high=client.post("/api/v1/queries/transactions",json={"query":"transactions over 5000"}).json()
    assert high["results"][0]["transaction_id"]==tx["transaction_id"]
    summary=client.get(f"/api/v1/investigations/{tx['transaction_id']}/assistant-summary").json()
    assert summary["llm_used"] is False
    assert summary["provider"]=="deterministic_evidence_fallback"
    assert "SYNTHETIC" in summary["summary"] or "synthetic" in summary["summary"]

def test_unrecognized_natural_language_is_controlled_error(client):
    assert client.post("/api/v1/queries/transactions",json={"query":"why did it happen"}).status_code==422
