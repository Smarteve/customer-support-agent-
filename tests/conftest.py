"""PostgreSQL tests roll back their own rows; existing demonstration data is preserved."""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db_engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Use docker compose run --rm test for migrated PostgreSQL")
    engine = create_engine(url, connect_args={"connect_timeout": 3})
    yield engine
    engine.dispose()


@pytest.fixture
def db_sessions(db_engine):
    with db_engine.connect() as connection:
        transaction = connection.begin()
        yield sessionmaker(bind=connection, join_transaction_mode="create_savepoint")
        transaction.rollback()


@pytest.fixture
def rq_queue(monkeypatch):
    from uuid import uuid4

    from support_engine.messaging import redis_connection, support_queue

    url = os.environ.get("TEST_REDIS_URL")
    if not url:
        pytest.skip("Use docker compose run --rm test for Redis")
    monkeypatch.setenv("REDIS_URL", url)
    monkeypatch.setenv("RQ_QUEUE", "test-" + uuid4().hex)
    with redis_connection() as connection:
        queue = support_queue(connection)
        yield queue
        # The random queue contains only this test's jobs. Never flush shared Redis.
        queue.delete(delete_jobs=True)
