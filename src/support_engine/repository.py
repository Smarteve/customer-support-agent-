"""Save the input and pending work together. Queue submission is a later step."""

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from support_engine.database import Event, Run
from support_engine.schemas import SupportEvent, WebhookReceipt


class EventConflict(ValueError):
    pass


def save_event(session: Session, sender_key_id: str, event: SupportEvent) -> WebhookReceipt:
    payload = event.model_dump(mode="json")
    with session.begin():
        # The unique constraint also protects simultaneous deliveries of the same event.
        saved_id = session.scalar(
            insert(Event)
            .values(
                id=uuid4(),
                sender_key_id=sender_key_id,
                event_id=event.event_id,
                event_type=event.event_type,
                occurred_at=event.occurred_at,
                payload=payload,
            )
            .on_conflict_do_nothing(constraint="uq_events_sender_event")
            .returning(Event.id)
        )
        if saved_id is None:
            existing = session.scalar(
                select(Event).where(
                    Event.sender_key_id == sender_key_id, Event.event_id == event.event_id
                )
            )
            if existing.payload != payload:
                raise EventConflict("Event ID already exists with different content")
            run = session.scalar(select(Run).where(Run.event_id == existing.id))
        else:
            run = Run(id=uuid4(), event_id=saved_id, status="pending")
            session.add(run)
            session.flush()
        receipt = WebhookReceipt(event_id=event.event_id, run_id=run.id, run_status=run.status)
    # session.begin() commits before this return. Failure rolls both writes back.
    return receipt
