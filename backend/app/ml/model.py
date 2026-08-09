"""
Загрузка модели и инференс — с поддержкой A/B (вариант A и опциональный
вариант B, "челленджер").

Feature engineering здесь НЕ дублируется вручную — модель это
sklearn Pipeline (FeatureEngineer -> ColumnTransformer -> LGBMClassifier),
сохранённый целиком через joblib в app/src/train.py. Значит инференс
всегда использует ровно ту же логику препроцессинга, что и обучение —
это устраняет training/serving skew.
"""

import uuid
from pathlib import Path
from typing import Any, Optional

import joblib
import numpy as np
import pandas as pd

from app.core.config import settings
from app.schemas.schemas import CustomerData, PredictionResponse

_models: dict[str, Any] = {}
_explainers: dict[str, Any] = {}
_feature_names: dict[str, list] = {}


def load_model() -> None:
    """Загружает вариант A (обязателен) и вариант B (опционален —
    если файла нет, A/B-тест просто не идёт, весь трафик остаётся в A).
    Вызывается один раз при старте приложения (см. main.py)."""
    _load_variant("A", settings.MODEL_PATH, required=True)
    if settings.AB_TEST_ENABLED:
        _load_variant("B", settings.MODEL_B_PATH, required=False)


def _load_variant(variant: str, path: Path, required: bool) -> None:
    if not path.exists():
        if required:
            raise FileNotFoundError(
                f"Модель не найдена: {path.resolve()}. "
                "Запусти обучение: python -m app.src.train --data <csv> --output ml_core/artifacts"
            )
        return

    model = joblib.load(path)
    _models[variant] = model
    _feature_names[variant] = list(model.named_steps["preprocessor"].get_feature_names_out())

    try:
        import shap
        _explainers[variant] = shap.TreeExplainer(model.named_steps["classifier"])
    except Exception:
        _explainers[variant] = None


def is_model_loaded() -> bool:
    return "A" in _models


def is_ab_test_active() -> bool:
    return "B" in _models


def _top_features(X_raw: pd.DataFrame, variant: str) -> Optional[dict[str, float]]:
    explainer = _explainers.get(variant)
    if explainer is None:
        return None
    try:
        model = _models[variant]
        fe = model.named_steps["fe"]
        preprocessor = model.named_steps["preprocessor"]
        X_fe = fe.transform(X_raw)
        X_transformed = preprocessor.transform(X_fe)

        shap_values = explainer.shap_values(X_transformed)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        shap_values = shap_values[0] if len(shap_values.shape) > 1 else shap_values

        names = _feature_names[variant]
        top_idx = np.argsort(np.abs(shap_values))[-5:][::-1]
        return {str(names[i]): round(float(shap_values[i]), 4) for i in top_idx}
    except Exception:
        return None


def predict(data: CustomerData, variant: str = "A") -> tuple[PredictionResponse, dict[str, Any], str]:
    """Возвращает (ответ API, сырой input dict, фактически использованный вариант).
    Если запрошенный вариант не загружен (например, B ещё не обучен) —
    тихо откатываемся на A, чтобы /predict не падал из-за отсутствия
    челленджера."""
    if not _models:
        raise RuntimeError("Модель не загружена. load_model() должен быть вызван при старте приложения.")

    if variant not in _models:
        variant = "A"

    model = _models[variant]
    raw = data.model_dump()
    X = pd.DataFrame([raw])

    proba = float(model.predict_proba(X)[0][1])
    prediction = proba >= settings.MODEL_THRESHOLD

    response = PredictionResponse(
        prediction_id=str(uuid.uuid4()),
        churn_probability=round(proba, 4),
        churn_prediction=prediction,
        top_features=_top_features(X, variant),
        model_version=f"{settings.MODEL_VERSION}-{variant}",
        ab_variant=variant,
    )
    return response, raw, variant
