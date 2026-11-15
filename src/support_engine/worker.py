"""Run the RQ consumer as a separate process."""

import argparse
import logging
import os

from redis import Redis
from rq import Worker
from rq.serializers import JSONSerializer

from support_engine.messaging import support_queue


def main() -> None:
    parser = argparse.ArgumentParser(description="Process saved support runs from RQ.")
    parser.add_argument("--burst", action="store_true", help="Exit when the queue is empty.")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)
    # Let RQ select a read timeout that exceeds its blocking queue wait.
    with Redis.from_url(
        os.environ.get("REDIS_URL", "redis://redis:6379/0"),
        socket_connect_timeout=3,
    ) as connection:
        worker = Worker(
            [support_queue(connection)], connection=connection, serializer=JSONSerializer
        )
        worker.work(burst=args.burst)


if __name__ == "__main__":
    main()
