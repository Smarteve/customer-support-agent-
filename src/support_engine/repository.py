from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from support_engine.database import Run, RunEvent, get_engine, identifier, now
from support_engine.schemas import SupportEvent


class EventConflict(Exception):
    pass


class StateConflict(Exception):
    pass


def snapshot(run: Run) -> dict:
    return {
        "run_id": run.id,
        "status": run.status,
        "last_sequence": run.last_sequence,
        "attempts": run.attempts,
        "response": run.response,
        "error": run.error,
        "enqueue_error": run.enqueue_error,
        "created_at": run.created_at.isoformat(),
        "updated_at": run.updated_at.isoformat(),
        "enqueued_at": run.enqueued_at.isoformat() if run.enqueued_at else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
    }


def append(session: Session, run: Run, event_type: str, details: dict) -> dict:
    run.last_sequence += 1
    run.updated_at = now()
    event = RunEvent(
        run_id=run.id,
        tenant_id=run.tenant_id,
        sequence=run.last_sequence,
        attempt=run.attempts,
        type=event_type,
        details={**details, "status": run.status},
    )
    session.add(event)
    session.flush()
    return {
        "schema_version": 1,
        "tenant_id": run.tenant_id,
        "run_id": run.id,
        "event_id": event.id,
        "sequence": event.sequence,
    }


def create_run(tenant_id: str, event: SupportEvent) -> tuple[dict, bool, dict | None]:
    with Session(get_engine(), expire_on_commit=False) as session:
        try:
            with session.begin():
                run = Run(
                    tenant_id=tenant_id,
                    source=event.source,
                    external_event_id=event.event_id,
                    payload_hash=event.payload_hash(),
                    input_payload=event.model_dump(mode="json"),
                    status="pending",
                    last_sequence=0,
                    attempts=0,
                )
                session.add(run)
                session.flush()
                notice = append(session, run, "run.received", {"source": event.source})
            return snapshot(run), False, notice
        except IntegrityError:
            session.rollback()
            existing = session.scalar(
                select(Run).where(
                    Run.tenant_id == tenant_id,
                    Run.source == event.source,
                    Run.external_event_id == event.event_id,
                )
            )
            if existing is None:
                raise
            if existing.payload_hash != event.payload_hash():
                raise EventConflict from None
            return snapshot(existing), True, None


def get_run(run_id: str, tenant_id: str) -> dict | None:
    with Session(get_engine()) as session:
        run = session.scalar(select(Run).where(Run.id == run_id, Run.tenant_id == tenant_id))
        return snapshot(run) if run else None


def events_after(run_id: str, tenant_id: str, sequence: int, limit: int = 100) -> list[dict]:
    with Session(get_engine()) as session:
        events = session.scalars(
            select(RunEvent)
            .where(
                RunEvent.run_id == run_id,
                RunEvent.tenant_id == tenant_id,
                RunEvent.sequence > sequence,
            )
            .order_by(RunEvent.sequence)
            .limit(limit)
        )
        return [
            {
                "event_id": e.id,
                "run_id": e.run_id,
                "sequence": e.sequence,
                "attempt": e.attempt,
                "type": e.type,
                "occurred_at": e.occurred_at.isoformat(),
                "details": e.details,
            }
            for e in events
        ]


def mark_submission(run_id: str, error: str | None = None) -> None:
    with Session(get_engine()) as session, session.begin():
        run = session.scalar(select(Run).where(Run.id == run_id).with_for_update())
        run.enqueue_error = error
        if error is None:
            run.enqueued_at = now()
        # Submission metadata must never move running/completed work back to pending.


def claim_run(run_id: str) -> tuple[dict, str, dict] | None:
    with Session(get_engine(), expire_on_commit=False) as session, session.begin():
        run = session.scalar(select(Run).where(Run.id == run_id).with_for_update())
        if run is None or run.status != "pending":
            return None
        run.status = "running"
        run.attempts += 1
        run.execution_token = identifier()
        run.started_at = now()
        run.lease_expires_at = now() + timedelta(seconds=120)
        run.error = None
        notice = append(session, run, "run.started", {"mode": "deterministic_fake_agent"})
        return (
            {
                "run_id": run.id,
                "tenant_id": run.tenant_id,
                "input": run.input_payload,
            },
            run.execution_token,
            notice,
        )


def record_step(
    run_id: str,
    event_type: str,
    details: dict,
    *,
    owner: str | None = None,
    status: str | None = None,
    response: str | None = None,
    error: str | None = None,
) -> dict:
    with Session(get_engine()) as session, session.begin():
        run = session.scalar(select(Run).where(Run.id == run_id).with_for_update())
        if run is None or (owner is not None and run.execution_token != owner):
            raise StateConflict("Run ownership changed")
        if status is not None:
            run.status = status
        if response is not None:
            run.response = response
        if error is not None:
            run.error = error
        if run.status in {"completed", "failed", "escalated"}:
            run.finished_at = now()
            run.lease_expires_at = None
        elif owner is not None:
            run.lease_expires_at = now() + timedelta(seconds=120)
        return append(session, run, event_type, details)


def prepare_retry(run_id: str, tenant_id: str) -> dict:
    with Session(get_engine()) as session, session.begin():
        run = session.scalar(
            select(Run).where(Run.id == run_id, Run.tenant_id == tenant_id).with_for_update()
        )
        if run is None:
            raise LookupError
        expired = (
            run.status == "running"
            and run.lease_expires_at is not None
            and run.lease_expires_at <= now()
        )
        if run.status not in {"pending", "failed"} and not expired:
            raise StateConflict("Run is active or already finished")
        run.status = "pending"
        run.execution_token = None
        run.lease_expires_at = None
        run.finished_at = None
        run.error = None
        return append(session, run, "run.retry_requested", {})
