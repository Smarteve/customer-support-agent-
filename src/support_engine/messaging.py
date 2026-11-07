import json
import logging

from redis import Redis
from redis.exceptions import RedisError
from rq import Queue
from rq.serializers import JSONSerializer

from support_engine.config import get_settings
from support_engine.schemas import ProgressNotice

logger = logging.getLogger(__name__)


def redis_connection() -> Redis:
    return Redis.from_url(get_settings().redis_url, socket_connect_timeout=2, socket_timeout=2)


def publish_notice(notice: dict) -> bool:
    validated = ProgressNotice.model_validate(notice)
    try:
        with redis_connection() as connection:
            connection.publish(
                get_settings().channel(validated.tenant_id),
                json.dumps(validated.model_dump()),
            )
        return True
    except RedisError:
        # Saved progress survives a notification failure. Never repeat a business action here.
        logger.warning("progress_notice_failed", extra={"run_id": validated.run_id})
        return False


def enqueue_run(run_id: str) -> str:
    with redis_connection() as connection:
        queue = Queue(get_settings().queue_name, connection=connection, serializer=JSONSerializer)
        job = queue.enqueue(
            "support_engine.jobs.process_run",
            run_id,
            job_timeout=90,
            result_ttl=3600,
            failure_ttl=86400,
        )
        return job.id
