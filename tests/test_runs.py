from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from support_engine.api import create_app
from support_engine.database import Run
from support_engine.repository import save_event
from support_engine.schemas import SupportEvent
from support_engine.simulator import build_event

TOKEN = "test-operator-token"
AUTH = {"Authorization": "Bearer " + TOKEN}


@pytest.fixture
def sessions(request):
    if request.node.get_closest_marker("database"):
        return request.getfixturevalue("db_sessions")
    return MagicMock()


@pytest.fixture
def client(sessions, monkeypatch):
    monkeypatch.setenv("OPERATOR_TOKEN", TOKEN)
    with TestClient(create_app(sessions)) as client:
        yield client


@pytest.mark.database
@pytest.mark.parametrize("status", ["pending", "running", "completed", "failed", "escalated"])
def test_run_snapshot_reads_saved_status(client, sessions, status):
    payload = SupportEvent.model_validate(build_event("Private message", "customer_17"))
    with sessions() as session:
        receipt = save_event(session, "run-route-test", payload)
    with sessions() as session, session.begin():
        run = session.get(Run, receipt.run_id)
        run.status = status
        created_at = run.created_at
    response = client.get(f"/runs/{receipt.run_id}", headers=AUTH)
    assert response.status_code == 200
    snapshot = response.json()
    assert set(snapshot) == {"run_id", "status", "created_at"}
    assert snapshot["run_id"] == str(receipt.run_id)
    assert snapshot["status"] == status
    assert datetime.fromisoformat(snapshot["created_at"].replace("Z", "+00:00")) == created_at


@pytest.mark.database
def test_unknown_run_returns_404(client):
    response = client.get(f"/runs/{uuid4()}", headers=AUTH)
    assert response.status_code == 404
    assert response.json() == {"detail": "Run not found"}


@pytest.mark.parametrize(
    "authorization", [None, "Bearer wrong", "Basic credentials", "Bearer", "Bearer café"]
)
def test_invalid_operator_credentials_do_not_open_database(client, sessions, authorization):
    headers = {} if authorization is None else {"Authorization": authorization.encode("utf-8")}
    response = client.get(f"/runs/{uuid4()}", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    sessions.assert_not_called()


def test_invalid_run_uuid_returns_422(client, sessions):
    response = client.get("/runs/invalid", headers=AUTH)
    assert response.status_code == 422
    sessions.return_value.__enter__.return_value.get.assert_not_called()


def test_database_failure_returns_503(client, sessions):
    sessions.return_value.__enter__.return_value.get.side_effect = SQLAlchemyError(
        "private details"
    )
    response = client.get(f"/runs/{uuid4()}", headers=AUTH)
    assert response.status_code == 503
    assert response.json() == {"detail": "Run storage unavailable. Retry later."}


def test_openapi_documents_operator_authentication(client):
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/runs/{run_id}"]["get"]
    assert operation["security"] == [{"HTTPBearer": []}]
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/RunSnapshot"
    }


def test_empty_operator_token_rejects_access(sessions, monkeypatch):
    monkeypatch.setenv("OPERATOR_TOKEN", "")
    with TestClient(create_app(sessions)) as client:
        response = client.get(f"/runs/{uuid4()}", headers=AUTH)
    assert response.status_code == 401
    sessions.assert_not_called()
