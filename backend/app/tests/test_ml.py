import pandas as pd
from app.src.features import add_features

def test_feature_engineering():
    sample = {
        "gender": "Female",
        "SeniorCitizen": 0,
        "Partner": "Yes",
        "Dependents": "No",
        "tenure": 1,
        "PhoneService": "No",
        "MultipleLines": "No phone service",
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
        "MonthlyCharges": "29.85",
        "TotalCharges": "29.85"
    }
    df = pd.DataFrame([sample])
    result = add_features(df, q75_monthly=70.0, service_cols=[
        'PhoneService', 'MultipleLines', 'OnlineSecurity', 'OnlineBackup',
        'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies'
    ])
    assert "AvgMonthlyCharge" in result.columns
    assert "ServiceCount" in result.columns
    assert result["IsNewCustomer"].iloc[0] == 1
    assert result["IsMonthToMonth"].iloc[0] == 1