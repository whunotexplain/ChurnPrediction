"""
Слой доступа к данным — единственное место, где код формирует SQL-запросы
через ORM. Роуты (app/api/v1/router.py) ходят сюда, а не в сессию напрямую.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import PredictionRecord


def save_prediction(
    db: Session,
    input_payload: dict,
    churn_probability: float,
    churn_prediction: bool,
    model_version: str,
) -> PredictionRecord:
    record = PredictionRecord(
        input_payload=input_payload,
        churn_probability=churn_probability,
        churn_prediction=churn_prediction,
        model_version=model_version,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_predictions(db: Session, limit: int = 10) -> list[PredictionRecord]:
    stmt = select(PredictionRecord).order_by(PredictionRecord.created_at.desc()).limit(limit)
    return list(db.scalars(stmt).all())
