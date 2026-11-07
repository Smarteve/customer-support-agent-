import hmac
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException

from support_engine.config import get_settings

app = FastAPI(title="Mock enterprise orders API")


@app.get("/health/live")
def live():
    return {"status": "ok", "synthetic": True}


@app.get("/orders/{order_id}")
def get_order(
    order_id: str,
    tenant_id: str,
    customer_id: str,
    x_service_token: Annotated[str | None, Header()] = None,
):
    settings = get_settings()
    if x_service_token is None or not hmac.compare_digest(
        x_service_token.encode(), settings.mock_service_token.encode()
    ):
        raise HTTPException(status_code=401, detail="Service token required")
    if tenant_id != settings.tenant_id or customer_id != "customer_17" or order_id != "ORD-1001":
        raise HTTPException(status_code=404, detail="Order not found")
    return {"order_id": order_id, "shipment_status": "in_transit", "synthetic": True}
