"""The customer event and the receiver's acknowledgement."""

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints

Identifier = Annotated[str, StringConstraints(min_length=1, max_length=128, pattern=r"^\S+$")]


class CustomerMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=10_000, pattern=r"\S")


class SupportEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: int = Field(strict=True, ge=1, le=1)
    event_id: Identifier
    event_type: Literal["support.message_received"]
    occurred_at: AwareDatetime
    source: Identifier
    conversation_id: Identifier
    customer_id: Identifier
    message: CustomerMessage


class WebhookReceipt(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: Identifier
    status: Literal["received"] = "received"
