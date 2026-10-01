from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base
class OutcomeFeedback(Base):
    __tablename__="outcome_feedback"
    feedback_id:Mapped[str]=mapped_column(String(36),primary_key=True)
    transaction_id:Mapped[str]=mapped_column(ForeignKey("transactions.transaction_id",ondelete="CASCADE"),index=True,nullable=False)
    outcome_label:Mapped[str]=mapped_column(String(40),nullable=False)
    verification_status:Mapped[str]=mapped_column(String(20),default="UNVERIFIED",nullable=False)
    reviewer_id:Mapped[str]=mapped_column(String(100),nullable=False)
    verified_by:Mapped[str|None]=mapped_column(String(100))
    verified_at:Mapped[datetime|None]=mapped_column(DateTime(timezone=True))
    evidence_reference:Mapped[str|None]=mapped_column(String(160))
    notes:Mapped[str|None]=mapped_column(Text)
    risk_snapshot:Mapped[dict]=mapped_column(JSON,nullable=False)
    created_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
