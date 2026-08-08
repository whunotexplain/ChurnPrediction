"""
Pydantic-схемы запроса/ответа.

БЫЛО: этот файл на деле содержал логику загрузки модели и инференса
(функции load_model/predict), а сами схемы CustomerData/PredictionResponse
нигде не были определены — при этом файл пытался импортировать их из
самого себя (`from backend.app.schemas.schemas import ...`), что упало бы
циклическим/несуществующим импортом при первом же обращении.

СТАЛО: здесь только Pydantic-схемы. Логика модели переехала в app/ml/model.py.
"""

from typing import Literal

from pydantic import BaseModel, Field


class CustomerData(BaseModel):
    gender: Literal["Male", "Female"]
    SeniorCitizen: Literal[0, 1]
    Partner: Literal["Yes", "No"]
    Dependents: Literal["Yes", "No"]
    tenure: int = Field(ge=0, le=100)
    PhoneService: Literal["Yes", "No"]
    MultipleLines: Literal["Yes", "No", "No phone service"]
    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: Literal["Yes", "No", "No internet service"]
    OnlineBackup: Literal["Yes", "No", "No internet service"]
    DeviceProtection: Literal["Yes", "No", "No internet service"]
    TechSupport: Literal["Yes", "No", "No internet service"]
    StreamingTV: Literal["Yes", "No", "No internet service"]
    StreamingMovies: Literal["Yes", "No", "No internet service"]
    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: Literal["Yes", "No"]
    PaymentMethod: Literal[
        "Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"
    ]
    MonthlyCharges: float = Field(ge=0)
    TotalCharges: float = Field(ge=0)


class PredictionResponse(BaseModel):
    prediction_id: str
    churn_probability: float = Field(ge=0, le=1)
    churn_prediction: bool
    top_features: dict[str, float] | None = None
    model_version: str


class PredictionListItem(BaseModel):
    id: str
    created_at: str
    churn_probability: float
    churn_prediction: bool
    model_version: str

    model_config = {"from_attributes": True}


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    db_connected: bool
