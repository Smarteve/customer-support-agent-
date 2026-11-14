import argparse
import json
import os
import time
from datetime import UTC, datetime
from uuid import uuid4

import httpx
from httpx_sse import SSEError, connect_sse

from support_engine.config import get_settings
from support_engine.security import signature


def build_event(message: str, customer_id: str) -> dict:
    """Create one customer event. The worker creates the progress events."""
    return {
        "schema_version": 1,
        "event_id": "demo_" + uuid4().hex,
        "event_type": "support.message_received",
        "occurred_at": datetime.now(UTC).isoformat(),
        "source": "simulator",
        "conversation_id": "demo_conversation_" + uuid4().hex,
        "customer_id": customer_id,
        "message": {"text": message},
    }


def run(base_url: str, message: str, customer_id: str, timeout: float) -> None:
    settings = get_settings()
    event = build_event(message, customer_id)
    # Sign and send the same bytes. Reserializing later can change the signature.
    body = json.dumps(event).encode()
    timestamp = str(int(time.time()))
    print(f"POST {base_url.rstrip('/')}/webhooks/support", flush=True)
    print(f"Event: {event['event_id']}", flush=True)
    with httpx.Client(base_url=base_url, timeout=timeout) as client:
        response = client.post(
            "/webhooks/support",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Key-Id": settings.webhook_key_id,
                "X-Webhook-Timestamp": timestamp,
                "X-Webhook-Signature": signature(settings.webhook_secret, timestamp, body),
            },
        )
        response.raise_for_status()
        print(f"HTTP {response.status_code}", flush=True)
        run_id = response.json()["run_id"]
        print(f"Run: {run_id} (deterministic fake agent; synthetic data)", flush=True)
        headers = {"Authorization": "Bearer " + settings.operator_token}
        with connect_sse(client, "GET", f"/runs/{run_id}/events", headers=headers) as source:
            if source.response.is_error:
                source.response.read()
            source.response.raise_for_status()
            for sse in source.iter_sse():
                event = sse.json()
                if "sequence" not in event:
                    continue
                print(f"{event['sequence']:02d} {event['type']}", flush=True)
                if event["type"] in {"run.completed", "run.failed", "run.escalated"}:
                    break
        result = client.get(f"/runs/{run_id}", headers=headers)
        result.raise_for_status()
        print(json.dumps(result.json(), indent=2))
        status = result.json()["status"]
        if status == "failed":
            raise SystemExit(1)
        if status not in {"completed", "escalated"}:
            raise RuntimeError("The stream ended before the run finished. Check the saved run ID.")


def main():
    parser = argparse.ArgumentParser(description="Send one signed synthetic customer event")
    parser.add_argument("--message", default="Where is order ORD-1001?")
    parser.add_argument("--customer-id", default="customer_17")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("API_BASE_URL", "http://localhost:8080"),
        help="FastAPI URL (default: API_BASE_URL or http://localhost:8080)",
    )
    parser.add_argument("--timeout", type=float, default=30, help="Network timeout in seconds")
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    try:
        run(args.base_url, args.message, args.customer_id, args.timeout)
    except httpx.HTTPStatusError as exc:
        parser.exit(1, f"HTTP {exc.response.status_code}: {exc.response.text}\n")
    except (httpx.RequestError, SSEError, ValueError, KeyError, RuntimeError) as exc:
        parser.exit(1, f"Simulator failed: {exc}\n")


if __name__ == "__main__":
    main()
