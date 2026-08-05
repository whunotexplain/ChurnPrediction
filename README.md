# Churn Prediction API

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/LightGBM-2C5F2D?logo=lightgbm" alt="LightGBM">
  <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL">
</p>

REST-сервис для прогнозирования оттока клиентов телеком-оператора.  
Модель обучена на датасете [Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn), развёрнута через **FastAPI** и контейнеризирована в **Docker**.

---

## Бизнес-задача

Снизить отток клиентов за счёт раннего выявления подписчиков с высокой вероятностью ухода.  
**Целевая метрика:** ROC-AUC (устойчива к дисбалансу классов 73:27).

**Почему это важно:** привлечение нового клиента в телекоме обходится в 5–25× дороже удержания существующего. Модель позволяет CRM-системе автоматически формировать списки клиентов на ретенционные предложения.

---


**Поток данных:**
1. Клиент отправляет JSON с анкетными данными абонента
2. FastAPI валидирует вход через Pydantic
3. Предобработочный pipeline (из `sklearn`) трансформирует признаки
4. LightGBM возвращает вероятность оттока + бинарное предсказание
5. Результат + SHAP-интерпретация записываются в PostgreSQL

---

## Структура проекта

```
churn-prediction-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI приложение (endpoints)
│   ├── schemas.py           # Pydantic-модели валидации
│   ├── model.py             # Загрузка модели + predict-функция
│   └── database.py          # Подключение к PostgreSQL + CRUD
├── notebooks/
│   ├── 01_eda.ipynb         # Разведочный анализ (распределения, корреляции)
│   ├── 02_feature_eng.ipynb # Feature Engineering (encoding, взаимодействия)
│   └── 03_modeling.ipynb    # Обучение, валидация, интерпретация
├── src/
│   ├── train.py             # Скрипт обучения модели
│   ├── preprocess.py        # Пайплайн предобработки (sklearn Pipeline)
│   └── utils.py             # Вспомогательные функции
├── models/
│   ├── churn_model.pkl      # Сериализованная модель + pipeline
│   └── churn_model.joblib   # Альтернативный формат
├── sql/
│   └── init.sql             # Схема таблицы predictions + индексы
├── tests/
│   ├── test_api.py          # Интеграционные тесты endpoint'ов
│   └── test_model.py        # Юнит-тесты предобработки
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## Быстрый старт

### Требования

- Docker 24.0+
- Docker Compose 2.20+
- 4 GB RAM (для контейнеров)

### 1. Клонирование

```bash
git clone https://github.com/whunotexplain/churn-prediction-api.git
cd churn-prediction-api
```

### 2. Запуск через Docker Compose

```bash
docker-compose up --build -d
```

**Поднимаются сервисы:**

| Сервис | URL | Назначение |
|--------|-----|------------|
| API | `http://localhost:8000` | Основное приложение |
| Swagger UI | `http://localhost:8000/docs` | Интерактивная документация |
| ReDoc | `http://localhost:8000/redoc` | Альтернативная документация |
| PostgreSQL | `localhost:5432` | База данных логов |

### 3. Проверка работоспособности

**Health-check:**
```bash
curl http://localhost:8000/health
```

**Ожидаемый ответ:**
```json
{
  "status": "ok",
  "model_loaded": true,
  "db_connected": true
}
```

### 4. Пример предсказания

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "gender": "Male",
    "senior_citizen": 0,
    "partner": "Yes",
    "dependents": "No",
    "tenure": 12,
    "phone_service": "Yes",
    "multiple_lines": "No",
    "internet_service": "Fiber optic",
    "online_security": "No",
    "online_backup": "No",
    "device_protection": "No",
    "tech_support": "No",
    "streaming_tv": "Yes",
    "streaming_movies": "No",
    "contract": "Month-to-month",
    "paperless_billing": "Yes",
    "payment_method": "Electronic check",
    "monthly_charges": 80.85,
    "total_charges": 868.45
  }'
