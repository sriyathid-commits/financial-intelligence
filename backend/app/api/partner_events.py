import hashlib, hmac, json, os, time
from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from app.db.session import get_db
from app.engines.state_engine import TransactionStatus, validate_transition
from app.models.partner_event import PartnerEvent
from app.models.transaction import TransactionEvent
from app.services.transaction_service import get_transaction
from app.websocket.manager import event_hub

router=APIRouter(prefix="/partner-events",tags=["authorized sandbox partner events"])
class PartnerPayload(BaseModel):
    transaction_id:str=Field(min_length=1,max_length=36)
    target_status:TransactionStatus
    details:str|None=Field(default=None,max_length=2000)

@router.post("")
async def ingest_partner_event(request:Request,db:Session=Depends(get_db)):
    partner_id=request.headers.get("x-partner-id","")
    event_id=request.headers.get("x-event-id","")
    timestamp=request.headers.get("x-event-timestamp","")
    signature=request.headers.get("x-event-signature","")
    expected_partner=os.getenv("SANDBOX_PARTNER_ID","")
    secret=os.getenv("SANDBOX_PARTNER_WEBHOOK_SECRET","")
    if not expected_partner or not secret: raise HTTPException(503,"Sandbox partner webhook is not configured")
    if not hmac.compare_digest(partner_id,expected_partner) or not event_id or not timestamp: raise HTTPException(401,"Invalid partner event identity")
    try: sent=int(timestamp)
    except ValueError as exc: raise HTTPException(401,"Invalid event timestamp") from exc
    if abs(time.time()-sent)>300: raise HTTPException(401,"Event timestamp is outside the accepted window")
    body=await request.body()
    signed=f"{timestamp}.{event_id}.".encode()+body
    calculated=hmac.new(secret.encode(),signed,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature,calculated): raise HTTPException(401,"Invalid event signature")
    try: payload=PartnerPayload.model_validate(json.loads(body))
    except Exception as exc: raise HTTPException(422,"Invalid partner event payload") from exc
    if db.scalar(select(PartnerEvent.id).where(PartnerEvent.partner_id==partner_id,PartnerEvent.event_id==event_id)):
        raise HTTPException(409,"Duplicate partner event")
    tx=get_transaction(db,payload.transaction_id)
    if tx is None: raise HTTPException(404,"Transaction not found")
    try: validate_transition(tx.status,payload.target_status)
    except ValueError as exc: raise HTTPException(409,str(exc)) from exc
    now=datetime.now(timezone.utc);previous=tx.status;target=payload.target_status.value
    tx.status=target;tx.updated_at=now
    tx.events.append(TransactionEvent(event_type="AUTHORIZED_PARTNER_EVENT",from_status=previous,to_status=target,details=payload.details or f"Sandbox partner event {event_id}"))
    db.add(PartnerEvent(id=str(uuid4()),partner_id=partner_id,event_id=event_id,transaction_id=tx.transaction_id,target_status=target,payload_digest=hashlib.sha256(body).hexdigest(),details=payload.details))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409,"Duplicate partner event") from exc
    db.refresh(tx)
    event_hub.publish_transaction(tx,"AUTHORIZED_PARTNER_EVENT")
    return {"event_id":event_id,"transaction_id":tx.transaction_id,"status":tx.status,"environment":"SYNTHETIC","message":"Verified sandbox partner event accepted"}
