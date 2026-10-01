from datetime import datetime, timezone
from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base
class PartnerEvent(Base):
    __tablename__="partner_events"
    __table_args__=(UniqueConstraint("partner_id","event_id",name="uq_partner_event_id"),)
    id:Mapped[str]=mapped_column(String(36),primary_key=True)
    partner_id:Mapped[str]=mapped_column(String(100),index=True,nullable=False)
    event_id:Mapped[str]=mapped_column(String(160),nullable=False)
    transaction_id:Mapped[str]=mapped_column(ForeignKey("transactions.transaction_id",ondelete="CASCADE"),index=True,nullable=False)
    target_status:Mapped[str]=mapped_column(String(20),nullable=False)
    payload_digest:Mapped[str]=mapped_column(String(64),nullable=False)
    received_at:Mapped[datetime]=mapped_column(DateTime(timezone=True),default=lambda:datetime.now(timezone.utc),nullable=False)
    details:Mapped[str|None]=mapped_column(Text)
