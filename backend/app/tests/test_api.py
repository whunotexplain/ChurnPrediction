"""
БЫЛО: payload использовал плоские lower_snake_case ключи
(customer_id, gender, "TotalCharges": "29.85" как строка), которые не
совпадают ни с одной реальной Pydantic-схемой в проекте — тест был бы
падал с 422 при первом же реальном запуске, даже если бы router.py
не был пустым.

СТАЛО: payload соответствует CustomerData (PascalCase-поля датасета
Telco), проверки — реальным полям PredictionResponse.
"""

import pytest

from app.ml.model import is_model_loaded


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_endpoint(client):
    if not is_model_loaded():
        pytest.skip("Модель не обучена в этом окружении — обучи через app/src/train.py")

    payload = {
        "gender": "Male",
        "SeniorCitizen": 0,
        "Partner": "No",
        "Dependents": "No",
        "tenure": 12,
        "PhoneService": "Yes",
        "MultipleLines": "No",
        "InternetService": "DSL",
        "OnlineSecurity": "No",
        "OnlineBackup": "Yes",
        "DeviceProtection": "No",
        "TechSupport": "No",
        "StreamingTV": "No",
        "StreamingMovies": "No",
        "Contract": "Month-to-month",
        "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check",
        "MonthlyCharges": 29.85,
        "TotalCharges": 29.85,
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "churn_probability" in data
    assert 0 <= data["churn_probability"] <= 1


def test_predict_invalid_tenure(client):
    payload = {
        "gender": "Male", "SeniorCitizen": 0, "Partner": "No", "Dependents": "No",
        "tenure": -5, "PhoneService": "Yes", "MultipleLines": "No",
        "InternetService": "DSL", "OnlineSecurity": "No", "OnlineBackup": "Yes",
        "DeviceProtection": "No", "TechSupport": "No", "StreamingTV": "No",
        "StreamingMovies": "No", "Contract": "Month-to-month", "PaperlessBilling": "Yes",
        "PaymentMethod": "Electronic check", "MonthlyCharges": 29.85, "TotalCharges": 29.85,
    }
    response = client.post("/api/v1/predict", json=payload)
    assert response.status_code == 422


def test_get_predictions(client):
    response = client.get("/api/v1/predictions?limit=10")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
