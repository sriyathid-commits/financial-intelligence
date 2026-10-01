from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import Boolean, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

def now_utc():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"
    user_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class Merchant(Base):
    __tablename__ = "merchants"
    merchant_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    category: Mapped[str | None] = mapped_column(String(80))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

class Device(Base):
    __tablename__ = "devices"
    device_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    label: Mapped[str | None] = mapped_column(String(120))
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class Beneficiary(Base):
    __tablename__ = "beneficiaries"
    beneficiary_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)

class Mandate(Base):
    __tablename__ = "mandates"
    mandate_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    merchant_id: Mapped[str | None] = mapped_column(String(100), index=True)
    expected_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    frequency: Mapped[str] = mapped_column(String(24), nullable=False)
    tolerance_percent: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("5.00"), nullable=False)
    next_expected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now_utc, nullable=False)
