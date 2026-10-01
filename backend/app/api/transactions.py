from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.transaction import Transaction, TransactionEvent
from app.schemas.transactions import TransactionCreate, TransactionOut, TransitionRequest
from app.services.transaction_service import create_transaction, get_transaction, transition_transaction

router = APIRouter(prefix="/transactions", tags=["transactions"])

@router.post("", response_model=TransactionOut, status_code=status.HTTP_201_CREATED)
def create(payload: TransactionCreate, db: Session = Depends(get_db)):
    return create_transaction(db, payload)

@router.get("", response_model=list[TransactionOut])
def list_transactions(limit: int = 100, db: Session = Depends(get_db)):
    if not 1 <= limit <= 500:
        raise HTTPException(422, "limit must be between 1 and 500")
    return list(db.scalars(select(Transaction).order_by(Transaction.created_at.desc()).limit(limit)))

@router.get("/{transaction_id}", response_model=TransactionOut)
def read(transaction_id: str, db: Session = Depends(get_db)):
    tx = get_transaction(db, transaction_id)
    if tx is None:
        raise HTTPException(404, "Transaction not found")
    return tx

@router.get("/{transaction_id}/timeline")
def timeline(transaction_id: str, db: Session = Depends(get_db)):
    if get_transaction(db, transaction_id) is None:
        raise HTTPException(404, "Transaction not found")
    events = db.scalars(select(TransactionEvent).where(TransactionEvent.transaction_id == transaction_id).order_by(TransactionEvent.created_at))
    return [{"event_id": e.event_id, "event_type": e.event_type, "from_status": e.from_status, "to_status": e.to_status, "details": e.details, "created_at": e.created_at} for e in events]

@router.post("/{transaction_id}/transitions", response_model=TransactionOut)
def transition(transaction_id: str, payload: TransitionRequest, db: Session = Depends(get_db)):
    tx = get_transaction(db, transaction_id)
    if tx is None:
        raise HTTPException(404, "Transaction not found")
    try:
        return transition_transaction(db, tx, payload.target_status, payload.event_type, payload.details)
    except ValueError as exc:
        db.rollback()
        raise HTTPException(409, str(exc)) from exc
