"""
БЫЛО: этот файл существовал, но был пустым — ни одного эндпоинта,
хотя main.py его подключал через app.include_router(router).
Из-за этого /api/v1/predict, /api/v1/health и /api/v1/predictions,
упомянутые в README и в тестах, на самом деле нигде не существовали.

СТАЛО: реализация трёх эндпоинтов.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.repository import list_predictions, save_prediction
from app.database.session import get_db
from app.ml.model import is_model_loaded, predict
from app.schemas.schemas import CustomerData, HealthResponse, PredictionListItem, PredictionResponse

router = APIRouter(prefix="/api/v1")


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)) -> HealthResponse:
    db_connected = True
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
    except Exception:
        db_connected = False

    return HealthResponse(status="ok", model_loaded=is_model_loaded(), db_connected=db_connected)


@router.post("/predict", response_model=PredictionResponse)
def predict_churn(payload: CustomerData, db: Session = Depends(get_db)) -> PredictionResponse:
    if not is_model_loaded():
        raise HTTPException(status_code=503, detail="Модель ещё не загружена")

    response, raw_input = predict(payload)

    save_prediction(
        db,
        input_payload=raw_input,
        churn_probability=response.churn_probability,
        churn_prediction=response.churn_prediction,
        model_version=response.model_version,
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
        )
        for r in records
    ]
