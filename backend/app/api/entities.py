from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.entities import User, Merchant, Device, Beneficiary, Mandate
from app.engines.mandate_engine import assess_mandate
from app.services.transaction_service import get_transaction
from app.schemas.entities import UserCreate, UserOut, MerchantCreate, MerchantOut, DeviceCreate, DeviceOut, BeneficiaryCreate, BeneficiaryOut, MandateCreate, MandateOut

router = APIRouter(tags=["context entities"])

def create_one(db: Session, model, payload):
    row = model(**payload.model_dump())
    db.add(row)
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(409, "Entity already exists or could not be created") from exc
    db.refresh(row)
    return row

def require_one(db: Session, model, key: str, value: str):
    row = db.get(model, value)
    if row is None:
        raise HTTPException(404, f"{key} not found")
    return row

@router.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, db: Session = Depends(get_db)): return create_one(db, User, payload)
@router.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)): return require_one(db, User, "User", user_id)
@router.post("/merchants", response_model=MerchantOut, status_code=status.HTTP_201_CREATED)
def create_merchant(payload: MerchantCreate, db: Session = Depends(get_db)): return create_one(db, Merchant, payload)
@router.get("/merchants/{merchant_id}", response_model=MerchantOut)
def get_merchant(merchant_id: str, db: Session = Depends(get_db)): return require_one(db, Merchant, "Merchant", merchant_id)
@router.post("/devices", response_model=DeviceOut, status_code=status.HTTP_201_CREATED)
def create_device(payload: DeviceCreate, db: Session = Depends(get_db)): return create_one(db, Device, payload)
@router.get("/devices/{device_id}", response_model=DeviceOut)
def get_device(device_id: str, db: Session = Depends(get_db)): return require_one(db, Device, "Device", device_id)
@router.post("/beneficiaries", response_model=BeneficiaryOut, status_code=status.HTTP_201_CREATED)
def create_beneficiary(payload: BeneficiaryCreate, db: Session = Depends(get_db)): return create_one(db, Beneficiary, payload)
@router.get("/beneficiaries/{beneficiary_id}", response_model=BeneficiaryOut)
def get_beneficiary(beneficiary_id: str, db: Session = Depends(get_db)): return require_one(db, Beneficiary, "Beneficiary", beneficiary_id)
@router.post("/mandates", response_model=MandateOut, status_code=status.HTTP_201_CREATED)
def create_mandate(payload: MandateCreate, db: Session = Depends(get_db)): return create_one(db, Mandate, payload)
@router.get("/mandates", response_model=list[MandateOut])
def list_mandates(db: Session = Depends(get_db)): return list(db.scalars(select(Mandate).order_by(Mandate.created_at.desc())))
@router.get("/mandates/{mandate_id}", response_model=MandateOut)
def get_mandate(mandate_id: str, db: Session = Depends(get_db)): return require_one(db, Mandate, "Mandate", mandate_id)

@router.get("/mandates/{mandate_id}/assessment")
def get_mandate_assessment(mandate_id: str, transaction_id: str | None = None, db: Session = Depends(get_db)):
    mandate = require_one(db, Mandate, "Mandate", mandate_id)
    tx = None
    if transaction_id:
        tx = get_transaction(db, transaction_id)
        if tx is None: raise HTTPException(404, "Transaction not found")
        if tx.mandate_id != mandate_id: raise HTTPException(422, "Transaction is not associated with this mandate")
    return assess_mandate(db, mandate, tx)
