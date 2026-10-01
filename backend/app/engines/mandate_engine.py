from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.entities import Mandate
from app.models.transaction import Transaction

def assess_mandate(db: Session, mandate: Mandate, transaction: Transaction | None=None) -> dict:
    history=list(db.scalars(select(Transaction).where(Transaction.mandate_id==mandate.mandate_id).order_by(Transaction.occurred_at.desc()).limit(10)))
    now=datetime.now(timezone.utc)
    due_state="UNKNOWN"
    if mandate.next_expected_at:
        due=mandate.next_expected_at
        if due.tzinfo is None: due=due.replace(tzinfo=timezone.utc)
        due_state="DUE_OR_PAST_DUE" if now>=due else "UPCOMING"
    result={"mandate_id":mandate.mandate_id,"active":mandate.active,"expected_amount":str(mandate.expected_amount),"frequency":mandate.frequency,"tolerance_percent":str(mandate.tolerance_percent),"next_expected_at":mandate.next_expected_at.isoformat() if mandate.next_expected_at else None,"schedule_state":due_state,"recorded_mandate_transaction_count":len(history),"recent_recorded_payments":[{"transaction_id":t.transaction_id,"amount":str(t.amount),"currency":t.currency,"status":t.status,"occurred_at":t.occurred_at.isoformat()} for t in history],"environment":"SYNTHETIC","limitations":["Schedule state is a descriptive comparison with the configured next expected date. It does not assert that a payment is due or overdue in the payment network."]}
    if transaction:
        actual=Decimal(transaction.amount); expected=Decimal(mandate.expected_amount)
        deviation=(abs(actual-expected)/expected*Decimal(100)) if expected else Decimal(0)
        result["transaction_comparison"]={"transaction_id":transaction.transaction_id,"associated_with_mandate":transaction.mandate_id==mandate.mandate_id,"actual_amount":str(actual),"deviation_percent":str(deviation.quantize(Decimal("0.01"))),"within_tolerance":deviation<=Decimal(mandate.tolerance_percent),"tolerance_percent":str(mandate.tolerance_percent)}
    return result
