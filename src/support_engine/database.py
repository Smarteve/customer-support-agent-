"""Database connection and the first two persistent records."""

import os
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    Uuid,
    create_engine,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("sender_key_id", "event_id", name="uq_events_sender_event"),)

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    sender_key_id: Mapped[str] = mapped_column(String(128))
    event_id: Mapped[str] = mapped_column(String(128))
    event_type: Mapped[str] = mapped_column(String(128))
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    payload: Mapped[dict] = mapped_column(JSONB)


class Run(Base):
    __tablename__ = "runs"
    __table_args__ = (
        UniqueConstraint("event_id", name="uq_runs_event"),
        CheckConstraint(
            "status IN ('pending', 'running', 'completed', 'failed', 'escalated')",
            name="ck_runs_status",
        ),
    )

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(ForeignKey("events.id"))
    status: Mapped[str] = mapped_column(String(20), server_default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


def database_url() -> str:
    return os.environ.get(
        "DATABASE_URL", "postgresql+psycopg://support:support_dev@postgres:5432/support"
    )


def make_engine():
    return create_engine(database_url(), pool_pre_ping=True, connect_args={"connect_timeout": 3})
