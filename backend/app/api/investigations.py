from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.context_engine import transaction_context
from app.engines.risk_engine import assess_transaction
from app.models.reconciliation import Reconciliation
from app.models.transaction import TransactionEvent
from app.services.transaction_service import get_transaction
from app.api.reconciliation import serialize

router=APIRouter(prefix="/investigations",tags=["investigations"])
@router.get("/{transaction_id}")
def investigate(transaction_id: str, db: Session=Depends(get_db)):
    tx=get_transaction(db,transaction_id)
    if tx is None: raise HTTPException(404,"Transaction not found")
    context=transaction_context(db,tx)
    risk=assess_transaction(db,tx,context)
    events=db.scalars(select(TransactionEvent).where(TransactionEvent.transaction_id==transaction_id).order_by(TransactionEvent.created_at))
    reconciliation=db.scalar(select(Reconciliation).where(Reconciliation.transaction_id==transaction_id))
    return {"transaction":{**{key:getattr(tx,key) for key in ("transaction_id","user_id","currency","payment_method","transaction_type","merchant_id","beneficiary_id","device_id","mandate_id","occurred_at","status","environment","created_at","updated_at")},"amount":str(tx.amount)},"context":context,"risk":risk,"timeline":[{"event_id":e.event_id,"event_type":e.event_type,"from_status":e.from_status,"to_status":e.to_status,"details":e.details,"created_at":e.created_at} for e in events],"reconciliation":serialize(reconciliation) if reconciliation else {"transaction_id":transaction_id,"status":"NOT_STARTED","evidence":[],"environment":"SYNTHETIC"}}

@router.get("/{transaction_id}/assistant-summary")
def assistant_summary(transaction_id: str, db: Session=Depends(get_db)):
    from app.llm.provider import summarize_investigation
    from app.api.reconciliation import serialize
    tx=get_transaction(db,transaction_id)
    if tx is None: raise HTTPException(404,"Transaction not found")
    context=transaction_context(db,tx)
    risk=assess_transaction(db,tx,context)
    reconciliation=db.scalar(select(Reconciliation).where(Reconciliation.transaction_id==transaction_id))
    facts={"transaction":{"transaction_id":tx.transaction_id,"status":tx.status,"amount":str(tx.amount),"currency":tx.currency,"merchant_id":tx.merchant_id},"risk":risk,"reconciliation":serialize(reconciliation) if reconciliation else {"status":"NOT_STARTED","evidence":None}}
    return summarize_investigation(facts)
