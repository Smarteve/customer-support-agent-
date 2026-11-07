import argparse
import json
import os
import time
from datetime import UTC, datetime
from uuid import uuid4

import httpx

from support_engine.config import get_settings
from support_engine.security import signature


def main():
    parser = argparse.ArgumentParser(description="Send a signed synthetic order question")
    parser.add_argument("--message", default="Where is order ORD-1001?")
    parser.add_argument("--customer-id", default="customer_17")
    args = parser.parse_args()
    settings = get_settings()
    base = os.environ.get("API_BASE_URL", "http://api:8000")
    event = {
        "schema_version": 1,
        "event_id": "demo_" + uuid4().hex,
        "event_type": "support.message_received",
        "occurred_at": datetime.now(UTC).isoformat(),
        "source": "simulator",
        "conversation_id": "demo_conversation_" + uuid4().hex,
        "customer_id": args.customer_id,
        "message": {"text": args.message},
    }
    body = json.dumps(event).encode()
    timestamp = str(int(time.time()))
    with httpx.Client(base_url=base, timeout=30) as client:
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
        run_id = response.json()["run_id"]
        print(f"Run: {run_id} (deterministic fake agent; synthetic data)", flush=True)
        headers = {"Authorization": "Bearer " + settings.operator_token}
        with client.stream("GET", f"/runs/{run_id}/events", headers=headers) as stream:
            stream.raise_for_status()
            for line in stream.iter_lines():
                if not line.startswith("data: "):
                    continue
                event = json.loads(line[6:])
                if "sequence" not in event:
                    continue
                print(f"{event['sequence']:02d} {event['type']}", flush=True)
                if event["type"] in {"run.completed", "run.failed", "run.escalated"}:
                    break
        result = client.get(f"/runs/{run_id}", headers=headers)
        result.raise_for_status()
        print(json.dumps(result.json(), indent=2))
        if result.json()["status"] == "failed":
            raise SystemExit(1)


if __name__ == "__main__":
    main()
