"""Receive signed events and provide authenticated run snapshots."""

import asyncio
import hmac
import logging
import os
from contextlib import asynccontextmanager, suppress
from typing import Annotated
from uuid import UUID

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from redis.exceptions import RedisError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from support_engine.database import Run, make_engine
from support_engine.messaging import QueueSubmissionError, enqueue_run
from support_engine.repository import EventConflict, save_event
from support_engine.schemas import RunSnapshot, SupportEvent, WebhookReceipt
from support_engine.security import verify_signature
from support_engine.subscriber import listen_for_run_notices

logger = logging.getLogger(__name__)


def create_app(sessions: sessionmaker | None = None) -> FastAPI:
    load_dotenv()
    key_id = os.environ.get("WEBHOOK_KEY_ID", "demo")
    secret = os.environ.get("WEBHOOK_SECRET", "local-webhook-secret-change-me")
    operator_token = os.environ.get("OPERATOR_TOKEN", "local-operator-token-change-me")
    bearer = HTTPBearer(auto_error=False)
    engine = make_engine() if sessions is None else None
    sessions = sessions or sessionmaker(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        logging.basicConfig(level=logging.INFO)
        subscriber = asyncio.create_task(listen_for_run_notices())
        try:
            yield
        finally:
            subscriber.cancel()
            try:
                with suppress(asyncio.CancelledError):
                    await subscriber
            finally:
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

    def verify_operator(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
    ) -> None:
        if (
            not operator_token
            or credentials is None
            or not hmac.compare_digest(credentials.credentials.encode(), operator_token.encode())
        ):
            raise HTTPException(
                status_code=401,
                detail="Invalid operator credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

    @app.get(
        "/runs/{run_id}",
        response_model=RunSnapshot,
        dependencies=[Depends(verify_operator)],
        description="Read the saved run status. Requires an operator bearer token.",
    )
    def read_run(
        run_id: UUID,
        session: Annotated[Session, Depends(database_session)],
    ) -> RunSnapshot:
        try:
            run = session.get(Run, run_id)
            if run is None:
                raise HTTPException(status_code=404, detail="Run not found")
            return RunSnapshot(run_id=run.id, status=run.status, created_at=run.created_at)
        except SQLAlchemyError as exc:
            logger.error("run_read_failed", extra={"category": type(exc).__name__})
            raise HTTPException(
                status_code=503, detail="Run storage unavailable. Retry later."
            ) from exc

    @app.post(
        "/webhooks/support",
        response_model=WebhookReceipt,
        response_model_exclude_none=True,
        status_code=202,
        dependencies=[Depends(verify_webhook)],
        description=(
            "Save a signed customer event and a pending run in one transaction. "
            "Submit the saved run ID to RQ after commit, then return HTTP 202. "
            "Repeated matching events reuse the run and queued job. "
            "Different content under the same event ID returns HTTP 409. "
            "A queue failure returns HTTP 503 with the saved run ID. "
            "A separate worker processes the queued run."
        ),
    )
    def receive_support_event(
        event: SupportEvent,
        response: Response,
        session: Annotated[Session, Depends(database_session)],
    ) -> WebhookReceipt:
        try:
            receipt = save_event(session, key_id, event)
        except EventConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except SQLAlchemyError as exc:
            logger.error("event_store_failed", extra={"category": type(exc).__name__})
            raise HTTPException(
                status_code=503, detail="Event storage failed. Retry with the same event ID."
            ) from exc

        if receipt.run_status != "pending":
            response.status_code = 200
            return receipt
        try:
            job_id = enqueue_run(str(receipt.run_id))
        except (RedisError, QueueSubmissionError) as exc:
            logger.error("queue_submission_unconfirmed", extra={"category": type(exc).__name__})
            raise HTTPException(
                status_code=503,
                detail={
                    "message": (
                        "Event saved, but queue submission is unconfirmed. "
                        "Retry the same event ID and content."
                    ),
                    **receipt.model_dump(mode="json", exclude_none=True),
                },
            ) from exc
        return receipt.model_copy(update={"status": "queued", "job_id": job_id})

    return app


app = create_app()
