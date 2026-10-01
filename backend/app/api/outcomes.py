from uuid import uuid4
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.context_engine import transaction_context
from app.engines.risk_engine import assess_transaction
from app.models.outcome import OutcomeFeedback
from app.services.transaction_service import get_transaction

router=APIRouter(prefix="/investigations",tags=["outcome feedback"])
class OutcomeRequest(BaseModel):
    outcome_label:str=Field(pattern="^(CONFIRMED_LEGITIMATE|CONFIRMED_UNAUTHORIZED|DISPUTED|REFUNDED|REVERSED|UNKNOWN_FINAL)$")
    reviewer_id:str=Field(min_length=1,max_length=100)
    evidence_reference:str|None=Field(default=None,max_length=160)
    notes:str|None=Field(default=None,max_length=2000)

@router.post("/{transaction_id}/outcomes",status_code=201)
def record_outcome(transaction_id:str,payload:OutcomeRequest,db:Session=Depends(get_db)):
    tx=get_transaction(db,transaction_id)
    if tx is None: raise HTTPException(404,"Transaction not found")
    context=transaction_context(db,tx);risk=assess_transaction(db,tx,context)
    snapshot={"overall_score":risk["overall_score"],"risk_band":risk["risk_band"],"dimensions":risk["dimensions"],"rule_ids":[r["rule_id"] for r in risk["rules"]],"anomaly_types":[a["type"] for a in risk["anomalies"]],"machine_learning_status":risk["machine_learning"]["status"]}
    record=OutcomeFeedback(feedback_id=str(uuid4()),transaction_id=transaction_id,outcome_label=payload.outcome_label,verification_status="UNVERIFIED",reviewer_id=payload.reviewer_id,evidence_reference=payload.evidence_reference,notes=payload.notes,risk_snapshot=snapshot)
    db.add(record);db.commit();db.refresh(record)
    return serialize(record)

def serialize(record):
    return {"feedback_id":record.feedback_id,"transaction_id":record.transaction_id,"outcome_label":record.outcome_label,"verification_status":record.verification_status,"reviewer_id":record.reviewer_id,"verified_by":record.verified_by,"verified_at":record.verified_at,"evidence_reference":record.evidence_reference,"notes":record.notes,"risk_snapshot":record.risk_snapshot,"created_at":record.created_at,"environment":"SYNTHETIC"}

@router.get("/{transaction_id}/outcomes")
def list_outcomes(transaction_id:str,db:Session=Depends(get_db)):
    if get_transaction(db,transaction_id) is None: raise HTTPException(404,"Transaction not found")
    records=db.scalars(select(OutcomeFeedback).where(OutcomeFeedback.transaction_id==transaction_id).order_by(OutcomeFeedback.created_at.desc()))
    return {"transaction_id":transaction_id,"feedback":[serialize(row) for row in records],"training_enabled":False,"note":"Feedback is preserved for review; this endpoint does not train or update a model."}

class VerificationRequest(BaseModel):
    reviewer_id:str=Field(min_length=1,max_length=100)

@router.post("/feedback/{feedback_id}/verify")
def verify_feedback(feedback_id:str,payload:VerificationRequest,db:Session=Depends(get_db)):
    record=db.get(OutcomeFeedback,feedback_id)
    if record is None: raise HTTPException(404,"Outcome feedback not found")
    if record.verification_status=="VERIFIED": raise HTTPException(409,"Feedback is already verified")
    record.verification_status="VERIFIED"
    record.verified_by=payload.reviewer_id
    record.verified_at=datetime.now(timezone.utc)
    db.commit();db.refresh(record)
    return serialize(record)
