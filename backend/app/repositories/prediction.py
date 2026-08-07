from sqlalchemy.orm import Session
from app.db_models.prediction import PredictionLog

class PredictionRepository:
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, customer_id: str, prediction: int, probability: float, 
               input_json: str, model_version: str = "catboost_v1"):
        log = PredictionLog(
            customer_id=customer_id,
            prediction=prediction,
            probability=probability,
            input_features=input_json,
            model_version=model_version
        )
        self.db.add(log)
        self.db.commit()
        self.db.refresh(log)
        return log
    
    def get_recent(self, limit: int = 100):
        return (self.db.query(PredictionLog)
                .order_by(PredictionLog.created_at.desc())
                .limit(limit)
                .all())