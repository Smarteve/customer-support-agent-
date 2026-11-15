"""Receive temporary run notices. SSE delivery is a later step."""

import asyncio
import logging
import os
from uuid import UUID

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)
RUN_NOTICE_PATTERN = "support:run:*"


async def listen_for_run_notices() -> None:
    """Log run IDs without blocking FastAPI or querying the database."""
    while True:
        try:
            # A subscription waits for messages. Do not use the publisher's read timeout.
            async with Redis.from_url(
                os.environ.get("REDIS_URL", "redis://redis:6379/0"),
                socket_connect_timeout=3,
                decode_responses=True,
            ) as connection:
                async with connection.pubsub() as subscription:
                    await subscription.psubscribe(RUN_NOTICE_PATTERN)
                    async for message in subscription.listen():
                        if message["type"] == "psubscribe":
                            logger.info(
                                "run_notice_subscriber_ready pattern=%s", RUN_NOTICE_PATTERN
                            )
                        elif message["type"] == "pmessage":
                            try:
                                run_id = UUID(message["channel"].removeprefix("support:run:"))
                            except ValueError:
                                logger.warning("run_notice_invalid_channel")
                                continue
                            logger.info("run_notice_received run_id=%s", run_id)
        except RedisError as exc:
            logger.warning("run_subscription_unavailable category=%s", type(exc).__name__)
            # Retry only the subscription. Saved progress stays in PostgreSQL.
            await asyncio.sleep(1)
