import os
from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database.database import init_db, AsyncSessionLocal, save_prediction, get_recent_predictions
from backend.app.models.model import load_model, is_model_loaded, predict
from backend.app.schemas.schemas import (
    CustomerData,
    PredictionResponse,
    BatchPredictionRequest,
    BatchPredictionResponse,
    HealthResponse,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при старте и cleanup при остановке."""
    # Startup
    await init_db()
    try:
        load_model()
        print("✅ Модель загружена успешно")
    except FileNotFoundError as e:
        print(f"⚠️ Модель не найден: {e}. API будет работать в деградированном режиме.")
    yield
    # Shutdown
    print("👋 Завершение работы")


app = FastAPI(
    title="Churn Prediction API",
    description="REST-сервис для прогнозирования оттока телеком-клиентов",
    version="1.0.0",
    lifespan=lifespan,
)


async def get_db() -> AsyncSession:
    """Dependency: получение сессии БД."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@app.get("/health", response_model=HealthResponse)
async def health_check(db: AsyncSession = Depends(get_db)) -> HealthResponse:
    """Проверка работоспособности сервиса."""
    db_ok = False
    try:
        await db.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok" if (is_model_loaded() and db_ok) else "degraded",
        model_loaded=is_model_loaded(),
        db_connected=db_ok,
    )


@app.post("/predict", response_model=PredictionResponse)
async def predict_single(
    data: CustomerData,
    db: AsyncSession = Depends(get_db),
) -> PredictionResponse:
    """Предсказание оттока для одного клиента."""
    if not is_model_loaded():
        raise HTTPException(status_code=503, detail="Модель не загружена")

    try:
        result = predict(data)
        # Сохраняем в БД
        await save_prediction(
            session=db,
            customer_id=result.customer_id,
            churn_probability=result.churn_probability,
            churn_prediction=bool(result.churn_prediction),
            risk_segment=result.risk_segment,
            top_features=result.top_features,
            model_version=result.model_version,
            raw_input=data.model_dump(),
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка предсказания: {str(e)}")


@app.post("/batch_predict", response_model=BatchPredictionResponse)
async def predict_batch(
    request: BatchPredictionRequest,
    db: AsyncSession = Depends(get_db),
) -> BatchPredictionResponse:
    """Пакетное предсказание для списка клиентов (до 1000)."""
    if not is_model_loaded():
        raise HTTPException(status_code=503, detail="Модель не загружена")

    results: List[PredictionResponse] = []
    errors: List[dict] = []

    for idx, customer in enumerate(request.customers):
        try:
            result = predict(customer)
            await save_prediction(
                session=db,
                customer_id=result.customer_id,
                churn_probability=result.churn_probability,
                churn_prediction=bool(result.churn_prediction),
                risk_segment=result.risk_segment,
                top_features=result.top_features,
                model_version=result.model_version,
                raw_input=customer.model_dump(),
            )
            results.append(result)
        except Exception as e:
            errors.append({"index": idx, "error": str(e)})

    if errors:
        # Частичный success: возвращаем предсказания + ошибки
        return JSONResponse(
            status_code=207,
            content={
                "predictions": [r.model_dump() for r in results],
                "errors": errors,
                "total": len(results),
                "model_version": "v1.0.0",
            },
        )

    return BatchPredictionResponse(
        predictions=results,
        total=len(results),
        model_version="v1.0.0",
    )


@app.get("/predictions", response_model=List[PredictionResponse])
async def list_predictions(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> List[PredictionResponse]:
    """Возвращает последние предсказания из БД."""
    records = await get_recent_predictions(db, limit=limit)
    return [
        PredictionResponse(
            customer_id=r.id,
            churn_probability=r.churn_probability,
            churn_prediction=int(r.churn_prediction),
            risk_segment=r.risk_segment,
            top_features=r.top_features or {},
            model_version=r.model_version,
            timestamp=r.created_at.isoformat() if r.created_at else "",
        )
        for r in records
    ]


@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return JSONResponse(status_code=422, content={"detail": str(exc)})
