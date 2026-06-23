from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_external_id: Mapped[str | None] = mapped_column(
        Text,
        unique=True,
        nullable=True,
        index=True,
    )
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    segment: Mapped[str | None] = mapped_column(Text, nullable=True)
    monthly_spend: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    tenure: Mapped[int | None] = mapped_column(Integer, nullable=True)
    monthly_charges: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    total_charges: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    contract_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    support_tickets: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    late_payments: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    churn: Mapped[int | None] = mapped_column(Integer, nullable=True)
    support_ticket_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    unpaid_invoice_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )
    churn_probability: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    risk_score: Mapped[Decimal | None] = mapped_column(Numeric, nullable=True)
    risk_level: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
