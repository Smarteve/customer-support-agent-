"""Execute real RQ jobs in a separate worker process and an isolated queue."""

import os
import subprocess
import sys
from uuid import uuid4

import pytest
from rq.job import JobStatus
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from support_engine.database import Event, Run, RunEvent
from support_engine.messaging import enqueue_run
from support_engine.repository import save_event
from support_engine.schemas import SupportEvent
from support_engine.simulator import build_event

pytestmark = [pytest.mark.database, pytest.mark.queue]


@pytest.mark.parametrize("missing_run", [False, True])
def test_worker_processes_json_job(db_engine, rq_queue, missing_run):
    run_id = uuid4()
    event_id = None
    if not missing_run:
        payload = SupportEvent.model_validate(build_event("Hello", "customer_17"))
        with Session(db_engine) as session:
            receipt = save_event(session, "worker-process-" + uuid4().hex, payload)
            run_id = receipt.run_id
            event_id = session.get(Run, run_id).event_id
    job = None
    try:
        job_id = enqueue_run(str(run_id))
        job = rq_queue.fetch_job(job_id)
        env = dict(os.environ, DATABASE_URL=os.environ["TEST_DATABASE_URL"])
        result = subprocess.run(
            [sys.executable, "-m", "support_engine.worker", "--burst"],
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr
        assert rq_queue.count == 0
        if missing_run:
            assert job.get_status() == JobStatus.FAILED
            assert "does not exist" in job.latest_result().exc_string
        else:
            assert job.get_status() == JobStatus.FINISHED
            with Session(db_engine) as session:
                assert session.get(Run, run_id).status == "completed"
                history = list(
                    session.scalars(
                        select(RunEvent.event_type)
                        .where(RunEvent.run_id == run_id)
                        .order_by(RunEvent.id)
                    )
                )
                assert history == ["run.started", "run.completed"]
            assert "event type" in result.stdout + result.stderr
    finally:
        if job is not None:
            job.delete()
        if event_id is not None:
            with db_engine.begin() as connection:
                connection.execute(delete(Run).where(Run.id == run_id))
                connection.execute(delete(Event).where(Event.id == event_id))
