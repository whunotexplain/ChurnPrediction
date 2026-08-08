-- Справочная схема БД (для ручного просмотра/psql).
-- Источник правды по схеме — ORM-модель в app/database/models.py и
-- миграция alembic/versions/0001_initial.py; в реальном запуске таблицу
-- создаёт alembic, этот файл не выполняется автоматически.

CREATE TABLE IF NOT EXISTS predictions (
    id UUID PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    input_payload JSONB NOT NULL,
    churn_probability FLOAT NOT NULL CHECK (churn_probability BETWEEN 0 AND 1),
    churn_prediction BOOLEAN NOT NULL,
    model_version VARCHAR(20) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at DESC);
