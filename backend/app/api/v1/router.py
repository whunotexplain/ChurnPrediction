"""
БЫЛО: этот файл существовал, но был пустым — ни одного эндпоинта.

СТАЛО: /health, /predict, /predictions — плюс в этой итерации:
/outcome (фиксация реального исхода) и /ab-test-results (статистическая
значимость разницы между вариантом A и B).
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.ab_testing import assign_variant
from app.core.config import settings
from app.core.statistics import compute_proportion_stats, two_proportion_z_test
from app.database.repository import (
    get_variant_accuracy,
    list_predictions,
    record_outcome,
    save_prediction,
)
from app.database.session import get_db
from app.ml.model import is_ab_test_active, is_model_loaded, predict
from app.schemas.schemas import (
    ABTestResultResponse,
    CustomerData,
    HealthResponse,
    OutcomeSubmission,
    PredictionListItem,
    PredictionResponse,
    VariantStats,
)

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    db_connected = True
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_connected = False

    return HealthResponse(
        status="ok", model_loaded=is_model_loaded(), ab_test_active=is_ab_test_active(), db_connected=db_connected
    )


@router.post("/predict", response_model=PredictionResponse)
def predict_churn(payload: CustomerData, db: Session = Depends(get_db)) -> PredictionResponse:
    if not is_model_loaded():
        raise HTTPException(status_code=503, detail="Модель ещё не загружена")

    variant = assign_variant(payload.customer_id)
    response, raw_input, variant = predict(payload, variant=variant)

    save_prediction(
        db,
        prediction_id=response.prediction_id,
        input_payload=raw_input,
        churn_probability=response.churn_probability,
        churn_prediction=response.churn_prediction,
        model_version=response.model_version,
        ab_variant=variant,
    )
    return response


@router.get("/predictions", response_model=list[PredictionListItem])
def get_predictions(limit: int = 10, db: Session = Depends(get_db)) -> list[PredictionListItem]:
    records = list_predictions(db, limit=limit)
    return [
        PredictionListItem(
            id=r.id,
            created_at=r.created_at.isoformat(),
            churn_probability=r.churn_probability,
            churn_prediction=r.churn_prediction,
            model_version=r.model_version,
            ab_variant=r.ab_variant,
        )
        for r in records
    ]


@router.post("/outcome")
def submit_outcome(payload: OutcomeSubmission, db: Session = Depends(get_db)) -> dict:
    """Бизнес присылает сюда, что произошло на самом деле — обычно
    через какое-то время после /predict (например, когда истёк
    биллинг-период и стало видно, продлил клиент подписку или ушёл)."""
    record = record_outcome(db, payload.prediction_id, payload.actual_churn)
    if record is None:
        raise HTTPException(status_code=404, detail="prediction_id не найден")
    return {"status": "ok", "prediction_id": record.id, "actual_churn": record.actual_churn}


@router.get("/ab-test-results", response_model=ABTestResultResponse)
def ab_test_results(db: Session = Depends(get_db)) -> ABTestResultResponse:
    """
    Двухвыборочный z-тест: сравнивает accuracy варианта A и варианта B
    среди предсказаний с уже известным исходом (см. app/core/statistics.py
    за подробным объяснением формул).

    Если исходов ещё мало — тест всё равно посчитается, но результат
    может быть недостоверным (широкий доверительный интервал,
    p_value близко к 1 даже при реальной разнице). Ориентир — n >= 30-50
    на группу для первого осмысленного взгляда, и заранее посчитанный
    через required_sample_size() размер для финального решения.
    """
    n_a, s_a = get_variant_accuracy(db, "A")
    n_b, s_b = get_variant_accuracy(db, "B")

    if n_a == 0 or n_b == 0:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Недостаточно данных с известным исходом: variant A={n_a}, variant B={n_b}. "
                "Пришли исходы через POST /outcome для обеих групп."
            ),
        )

    a_stats = compute_proportion_stats(n_a, s_a)
    b_stats = compute_proportion_stats(n_b, s_b)
    result = two_proportion_z_test(a_stats, b_stats, alpha=settings.AB_ALPHA)

    if result.significant:
        better = "B" if result.diff > 0 else "A"
        message = (
            f"Различие статистически значимо (p={result.p_value:.4f} < {result.alpha}). "
            f"Вариант {better} точнее."
        )
    else:
        message = (
            f"Различие НЕ значимо (p={result.p_value:.4f} >= {result.alpha}) — "
            f"либо моделей действительно не отличаются, либо данных пока мало "
            f"(n_A={n_a}, n_B={n_b}) для обнаружения разницы такого размера."
        )

    return ABTestResultResponse(
        variant_a=VariantStats(n=a_stats.n, accuracy=round(a_stats.p, 4)),
        variant_b=VariantStats(n=b_stats.n, accuracy=round(b_stats.p, 4)),
        diff=round(result.diff, 4),
        z_stat=round(result.z_stat, 4),
        p_value=round(result.p_value, 6),
        significant=result.significant,
        confidence_interval=(round(result.ci_low, 4), round(result.ci_high, 4)),
        alpha=result.alpha,
        message=message,
    )
