"""
БЫЛО: приложение никогда не вызывало load_model() — модель физически
не загружалась в память, и любой запрос к /predict упал бы с
AttributeError на None. Ошибка не проявлялась раньше только потому,
что /predict тоже не существовал (пустой router.py).

СТАЛО: модель грузится один раз на старте приложения через lifespan
(современный способ в FastAPI — @app.on_event("startup") устарел и
пишет DeprecationWarning на каждый старт). Если файла модели нет,
приложение всё равно поднимается (чтобы /health можно было опросить
и увидеть model_loaded: false), но лог явно покажет причину.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database.base import Base
from app.database.session import engine
from app.api.v1.router import router
from app.ml.model import load_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("churn-api")

# Таблицы создаются здесь только как fallback для локальной разработки.
# В докере это делает alembic (см. entrypoint.sh) — таблицы уже будут
# существовать к моменту старта uvicorn, и create_all() станет no-op.
Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        load_model()
        logger.info("Модель загружена: %s", settings.MODEL_PATH)
    except FileNotFoundError as e:
        logger.warning("Модель не загружена при старте: %s", e)
    yield  # приложение работает; код после yield выполнился бы при shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="ML API для предсказания оттока клиентов (Telco Churn)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "message": "Churn Prediction API",
        "docs": "/docs",
        "health": "/api/v1/health",
        "version": settings.VERSION,
    }



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)