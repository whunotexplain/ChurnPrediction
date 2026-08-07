from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.database.base import Base

class PredictionLog(Base):
    __tablename__ = "predictions"
    
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(String, index=True, nullable=True)
    prediction = Column(Integer)
    probability = Column(Float)
    model_version = Column(String, default="catboost_v1")
    created_at = Column(DateTime, default=datetime.utcnow)
    input_features = Column(String)