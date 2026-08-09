"""
ORM-модель истории предсказаний.

НОВОЕ (эта итерация): добавлены поля для A/B-тестирования —
ab_variant (какая модель отвечала) и actual_churn/outcome_recorded_at
(фактический исход, который приходит позже через POST /outcome).
Без actual_churn A/B-тест мог сравнивать только то, что предсказали
модели, а не то, кто из них оказался прав.
"""

import datetime
import uuid

from sqlalchemy import JSON, Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PredictionRecord(Base):
    __tablename__ = "predictions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.datetime.now(datetime.timezone.utc), index=True
    )

    input_payload: Mapped[dict] = mapped_column(JSON)

    churn_probability: Mapped[float] = mapped_column(Float)
    churn_prediction: Mapped[bool] = mapped_column(Boolean)
    model_version: Mapped[str] = mapped_column(String, default="v1.0.0")

    # Какая модель отвечала — "A" (champion) или "B" (challenger)
    ab_variant: Mapped[str] = mapped_column(String, default="A", index=True)

    # Заполняется позже, когда становится известен факт: ушёл клиент или нет.
    # NULL — значит исход ещё не наступил / не подтверждён.
    actual_churn: Mapped[bool | None] = mapped_column(Boolean, nullable=True, default=None)
    outcome_recorded_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, default=None
    )
