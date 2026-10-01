import re
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.engines.context_engine import transaction_context
from app.engines.risk_engine import assess_transaction
from app.models.transaction import Transaction

router=APIRouter(prefix="/queries",tags=["natural language queries"])
class QueryRequest(BaseModel):
    query: str=Field(min_length=2,max_length=500)
    limit: int=Field(default=50,ge=1,le=100)

STATUSES={"unknown":"UNKNOWN","failed":"FAILED","success":"SUCCESS","settled":"SETTLED","reversed":"REVERSED","processing":"PROCESSING","reconciling":"RECONCILING","initiated":"INITIATED"}
def parse_query(query:str)->dict:
    q=query.lower(); filters={}
    for word,status in STATUSES.items():
        if re.search(rf"\b{word}\b",q): filters["status"]=status;break
    risk_match=re.search(r"\b(high|medium|low)\s+risk\b",q)
    if risk_match: filters["risk_band"]=risk_match.group(1).upper()
    amount=re.search(r"\b(over|above|greater than|under|below|less than)\s*[₹$]?\s*([\d,]+(?:\.\d{1,2})?)",q)
    if amount:
        op="gt" if amount.group(1) in {"over","above","greater than"} else "lt"
        filters["amount_"+op]=Decimal(amount.group(2).replace(",",""))
    merchant=re.search(r"\bmerchant\s*:\s*([\w -]+)",q)
    if merchant: filters["merchant_id_contains"]=merchant.group(1).strip()
    if "today" in q: filters["today_utc"]=True
    if not filters: raise HTTPException(422,"Could not interpret the query. Try a state, 'high risk', an amount like 'over 5000', 'today', or 'merchant: id'.")
    return filters

@router.post("/transactions")
def query_transactions(payload:QueryRequest,db:Session=Depends(get_db)):
    filters=parse_query(payload.query)
    candidates=list(db.scalars(select(Transaction).order_by(Transaction.created_at.desc()).limit(500)))
    results=[]
    now=datetime.now(timezone.utc)
    for tx in candidates:
        if filters.get("status") and tx.status!=filters["status"]: continue
        if "amount_gt" in filters and Decimal(tx.amount)<=filters["amount_gt"]: continue
        if "amount_lt" in filters and Decimal(tx.amount)>=filters["amount_lt"]: continue
        if "merchant_id_contains" in filters and filters["merchant_id_contains"] not in (tx.merchant_id or "").lower(): continue
        if filters.get("today_utc"):
            occurred=tx.created_at if tx.created_at.tzinfo else tx.created_at.replace(tzinfo=timezone.utc)
            if occurred.date()!=now.date(): continue
        risk_band=None
        if "risk_band" in filters:
            risk=assess_transaction(db,tx,transaction_context(db,tx))
            risk_band=risk["risk_band"]
            if risk_band!=filters["risk_band"]: continue
        results.append({"transaction_id":tx.transaction_id,"amount":str(tx.amount),"currency":tx.currency,"merchant_id":tx.merchant_id,"status":tx.status,"risk_band":risk_band,"created_at":tx.created_at})
        if len(results)>=payload.limit: break
    serial_filters={k:(str(v) if isinstance(v,Decimal) else v) for k,v in filters.items()}
    return {"query":payload.query,"interpreted_filters":serial_filters,"results":results,"result_count":len(results),"search_scope":"Most recent 500 recorded transactions","environment":"SYNTHETIC","limitations":["This is a constrained deterministic query parser, not an LLM. High/medium/low risk uses the configured illustrative risk heuristics."]}
