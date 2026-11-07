import asyncio
import re

import httpx

from support_engine import repository
from support_engine.config import get_settings
from support_engine.messaging import publish_notice


async def execute(run_id: str) -> None:
    claimed = await asyncio.to_thread(repository.claim_run, run_id)
    if claimed is None:
        return  # Duplicate delivery cannot start an active or finished logical run.
    run, owner, notice = claimed
    await asyncio.to_thread(publish_notice, notice)
    settings = get_settings()

    async def step(event_type: str, details: dict, **changes):
        notice = await asyncio.to_thread(
            repository.record_step, run_id, event_type, details, owner=owner, **changes
        )
        await asyncio.to_thread(publish_notice, notice)
        if settings.demo_step_delay_seconds:
            await asyncio.sleep(settings.demo_step_delay_seconds)

    try:
        payload = run["input"]
        await step("model.requested", {"provider": "fake", "paid_api_call": False})
        match = re.search(r"\bORD-\d+\b", payload["message"]["text"])
        if match is None:
            await step(
                "run.escalated",
                {"reason": "demo_requires_order_id"},
                status="escalated",
                response="Please provide an order ID such as ORD-1001.",
            )
            return
        order_id = match.group()
        await step("model.completed", {"proposed_tool": "get_order"})
        await step("tool.requested", {"tool": "get_order", "order_id": order_id})
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                settings.mock_api_url + f"/orders/{order_id}",
                params={"tenant_id": run["tenant_id"], "customer_id": payload["customer_id"]},
                headers={"X-Service-Token": settings.mock_service_token},
            )
        if response.status_code == 404:
            await step(
                "run.escalated",
                {"reason": "order_unavailable_for_customer"},
                status="escalated",
                response="This order is unavailable for the verified customer.",
            )
            return
        response.raise_for_status()
        order = response.json()
        await step("tool.completed", {"tool": "get_order", "result": order})
        answer = f"Order {order_id} is {order['shipment_status'].replace('_', ' ')}."
        await step("response.created", {"response": answer}, response=answer)
        await step("run.completed", {"outcome": "answered", "provider": "fake"}, status="completed")
    except repository.StateConflict:
        raise
    except Exception as exc:
        await step(
            "run.failed",
            {"category": type(exc).__name__},
            status="failed",
            error=type(exc).__name__,
        )
        raise


def process_run(run_id: str) -> None:
    asyncio.run(execute(run_id))
