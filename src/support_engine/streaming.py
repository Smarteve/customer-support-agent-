import asyncio
import json
from contextlib import suppress

from fastapi import Request
from redis import asyncio as redis_async
from redis.exceptions import RedisError

from support_engine import repository
from support_engine.config import get_settings
from support_engine.schemas import ProgressNotice


class RunStream:
    """Subscribe first; replay persisted records; wait for coalesced Redis wake-ups."""

    def __init__(self, run_id: str, tenant_id: str, cursor: int):
        self.run_id = run_id
        self.tenant_id = tenant_id
        self.cursor = cursor
        self.client = redis_async.Redis.from_url(get_settings().redis_url, socket_connect_timeout=2)
        self.pubsub = self.client.pubsub()
        self.wake = asyncio.Queue(maxsize=1)
        self.failed = False
        self.reader = None

    async def prepare(self) -> None:
        try:
            await self.pubsub.subscribe(get_settings().channel(self.tenant_id))
            ack = await self.pubsub.get_message(ignore_subscribe_messages=False, timeout=5)
            if not ack or ack["type"] != "subscribe":
                raise RedisError("Subscription acknowledgment missing")
            # Reader buffers notices before the initial database replay starts.
            self.reader = asyncio.create_task(self.read_notices())
        except BaseException:
            await self.close()
            raise

    async def read_notices(self) -> None:
        try:
            async for item in self.pubsub.listen():
                if item["type"] == "subscribe":
                    if not self.wake.full():
                        self.wake.put_nowait(True)
                    continue
                if item["type"] != "message":
                    continue
                try:
                    notice = ProgressNotice.model_validate_json(item["data"])
                except ValueError:
                    continue
                if notice.run_id == self.run_id and notice.tenant_id == self.tenant_id:
                    if not self.wake.full():
                        self.wake.put_nowait(True)
        except (RedisError, OSError):
            self.failed = True
            if not self.wake.full():
                self.wake.put_nowait(True)

    async def events(self, request: Request):
        try:
            while True:
                if self.failed:
                    yield 'event: stream.reconnect\ndata: {"reason":"redis_disconnected"}\n\n'
                    return
                while True:
                    batch = await asyncio.to_thread(
                        repository.events_after, self.run_id, self.tenant_id, self.cursor
                    )
                    for event in batch:
                        self.cursor = event["sequence"]
                        yield (
                            f"id: {self.cursor}\nevent: {event['type']}\n"
                            f"data: {json.dumps(event)}\n\n"
                        )
                    if len(batch) < 100:
                        break
                # No database polling: only a notice or connection replay triggers a read.
                while True:
                    if await request.is_disconnected():
                        return
                    try:
                        await asyncio.wait_for(self.wake.get(), timeout=10)
                        break
                    except TimeoutError:
                        yield ": keep-alive\n\n"
        finally:
            await self.close()

    async def close(self) -> None:
        if self.reader is not None:
            self.reader.cancel()
            with suppress(asyncio.CancelledError):
                await self.reader
        await self.pubsub.aclose()
        await self.client.aclose()
