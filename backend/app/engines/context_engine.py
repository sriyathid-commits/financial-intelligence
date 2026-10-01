from collections import Counter
from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.models.transaction import Transaction
from app.models.entities import User, Merchant, Device, Beneficiary, Mandate

def transaction_context(db: Session, tx: Transaction) -> dict:
    user_exists = db.get(User, tx.user_id) is not None
    user_history = list(db.scalars(select(Transaction).where(Transaction.user_id == tx.user_id, Transaction.transaction_id != tx.transaction_id)))
    amounts = [Decimal(t.amount) for t in user_history]
    merchant_counts = Counter(t.merchant_id for t in user_history if t.merchant_id)
    hour_counts = Counter(t.occurred_at.hour for t in user_history if t.occurred_at)
    method_counts = Counter(t.payment_method for t in user_history if t.payment_method)
    merchant_count = db.scalar(select(func.count()).select_from(Transaction).where(Transaction.user_id == tx.user_id, Transaction.merchant_id == tx.merchant_id, Transaction.transaction_id != tx.transaction_id)) if tx.merchant_id else 0
    device_history = db.scalar(select(func.count()).select_from(Transaction).where(Transaction.user_id == tx.user_id, Transaction.device_id == tx.device_id, Transaction.transaction_id != tx.transaction_id)) if tx.device_id else 0
    beneficiary_history = db.scalar(select(func.count()).select_from(Transaction).where(Transaction.user_id == tx.user_id, Transaction.beneficiary_id == tx.beneficiary_id, Transaction.transaction_id != tx.transaction_id)) if tx.beneficiary_id else 0
    device = db.get(Device, tx.device_id) if tx.device_id else None
    beneficiary = db.get(Beneficiary, tx.beneficiary_id) if tx.beneficiary_id else None
    mandate = db.get(Mandate, tx.mandate_id) if tx.mandate_id else None
    evidence = []
    if amounts:
        mean = sum(amounts) / Decimal(len(amounts))
        evidence.append({"type":"USER_AMOUNT_HISTORY", "sample_size":len(amounts), "average_amount":str(mean.quantize(Decimal('0.01'))), "highest_amount":str(max(amounts).quantize(Decimal('0.01'))), "current_vs_average_ratio":str((Decimal(tx.amount) / mean).quantize(Decimal('0.01'))) if mean else None})
    else:
        evidence.append({"type":"USER_AMOUNT_HISTORY", "sample_size":0, "note":"No prior transactions available"})
    return {
        "transaction_id": tx.transaction_id,
        "environment": "SYNTHETIC",
        "user": {"user_id":tx.user_id, "profile_registered":user_exists, "historical_transaction_count":len(user_history), "usual_merchants":merchant_counts.most_common(5), "usual_utc_hours":hour_counts.most_common(5), "usual_payment_methods":method_counts.most_common(5), "frequency_last_24h":sum(1 for t in user_history if t.occurred_at and 0 <= (tx.occurred_at-t.occurred_at).total_seconds() <= 86400)},
        "merchant": {"merchant_id":tx.merchant_id, "historical_transaction_count":merchant_count, "seen_before_by_user":bool(merchant_count), "merchant_registered":db.get(Merchant, tx.merchant_id) is not None if tx.merchant_id else False},
        "device": {"device_id":tx.device_id, "known_device":device is not None and device.user_id == tx.user_id, "prior_transactions_for_user":device_history},
        "beneficiary": {"beneficiary_id":tx.beneficiary_id, "known_beneficiary":beneficiary is not None and beneficiary.user_id == tx.user_id, "prior_transactions_for_user":beneficiary_history},
        "mandate": {"mandate_id":tx.mandate_id, "active":bool(mandate and mandate.active), "expected_amount":str(mandate.expected_amount) if mandate else None, "frequency":mandate.frequency if mandate else None, "tolerance_percent":str(mandate.tolerance_percent) if mandate else None, "next_expected_at":mandate.next_expected_at.isoformat() if mandate and mandate.next_expected_at else None},
        "evidence": evidence,
        "limitations": ["Signals are descriptive baselines from recorded synthetic transactions; they are not validated risk or fraud conclusions."]
    }
