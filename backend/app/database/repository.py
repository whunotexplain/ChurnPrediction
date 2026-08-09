"""
Слой доступа к данным — единственное место, где код формирует SQL-запросы
через ORM. Роуты (app/api/v1/router.py) ходят сюда, а не в сессию напрямую.
"""

import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import PredictionRecord


def save_prediction(
    db: Session,
    prediction_id: str,
    input_payload: dict,
    churn_probability: float,
    churn_prediction: bool,
    model_version: str,
    ab_variant: str = "A",
) -> PredictionRecord:
    """
    БЫЛО: id записи генерировался здесь заново (PredictionRecord.id имеет
    default=uuid4), а PredictionResponse.prediction_id, который видит
    клиент, генерировался отдельно в app/ml/model.py — двумя независимыми
    вызовами uuid.uuid4(). Они никогда не совпадали, поэтому POST /outcome
    с prediction_id из ответа /predict не находил запись в БД (всегда 404).

    СТАЛО: id передаётся явно — тот же самый, что ушёл клиенту в ответе.
    """
    record = PredictionRecord(
        id=prediction_id,
        input_payload=input_payload,
        churn_probability=churn_probability,
        churn_prediction=churn_prediction,
        model_version=model_version,
        ab_variant=ab_variant,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def list_predictions(db: Session, limit: int = 10) -> list[PredictionRecord]:
    stmt = select(PredictionRecord).order_by(PredictionRecord.created_at.desc()).limit(limit)
    return list(db.scalars(stmt).all())


def get_prediction(db: Session, prediction_id: str) -> PredictionRecord | None:
    return db.get(PredictionRecord, prediction_id)


def record_outcome(db: Session, prediction_id: str, actual_churn: bool) -> PredictionRecord | None:
    """Записывает фактический исход по ранее сделанному предсказанию.
    Идемпотентно: повторный вызов с тем же prediction_id перезаписывает
    исход (например, если бизнес прислал уточнённые данные) — но не
    создаёт дублей."""
    record = db.get(PredictionRecord, prediction_id)
    if record is None:
        return None

    record.actual_churn = actual_churn
    record.outcome_recorded_at = datetime.datetime.now(datetime.timezone.utc)
    db.commit()
    db.refresh(record)
    return record


def get_variant_accuracy(db: Session, variant: str) -> tuple[int, int]:
    """Возвращает (n, successes) — сколько предсказаний с известным
    исходом накопилось у варианта и сколько из них оказались верными.
    Верное предсказание = churn_prediction совпал с actual_churn.
    Только записи с уже подтверждённым исходом (actual_churn IS NOT NULL)
    участвуют — иначе тест был бы искажён "недозревшими" предсказаниями."""
    stmt = select(PredictionRecord).where(
        PredictionRecord.ab_variant == variant,
        PredictionRecord.actual_churn.is_not(None),
    )
    records = db.scalars(stmt).all()
    n = len(records)
    successes = sum(1 for r in records if r.churn_prediction == r.actual_churn)
    return n, successes
