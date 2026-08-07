import joblib
import json
import pandas as pd
from pathlib import Path
from catboost import CatBoostClassifier
from app.core.config import settings
from app.src.features import add_features

class ChurnPredictor:
    def __init__(self):
        self.model: CatBoostClassifier = None
        self.fe_params: dict = {}
        self.q75_monthly: float = 0.0
        self.cat_features: list = []
        self.num_features: list = []
        self.service_cols: list = []
        self.threshold: float = 0.5
        self._load_artifacts()
    
    def _load_artifacts(self):
        if not settings.MODEL_PATH.exists():
            raise FileNotFoundError(f"Model not found at {settings.MODEL_PATH}")
        if not settings.FE_PARAMS_PATH.exists():
            raise FileNotFoundError(f"FE params not found at {settings.FE_PARAMS_PATH}")
        
        self.model = joblib.load(settings.MODEL_PATH)
        with open(settings.FE_PARAMS_PATH, 'r') as f:
            self.fe_params = json.load(f)
        
        self.q75_monthly = self.fe_params['q75_monthly']
        self.cat_features = self.fe_params['cat_features']
        self.num_features = self.fe_params['num_features']
        self.service_cols = self.fe_params['service_cols']
        
        # Загружаем порог, если есть
        threshold_path = settings.FE_PARAMS_PATH.parent / "threshold.json"
        if threshold_path.exists():
            with open(threshold_path, 'r') as f:
                self.threshold = json.load(f)['threshold']
    
    def predict(self, data: dict) -> dict:
        df = pd.DataFrame([data])
        df_processed = add_features(df, self.q75_monthly, self.service_cols)
        
        # Добавляем недостающие колонки, если нужно
        for col in self.num_features:
            if col not in df_processed.columns:
                df_processed[col] = 0
        
        proba = self.model.predict_proba(df_processed)[:, 1][0]
        pred = int(proba >= self.threshold)
        
        risk = "low"
        if proba > 0.7:
            risk = "high"
        elif proba > 0.4:
            risk = "medium"
        
        return {
            "prediction": pred,
            "probability": round(float(proba), 4),
            "churn_risk": risk,
            "threshold_used": self.threshold
        }

# Singleton
predictor = ChurnPredictor()