from __future__ import annotations

from pydantic import BaseModel


class OrderStatusOut(BaseModel):
    order_id: str
    status: str
    payment_status: str
