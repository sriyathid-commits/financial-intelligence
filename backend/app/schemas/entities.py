from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field

class UserCreate(BaseModel):
    user_id: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=160)
class UserOut(UserCreate):
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime

class MerchantCreate(BaseModel):
    merchant_id: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=160)
    category: str | None = Field(default=None, max_length=80)
class MerchantOut(MerchantCreate):
    model_config = ConfigDict(from_attributes=True)
    active: bool

class DeviceCreate(BaseModel):
    device_id: str = Field(min_length=1, max_length=100)
    user_id: str = Field(min_length=1, max_length=100)
    label: str | None = Field(default=None, max_length=120)
class DeviceOut(DeviceCreate):
    model_config = ConfigDict(from_attributes=True)
    first_seen_at: datetime

class BeneficiaryCreate(BaseModel):
    beneficiary_id: str = Field(min_length=1, max_length=100)
    user_id: str = Field(min_length=1, max_length=100)
    display_name: str = Field(min_length=1, max_length=160)
class BeneficiaryOut(BeneficiaryCreate):
    model_config = ConfigDict(from_attributes=True)
    created_at: datetime

class MandateCreate(BaseModel):
    mandate_id: str = Field(min_length=1, max_length=100)
    user_id: str = Field(min_length=1, max_length=100)
    merchant_id: str | None = None
    expected_amount: Decimal = Field(gt=0, max_digits=18, decimal_places=2)
    frequency: str = Field(pattern="^(WEEKLY|MONTHLY|QUARTERLY|YEARLY)$")
    tolerance_percent: Decimal = Field(default=Decimal("5.00"), ge=0, le=100, max_digits=7, decimal_places=2)
    next_expected_at: datetime | None = None
class MandateOut(MandateCreate):
    model_config = ConfigDict(from_attributes=True)
    active: bool
    created_at: datetime
