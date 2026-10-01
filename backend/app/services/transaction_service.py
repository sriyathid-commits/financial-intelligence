from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.engines.state_engine import TransactionStatus, validate_transition
from app.models.transaction import Transaction, TransactionEvent
from app.schemas.transactions import TransactionCreate

def create_transaction(db: Session, payload: TransactionCreate) -> Transaction:
    tx = Transaction(**payload.model_dump(exclude_none=True), status=TransactionStatus.INITIATED.value, environment="SYNTHETIC")
    tx.events.append(TransactionEvent(event_type="TRANSACTION_CREATED", to_status=TransactionStatus.INITIATED.value, details="Synthetic/sandbox transaction created"))
    db.add(tx)
    db.commit()
    db.refresh(tx)
    from app.websocket.manager import event_hub
    event_hub.publish_transaction(tx, "TRANSACTION_CREATED")
    return tx

def get_transaction(db: Session, transaction_id: str) -> Transaction | None:
    return db.scalar(select(Transaction).where(Transaction.transaction_id == transaction_id))

def transition_transaction(db: Session, tx: Transaction, target: TransactionStatus, event_type: str, details: str | None) -> Transaction:
    validate_transition(tx.status, target)
    previous = tx.status
    tx.status = target.value
    tx.updated_at = datetime.now(timezone.utc)
    tx.events.append(TransactionEvent(event_type=event_type, from_status=previous, to_status=target.value, details=details))
    db.commit()
    db.refresh(tx)
    from app.websocket.manager import event_hub
    event_hub.publish_transaction(tx)
    return tx
