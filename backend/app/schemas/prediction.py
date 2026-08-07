from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class CustomerFeatures(BaseModel):
    customer_id: Optional[str] = "anonymous"
    gender: Literal["Male", "Female"]
    SeniorCitizen: int = Field(..., ge=0, le=1)
    Partner: Literal["Yes", "No"]
    Dependents: Literal["Yes", "No"]
    tenure: int = Field(..., ge=0)
    PhoneService: Literal["Yes", "No"]
    MultipleLines: Literal["Yes", "No", "No phone service"]
    InternetService: Literal["DSL", "Fiber optic", "No"]
    OnlineSecurity: Literal["Yes", "No", "No internet service"]
    OnlineBackup: Literal["Yes", "No", "No internet service"]
    DeviceProtection: Literal["Yes", "No", "No internet service"]
    TechSupport: Literal["Yes", "No", "No internet service"]
    StreamingTV: Literal["Yes", "No", "No internet service"]
    StreamingMovies: Literal["Yes", "No", "No internet service"]
    Contract: Literal["Month-to-month", "One year", "Two year"]
    PaperlessBilling: Literal["Yes", "No"]
    PaymentMethod: Literal["Electronic check", "Mailed check", "Bank transfer (automatic)", "Credit card (automatic)"]
    MonthlyCharges: float = Field(..., ge=0)
    TotalCharges: str = Field(..., description="Can be empty string for new customers")

class PredictionResponse(BaseModel):
    prediction: int
    probability: float
    churn_risk: Literal["low", "medium", "high"]
    threshold_used: float

class PredictionLogResponse(BaseModel):
    id: int
    customer_id: Optional[str]
    prediction: int
    probability: float
    created_at: datetime