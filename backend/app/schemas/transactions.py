from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.engines.state_engine import TransactionStatus

class TransactionCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    payment_method: str = Field(default="UPI_SANDBOX", max_length=40)
    transaction_type: str = Field(default="PAYMENT", max_length=40)
    merchant_id: str | None = Field(default=None, max_length=100)
    beneficiary_id: str | None = Field(default=None, max_length=100)
    device_id: str | None = Field(default=None, max_length=100)
    mandate_id: str | None = Field(default=None, max_length=100)
    occurred_at: datetime | None = None

    @field_validator("currency")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()

class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    transaction_id: str
    user_id: str
    amount: Decimal
    currency: str
    payment_method: str
    transaction_type: str
    merchant_id: str | None
    beneficiary_id: str | None
    device_id: str | None
    mandate_id: str | None
    occurred_at: datetime
    status: TransactionStatus
    environment: str
    created_at: datetime
    updated_at: datetime

class TransitionRequest(BaseModel):
    target_status: TransactionStatus
    event_type: str = Field(default="STATE_TRANSITION", max_length=60)
    details: str | None = None
