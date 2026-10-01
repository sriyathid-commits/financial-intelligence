from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base

class Reconciliation(Base):
    __tablename__="reconciliations"
    __table_args__=(UniqueConstraint("transaction_id",name="uq_reconciliation_transaction"),)
    reconciliation_id: Mapped[str]=mapped_column(String(36),primary_key=True)
    transaction_id: Mapped[str]=mapped_column(ForeignKey("transactions.transaction_id",ondelete="CASCADE"),index=True,nullable=False)
    status: Mapped[str]=mapped_column(String(20),default="OPEN",nullable=False)
    evidence_type: Mapped[str|None]=mapped_column(String(40))
    evidence_reference: Mapped[str|None]=mapped_column(String(160))
    evidence_details: Mapped[str|None]=mapped_column(Text)
    evidence_payload: Mapped[dict|None]=mapped_column(JSON)
    started_at: Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
    resolved_at: Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
