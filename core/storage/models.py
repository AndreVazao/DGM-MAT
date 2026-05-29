from datetime import datetime
from sqlalchemy import String, Text, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from core.storage.database import Base

class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    event_id: Mapped[str] = mapped_column(
        String(255),
    )

    source: Mapped[str] = mapped_column(
        String(255),
    )

    target: Mapped[str] = mapped_column(
        String(255),
    )

    event_type: Mapped[str] = mapped_column(
        String(255),
    )

    payload: Mapped[str] = mapped_column(
        Text,
    )

    trace_id: Mapped[str] = mapped_column(
        String(255),
    )

class ActionRecord(Base):
    __tablename__ = "safe_action_queue"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    action_type: Mapped[str] = mapped_column(String(255))
    payload: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(50), default="DISCOVERED")
    is_approved: Mapped[bool] = mapped_column(Boolean, default=False)
    approved_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    audit_trail: Mapped[str] = mapped_column(Text, default="[]")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
