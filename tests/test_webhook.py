import hashlib
import hmac
import json
import time

import pytest
from fastapi.testclient import TestClient

from support_engine.api import create_app
from support_engine.simulator import build_event

SECRET = "test-webhook-secret"


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("WEBHOOK_KEY_ID", "test")
    monkeypatch.setenv("WEBHOOK_SECRET", SECRET)
    with TestClient(create_app()) as client:
        yield client


def headers(body: bytes, timestamp: str | None = None) -> dict:
    timestamp = timestamp or str(int(time.time()))
    digest = hmac.new(SECRET.encode(), timestamp.encode() + b"." + body, hashlib.sha256)
    return {
        "Content-Type": "application/json",
        "X-Webhook-Key-Id": "test",
        "X-Webhook-Timestamp": timestamp,
        "X-Webhook-Signature": "sha256=" + digest.hexdigest(),
    }


def test_signed_event_returns_a_receipt_without_a_run(client):
    event = build_event("Where is ORD-1001?", "customer_17")
    body = json.dumps(event).encode()
    response = client.post("/webhooks/support", content=body, headers=headers(body))
    assert response.status_code == 200
    assert response.json() == {"event_id": event["event_id"], "status": "received"}
    # There is no storage yet. Repeated events receive the same acknowledgement.
    repeat = client.post("/webhooks/support", content=body, headers=headers(body))
    assert repeat.json() == response.json()


@pytest.mark.parametrize(
    "change",
    [
        {"schema_version": "1"},
        {"schema_version": True},
        {"event_type": "run.started"},
        {"occurred_at": "2026-11-14T12:00:00"},
        {"event_id": ""},
        {"customer_id": 17},
        {"message": {"text": "   "}},
        {"message": {"text": "Hello", "approved": True}},
        {"message": {}},
        {"tenant_id": "customer-controlled"},
    ],
)
def test_invalid_signed_event_is_rejected(client, change):
    event = build_event("Where is ORD-1001?", "customer_17")
    event.update(change)
    body = json.dumps(event).encode()
    response = client.post("/webhooks/support", content=body, headers=headers(body))
    assert response.status_code == 422


@pytest.mark.parametrize("offset", [-301, 301])
def test_expired_and_future_request_signatures_are_rejected(client, offset):
    body = json.dumps(build_event("Hello", "customer_17")).encode()
    timestamp = str(int(time.time()) + offset)
    response = client.post("/webhooks/support", content=body, headers=headers(body, timestamp))
    assert response.status_code == 401


@pytest.mark.parametrize("problem", ["missing", "wrong-key", "invalid-time", "tampered-body"])
def test_bad_webhook_credentials_are_rejected(client, problem):
    body = json.dumps(build_event("Hello", "customer_17")).encode()
    signed = headers(body)
    if problem == "missing":
        signed = {"Content-Type": "application/json"}
    elif problem == "wrong-key":
        signed["X-Webhook-Key-Id"] = "unknown"
    elif problem == "invalid-time":
        signed["X-Webhook-Timestamp"] = "not-a-timestamp"
    else:
        body += b" "  # Same parsed JSON, but the signed bytes changed.
    response = client.post("/webhooks/support", content=body, headers=signed)
    assert response.status_code == 401


def test_malformed_signed_json_is_rejected(client):
    body = b'{"event_id":'
    response = client.post("/webhooks/support", content=body, headers=headers(body))
    assert response.status_code == 422


def test_openapi_contains_request_and_response_schemas(client):
    schema = client.get("/openapi.json").json()
    operation = schema["paths"]["/webhooks/support"]["post"]
    assert operation["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/SupportEvent"
    }
    assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/WebhookReceipt"
    }
