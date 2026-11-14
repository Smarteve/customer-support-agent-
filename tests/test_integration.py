import asyncio
import json
import os
import time
from datetime import UTC, datetime
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError
from rq.job import Job, JobStatus

from support_engine import api, repository
from support_engine.config import get_settings
from support_engine.messaging import enqueue_run, publish_notice, redis_connection
from support_engine.schemas import SupportEvent
from support_engine.security import signature

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_INTEGRATION_TESTS") != "1", reason="Use the Compose test service"
    ),
]
BASE = os.getenv("API_BASE_URL", "http://localhost:8080")


def event_payload(customer_id="customer_17"):
    return {
        "schema_version": 1,
        "event_id": "test_" + uuid4().hex,
        "event_type": "support.message_received",
        "occurred_at": datetime.now(UTC).isoformat(),
        "source": "integration-test",
        "conversation_id": "test_conversation_" + uuid4().hex,
        "customer_id": customer_id,
        "message": {"text": "Where is ORD-1001?"},
    }


def signed(payload):
    settings = get_settings()
    body = json.dumps(payload).encode()
    timestamp = str(int(time.time()))
    return body, {
        "Content-Type": "application/json",
        "X-Webhook-Key-Id": settings.webhook_key_id,
        "X-Webhook-Timestamp": timestamp,
        "X-Webhook-Signature": signature(settings.webhook_secret, timestamp, body),
    }


def headers(cursor=None):
    result = {"Authorization": "Bearer " + get_settings().operator_token}
    if cursor is not None:
        result["Last-Event-ID"] = str(cursor)
    return result


async def next_event(lines):
    async for line in lines:
        if line.startswith("data: "):
            item = json.loads(line[6:])
            if "sequence" in item:
                return item
    raise AssertionError("SSE ended before a saved event arrived")


async def until_terminal(run_id, cursor=None):
    events = []
    async with asyncio.timeout(25), httpx.AsyncClient(base_url=BASE, timeout=25) as client:
        async with client.stream(
            "GET", f"/runs/{run_id}/events", headers=headers(cursor)
        ) as stream:
            assert stream.status_code == 200
            lines = stream.aiter_lines()
            while True:
                event = await next_event(lines)
                events.append(event)
                if event["type"] in {"run.completed", "run.failed", "run.escalated"}:
                    return events


async def test_signed_webhook_real_worker_duplicate_delivery_and_replay():
    payload = event_payload()
    body, auth = signed(payload)
    async with httpx.AsyncClient(base_url=BASE, timeout=10) as client:
        accepted = await client.post("/webhooks/support", content=body, headers=auth)
        assert accepted.status_code == 202, accepted.text
        run_id = accepted.json()["run_id"]
        events = await until_terminal(run_id)
        assert events[-1]["type"] == "run.completed"
        assert [e["sequence"] for e in events] == list(range(1, len(events) + 1))
        assert any(e["type"] == "tool.completed" for e in events)
        result = (await client.get(f"/runs/{run_id}", headers=headers())).json()
        assert result["response"] == "Order ORD-1001 is in transit."
        assert result["attempts"] == 1
        duplicate = await client.post("/webhooks/support", content=body, headers=auth)
        assert duplicate.status_code == 202
        assert duplicate.json()["duplicate"] is True
        assert duplicate.json()["run_id"] == run_id
        replay = await until_terminal(run_id, cursor=2)
        assert [e["sequence"] for e in replay] == list(range(3, len(events) + 1))
        changed = {**payload, "message": {"text": "Changed message"}}
        changed_body, changed_auth = signed(changed)
        conflict = await client.post(
            "/webhooks/support", content=changed_body, headers=changed_auth
        )
        assert conflict.status_code == 409

    # Duplicate RQ delivery is separate from duplicate webhook delivery.
    job_id = await asyncio.to_thread(enqueue_run, run_id)
    with redis_connection() as connection:
        for _ in range(100):
            job = Job.fetch(job_id, connection=connection)
            if job.get_status(refresh=True) == JobStatus.FINISHED:
                break
            await asyncio.sleep(0.05)
        else:
            raise AssertionError("Duplicate RQ delivery did not finish")
    assert repository.get_run(run_id, get_settings().tenant_id)["attempts"] == 1


