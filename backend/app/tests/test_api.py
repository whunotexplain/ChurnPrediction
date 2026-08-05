"""Интеграционные и юнит-тесты для Churn Prediction API."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from app.main import app, lifespan
from backend.app.database.database import PredictionRecord

client = TestClient(app)


# Фикстура для мока модели
@pytest.fixture(autouse=True)
def mock_model_and_db():
    """Мокаем модель и БД перед каждым тестом."""
    with patch("app.main.load_model") as mock_load, \
         patch("app.main.init_db") as mock_init, \
         patch("app.main.is_model_loaded", return_value=True), \
         patch("app.main.predict") as mock_predict, \
         patch("app.main.save_prediction") as mock_save:

        mock_load.return_value = None
        mock_init.return_value = None
        mock_save.return_value = MagicMock()

        # Стандартный ответ предсказания
        mock_predict.return_value = MagicMock(
            customer_id="test-uuid-123",
            churn_probability=0.87,
            churn_prediction=1,
            risk_segment="high",
            top_features={"contract": -1.24, "tenure": -0.98},
            model_version="v1.0.0",
            timestamp="2026-08-05T12:00:00Z",
        )
        yield


# ---------- Health ----------

def test_health_ok():
    """Health-check при работающей модели и БД."""
    with patch("app.main.is_model_loaded", return_value=True):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["model_loaded"] is True
        assert data["db_connected"] is True
        assert data["status"] == "ok"


def test_health_degraded_no_model():
    """Health-check когда модель не загружена."""
    with patch("app.main.is_model_loaded", return_value=False):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "degraded"


# ---------- Predict ----------

def test_predict_valid_payload():
    """Корректный запрос на предсказание."""
    payload = {
        "gender": "Male",
        "senior_citizen": 0,
        "partner": "Yes",
        "dependents": "No",
        "tenure": 12,
        "phone_service": "Yes",
        "multiple_lines": "No",
        "internet_service": "Fiber optic",
        "online_security": "No",
        "online_backup": "No",
        "device_protection": "No",
        "tech_support": "No",
        "streaming_tv": "Yes",
        "streaming_movies": "No",
        "contract": "Month-to-month",
        "paperless_billing": "Yes",
        "payment_method": "Electronic check",
        "monthly_charges": 80.85,
        "total_charges": 868.45,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "churn_probability" in data
    assert 0.0 <= data["churn_probability"] <= 1.0
    assert data["risk_segment"] in ["low", "medium", "high"]
    assert data["model_version"] == "v1.0.0"


def test_predict_invalid_gender():
    """Невалидное значение gender."""
    payload = {
        "gender": "Unknown",
        "senior_citizen": 0,
        "partner": "Yes",
        "dependents": "No",
        "tenure": 12,
        "phone_service": "Yes",
        "multiple_lines": "No",
        "internet_service": "Fiber optic",
        "online_security": "No",
        "online_backup": "No",
        "device_protection": "No",
        "tech_support": "No",
        "streaming_tv": "Yes",
        "streaming_movies": "No",
        "contract": "Month-to-month",
        "paperless_billing": "Yes",
        "payment_method": "Electronic check",
        "monthly_charges": 80.85,
        "total_charges": 868.45,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


def test_predict_invalid_tenure_negative():
    """Отрицательный tenure должен отклоняться."""
    payload = {
        "gender": "Male",
        "senior_citizen": 0,
        "partner": "Yes",
        "dependents": "No",
        "tenure": -5,
        "phone_service": "Yes",
        "multiple_lines": "No",
        "internet_service": "Fiber optic",
        "online_security": "No",
        "online_backup": "No",
        "device_protection": "No",
        "tech_support": "No",
        "streaming_tv": "Yes",
        "streaming_movies": "No",
        "contract": "Month-to-month",
        "paperless_billing": "Yes",
        "payment_method": "Electronic check",
        "monthly_charges": 80.85,
        "total_charges": 868.45,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert "tenure" in str(response.json()["detail"])


def test_predict_invalid_monthly_charges_too_high():
    """MonthlyCharges > 200 должен отклоняться."""
    payload = {
        "gender": "Male",
        "senior_citizen": 0,
        "partner": "Yes",
        "dependents": "No",
        "tenure": 12,
        "phone_service": "Yes",
        "multiple_lines": "No",
        "internet_service": "Fiber optic",
        "online_security": "No",
        "online_backup": "No",
        "device_protection": "No",
        "tech_support": "No",
        "streaming_tv": "Yes",
        "streaming_movies": "No",
        "contract": "Month-to-month",
        "paperless_billing": "Yes",
        "payment_method": "Electronic check",
        "monthly_charges": 250.0,
        "total_charges": 868.45,
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422


# ---------- Batch Predict ----------

def test_batch_predict_valid():
    """Пакетный запрос с 2 клиентами."""
    payload = {
        "customers": [
            {
                "gender": "Male", "senior_citizen": 0, "partner": "Yes", "dependents": "No",
                "tenure": 12, "phone_service": "Yes", "multiple_lines": "No",
                "internet_service": "Fiber optic", "online_security": "No",
                "online_backup": "No", "device_protection": "No", "tech_support": "No",
                "streaming_tv": "Yes", "streaming_movies": "No", "contract": "Month-to-month",
                "paperless_billing": "Yes", "payment_method": "Electronic check",
                "monthly_charges": 80.85, "total_charges": 868.45,
            },
            {
                "gender": "Female", "senior_citizen": 1, "partner": "No", "dependents": "Yes",
                "tenure": 48, "phone_service": "Yes", "multiple_lines": "Yes",
                "internet_service": "DSL", "online_security": "Yes",
                "online_backup": "Yes", "device_protection": "Yes", "tech_support": "Yes",
                "streaming_tv": "No", "streaming_movies": "No", "contract": "Two year",
                "paperless_billing": "No", "payment_method": "Bank transfer (automatic)",
                "monthly_charges": 55.0, "total_charges": 2640.0,
            },
        ]
    }
    response = client.post("/batch_predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["predictions"]) == 2


def test_batch_predict_empty_list():
    """Пустой список должен отклоняться."""
    payload = {"customers": []}
    response = client.post("/batch_predict", json=payload)
    assert response.status_code == 422


# ---------- Predictions History ----------

def test_list_predictions():
    """Получение истории предсказаний."""
    with patch("app.main.get_recent_predictions") as mock_get:
        mock_get.return_value = [
            PredictionRecord(
                id="rec-1",
                churn_probability=0.9,
                churn_prediction=True,
                risk_segment="high",
                top_features={"a": 1.0},
                model_version="v1.0.0",
            )
        ]
        response = client.get("/predictions?limit=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["risk_segment"] == "high"
