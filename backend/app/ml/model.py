"""
Загрузка модели и инференс.

Feature engineering здесь НЕ дублируется вручную — модель это
sklearn Pipeline (FeatureEngineer -> ColumnTransformer -> LGBMClassifier),
сохранённый целиком через joblib в app/src/train.py. Значит инференс
всегда использует ровно ту же логику препроцессинга, что и обучение —
это устраняет риск training/serving skew, о котором мы говорили раньше
для отдельного churn-проекта.
"""

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