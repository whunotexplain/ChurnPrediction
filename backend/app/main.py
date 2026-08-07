from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.database.base import Base
from app.database.session import engine
from app.api.v1.router import router

# Авто-создание таблиц (для разработки; в проде используй Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="ML API для предсказания оттока клиентов (Telco Churn)"
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
        "version": settings.VERSION
    }