#!/bin/sh
set -e

echo "Waiting for Postgres..."
until python -c "
import sys, time
from sqlalchemy import create_engine
from app.core.config import settings
for _ in range(30):
    try:
        create_engine(settings.DATABASE_URL).connect().close()
        sys.exit(0)
    except Exception:
        time.sleep(1)
sys.exit(1)
"; do
  echo "Postgres not ready yet, retrying..."
  sleep 1
done
echo "Postgres is up."

echo "Running migrations..."
cd /app && alembic -c alembic/alembic.ini upgrade head

MODEL_FILE="/app/ml_core/artifacts/churn_model.joblib"
if [ ! -f "$MODEL_FILE" ]; then
  echo "No trained model found at $MODEL_FILE — training now (this runs once, result is cached in the ml_core volume)..."
  DATA_FILE="/app/ml_core/data/WA_Fn-UseC_-Telco-Customer-Churn.csv"
  if [ ! -f "$DATA_FILE" ]; then
    echo "WARNING: dataset not found at $DATA_FILE — /predict will return 503 until you add it and restart."
  else
    python -m app.src.train --data "$DATA_FILE" --output ml_core/artifacts --trials "${TRAIN_TRIALS:-20}"
  fi
else
  echo "Found existing model at $MODEL_FILE — skipping training."
fi

echo "Starting API..."
exec uvicorn main:app --host 0.0.0.0 --port 8000
