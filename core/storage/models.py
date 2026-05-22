from sqlalchemy import String, Text, Integer
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
