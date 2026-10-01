from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.context_engine import transaction_context
from app.engines.risk_engine import assess_transaction
from app.services.transaction_service import get_transaction

router=APIRouter(prefix="/transactions",tags=["risk intelligence"])
def get_assessment(transaction_id: str, db: Session):
    tx=get_transaction(db,transaction_id)
    if tx is None: raise HTTPException(404,"Transaction not found")
    return assess_transaction(db,tx,transaction_context(db,tx))
@router.get("/{transaction_id}/risk")
def risk(transaction_id: str, db: Session=Depends(get_db)):
    return get_assessment(transaction_id,db)
@router.get("/{transaction_id}/explanation")
def explanation(transaction_id: str, db: Session=Depends(get_db)):
    result=get_assessment(transaction_id,db)
    return {"transaction_id":result["transaction_id"],"risk_band":result["risk_band"],"explanation":result["explanation"],"rules":result["rules"],"anomalies":result["anomalies"],"methodology":result["methodology"]}