```

**Ответ:**
```json
{
  "customer_id": "auto-generated-uuid",
  "churn_probability": 0.87,
  "churn_prediction": 1,
  "risk_segment": "high",
  "top_features": {
    "contract": -1.24,
    "tenure": -0.98,
    "internet_service": 0.76,
    "monthly_charges": 0.54,
    "payment_method": 0.31
  },
  "model_version": "v1.0.0",
  "timestamp": "2026-08-05T12:34:56.789Z"
}
```

### 5. Просмотр логов в БД

```bash
docker-compose exec db psql -U churn_user -d churn_db -c \
  "SELECT customer_id, churn_probability, risk_segment, created_at FROM predictions ORDER BY created_at DESC LIMIT 5;"
```

---

## ML-часть

### Датасет

- **Источник:** [Telco Customer Churn](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
- **Объём:** 7 043 клиента, 21 признак
- **Целевая переменная:** `Churn` (Yes / No)
- **Дисбаланс:** 73% остаются, 27% уходят

### EDA — ключевые находки

| Находка | Влияние на бизнес | Действие в модели |
|---------|-------------------|-------------------|
| Churn-rate при `Month-to-month` в **4.5×** выше, чем при Two year | Краткосрочные клиенты — приоритетная аудитория для ретеншена | Создан бинарный признак `is_short_contract` |
| `Fiber optic` уходят чаще DSL на 18 п.п. | Возможно, проблема качества связи или ценообразования | Target encoding по `internet_service` |
| `TotalCharges` ≈ `tenure × MonthlyCharges` с точностью 99% | Мультиколлинеарность | Оставлено только `tenure` и `MonthlyCharges`, `TotalCharges` удалён |
| `Electronic check` — самый рискованный способ оплаты | Возможно, связано с низкой вовлечённостью | Отдельный признак `is_electronic_check` |
| Клиенты без `OnlineSecurity` и `TechSupport` уходят в 2.3× чаще | Кросс-сейл дополнительных услуг снижает отток | Создан агрегированный признак `services_count` |

### Feature Engineering

**Категориальные признаки:**
- **One-Hot Encoding:** бинарные признаки (`gender`, `Partner`, `Dependents`)
- **Target Encoding:** высококарднальные (`InternetService`, `Contract`, `PaymentMethod`)
- **Frequency Encoding:** редкие категории

**Числовые признаки:**
- `tenure` → бины: `[0–12]`, `[12–24]`, `[24–48]`, `[48+]`
- `MonthlyCharges` → логарифмирование (правый хвост)
- `TotalCharges` → удалён (мультиколлинеарность с `tenure × MonthlyCharges`)

**Взаимодействия (feature crosses):**
- `tenure × MonthlyCharges` — "накопленная ценность клиента"
- `is_new_and_expensive` — `tenure < 12` & `MonthlyCharges > 70`
- `services_count` — сумма подключённых доп.услуг
- `is_high_risk_payment` — `Electronic check` | `Mailed check`

**Итого:** 8 новых признаков, финальная размерность — 28 признаков.

### Модели и валидация

**Стратегия валидации:** `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`  
**Метрика оптимизации:** ROC-AUC

| Модель | ROC-AUC | PR-AUC | F1 | Precision | Recall |
|--------|---------|--------|-----|-----------|--------|
| Logistic Regression (baseline) | 0.79 | 0.61 | 0.58 | 0.52 | 0.66 |
| Random Forest | 0.82 | 0.67 | 0.63 | 0.58 | 0.69 |
| **LightGBM (Optuna)** | **0.85** | **0.71** | **0.68** | **0.64** | **0.73** |
| XGBoost | 0.84 | 0.70 | 0.67 | 0.63 | 0.72 |

**Оптимизация гиперпараметров:**
- Инструмент: `Optuna` (100 trials, TPE sampler)
- Ключевые параметры LightGBM:
  - `n_estimators`: 287
  - `max_depth`: 7
  - `learning_rate`: 0.045
  - `num_leaves`: 31
  - `class_weight`: `balanced`

### Интерпретация модели (SHAP)

Топ-5 признаков, влияющих на отток:

| Признак | Средний |SHAP| | Интерпретация |
|---------|-------------|---------------|
| `contract` | 1.24 | Month-to-month резко повышает вероятность оттока |
| `tenure` | 0.98 | Каждый месяц tenure снижает риск на ~2.5% |
| `internet_service` | 0.76 | Fiber optic ассоциирован с оттоком |
| `monthly_charges` | 0.54 | Высокий чек без длительной истории = риск |
| `payment_method` | 0.31 | Electronic check — маркер низкой лояльности |

**Вывод для бизнеса:** CRM-система должна первоочередно обрабатывать клиентов с `Month-to-month` + `tenure < 12` + `Fiber optic` — их вероятность оттока превышает 80%.

### Анализ ошибок

- **15% ложных отрицаний (FN):** клиенты с `tenure = 1–2` и высоким `MonthlyCharges` — модель недооценивает "импульсный" отток
- **12% ложных тревог (FP):** долгосрочные клиенты с `Two year`, которые внезапно меняют `PaymentMethod` — сигнал к мониторингу изменений в профиле

---

## 🛠️ Технологический стек

### ML / Data Science
- **Python 3.11**
- **LightGBM** — градиентный бустинг (основная модель)
- **Optuna** — байесовская оптимизация гиперпараметров
- **SHAP** — интерпретация предсказаний
- **Scikit-learn** — предобработка, метрики, Pipeline
- **Pandas / Polars** — манипуляции с данными
- **NumPy** — численные операции

### Backend / API
- **FastAPI** — асинхронный веб-фреймворк
- **Pydantic v2** — валидация и сериализация
- **Uvicorn** — ASGI-сервер
- **SQLAlchemy 2.0** + **asyncpg** — асинхронная работа с PostgreSQL

### Инфраструктура
- **Docker** — контейнеризация приложения
- **Docker Compose** — оркестрация сервисов
- **PostgreSQL 15** — хранение логов предсказаний
- **Git + GitHub** — версионирование

### Тестирование
- **PyTest** — фреймворк тестирования
- **HTTPX** — асинхронный HTTP-клиент для тестов API
- **Coverage.py** — анализ покрытия кода

---

## Тестирование

### Запуск тестов

```bash
# Локально (требуется Python 3.11 + зависимости)
pip install -r requirements.txt
pytest tests/ -v --cov=app --cov-report=term-missing
```

```bash
# Внутри контейнера
docker-compose exec api pytest tests/ -v
```

### Покрытие

| Модуль | Покрытие | Тестируемые сценарии |
|--------|----------|---------------------|
| `app/schemas.py` | 100% | Валидация корректных/некорректных входных данных, граничные значения |
| `app/model.py` | 95% | Загрузка модели, predict, обработка ошибок при битом файле |
| `app/main.py` | 90% | Endpoints `/predict`, `/health`, `/batch_predict`, обработка исключений |
| `app/database.py` | 88% | CRUD-операции, подключение к БД, retry-логика |

**Пример тест-кейса (негативный сценарий):**
```python
def test_predict_invalid_tenure(client):
    """Tenure не может быть отрицательным"""
    payload = {..., "tenure": -5, ...}
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
    assert "tenure" in response.json()["detail"][0]["loc"]
