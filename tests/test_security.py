import json
import time

import pytest
from pydantic import ValidationError

from support_engine.schemas import SupportEvent
from support_engine.security import signature, verify_signature

SECRET = "test-webhook-secret-at-least-16"


def test_signature_binds_raw_body_and_timestamp():
    body = b'{"event_id":"one"}'
    timestamp = str(int(time.time()))
    signed = signature(SECRET, timestamp, body)
    assert verify_signature(SECRET, timestamp, signed, body)
    assert not verify_signature(SECRET, timestamp, signed, body + b" ")
    assert not verify_signature("a-different-secret", timestamp, signed, body)
    assert not verify_signature(SECRET, "not-a-time", signed, body)
    assert not verify_signature(SECRET, timestamp, "non-ascii-\u00e9", body)


@pytest.mark.parametrize("offset", [-301, 301])
def test_rejects_expired_and_future_signatures(offset):
    timestamp = str(int(time.time()) + offset)
    body = b"{}"
    assert not verify_signature(SECRET, timestamp, signature(SECRET, timestamp, body), body)


def sample():
    return {
        "schema_version": 1,
        "event_id": "sample",
        "occurred_at": "2026-11-07T12:00:00Z",
        "source": "simulator",
        "conversation_id": "conversation",
        "customer_id": "customer_17",
        "message": {"text": "Where is ORD-1001?"},
    }


def test_payload_identity_ignores_json_whitespace_but_not_changed_content():
    event = SupportEvent.model_validate(sample())
    reformatted = SupportEvent.model_validate_json(json.dumps(sample(), indent=4))
    assert event.payload_hash() == reformatted.payload_hash()
    changed = sample()
    changed["message"]["text"] = "Different request"
    assert event.payload_hash() != SupportEvent.model_validate(changed).payload_hash()


def test_customer_cannot_inject_tenant_or_approval_fields():
    payload = sample()
    payload["tenant_id"] = "another-company"
    payload["approved"] = True
    with pytest.raises(ValidationError):
        SupportEvent.model_validate(payload)
