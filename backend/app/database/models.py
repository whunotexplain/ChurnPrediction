"""
ORM-модель истории предсказаний.

НОВОЕ: раньше в репозитории было три источника правды по схеме этой
таблицы, и все три расходились между собой:
  - app/database/sql/init.sql (customer_id, risk_segment, top_features JSONB...)
  - alembic/001_initial.py (id INTEGER, prediction INTEGER, probability FLOAT...)
  - ничего в коде реально эту таблицу не описывало и не использовало
Теперь ORM-модель здесь — единственный источник правды, alembic-миграция
и init.sql приведены в соответствие с ней.
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

    # Сырые входные данные клиента — JSON, чтобы не заводить по колонке
    # на каждый признак датасета (их 19+)
    input_payload: Mapped[dict] = mapped_column(JSON)

    churn_probability: Mapped[float] = mapped_column(Float)
    churn_prediction: Mapped[bool] = mapped_column(Boolean)
    model_version: Mapped[str] = mapped_column(String, default="v1.0.0")
