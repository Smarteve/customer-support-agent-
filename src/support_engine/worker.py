from rq import Queue, Worker
from rq.serializers import JSONSerializer

from support_engine.config import get_settings
from support_engine.messaging import redis_connection


def main():
    with redis_connection() as connection:
        queue = Queue(get_settings().queue_name, connection=connection, serializer=JSONSerializer)
        Worker([queue], connection=connection, serializer=JSONSerializer).work()


if __name__ == "__main__":
    main()
