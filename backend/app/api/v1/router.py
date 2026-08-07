from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import json

from app.database.session import get_db
from app.schemas.prediction import CustomerFeatures, PredictionResponse, PredictionLogResponse
from app.services.ml_service import predictor
from app.repositories.prediction import PredictionRepository

router = APIRouter(prefix="/api/v1", tags=["predictions"])

@router.post("/predict", response_model=PredictionResponse)
def predict_churn(data: CustomerFeatures, db: Session = Depends(get_db)):
    try:
        input_dict = data.model_dump()
        result = predictor.predict(input_dict)
        
        repo = PredictionRepository(db)
        repo.create(
            customer_id=input_dict.get("customer_id", "anonymous"),
            prediction=result["prediction"],
            probability=result["probability"],
            input_json=json.dumps(input_dict)
        )
        
        return PredictionResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
def health_check():
    return {
        "status": "ok",
        "model_loaded": predictor.model is not None,
        "model_type": type(predictor.model).__name__ if predictor.model else None,
        "threshold": predictor.threshold
    }

@router.get("/predictions", response_model=List[PredictionLogResponse])
def get_recent_predictions(limit: int = 100, db: Session = Depends(get_db)):
    repo = PredictionRepository(db)
    return repo.get_recent(limit)