async def test_pubsub_triggers_live_delivery_and_database_replays_missed_notices():
    settings = get_settings()
    run, _, _ = repository.create_run(
        settings.tenant_id, SupportEvent.model_validate(event_payload())
    )
    run_id = run["run_id"]  # Do not enqueue: this test controls the producer's commits.
    async with asyncio.timeout(20), httpx.AsyncClient(base_url=BASE, timeout=20) as client:
        async with client.stream("GET", f"/runs/{run_id}/events", headers=headers()) as stream:
            assert stream.status_code == 200
            lines = stream.aiter_lines()
            assert (await next_event(lines))["sequence"] == 1
            notice = repository.record_step(run_id, "test.saved_before_publish", {})
            pending = asyncio.create_task(next_event(lines))
            # A saved row alone must not produce a routine one-second polling update.
            with pytest.raises(TimeoutError):
                await asyncio.wait_for(asyncio.shield(pending), timeout=1.3)
            assert publish_notice(notice)
            received = await asyncio.wait_for(pending, timeout=5)
            assert received["sequence"] == 2
            assert received["type"] == "test.saved_before_publish"
        # No subscriber is connected; intentionally publish nothing for the next event.
        repository.record_step(run_id, "test.missed_notice", {})
        async with client.stream("GET", f"/runs/{run_id}/events", headers=headers(2)) as replay:
            assert replay.status_code == 200
            missing = await next_event(replay.aiter_lines())
            assert missing["sequence"] == 3
            assert missing["type"] == "test.missed_notice"


def test_authentication_tenant_scope_and_invalid_cursor():
    run, _, _ = repository.create_run("other-tenant", SupportEvent.model_validate(event_payload()))
    with httpx.Client(base_url=BASE, timeout=10) as client:
        assert client.get(f"/runs/{run['run_id']}").status_code == 401
        assert client.get(f"/runs/{run['run_id']}", headers=headers()).status_code == 404
        assert client.get(f"/runs/{run['run_id']}/events", headers=headers()).status_code == 404
        body, auth = signed(event_payload())
        auth["X-Webhook-Signature"] = "sha256=invalid"
        assert client.post("/webhooks/support", content=body, headers=auth).status_code == 401
        own, _, _ = repository.create_run(
            get_settings().tenant_id, SupportEvent.model_validate(event_payload())
        )
        bad_cursor = client.get(f"/runs/{own['run_id']}/events", headers=headers(-1))
        assert bad_cursor.status_code == 400


async def test_wrong_customer_cannot_read_order():
    body, auth = signed(event_payload(customer_id="customer_unrelated"))
    async with httpx.AsyncClient(base_url=BASE, timeout=10) as client:
        accepted = await client.post("/webhooks/support", content=body, headers=auth)
        assert accepted.status_code == 202
        events = await until_terminal(accepted.json()["run_id"])
        assert events[-1]["type"] == "run.escalated"
        assert not any(e["type"] == "tool.completed" for e in events)


async def test_queue_failure_preserves_run_and_sender_retry_reuses_identity(monkeypatch):
    original = api.enqueue_run

    def unavailable(_run_id):
        raise RedisConnectionError("injected queue failure")

    body, auth = signed(event_payload())
    monkeypatch.setattr(api, "enqueue_run", unavailable)
    with TestClient(api.app) as client:
        failed = client.post("/webhooks/support", content=body, headers=auth)
        assert failed.status_code == 503
        run_id = failed.json()["detail"]["run_id"]
        saved = repository.get_run(run_id, get_settings().tenant_id)
        assert saved["status"] == "pending"
        assert saved["enqueue_error"] == "queue_unavailable"
        monkeypatch.setattr(api, "enqueue_run", original)
        retried = client.post("/webhooks/support", content=body, headers=auth)
        assert retried.status_code == 202
        assert retried.json()["duplicate"] is True
        assert retried.json()["run_id"] == run_id
    assert (await until_terminal(run_id))[-1]["type"] == "run.completed"
