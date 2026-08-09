# Churn Prediction API

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11-blue?logo=python" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/LightGBM-2C5F2D?logo=lightgbm" alt="LightGBM">
  <img src="https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white" alt="PostgreSQL">
</p>

# ChurnPrediction

> End-to-end ML-система для прогнозирования оттока клиентов, сегментации пользователей и проведения A/B-тестов retention-стратегий.

## 📌 О проекте

**ChurnPrediction** — учебный end-to-end проект, моделирующий production-систему для работы с оттоком клиентов.

Система позволяет:

* анализировать клиентские данные;
* обучать и оценивать ML-модели для прогнозирования churn;
* определять клиентов с высоким риском ухода;
* предоставлять ML-предсказания через REST API;
* хранить и обрабатывать данные через PostgreSQL;
* проводить A/B-эксперименты;
* оценивать статистическую значимость результатов;
* рассчитывать необходимый размер выборки и Minimum Detectable Effect (MDE).

Главная идея проекта — пройти полный путь от **данных и ML-модели до backend-сервиса и экспериментирования**.

---

## 🏗️ Архитектура

<img width="1434" height="898" alt="Architecture" src="https://github.com/user-attachments/assets/305526c9-68ba-4c2d-84c4-9e66d05acdc4" />


---

# 🤖 Machine Learning

## Задача

Бинарная классификация:

> **Предсказать вероятность того, что клиент уйдёт из компании.**

Target:

```text
Churn = 1 → клиент ушёл
Churn = 0 → клиент остался
```

## ML Pipeline

```text
Raw Data
   ↓
Data Cleaning
   ↓
EDA
   ↓
Feature Engineering
   ↓
Train / Validation Split
   ↓
Model Training
   ↓
Hyperparameter Tuning
   ↓
Model Evaluation
   ↓
Prediction API
```

В проекте используются:

* Python
* Pandas / NumPy
* Scikit-learn
* CatBoost / LightGBM
* Matplotlib / Seaborn
* Jupyter Notebook

### Оценка модели

Используются:

* ROC-AUC
* Precision
* Recall
* F1-score
* Confusion Matrix
* classification threshold analysis

Для задачи churn особое внимание уделяется **Recall и Precision**, поскольку стоимость ошибок для бизнеса различается.

---

# 📊 Explainable ML

Для интерпретации модели используются методы анализа feature importance / SHAP.

Это позволяет отвечать на вопросы:

* какие признаки сильнее всего влияют на churn;
* почему конкретный клиент получил высокий risk score;
* какие характеристики связаны с повышенным риском оттока.

Пример:

```text
Customer
   ↓
ML Model
   ↓
Churn Probability = 0.87
   ↓
High Risk
   ↓
Retention Strategy
```

---

# 🧪 A/B Testing

В проект добавлен модуль для проведения A/B-экспериментов.

Основная задача эксперимента — проверить, приводит ли изменение стратегии обработки клиентов к статистически значимому изменению целевой метрики.

## Распределение пользователей

Для распределения клиентов используется **детерминированная рандомизация** на основе `customer_id`.

```text
customer_id
     ↓
 SHA-256 hash
     ↓
 bucket
     ↓
 ┌───────────────┐
 │               │
 ▼               ▼
Control       Treatment
```

Это позволяет гарантировать, что один и тот же пользователь будет стабильно попадать в одну экспериментальную группу.

Также предусмотрены:

* configurable traffic split;
* feature flag для включения/выключения эксперимента;
* fallback для пользователей без `customer_id`.

---

# 📐 Statistical Testing

Модуль `statistics.py` содержит инструменты для статистического анализа результатов эксперимента.

Реализованы:

* формулировка нулевой и альтернативной гипотез;
* two-proportion z-test;
* расчёт pooled proportion;
* standard error;
* p-value;
* confidence interval;
* statistical significance;
* sample size calculation;
* Minimum Detectable Effect (MDE);
* statistical power.

Пример постановки:

```text
H₀:
p_control = p_treatment

H₁:
p_control ≠ p_treatment
```

При:

```text
α = 0.05
```

результат считается статистически значимым при:

```text
p-value < 0.05
```

---

# 🧮 Experiment Design

Перед запуском эксперимента можно определить необходимый размер выборки.

Основные параметры:

```text
Baseline conversion
        +
Minimum Detectable Effect
        +
Significance level
        +
Statistical power
        ↓
Required Sample Size
```

Стандартные параметры:

```text
α = 0.05
Power = 0.80
```

