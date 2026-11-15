"""Authenticate, validate, and commit an event and its pending run."""

import logging
import os
from contextlib import asynccontextmanager
from typing import Annotated

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from support_engine.database import make_engine
from support_engine.repository import EventConflict, save_event
from support_engine.schemas import SupportEvent, WebhookReceipt
from support_engine.security import verify_signature

logger = logging.getLogger(__name__)


def create_app(sessions: sessionmaker | None = None) -> FastAPI:
    load_dotenv()
    key_id = os.environ.get("WEBHOOK_KEY_ID", "demo")
    secret = os.environ.get("WEBHOOK_SECRET", "local-webhook-secret-change-me")
    engine = make_engine() if sessions is None else None
    sessions = sessions or sessionmaker(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        if engine is not None:
            engine.dispose()

    app = FastAPI(title="Support webhook receiver", version="0.1.0", lifespan=lifespan)

    def database_session():
        with sessions() as session:
            yield session

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
            "Save a signed customer event and a pending run in one transaction. "
            "Return HTTP 200 after commit. Repeated matching events return the same run. "
            "Different content under the same event ID returns HTTP 409. "
            "The run is not queued; Redis and worker execution are later steps."
        ),
    )
    def receive_support_event(
        event: SupportEvent, session: Annotated[Session, Depends(database_session)]
    ) -> WebhookReceipt:
        try:
            return save_event(session, key_id, event)
        except EventConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SQLAlchemyError as exc:
            logger.error("event_store_failed", extra={"category": type(exc).__name__})
            raise HTTPException(
                status_code=503, detail="Event storage failed. Retry with the same event ID."
            ) from exc

    return app


app = create_app()
