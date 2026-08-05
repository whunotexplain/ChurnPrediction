"""Загрузка ML-модели и инференс."""
import os
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import joblib
import numpy as np
import shap
from sklearn.pipeline import Pipeline

from backend.app.schemas.schemas import CustomerData, PredictionResponse

MODEL_PATH = os.getenv("MODEL_PATH", "models/churn_model.joblib")

# Глобальные переменные для модели и объяснителя
_model: Optional[Pipeline] = None
_explainer: Optional[Any] = None
_feature_names: Optional[list] = None


def load_model() -> None:
    """Загружает модель и инициализирует SHAP."""
    global _model, _explainer, _feature_names

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Модель не найдена по пути: {MODEL_PATH}")

    _model = joblib.load(MODEL_PATH)

    # Извлекаем feature names из последнего шага (классификатор ожидает определённые колонки)
    # Предполагаем, что pipeline состоит из preprocessor + classifier
    preprocessor = _model.named_steps["preprocessor"]
    _feature_names = list(preprocessor.get_feature_names_out())

    # Инициализируем TreeExplainer для LightGBM
    classifier = _model.named_steps["classifier"]
    _explainer = shap.TreeExplainer(classifier)


def is_model_loaded() -> bool:
    return _model is not None


def _extract_features(data: CustomerData) -> Dict[str, Any]:
    """Преобразует Pydantic-модель в словарь признаков."""
    return {
        "gender": data.gender,
        "SeniorCitizen": data.senior_citizen,
        "Partner": data.partner,
        "Dependents": data.dependents,
        "tenure": data.tenure,
        "PhoneService": data.phone_service,
        "MultipleLines": data.multiple_lines,
        "InternetService": data.internet_service,
        "OnlineSecurity": data.online_security,
        "OnlineBackup": data.online_backup,
        "DeviceProtection": data.device_protection,
        "TechSupport": data.tech_support,
        "StreamingTV": data.streaming_tv,
        "StreamingMovies": data.streaming_movies,
        "Contract": data.contract,
        "PaperlessBilling": data.paperless_billing,
        "PaymentMethod": data.payment_method,
        "MonthlyCharges": data.monthly_charges,
        "TotalCharges": data.total_charges,
    }


def _build_rich_features(features: Dict[str, Any]) -> Dict[str, Any]:
    """Добавляет инженерные признаки, которые ожидает модель."""
    # Внимание: эти признаки должны точно совпадать с тем, что делает src/preprocess.py
    features["is_short_contract"] = 1 if features["Contract"] == "Month-to-month" else 0
    features["is_fiber"] = 1 if features["InternetService"] == "Fiber optic" else 0
    features["is_electronic_check"] = 1 if features["PaymentMethod"] == "Electronic check" else 0
    features["is_new_and_expensive"] = 1 if (features["tenure"] < 12 and features["MonthlyCharges"] > 70) else 0
    features["services_count"] = sum([
        1 if features.get(k) == "Yes" else 0
        for k in ["OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies"]
    ])
    features["has_internet"] = 0 if features["InternetService"] == "No" else 1
    features["tenure_group"] = (
        "0-12" if features["tenure"] <= 12 else
        "12-24" if features["tenure"] <= 24 else
        "24-48" if features["tenure"] <= 48 else
        "48+"
    )
    return features


def predict(data: CustomerData) -> PredictionResponse:
    """Основная функция предсказания."""
    if _model is None:
        raise RuntimeError("Модель не загружена. Вызовите load_model() при старте.")

    features = _extract_features(data)
    features = _build_rich_features(features)

    # Преобразуем в DataFrame (pipeline ожидает DataFrame)
    import pandas as pd
    X = pd.DataFrame([features])

    # Предсказание вероятности
    proba = _model.predict_proba(X)[0][1]
    prediction = 1 if proba >= 0.5 else 0

    # Сегмент риска
    if proba >= 0.7:
        risk = "high"
    elif proba >= 0.4:
        risk = "medium"
    else:
        risk = "low"

    # SHAP-интерпретация
    preprocessor = _model.named_steps["preprocessor"]
    X_transformed = preprocessor.transform(X)
    shap_values = _explainer.shap_values(X_transformed)
    # Для бинарной классификации shap_values может быть списком [neg, pos]
    if isinstance(shap_values, list):
        shap_values = shap_values[1]
    shap_values = shap_values[0] if len(shap_values.shape) > 1 else shap_values

    # Топ-5 признаков по модулю SHAP
    top_idx = np.argsort(np.abs(shap_values))[-5:][::-1]
    top_features = {
        str(_feature_names[i]): round(float(shap_values[i]), 2)
        for i in top_idx
    }

    return PredictionResponse(
        customer_id=str(uuid.uuid4()),
        churn_probability=round(float(proba), 4),
        churn_prediction=prediction,
        risk_segment=risk,
        top_features=top_features,
        model_version="v1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