Это позволяет избежать ситуации, когда эксперимент запускается на слишком маленькой выборке и не способен обнаружить практически значимый эффект.

---

# 🔬 ML + Experimentation

Ключевая идея проекта — не останавливаться на качестве ML-модели.

```text
                    ML
                     │
                     ▼
             Churn Probability
                     │
                     ▼
              High-risk users
                     │
                     ▼
             Experimentation
              ┌──────┴──────┐
              ▼             ▼
           Control       Treatment
              │             │
              └──────┬──────┘
                     ▼
              Business Metric
                     │
                     ▼
             Statistical Test
                     │
                     ▼
              Business Decision
```

Таким образом, ML-модель рассматривается не как конечный результат, а как часть продукта.

---

# ⚙️ Backend

Backend реализован на **FastAPI**.

Основные задачи:

* REST API;
* inference ML-модели;
* работа с клиентскими данными;
* A/B assignment;
* сбор результатов эксперимента;
* взаимодействие с PostgreSQL.

Структура backend:

```text
backend/
├── app/
│   ├── api/
│   ├── core/
│   │   ├── ab_testing.py
│   │   └── statistics.py
│   ├── models/
│   ├── schemas/
│   └── services/
├── tests/
└── Dockerfile
```

---

# 🗄️ Database

В качестве основной СУБД используется **PostgreSQL**.

База данных используется для:

* хранения клиентов;
* хранения prediction results;
* хранения результатов экспериментов;
* работы backend-сервиса.

---

# 🖥️ Frontend

Для проекта реализован frontend, позволяющий взаимодействовать с ML-сервисом.

Основные возможности:

* просмотр клиентских данных;
* получение churn prediction;
* отображение результатов;
* взаимодействие с backend API.

---

# 🧪 Testing

Для backend реализованы автоматизированные тесты.

Проверяются:

* API endpoints;
* бизнес-логика;
* A/B assignment;
* статистические функции;
* обработка некорректных входных данных.

Используется:

```text
pytest
```

---

# 🐳 Infrastructure

Проект контейнеризирован с использованием Docker.

Основные компоненты:

```text
Docker
Docker Compose
FastAPI
PostgreSQL
```

Запуск проекта:

```bash
docker compose up --build
```

---

# 📁 Project Structure

```text
ChurnPrediction/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   │   ├── ab_testing.py
│   │   │   └── statistics.py
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── tests/
│   └── Dockerfile
│
├── frontend/
│
├── ml_core/
│   └── notebooks/
│
├── docs/
│
├── docker-compose.yml
└── README.md
```

---

# 🛠️ Tech Stack

### Data Science

* Python
* Pandas
* NumPy
* Scikit-learn
* CatBoost
* LightGBM
* SHAP
* Matplotlib
* Seaborn
* Jupyter

### Statistics

* Hypothesis Testing
* Two-Proportion Z-Test
* Confidence Intervals
* Statistical Power
* Sample Size Estimation
* MDE

### Backend

* FastAPI
* Pydantic
* REST API
* Pytest

### Database

* PostgreSQL
* SQL

### Infrastructure

* Docker
* Docker Compose
* Git

---

# 🎯 Что демонстрирует проект

Проект демонстрирует навыки работы с полным ML lifecycle:

```text
Data
 ↓
EDA
 ↓
Feature Engineering
 ↓
Machine Learning
 ↓
Model Evaluation
 ↓
Explainability
 ↓
REST API
 ↓
Database
 ↓
A/B Testing
 ↓
Statistical Analysis
 ↓
Business Decision
```

Особое внимание уделено переходу от **«модель показывает хороший score»** к вопросу:

> **«Приносит ли использование модели реальную пользу продукту?»**

---

# 🚀 Возможные дальнейшие улучшения

* [ ] Добавить полноценный business-oriented retention A/B test
* [ ] Добавить CUPED
* [ ] Добавить guardrail metrics
* [ ] Добавить monitoring ML-модели
* [ ] Добавить data drift detection
* [ ] Добавить experiment dashboard
* [ ] Добавить CI/CD
* [ ] Добавить model registry
* [ ] Добавить automated retraining pipeline

---

# 👨‍💻 Author

**whunotexplain**

Student / Junior Data Scientist & Backend Developer

Интересы:

* Machine Learning
* Data Science
* Data Analytics
* Statistics
* Backend Development
* MLOps

---

## ⭐ Основная идея

> **ChurnPrediction — это не просто модель классификации. Это попытка построить полноценную систему, в которой ML-модель становится частью продукта, а её влияние проверяется с помощью статистического эксперимента.**
