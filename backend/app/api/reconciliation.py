from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.state_engine import TransactionStatus, validate_transition
from app.models.reconciliation import Reconciliation
from app.models.transaction import Transaction, TransactionEvent
from app.services.transaction_service import get_transaction
from app.websocket.manager import event_hub

router=APIRouter(prefix="/reconciliation",tags=["reconciliation"])
class EvidenceRequest(BaseModel):
    evidence_type: str = Field(pattern="^(MERCHANT_CONFIRMED|REVERSAL_RECEIVED)$")
    evidence_reference: str = Field(min_length=1,max_length=160)
    details: str = Field(min_length=1,max_length=2000)
    source: str = Field(default="SYNTHETIC_SANDBOX",max_length=80)

def serialize(record: Reconciliation):
    return {"reconciliation_id":record.reconciliation_id,"transaction_id":record.transaction_id,"status":record.status,"evidence_type":record.evidence_type,"evidence_reference":record.evidence_reference,"evidence_details":record.evidence_details,"evidence":record.evidence_payload,"started_at":record.started_at,"resolved_at":record.resolved_at,"environment":"SYNTHETIC"}

@router.get("/{transaction_id}")
def get_reconciliation(transaction_id: str, db: Session=Depends(get_db)):
    if get_transaction(db,transaction_id) is None: raise HTTPException(404,"Transaction not found")
    record=db.scalar(select(Reconciliation).where(Reconciliation.transaction_id==transaction_id))
    if record is None: return {"transaction_id":transaction_id,"status":"NOT_STARTED","evidence":[],"environment":"SYNTHETIC"}
    return serialize(record)

@router.post("/{transaction_id}/start")
def start_reconciliation(transaction_id: str, db: Session=Depends(get_db)):
    tx=get_transaction(db,transaction_id)
    if tx is None: raise HTTPException(404,"Transaction not found")
    record=db.scalar(select(Reconciliation).where(Reconciliation.transaction_id==transaction_id))
    if record:
        if record.status!="OPEN": raise HTTPException(409,"Reconciliation is already resolved")
        return serialize(record)
    if tx.status not in {TransactionStatus.UNKNOWN.value,TransactionStatus.RECONCILING.value}:
        raise HTTPException(409,"Only UNKNOWN or RECONCILING transactions can enter reconciliation")
    now=datetime.now(timezone.utc)
    if tx.status==TransactionStatus.UNKNOWN.value:
        validate_transition(tx.status,TransactionStatus.RECONCILING)
        tx.status=TransactionStatus.RECONCILING.value
        tx.updated_at=now
        tx.events.append(TransactionEvent(event_type="RECONCILIATION_STARTED",from_status=TransactionStatus.UNKNOWN.value,to_status=TransactionStatus.RECONCILING.value,details="Reconciliation opened; awaiting explicit settlement evidence"))
    record=Reconciliation(reconciliation_id=str(uuid4()),transaction_id=transaction_id,status="OPEN",started_at=now)
    db.add(record)
    db.commit()
    db.refresh(record)
    db.refresh(tx)
    event_hub.publish_transaction(tx,"RECONCILIATION_STARTED")
    return serialize(record)

@router.post("/{transaction_id}/evidence")
def submit_evidence(transaction_id: str, payload: EvidenceRequest, db: Session=Depends(get_db)):
    tx=get_transaction(db,transaction_id)
    if tx is None: raise HTTPException(404,"Transaction not found")
    record=db.scalar(select(Reconciliation).where(Reconciliation.transaction_id==transaction_id))
    if record is None or record.status!="OPEN": raise HTTPException(409,"An open reconciliation must be started before evidence can be submitted")
    target=TransactionStatus.SETTLED if payload.evidence_type=="MERCHANT_CONFIRMED" else TransactionStatus.REVERSED
    try: validate_transition(tx.status,target)
    except ValueError as exc: raise HTTPException(409,str(exc)) from exc
    now=datetime.now(timezone.utc)
    previous=tx.status
    tx.status=target.value
    tx.updated_at=now
    tx.events.append(TransactionEvent(event_type=payload.evidence_type,from_status=previous,to_status=target.value,details=payload.details))
    record.status=target.value
    record.evidence_type=payload.evidence_type
    record.evidence_reference=payload.evidence_reference
    record.evidence_details=payload.details
    record.evidence_payload={"source":payload.source,"reference":payload.evidence_reference,"type":payload.evidence_type,"details":payload.details}
    record.resolved_at=now
    db.commit()
    db.refresh(tx)
    db.refresh(record)
    event_hub.publish_transaction(tx,"RECONCILIATION_RESOLVED")
    return serialize(record)
