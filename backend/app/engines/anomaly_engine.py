from decimal import Decimal
from datetime import timedelta
from sqlalchemy import select
from app.models.transaction import Transaction

def detect_anomalies(db, tx, context: dict) -> list[dict]:
    signals=[]
    evidence=context["evidence"][0]
    ratio=Decimal(evidence["current_vs_average_ratio"]) if evidence.get("current_vs_average_ratio") else None
    if ratio and ratio >= Decimal("3"):
        signals.append({"type":"AMOUNT_ANOMALY","strength":"HIGH" if ratio>=8 else "MEDIUM","observed":{"ratio_to_average":str(ratio)}})
    if context["user"]["frequency_last_24h"] >= 10:
        signals.append({"type":"FREQUENCY_ANOMALY","strength":"HIGH","observed":{"prior_transactions_24h":context["user"]["frequency_last_24h"]}})
    if tx.merchant_id and not context["merchant"]["seen_before_by_user"]:
        signals.append({"type":"MERCHANT_ANOMALY","strength":"LOW","observed":{"merchant_id":tx.merchant_id}})
    if tx.device_id and not context["device"]["known_device"]:
        signals.append({"type":"DEVICE_ANOMALY","strength":"MEDIUM","observed":{"device_id":tx.device_id}})
    if tx.mandate_id and context["mandate"]["active"] and context["mandate"]["expected_amount"]:
        expected=Decimal(context["mandate"]["expected_amount"])
        deviation=(abs(Decimal(tx.amount)-expected)/expected*100) if expected else Decimal(0)
        tolerance=Decimal(context["mandate"]["tolerance_percent"])
        if deviation>tolerance:
            signals.append({"type":"MANDATE_ANOMALY","strength":"HIGH" if deviation>=100 else "MEDIUM","observed":{"deviation_percent":str(deviation.quantize(Decimal('0.01')))}})
    event_time=tx.occurred_at.replace(tzinfo=None)
    candidates=db.scalars(select(Transaction).where(Transaction.transaction_id != tx.transaction_id, Transaction.user_id == tx.user_id, Transaction.amount == tx.amount, Transaction.merchant_id == tx.merchant_id, Transaction.occurred_at >= event_time-timedelta(minutes=5), Transaction.occurred_at <= event_time).limit(1))
    duplicate=next(iter(candidates),None)
    if duplicate:
        signals.append({"type":"DUPLICATE_ANOMALY","strength":"HIGH","observed":{"matching_transaction_id":duplicate.transaction_id}})
    return signals
