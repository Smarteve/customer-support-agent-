import os
from uuid import UUID

from redis import Redis
from rq import Queue
from rq.exceptions import DuplicateJobError
from rq.job import JobStatus
from rq.serializers import JSONSerializer

class QueueSubmissionError(RuntimeError):
    pass

def redis_connection() -> Redis:
    """Producer connection. Worker blocking reads will need separate timeout settings."""
    return Redis.from_url(
        os.environ.get("REDIS_URL", "redis://redis:6379/0"),
        socket_connect_timeout=3,
        socket_timeout=3,
    )


def support_queue(connection: Redis) -> Queue:
    return Queue(
        os.environ.get("RQ_QUEUE", "support"),
        connection=connection,
        serializer=JSONSerializer,
    )





def enqueue_run(run_id: str) -> str:
    """Submit a saved run ID. Repeated submissions reuse an existing queued job."""
    run_id = str(UUID(str(run_id)))
    job_id = f"run-{run_id}"
    with redis_connection() as connection:
        queue = support_queue(connection)
        try:
            queue.enqueue(
                "support_engine.jobs.process_run",
                run_id,
                job_id=job_id,
                unique=True,
                job_timeout=90,
            )
        except DuplicateJobError as exc:
            existing = queue.fetch_job(job_id)
            if (
                existing is None
                or existing.get_status() != JobStatus.QUEUED
                or existing.func_name != "support_engine.jobs.process_run"
                or tuple(existing.args) != (run_id,)
                or existing.kwargs
            ):
                raise QueueSubmissionError("Existing job is not the expected queued run") from exc
    return job_id
