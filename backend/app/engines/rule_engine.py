from decimal import Decimal
from datetime import timezone

def evaluate_rules(tx, context: dict) -> list[dict]:
    rules=[]
    def add(code, dimension, severity, score, description, observed=None):
        rules.append({"rule_id":code,"dimension":dimension,"severity":severity,"score":score,"description":description,"observed":observed or {}})
    evidence = context["evidence"][0]
    ratio = Decimal(evidence["current_vs_average_ratio"]) if evidence.get("current_vs_average_ratio") else None
    if ratio and ratio >= Decimal("3"):
        add("AMOUNT_ABOVE_USER_BASELINE","transaction","HIGH" if ratio >= 8 else "MEDIUM",min(95,40+int(ratio)*8),"Amount is elevated relative to the recorded user average.",{"ratio_to_average":str(ratio),"average_amount":evidence["average_amount"],"sample_size":evidence["sample_size"]})
    elif not ratio and Decimal(tx.amount) >= Decimal("25000"):
        add("LARGE_AMOUNT_NO_BASELINE","transaction","MEDIUM",45,"Large amount with no user history available for comparison.",{"amount":str(tx.amount),"currency":tx.currency})
    if tx.merchant_id and not context["merchant"]["seen_before_by_user"] and Decimal(tx.amount) >= Decimal("5000"):
        add("NEW_MERCHANT_LARGE_AMOUNT","merchant","HIGH",75,"Merchant has no prior recorded relationship with this user and amount is at least 5000.",{"merchant_id":tx.merchant_id,"amount":str(tx.amount)})
    if context["user"]["frequency_last_24h"] >= 10:
        add("HIGH_TRANSACTION_VELOCITY","behavior","HIGH",80,"At least ten earlier transactions are recorded in the preceding 24 hours.",{"prior_transactions_24h":context["user"]["frequency_last_24h"]})
    if tx.device_id and not context["device"]["known_device"]:
        add("NEW_DEVICE","device","MEDIUM",60,"Device is not registered to this user in the synthetic context.",{"device_id":tx.device_id})
    if tx.beneficiary_id and not context["beneficiary"]["known_beneficiary"]:
        add("NEW_BENEFICIARY","beneficiary","MEDIUM",55,"Beneficiary is not registered to this user in the synthetic context.",{"beneficiary_id":tx.beneficiary_id})
    mandate=context["mandate"]
    if tx.mandate_id and mandate["active"] and mandate["expected_amount"]:
        expected=Decimal(mandate["expected_amount"]); tolerance=Decimal(mandate["tolerance_percent"])
        deviation=(abs(Decimal(tx.amount)-expected)/expected*100) if expected else Decimal(0)
        if deviation > tolerance:
            add("MANDATE_AMOUNT_DEVIATION","mandate","HIGH" if deviation >= 100 else "MEDIUM",min(100,55+int(min(deviation,45))),"Transaction amount exceeds the mandate tolerance.",{"expected_amount":str(expected),"actual_amount":str(tx.amount),"deviation_percent":str(deviation.quantize(Decimal('0.01'))),"tolerance_percent":str(tolerance)})
    if tx.status in {"UNKNOWN","RECONCILING"}:
        add("UNRESOLVED_TRANSACTION_STATE","state","MEDIUM",50,"Transaction outcome is unresolved and requires reconciliation.",{"status":tx.status})
    return rules
