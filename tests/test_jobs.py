from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest.mock import Mock
from uuid import uuid4

import pytest
from sqlalchemy import delete
from sqlalchemy.orm import Session

from support_engine import jobs
from support_engine.database import Event, Run
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
    assert "event type" in caplog.text


@pytest.mark.parametrize("status", ["running", "completed", "failed", "escalated"])
def test_non_pending_run_is_skipped(saved_run, db_sessions, status, caplog):
    with db_sessions() as session, session.begin():
        session.get(Run, saved_run).status = status
    with caplog.at_level("INFO", logger=jobs.__name__):
        jobs.process_run(str(saved_run))
    with db_sessions() as session:
        assert session.get(Run, saved_run).status == status
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
    finally:
        with db_engine.begin() as connection:
            connection.execute(delete(Run).where(Run.id == receipt.run_id))
            connection.execute(delete(Event).where(Event.id == event_id))
