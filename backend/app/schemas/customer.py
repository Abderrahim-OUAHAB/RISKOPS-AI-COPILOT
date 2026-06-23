from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CustomerBase(BaseModel):
    customer_external_id: str | None = None
    name: str | None = None
    segment: str | None = None
    monthly_spend: Decimal | None = None
    support_ticket_count: int = 0
    unpaid_invoice_count: int = 0
    churn_probability: Decimal | None = None
    risk_score: Decimal | None = None


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
