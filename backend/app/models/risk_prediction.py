from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import DateTime, Integer, Numeric, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class RiskPrediction(Base):
    __tablename__ = "risk_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    customer_id: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    churn_probability: Mapped[Decimal] = mapped_column(Numeric, nullable=False)
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False)
    risk_level: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    reasons: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    recommended_actions: Mapped[list[str]] = mapped_column(
        JSONB,
        default=list,
        nullable=False,
    )
    model_version: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        index=True,
    )
