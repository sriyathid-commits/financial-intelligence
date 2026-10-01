from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.transaction_service import get_transaction
from app.engines.context_engine import transaction_context
router = APIRouter(prefix="/transactions", tags=["transaction context"])
@router.get("/{transaction_id}/context")
def get_context(transaction_id: str, db: Session = Depends(get_db)):
    tx = get_transaction(db, transaction_id)
    if tx is None:
        raise HTTPException(404, "Transaction not found")
    return transaction_context(db, tx)
