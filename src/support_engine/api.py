import asyncio
import hmac
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.orm import Session

from support_engine import repository
from support_engine.config import get_settings
from support_engine.database import get_engine
from support_engine.messaging import enqueue_run, publish_notice, redis_connection
from support_engine.schemas import SupportEvent
from support_engine.security import verify_signature
from support_engine.streaming import RunStream

app = FastAPI(title="Customer Support Engine", version="0.1.0")


def operator(authorization: Annotated[str | None, Header()] = None) -> str:
    expected = "Bearer " + get_settings().operator_token
    if authorization is None or not hmac.compare_digest(authorization.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Operator token required")
    return get_settings().tenant_id


@app.get("/health/live")
def live():
    return {"status": "ok", "mode": "deterministic_fake_agent"}


@app.get("/health/ready")
def ready():
    try:
        with Session(get_engine()) as session:
            session.execute(text("SELECT 1"))
        with redis_connection() as connection:
            connection.ping()
    except Exception:
        raise HTTPException(status_code=503, detail="Dependency unavailable") from None
    return {"status": "ready"}


def submit(run_id: str) -> None:
    try:
        enqueue_run(run_id)
    except RedisError:
        repository.mark_submission(run_id, "queue_unavailable")
        raise HTTPException(
            status_code=503,
            detail={"reason": "queue_unavailable", "run_id": run_id, "retryable": True},
        ) from None
    repository.mark_submission(run_id)


@app.post("/webhooks/support", status_code=202)
async def webhook(request: Request):
    settings = get_settings()
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 65536:
            raise HTTPException(status_code=413, detail="Webhook body exceeds 64 KiB")
    key_id = request.headers.get("X-Webhook-Key-Id", "")
    timestamp = request.headers.get("X-Webhook-Timestamp", "")
    supplied = request.headers.get("X-Webhook-Signature", "")
    if key_id != settings.webhook_key_id or not verify_signature(
        settings.webhook_secret, timestamp, supplied, bytes(body), settings.webhook_window_seconds
    ):
        raise HTTPException(status_code=401, detail="Invalid webhook signature or timestamp")
    try:
        event = SupportEvent.model_validate_json(body)
    except ValidationError:
        raise HTTPException(status_code=422, detail="Invalid support event schema") from None
    try:
        run, duplicate, notice = await asyncio.to_thread(
            repository.create_run, settings.tenant_id, event
        )
    except repository.EventConflict:
        raise HTTPException(status_code=409, detail="Event ID has different content") from None
    if notice:
        await asyncio.to_thread(publish_notice, notice)
    if run["status"] == "pending":
        await asyncio.to_thread(submit, run["run_id"])
    return {"run_id": run["run_id"], "duplicate": duplicate, "status": run["status"]}


@app.get("/runs/{run_id}")
def read_run(run_id: str, tenant: Annotated[str, Depends(operator)]):
    run = repository.get_run(run_id, tenant)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@app.post("/runs/{run_id}/retry", status_code=202)
def retry_run(run_id: str, tenant: Annotated[str, Depends(operator)]):
    try:
        notice = repository.prepare_retry(run_id, tenant)
    except LookupError:
        raise HTTPException(status_code=404, detail="Run not found") from None
    except repository.StateConflict:
        raise HTTPException(status_code=409, detail="Run is active or finished") from None
    publish_notice(notice)
    submit(run_id)
    return {"run_id": run_id, "status": "pending"}


@app.get("/runs/{run_id}/events")
async def stream_run(
    run_id: str,
    request: Request,
    tenant: Annotated[str, Depends(operator)],
    last_event_id: Annotated[str | None, Header()] = None,
):
    run = await asyncio.to_thread(repository.get_run, run_id, tenant)
    if run is None:
        raise HTTPException(status_code=404, detail="Run not found")
    try:
        cursor = int(last_event_id or "0")
        if not 0 <= cursor <= run["last_sequence"]:
            raise ValueError
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid Last-Event-ID") from None
    stream = RunStream(run_id, tenant, cursor)
    try:
        await stream.prepare()
    except RedisError:
        return JSONResponse(status_code=503, content={"detail": "Live stream unavailable"})
    return StreamingResponse(
        stream.events(request),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
