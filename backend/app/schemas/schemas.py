"""
Pydantic-схемы запроса/ответа.

БЫЛО: этот файл на деле содержал логику загрузки модели и инференса
(функции load_model/predict), а сами схемы CustomerData/PredictionResponse
нигде не были определены — при этом файл пытался импортировать их из
самого себя, что упало бы циклическим/несуществующим импортом.

СТАЛО: здесь только Pydantic-схемы. Логика модели — в app/ml/model.py.

Также добавлено protected_namespaces=() в схемах с полями model_version/
model_loaded — pydantic по умолчанию резервирует префикс "model_" для
своих внутренних полей и иначе на старте пишет предупреждение
"Field has conflict with protected namespace 'model_'" (то самое, что
было видно в консоли при запуске main.py).
"""

from typing import Literal

from pydantic import BaseModel, Field


class CustomerData(BaseModel):
    # customer_id — опционален. Если передан, используется для
    # детерминированного распределения по A/B-группам (см.
    # app/core/ab_testing.py) — один и тот же клиент всегда попадает
    # в одну и ту же группу между визитами.
    customer_id: str | None = None

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
    model_config = {"protected_namespaces": ()}

    prediction_id: str
    churn_probability: float = Field(ge=0, le=1)
    churn_prediction: bool
    top_features: dict[str, float] | None = None
    model_version: str
    ab_variant: str = "A"


class PredictionListItem(BaseModel):
    model_config = {"protected_namespaces": (), "from_attributes": True}

    id: str
    created_at: str
    churn_probability: float
    churn_prediction: bool
    model_version: str
    ab_variant: str


class HealthResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    status: str
    model_loaded: bool
    ab_test_active: bool
    db_connected: bool


class OutcomeSubmission(BaseModel):
    """Фактический исход по ранее сделанному предсказанию — присылается
    позже (например, через N дней, когда стало известно, ушёл клиент
    или нет). Без этого A/B-тест сравнивает только то, ЧТО предсказали
    модели, а не то, ПРАВЫ ли они были."""

    prediction_id: str
    actual_churn: bool


class VariantStats(BaseModel):
    n: int = Field(description="Сколько исходов собрано в группе")
    accuracy: float = Field(description="Доля верных предсказаний")


class ABTestResultResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    variant_a: VariantStats
    variant_b: VariantStats
    diff: float = Field(description="accuracy(B) - accuracy(A)")
    z_stat: float
    p_value: float
    significant: bool
    confidence_interval: tuple[float, float]
    alpha: float
    message: str
