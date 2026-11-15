import asyncio
from threading import Event
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from redis.exceptions import ConnectionError as RedisConnectionError

from support_engine import subscriber
from support_engine.api import create_app
from support_engine.messaging import publish_run_notice


@pytest.mark.queue
def test_subscriber_receives_a_published_notice(rq_queue, monkeypatch, caplog):
    async def exercise():
        ready = asyncio.Event()
        received = asyncio.Event()
        run_id = uuid4()
        original_info = subscriber.logger.info

        def observe(message, value):
            original_info(message, value)
            if message.startswith("run_notice_subscriber_ready"):
                ready.set()
            elif value == run_id:
                received.set()

        monkeypatch.setattr(subscriber.logger, "info", observe)
        task = asyncio.create_task(subscriber.listen_for_run_notices())
        try:
            await asyncio.wait_for(ready.wait(), timeout=5)
            publish_run_notice(str(run_id))
            await asyncio.wait_for(received.wait(), timeout=5)
            assert f"run_notice_received run_id={run_id}" in caplog.text
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    with caplog.at_level("INFO", logger=subscriber.__name__):
        asyncio.run(exercise())


def test_subscriber_reconnects_and_closes_connections(monkeypatch):
    async def exercise():
        ready = asyncio.Event()
        clients = [AsyncMock(), AsyncMock()]
        subscriptions = [AsyncMock(), AsyncMock()]
        for client, subscription in zip(clients, subscriptions, strict=True):
            client.__aenter__.return_value = client
            client.pubsub = MagicMock(return_value=subscription)
            subscription.__aenter__.return_value = subscription
        subscriptions[0].psubscribe.side_effect = RedisConnectionError("injected disconnect")

        async def messages():
            yield {"type": "psubscribe"}
            ready.set()
            await asyncio.Event().wait()

        subscriptions[1].listen = MagicMock(side_effect=messages)
        factory = MagicMock(side_effect=clients)
        monkeypatch.setattr(subscriber.Redis, "from_url", factory)
        task = asyncio.create_task(subscriber.listen_for_run_notices())
        try:
            await asyncio.wait_for(ready.wait(), timeout=5)
            assert factory.call_count == 2
            subscriptions[0].__aexit__.assert_awaited_once()
            clients[0].__aexit__.assert_awaited_once()
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
        subscriptions[1].__aexit__.assert_awaited_once()
        clients[1].__aexit__.assert_awaited_once()

    asyncio.run(exercise())


def test_fastapi_starts_and_stops_subscriber(monkeypatch):
    started = Event()
    stopped = Event()

    async def listen():
        started.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    monkeypatch.setattr("support_engine.api.listen_for_run_notices", listen)
    with TestClient(create_app(MagicMock())) as client:
        assert started.wait(timeout=2)
        assert client.get("/openapi.json").status_code == 200
    assert stopped.is_set()


def test_publication_failure_does_not_fail_the_job(monkeypatch, caplog):
    connection = MagicMock()
    connection.__enter__.return_value = connection
    connection.publish.side_effect = RedisConnectionError("injected publication failure")
    monkeypatch.setattr("support_engine.messaging.redis_connection", lambda: connection)
    publish_run_notice(str(uuid4()))
    assert "run_notice_failed" in caplog.text
