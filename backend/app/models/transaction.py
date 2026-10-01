from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base

class Transaction(Base):
    __tablename__ = "transactions"
    transaction_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(String(100), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="INR", nullable=False)
    payment_method: Mapped[str] = mapped_column(String(40), default="UPI_SANDBOX", nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(40), default="PAYMENT", nullable=False)
    merchant_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    beneficiary_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    device_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    mandate_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="INITIATED", nullable=False, index=True)
    environment: Mapped[str] = mapped_column(String(20), default="SYNTHETIC", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    events: Mapped[list["TransactionEvent"]] = relationship(back_populates="transaction", cascade="all, delete-orphan", order_by="TransactionEvent.created_at")

class TransactionEvent(Base):
    __tablename__ = "transaction_events"
    event_id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    transaction_id: Mapped[str] = mapped_column(ForeignKey("transactions.transaction_id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(60), nullable=False)
    from_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    to_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    details: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    transaction: Mapped[Transaction] = relationship(back_populates="events")
