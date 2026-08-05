"""Асинхронная работа с PostgreSQL через SQLAlchemy 2.0."""
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, Float, Boolean, DateTime, JSON, Integer

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://churn_user:churn_pass@db:5432/churn_db"
)

# Создаём асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


class PredictionRecord(Base):
    """Таблица логов предсказаний."""

    __tablename__ = "predictions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = Column(String, nullable=True)
    churn_probability = Column(Float, nullable=False)
    churn_prediction = Column(Boolean, nullable=False)
    risk_segment = Column(String(20), nullable=False)
    top_features = Column(JSON, nullable=True)
    model_version = Column(String(20), nullable=False)
    raw_input = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


async def init_db() -> None:
    """Создание таблиц при старте (если их нет)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def save_prediction(
    session: AsyncSession,
    customer_id: Optional[str],
    churn_probability: float,
    churn_prediction: bool,
    risk_segment: str,
    top_features: dict,
    model_version: str,
    raw_input: dict,
) -> PredictionRecord:
    """Сохраняет предсказание в БД."""
    record = PredictionRecord(
        customer_id=customer_id,
        churn_probability=churn_probability,
        churn_prediction=churn_prediction,
        risk_segment=risk_segment,
        top_features=top_features,
        model_version=model_version,
        raw_input=raw_input,
    )
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return record


async def get_recent_predictions(session: AsyncSession, limit: int = 10) -> List[PredictionRecord]:
    """Возвращает последние N предсказаний."""
    from sqlalchemy import select
    result = await session.execute(
        select(PredictionRecord).order_by(PredictionRecord.created_at.desc()).limit(limit)
    )
    return result.scalars().all()
