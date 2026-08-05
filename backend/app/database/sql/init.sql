-- Инициализация схемы БД для Churn Prediction API
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(50),
    churn_probability FLOAT NOT NULL CHECK (churn_probability BETWEEN 0 AND 1),
    churn_prediction BOOLEAN NOT NULL,
    risk_segment VARCHAR(20) NOT NULL CHECK (risk_segment IN ('low', 'medium', 'high')),
    top_features JSONB,
    model_version VARCHAR(20) NOT NULL,
    raw_input JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Индексы для быстрой выборки
CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_risk_segment ON predictions(risk_segment);
CREATE INDEX IF NOT EXISTS idx_predictions_customer_id ON predictions(customer_id);