```

---

## Мониторинг и логирование

### Структура таблицы `predictions`

```sql
CREATE TABLE predictions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id VARCHAR(50),
    churn_probability FLOAT NOT NULL CHECK (churn_probability BETWEEN 0 AND 1),
    churn_prediction BOOLEAN NOT NULL,
    risk_segment VARCHAR(20) CHECK (risk_segment IN ('low', 'medium', 'high')),
    top_features JSONB,
    model_version VARCHAR(20) NOT NULL,
    raw_input JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_predictions_created_at ON predictions(created_at DESC);
CREATE INDEX idx_predictions_risk_segment ON predictions(risk_segment);
```


## Как использовать в своём проекте

Этот репозиторий может служить **шаблоном** для развёртывания ML-моделей в продакшен.  
Для адаптации под другую задачу:

1. Замените датасет в `notebooks/`
2. Переобучите модель через `src/train.py`
3. Обновите Pydantic-схемы в `app/schemas.py` под новые признаки
4. Пересоберите контейнер: `docker-compose up --build`

---

## Контакты

**Егор Козин** — Data Scientist / ML Engineer  
[kozinegor2906@gmail.com](mailto:kozinegor2906@gmail.com)  
[GitHub](https://github.com/whunotexplain)  
[Kaggle](https://www.kaggle.com/bigbddgccibrgr)

---

<p align="center">
  <sub>Built with ❤️ for learning and production-ready ML deployment.</sub>
</p>
