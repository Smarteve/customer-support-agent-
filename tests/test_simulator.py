import json

import httpx
import pytest

from support_engine import simulator
from support_engine.config import get_settings
from support_engine.schemas import SupportEvent
from support_engine.security import verify_signature


@pytest.mark.parametrize("status", ["completed", "escalated", "failed", "running"])
def test_simulator_sends_signed_event_and_checks_final_outcome(monkeypatch, capsys, status):
    calls = []
    settings = get_settings()

    def respond(request):
        calls.append(request)
        if request.method == "POST":
            assert request.url.path == "/webhooks/support"
            event = SupportEvent.model_validate_json(request.content)
            assert event.customer_id == "customer_17"
            assert event.message.text == "Where is ORD-1001?"
            assert verify_signature(
                settings.webhook_secret,
                request.headers["X-Webhook-Timestamp"],
                request.headers["X-Webhook-Signature"],
                request.content,
            )
            return httpx.Response(202, json={"run_id": "test-run"})
        assert request.headers["Authorization"] == "Bearer " + settings.operator_token
        if request.url.path.endswith("/events"):
            event_type = "run.started" if status == "running" else "run." + status
            event = {"sequence": 1, "type": event_type}
            assert request.headers["Accept"] == "text/event-stream"
            # SSE permits a comment heartbeat and multiple data lines per event.
            data = "\n".join("data: " + line for line in json.dumps(event, indent=2).splitlines())
            return httpx.Response(
                200,
                headers={"Content-Type": "text/event-stream"},
                text=": heartbeat\n\nid: 1\nevent: progress\n" + data + "\n\n",
            )
        return httpx.Response(200, json={"run_id": "test-run", "status": status})

    original_client = httpx.Client
    monkeypatch.setattr(
        simulator.httpx,
        "Client",
        lambda **kwargs: original_client(transport=httpx.MockTransport(respond), **kwargs),
    )
    if status == "failed":
        with pytest.raises(SystemExit) as error:
            simulator.run("http://localhost:8080", "Where is ORD-1001?", "customer_17", 10)
        assert error.value.code == 1
    elif status == "running":
        with pytest.raises(RuntimeError, match="before the run finished"):
            simulator.run("http://localhost:8080", "Where is ORD-1001?", "customer_17", 10)
    else:
        simulator.run("http://localhost:8080", "Where is ORD-1001?", "customer_17", 10)
    assert len(calls) == 3
    assert "HTTP 202" in capsys.readouterr().out


@pytest.mark.parametrize(
    "stream_status,expected_error",
    [(200, "text/event-stream"), (401, "HTTP 401")],
)
def test_simulator_reports_stream_errors(monkeypatch, capsys, stream_status, expected_error):
    def respond(request):
        if request.method == "POST":
            return httpx.Response(202, json={"run_id": "test-run"})
        return httpx.Response(stream_status, json={"detail": "Not an SSE response"})

    original_client = httpx.Client
    monkeypatch.setattr(
        simulator.httpx,
        "Client",
        lambda **kwargs: original_client(transport=httpx.MockTransport(respond), **kwargs),
    )
    monkeypatch.setattr("sys.argv", ["simulator"])
    with pytest.raises(SystemExit) as error:
        simulator.main()
    assert error.value.code == 1
    assert expected_error in capsys.readouterr().err
