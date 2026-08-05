"""Пайплайн предобработки данных."""
from typing import List, Tuple

import pandas as pd
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler, OrdinalEncoder


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """Кастомный трансформер для создания новых признаков."""

    def fit(self, X, y=None):
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        # Бинарные признаки
        X["is_short_contract"] = (X["Contract"] == "Month-to-month").astype(int)
        X["is_fiber"] = (X["InternetService"] == "Fiber optic").astype(int)
        X["is_electronic_check"] = (X["PaymentMethod"] == "Electronic check").astype(int)
        X["is_new_and_expensive"] = ((X["tenure"] < 12) & (X["MonthlyCharges"] > 70)).astype(int)
        X["has_internet"] = (X["InternetService"] != "No").astype(int)

        # Количество подключённых услуг
        service_cols = [
            "OnlineSecurity", "OnlineBackup", "DeviceProtection",
            "TechSupport", "StreamingTV", "StreamingMovies"
        ]
        X["services_count"] = X[service_cols].apply(
            lambda row: sum(1 for v in row if v == "Yes"), axis=1
        )

        # Группы tenure
        X["tenure_group"] = pd.cut(
            X["tenure"],
            bins=[-1, 12, 24, 48, 100],
            labels=["0-12", "12-24", "24-48", "48+"]
        ).astype(str)

        # Логарифм MonthlyCharges (для уменьшения скоса)
        X["log_monthly_charges"] = np.log1p(X["MonthlyCharges"])

        # Удаляем мультиколлинеарный TotalCharges
        if "TotalCharges" in X.columns:
            X = X.drop(columns=["TotalCharges"])

        return X


def build_preprocessor(
    cat_features: List[str],
    num_features: List[str],
    ord_features: List[str] = None,
) -> ColumnTransformer:
    """Создаёт ColumnTransformer для предобработки."""
    transformers = []

    # Числовые признаки: стандартизация
    transformers.append(("num", StandardScaler(), num_features))

    # Категориальные: One-Hot
    transformers.append(("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), cat_features))

    # Ординальные (если есть)
    if ord_features:
        transformers.append(("ord", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1), ord_features))

    return ColumnTransformer(transformers, remainder="drop")


def get_feature_columns() -> Tuple[List[str], List[str], List[str]]:
    """Возвращает списки признаков по типам."""
    # После FeatureEngineer
    numeric = [
        "SeniorCitizen", "tenure", "MonthlyCharges",
        "is_short_contract", "is_fiber", "is_electronic_check",
        "is_new_and_expensive", "has_internet", "services_count",
        "log_monthly_charges",
    ]
    categorical = [
        "gender", "Partner", "Dependents", "PhoneService",
        "MultipleLines", "InternetService", "OnlineSecurity",
        "OnlineBackup", "DeviceProtection", "TechSupport",
        "StreamingTV", "StreamingMovies", "Contract",
        "PaperlessBilling", "PaymentMethod", "tenure_group",
    ]
    ordinal = []  # при необходимости добавить
    return numeric, categorical, ordinal
