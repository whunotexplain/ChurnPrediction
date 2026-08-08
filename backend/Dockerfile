FROM python:3.11-slim

WORKDIR /app

# libgomp1 нужен LightGBM (OpenMP), gcc/libpq-dev нужны для сборки psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 gcc libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Датасет и место для артефактов модели — монтируются/копируются отдельно,
# см. docker-compose.yml (volume ml_core примонтирован с хоста)
RUN mkdir -p ml_core/artifacts ml_core/data

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
