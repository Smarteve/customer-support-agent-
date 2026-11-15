from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import delete, event, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from support_engine import jobs
from support_engine.database import Event, Run, RunEvent
from support_engine.repository import save_event
from support_engine.schemas import SupportEvent
from support_engine.simulator import build_event

pytestmark = pytest.mark.database


@pytest.fixture
def saved_run(db_sessions, db_engine, monkeypatch):
    monkeypatch.setattr(jobs, "make_engine", lambda: db_engine)
    monkeypatch.setattr(jobs, "Session", lambda engine: db_sessions())
    payload = SupportEvent.model_validate(build_event("Hello", "customer_17"))
    with db_sessions() as session:
        receipt = save_event(session, "worker-test", payload)
    return receipt.run_id


def test_pending_run_completes(saved_run, db_sessions, caplog):
    with caplog.at_level("INFO", logger=jobs.__name__):
        jobs.process_run(str(saved_run))
    with db_sessions() as session:
        assert session.get(Run, saved_run).status == "completed"
    jobs.process_run(str(saved_run))
    with db_sessions() as session:
        history = list(
            session.scalars(
                select(RunEvent).where(RunEvent.run_id == saved_run).order_by(RunEvent.id)
            )
        )
        assert [row.event_type for row in history] == ["run.started", "run.completed"]
        assert history[0].id < history[1].id
        assert history[0].created_at is not None
        assert history[0].details == {}
        assert history[1].details == {"operation": "log_event_type"}
    assert "event type" in caplog.text


@pytest.mark.parametrize("status", ["running", "completed", "failed", "escalated"])
def test_non_pending_run_is_skipped(saved_run, db_sessions, status, caplog):
    with db_sessions() as session, session.begin():
        session.get(Run, saved_run).status = status
    with caplog.at_level("INFO", logger=jobs.__name__):
        jobs.process_run(str(saved_run))
    with db_sessions() as session:
        assert session.get(Run, saved_run).status == status
        assert list(session.scalars(select(RunEvent).where(RunEvent.run_id == saved_run))) == []
    assert "Processing run" not in caplog.text


def test_missing_run_raises(saved_run):
    with pytest.raises(ValueError, match="does not exist"):
        jobs.process_run(str(uuid4()))


def test_work_failure_is_saved_and_raised(saved_run, db_sessions, monkeypatch):
    def fail_log(*args, **kwargs):
        raise RuntimeError("injected work failure")

    monkeypatch.setattr(jobs.logger, "info", fail_log)
    with pytest.raises(RuntimeError, match="injected work failure"):
        jobs.process_run(str(saved_run))
    with db_sessions() as session:
        assert session.get(Run, saved_run).status == "failed"
        history = list(
            session.scalars(
                select(RunEvent).where(RunEvent.run_id == saved_run).order_by(RunEvent.id)
            )
        )
        assert [row.event_type for row in history] == ["run.started", "run.failed"]
        assert history[-1].details == {"error_type": "RuntimeError"}


def test_invalid_id_does_not_open_database(monkeypatch):
    def unexpected_engine():
        pytest.fail("Invalid UUID must fail before opening the database")

    monkeypatch.setattr(jobs, "make_engine", unexpected_engine)
    with pytest.raises(ValueError):
        jobs.process_run("invalid")


def test_simultaneous_calls_process_once(db_engine, monkeypatch):
    monkeypatch.setattr(jobs, "make_engine", lambda: db_engine)
    log = Mock()
    monkeypatch.setattr(jobs.logger, "info", log)
    payload = SupportEvent.model_validate(build_event("Hello", "customer_17"))
    with Session(db_engine) as session:
        receipt = save_event(session, "worker-" + uuid4().hex, payload)
        event_id = session.get(Run, receipt.run_id).event_id
    barrier = Barrier(2)

    def process():
        barrier.wait(timeout=10)
        jobs.process_run(str(receipt.run_id))

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            calls = [pool.submit(process) for _ in range(2)]
            for call in calls:
                call.result(timeout=15)
        processed = [call for call in log.call_args_list if call.args[0].startswith("Processing")]
        assert len(processed) == 1
        with Session(db_engine) as session:
            assert session.get(Run, receipt.run_id).status == "completed"
            history = list(
                session.scalars(
                    select(RunEvent.event_type)
                    .where(RunEvent.run_id == receipt.run_id)
                    .order_by(RunEvent.id)
                )
            )
            assert history == ["run.started", "run.completed"]
    finally:
        with db_engine.begin() as connection:
            connection.execute(delete(Run).where(Run.id == receipt.run_id))
            connection.execute(delete(Event).where(Event.id == event_id))


@pytest.mark.parametrize(
    ("failed_type", "expected_status", "expected_history"),
    [
        ("run.started", "pending", []),
        ("run.completed", "failed", ["run.started", "run.failed"]),
        ("run.failed", "running", ["run.started"]),
    ],
)
def test_progress_insert_failure_rolls_back_status(
    saved_run, db_sessions, monkeypatch, failed_type, expected_status, expected_history
):
    def reject_progress(mapper, connection, target):
        if target.event_type == failed_type:
            raise SQLAlchemyError("injected progress insert failure")

    def fail_work(*args, **kwargs):
        raise RuntimeError("injected work failure")

    if failed_type == "run.failed":
        monkeypatch.setattr(jobs.logger, "info", fail_work)
    event.listen(RunEvent, "before_insert", reject_progress)
    try:
        with pytest.raises(SQLAlchemyError, match="injected progress insert failure"):
            jobs.process_run(str(saved_run))
    finally:
        event.remove(RunEvent, "before_insert", reject_progress)
    with db_sessions() as session:
        assert session.get(Run, saved_run).status == expected_status
        history = list(
            session.scalars(
                select(RunEvent.event_type)
                .where(RunEvent.run_id == saved_run)
                .order_by(RunEvent.id)
            )
        )
        assert history == expected_history


@pytest.mark.parametrize("work_fails", [False, True])
def test_notices_are_published_after_committed_progress(db_engine, monkeypatch, work_fails):
    monkeypatch.setattr(jobs, "make_engine", lambda: db_engine)
    payload = SupportEvent.model_validate(build_event("Hello", "customer_17"))
    with Session(db_engine) as session:
        receipt = save_event(session, "notice-" + uuid4().hex, payload)
        event_id = session.get(Run, receipt.run_id).event_id
    observed = []

    def check_committed(run_id):
        # A different connection can see only committed state and progress.
        with Session(db_engine) as session:
            run = session.get(Run, receipt.run_id)
            history = list(
                session.scalars(
                    select(RunEvent.event_type)
                    .where(RunEvent.run_id == receipt.run_id)
                    .order_by(RunEvent.id)
                )
            )
            observed.append((run.status, history))

    monkeypatch.setattr(jobs, "publish_run_notice", check_committed)
    try:
        if work_fails:
            monkeypatch.setattr(jobs.logger, "info", Mock(side_effect=RuntimeError("work failed")))
            with pytest.raises(RuntimeError, match="work failed"):
                jobs.process_run(str(receipt.run_id))
            expected_status, expected_event = "failed", "run.failed"
        else:
            jobs.process_run(str(receipt.run_id))
            expected_status, expected_event = "completed", "run.completed"
        assert observed == [
            ("running", ["run.started"]),
            (expected_status, ["run.started", expected_event]),
        ]
    finally:
        with db_engine.begin() as connection:
            connection.execute(delete(Run).where(Run.id == receipt.run_id))
            connection.execute(delete(Event).where(Event.id == event_id))
