from pydantic_settings import BaseSettings
import psycopg2
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings(BaseSettings):
    PROJECT_NAME: str = "Churn Prediction API"
    VERSION: str = "1.0.0"
    DATABASE_URL: str = "sqlite:///./churn_api.db"
    MODEL_PATH: Path = Path("../ml_core/artifacts/catboost_model.pkl")
    FE_PARAMS_PATH: Path = Path("../ml_core/artifacts/fe_params.json")
    
    class Config:
        env_file = ".env"

settings = Settings()