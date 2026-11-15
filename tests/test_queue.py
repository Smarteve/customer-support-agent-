import json
import time
from concurrent.futures import ThreadPoolExecutor
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError
from rq.job import JobStatus
from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from support_engine.api import create_app
from support_engine.database import Event, Run
from support_engine.jobs import process_run
from support_engine.messaging import QueueSubmissionError, enqueue_run
from support_engine.security import signature
from support_engine.simulator import build_event


@pytest.mark.queue
def test_queue_stores_only_the_saved_run_id(rq_queue):
    run_id = str(uuid4())
    job_id = enqueue_run(run_id)
    job = rq_queue.fetch_job(job_id)
    assert job_id == f"run-{run_id}"
    assert tuple(job.args) == (run_id,)
    assert job.kwargs == {}
    assert job.func is process_run
    assert job.get_status() == JobStatus.QUEUED
    assert rq_queue.count == 1


@pytest.mark.queue
def test_simultaneous_enqueue_retries_reuse_one_job(rq_queue):
    run_id = str(uuid4())
    with ThreadPoolExecutor(max_workers=4) as pool:
        job_ids = list(pool.map(enqueue_run, [run_id] * 4))
    assert len(set(job_ids)) == 1
    assert rq_queue.count == 1


@pytest.mark.queue
def test_nonqueued_existing_job_is_not_reported_as_queued(rq_queue):
    run_id = str(uuid4())
    job_id = enqueue_run(run_id)
    rq_queue.fetch_job(job_id).set_status(JobStatus.FAILED)
    with pytest.raises(QueueSubmissionError):
        enqueue_run(run_id)


def test_invalid_run_id_is_rejected_before_redis():
    with pytest.raises(ValueError):
        enqueue_run("not-a-run-id")


@pytest.fixture
def committed_client(db_engine, rq_queue, monkeypatch):
    key_id = "test-" + uuid4().hex
    monkeypatch.setenv("WEBHOOK_KEY_ID", key_id)
    monkeypatch.setenv("WEBHOOK_SECRET", "queue-test-secret")
    with TestClient(create_app(sessionmaker(db_engine))) as client:
        yield client, key_id
    # These tests must commit to prove the ordering of commit and enqueue.
    with db_engine.begin() as connection:
        ids = select(Event.id).where(Event.sender_key_id == key_id)
        connection.execute(delete(Run).where(Run.event_id.in_(ids)))
        connection.execute(delete(Event).where(Event.sender_key_id == key_id))


def signed_headers(body, key_id):
    timestamp = str(int(time.time()))
    return {
        "Content-Type": "application/json",
        "X-Webhook-Key-Id": key_id,
        "X-Webhook-Timestamp": timestamp,
        "X-Webhook-Signature": signature("queue-test-secret", timestamp, body),
    }


@pytest.mark.database
@pytest.mark.queue
def test_webhook_commits_before_enqueue(committed_client, db_engine, rq_queue, monkeypatch):
    client, key_id = committed_client
    calls = []

    def checked_enqueue(run_id):
        # This independent connection cannot see the row before commit.
        with Session(db_engine) as session:
            saved_run = session.get(Run, UUID(run_id))
            assert saved_run is not None
            assert saved_run.status == "pending"
            assert session.get(Event, saved_run.event_id) is not None
        calls.append(run_id)
        return enqueue_run(run_id)

    monkeypatch.setattr("support_engine.api.enqueue_run", checked_enqueue)
    body = json.dumps(build_event("Hello", "customer_17")).encode()
    response = client.post("/webhooks/support", content=body, headers=signed_headers(body, key_id))
    assert response.status_code == 202
    assert response.json()["status"] == "queued"
    assert response.json()["run_status"] == "pending"
    assert calls == [response.json()["run_id"]]
    assert rq_queue.fetch_job(response.json()["job_id"]) is not None


@pytest.mark.database
@pytest.mark.queue
def test_queue_failure_keeps_saved_work_and_matching_retry_recovers(
    committed_client, db_engine, rq_queue, monkeypatch
):
    client, key_id = committed_client

    def unavailable(run_id):
        raise RedisConnectionError("test Redis failure")

    monkeypatch.setattr("support_engine.api.enqueue_run", unavailable)
    body = json.dumps(build_event("Hello", "customer_17")).encode()
    failed = client.post("/webhooks/support", content=body, headers=signed_headers(body, key_id))
    assert failed.status_code == 503
    receipt = failed.json()["detail"]
    assert receipt["status"] == "saved"
    run_id = UUID(receipt["run_id"])
    with Session(db_engine) as session:
        saved_run = session.get(Run, run_id)
        assert saved_run.status == "pending"
        assert session.get(Event, saved_run.event_id) is not None
    assert rq_queue.count == 0

    monkeypatch.setattr("support_engine.api.enqueue_run", enqueue_run)
    for _ in range(2):
        retried = client.post(
            "/webhooks/support", content=body, headers=signed_headers(body, key_id)
        )
        assert retried.status_code == 202
        assert retried.json()["run_id"] == str(run_id)
    assert rq_queue.count == 1


@pytest.mark.database
@pytest.mark.queue
def test_uncertain_acknowledgement_retry_reuses_job(committed_client, rq_queue, monkeypatch):
    client, key_id = committed_client

    def lost_ack(run_id):
        enqueue_run(run_id)
        raise RedisConnectionError("simulated lost acknowledgement")

    monkeypatch.setattr("support_engine.api.enqueue_run", lost_ack)
    body = json.dumps(build_event("Hello", "customer_17")).encode()
    failed = client.post("/webhooks/support", content=body, headers=signed_headers(body, key_id))
    assert failed.status_code == 503
    run_id = failed.json()["detail"]["run_id"]
    assert rq_queue.count == 1
    monkeypatch.setattr("support_engine.api.enqueue_run", enqueue_run)
    retried = client.post("/webhooks/support", content=body, headers=signed_headers(body, key_id))
    assert retried.status_code == 202
    assert retried.json()["run_id"] == run_id
    assert rq_queue.count == 1
