"""
Загрузка модели и инференс.

Feature engineering здесь НЕ дублируется вручную — модель это
sklearn Pipeline (FeatureEngineer -> ColumnTransformer -> LGBMClassifier),
сохранённый целиком через joblib в app/src/train.py. Значит инференс
всегда использует ровно ту же логику препроцессинга, что и обучение —
это устраняет риск training/serving skew, о котором мы говорили раньше
для отдельного churn-проекта.
"""
import shap
import uuid
from typing import Any, Optional

import joblib 
import numpy as np
import pandas as pd

from app.core.config import settings
from app.schemas.schemas import CustomerData, PredictionResponse


_model = None
_explainer = None
_feature_names: Optional[list] = None


def load_model() -> None:
    """Загружает модель с диска. Вызывается один раз при старте приложения
    (см. main.py). Поднимает FileNotFoundError с понятным сообщением,
    если артефакт не обучен — вместо непонятного упавшего /predict."""
    global _model, _explainer, _feature_names
    path = settings.MODEL_PATH
    if not path.exists():
        raise FileNotFoundError(
            f"Модель не найдена: {path.resolve()}. "
            "Запусти обучение: python -m app.src.train --data <csv> --output ml_core/artifacts"
        )
    _model = joblib.load(path)
    preprocessor = _model.named_steps["preprocessor"]
    _feature_names = list(preprocessor.get_feature_names_out())

    # SHAP — необязательная часть: если explainer не строится (например,
    # несовместимая версия модели), /predict всё равно должен работать,
    # просто без top_features.
    try:
        classifier = _model.named_steps["classifier"]
        _explainer = shap.TreeExplainer(classifier)
    except Exception:
        _explainer = None

def is_model_loaded() -> bool:
    """Проверяет, что модель загружена в память. Используется в /predict."""
    return _model is not None


def _top_features(X_raw: pd.DataFrame) -> Optional[dict[str, float]]:
    """Возвращает словарь из 5 наиболее важных признаков для конкретного"""

    if _explainer is None:
        return None
    try:
        fe = _model.named_steps["fe"]
        preprocessor = _model.named_steps["preprocessor"]
        X_fe = fe.transform(X_raw)
        X_transformed = preprocessor.transform(X_fe)

        shap_values = _explainer.shap_values(X_transformed)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]
        shap_values = shap_values[0] if len(shap_values.shape) > 1 else shap_values

        top_idx = np.argsort(np.abs(shap_values))[-5:][::-1]
        return {str(_feature_names[i]): round(float(shap_values[i]), 4) for i in top_idx}
    except Exception:
        return None


def predict(data: CustomerData) -> tuple[PredictionResponse, dict[str, Any]]:
    """Возвращает (ответ API, сырой input dict) — второе нужно роуту,
    чтобы сохранить исходный payload в БД без повторной сериализации."""
    if _model is None:
        raise RuntimeError("Модель не загружена. load_model() должен быть вызван при старте приложения.")

    raw = data.model_dump()
    X = pd.DataFrame([raw])

    proba = float(_model.predict_proba(X)[0][1])
    prediction = proba >= settings.MODEL_THRESHOLD

    response = PredictionResponse(
        prediction_id=str(uuid.uuid4()),
        churn_probability=round(proba, 4),
        churn_prediction=prediction,
        top_features=_top_features(X),
        model_version=settings.MODEL_VERSION,
    )
    return response, raw