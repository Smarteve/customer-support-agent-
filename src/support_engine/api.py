"""First receiver step: authenticate, validate, and acknowledge one event."""

import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request

from support_engine.schemas import SupportEvent, WebhookReceipt
from support_engine.security import verify_signature


def create_app() -> FastAPI:
    load_dotenv()
    key_id = os.environ.get("WEBHOOK_KEY_ID", "demo")
    secret = os.environ.get("WEBHOOK_SECRET", "local-webhook-secret-change-me")
    app = FastAPI(title="Support webhook receiver", version="0.1.0")

    async def verify_webhook(
        request: Request,
        supplied_key: Annotated[str | None, Header(alias="X-Webhook-Key-Id")] = None,
        timestamp: Annotated[str | None, Header(alias="X-Webhook-Timestamp")] = None,
        supplied_signature: Annotated[str | None, Header(alias="X-Webhook-Signature")] = None,
    ) -> None:
        if (
            supplied_key != key_id
            or timestamp is None
            or supplied_signature is None
            or not verify_signature(secret, timestamp, supplied_signature, await request.body())
        ):
            raise HTTPException(status_code=401, detail="Invalid webhook credentials")

    @app.post(
        "/webhooks/support",
        response_model=WebhookReceipt,
        dependencies=[Depends(verify_webhook)],
        description=(
            "Validate a signed customer event and return a receipt. "
            "This step does not save the event, create a run, or submit work. "
            "Repeated events are acknowledged again; deduplication needs later storage."
        ),
    )
    async def receive_support_event(event: SupportEvent) -> WebhookReceipt:
        return WebhookReceipt(event_id=event.event_id)

    return app


app = create_app()
