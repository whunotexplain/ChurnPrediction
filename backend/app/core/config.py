from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    PROJECT_NAME: str = "Churn Prediction API"
    VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite:///./churn_api.db"
    MODEL_PATH: Path = Path("../ml_core/artifacts/catboost_model.pkl")
    FE_PARAMS_PATH: Path = Path("../ml_core/artifacts/fe_params.json")
    
    class Config:
        env_file = ".env"

settings = Settings()