from app.engines.rule_engine import evaluate_rules
from app.engines.anomaly_engine import detect_anomalies
from app.ml.feature_engineering import transaction_features
from app.ml.model_adapter import risk_model

FUSION_PEAK_WEIGHT=0.50
RISK_WEIGHTS={"transaction":0.22,"behavior":0.18,"merchant":0.12,"device":0.12,"beneficiary":0.10,"mandate":0.16,"state":0.10}

def assess_transaction(db, tx, context: dict) -> dict:
    rules=evaluate_rules(tx,context)
    anomalies=detect_anomalies(db,tx,context)
    dimensions={key:0 for key in RISK_WEIGHTS}
    for rule in rules:
        dimensions[rule["dimension"]]=max(dimensions[rule["dimension"]],rule["score"])
    # Anomaly strength contributes only when no corresponding rule already supplied a score.
    anomaly_dimension={"AMOUNT_ANOMALY":"transaction","FREQUENCY_ANOMALY":"behavior","MERCHANT_ANOMALY":"merchant","DEVICE_ANOMALY":"device","MANDATE_ANOMALY":"mandate","DUPLICATE_ANOMALY":"transaction"}
    for anomaly in anomalies:
        dim=anomaly_dimension.get(anomaly["type"])
        score={"LOW":25,"MEDIUM":55,"HIGH":85}[anomaly["strength"]]
        if dim:
            dimensions[dim]=max(dimensions[dim],score)
    weighted=sum(dimensions[k]*RISK_WEIGHTS[k] for k in dimensions)
    overall=round(FUSION_PEAK_WEIGHT*max(dimensions.values(),default=0)+(1-FUSION_PEAK_WEIGHT)*weighted)
    sample=context["user"]["historical_transaction_count"]
    coverage=min(1.0,0.35+0.1*sample+0.08*len([x for x in (tx.merchant_id,tx.device_id,tx.beneficiary_id,tx.mandate_id) if x]))
    confidence=round(coverage*100)
    band="HIGH" if overall>=70 else "MEDIUM" if overall>=35 else "LOW"
    ml_assessment=risk_model.assess(transaction_features(tx,context))
    return {"transaction_id":tx.transaction_id,"environment":"SYNTHETIC","overall_score":overall,"risk_band":band,"confidence_percent":confidence,"dimensions":dimensions,"weights":RISK_WEIGHTS,"rules":rules,"anomalies":anomalies,"machine_learning":ml_assessment,"decision_authority":"Advisory demo score only; no allow/block/fraud decision.","methodology":"Deterministic illustrative heuristics: score is 50% peak dimension plus 50% weighted sum. Dimension weights and thresholds are configurable demo values, not scientifically validated.","explanation":build_explanation(rules,anomalies)}

def build_explanation(rules: list[dict], anomalies: list[dict]) -> list[str]:
    # Sentences are emitted only from the structured rule/anomaly records above.
    return [r["description"] for r in rules] + [f"Observed {a['type'].lower().replace('_',' ')} ({a['strength'].lower()} signal)." for a in anomalies if not any(a["type"].startswith(r["rule_id"].split("_")[0]) for r in rules)]
