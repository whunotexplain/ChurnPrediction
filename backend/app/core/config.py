"""
Настройки приложения. Всё конфигурируемое читается из переменных окружения
(или .env файла), а не хардкодится.

БЫЛО: DATABASE_URL по умолчанию указывал на sqlite:///./churn_api.db —
удобно для локального запуска без Docker, но означает, что данные живут
в файле внутри контейнера и пропадают при пересоздании контейнера.

СТАЛО: по умолчанию Postgres, адрес берётся из переменной окружения
DATABASE_URL. docker-compose.yml прокидывает туда адрес контейнера с
Postgres. Для локального запуска без Docker можно переопределить
DATABASE_URL на sqlite в .env.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    PROJECT_NAME: str = "Churn Prediction API"
    VERSION: str = "1.0.0"

    # Postgres по умолчанию — адрес сервиса "db" из docker-compose.yml
    DATABASE_URL: str = "postgresql+psycopg2://churn_user:churn_password@db:5432/churn_db"

    # Модель обучается скриптом app/src/train.py и сохраняется сюда;
    # backend читает её при старте (см. main.py -> startup event)
    MODEL_PATH: Path = Path("ml_core/artifacts/churn_model.joblib")
    MODEL_VERSION: str = "v1.0.0"

    # Порог классификации Churn/No Churn
    MODEL_THRESHOLD: float = 0.5

    # --- A/B тестирование ---
    # Вариант A — модель выше (MODEL_PATH). Вариант B — челленджер;
    # если файла нет, весь трафик молча идёт в A (см. app/ml/model.py).
    AB_TEST_ENABLED: bool = True
    MODEL_B_PATH: Path = Path("ml_core/artifacts/churn_model_b.joblib")
    AB_TRAFFIC_SPLIT: float = 0.5  # доля трафика на вариант B
    AB_ALPHA: float = 0.05          # уровень значимости для /ab-test-results


settings = Settings()
