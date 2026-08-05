"""Скрипт обучения модели Churn Prediction."""
import argparse
import json
import warnings
from pathlib import Path

import joblib
import numpy as np
import optuna
import pandas as pd
import shap
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    roc_auc_score,
    precision_recall_curve,
    average_precision_score,
    f1_score,
    classification_report,
)
import lightgbm as lgb

from src.preprocess import FeatureEngineer, build_preprocessor, get_feature_columns
from src.utils import setup_logging, ensure_dir

warnings.filterwarnings("ignore")
logger = setup_logging()


def load_data(path: str) -> pd.DataFrame:
    """Загружает датасет Telco Customer Churn."""
    df = pd.read_csv(path)
    # TotalCharges может быть строкой с пробелами
    df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
    df = df.dropna(subset=["TotalCharges"])
    return df


def objective(trial, X_train, y_train, preprocessor, cv):
    """Целевая функция для Optuna."""
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 100, 500),
        "max_depth": trial.suggest_int("max_depth", 3, 12),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.3, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 15, 127),
        "subsample": trial.suggest_float("subsample", 0.5, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.5, 1.0),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True),
        "class_weight": "balanced",
        "random_state": 42,
        "verbosity": -1,
    }

    aucs = []
    for train_idx, val_idx in cv.split(X_train, y_train):
        X_tr, X_val = X_train.iloc[train_idx], X_train.iloc[val_idx]
        y_tr, y_val = y_train.iloc[train_idx], y_train.iloc[val_idx]

        model = lgb.LGBMClassifier(**params)
        pipe = Pipeline([
            ("fe", FeatureEngineer()),
            ("preprocessor", preprocessor),
            ("classifier", model),
        ])
        pipe.fit(X_tr, y_tr)
        val_proba = pipe.predict_proba(X_val)[:, 1]
        aucs.append(roc_auc_score(y_val, val_proba))

    return np.mean(aucs)


def train_model(data_path: str, output_dir: str, n_trials: int = 100) -> None:
    """Полный пайплайн обучения."""
    output_dir = Path(output_dir)
    ensure_dir(output_dir)
    models_dir = output_dir / "models"
    ensure_dir(models_dir)

    # 1. Загрузка
    logger.info("Загрузка данных...")
    df = load_data(data_path)
    logger.info(f"Датасет: {df.shape}")

    # 2. Разделение
    X = df.drop(columns=["Churn"])
    y = df["Churn"].map({"Yes": 1, "No": 0})
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f"Train: {X_train.shape}, Test: {X_test.shape}")

    # 3. Предобработка (fit на train)
    logger.info("Создание preprocessor...")
    numeric, categorical, ordinal = get_feature_columns()
    preprocessor = build_preprocessor(categorical, numeric, ordinal)

    # 4. Optuna
    logger.info(f"Оптимизация гиперпараметров (Optuna, {n_trials} trials)...")
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

    study = optuna.create_study(direction="maximize", sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(
        lambda trial: objective(trial, X_train, y_train, preprocessor, cv),
        n_trials=n_trials,
        show_progress_bar=True,
    )

    logger.info(f"Лучший ROC-AUC (CV): {study.best_value:.4f}")
    logger.info(f"Лучшие параметры: {json.dumps(study.best_params, indent=2)}")

    # 5. Финальное обучение на всём train
    logger.info("Финальное обучение...")
    best_model = lgb.LGBMClassifier(
        **study.best_params,
        class_weight="balanced",
        random_state=42,
        verbosity=-1,
    )
    final_pipe = Pipeline([
        ("fe", FeatureEngineer()),
        ("preprocessor", preprocessor),
        ("classifier", best_model),
    ])
    final_pipe.fit(X_train, y_train)

    # 6. Оценка на test
    logger.info("Оценка на test...")
    test_proba = final_pipe.predict_proba(X_test)[:, 1]
    test_pred = final_pipe.predict(X_test)

    metrics = {
        "roc_auc": float(roc_auc_score(y_test, test_proba)),
        "pr_auc": float(average_precision_score(y_test, test_proba)),
        "f1": float(f1_score(y_test, test_pred)),
        "best_params": study.best_params,
    }
    logger.info(f"Test ROC-AUC: {metrics['roc_auc']:.4f}")
    logger.info(f"Test PR-AUC:  {metrics['pr_auc']:.4f}")
    logger.info(f"Test F1:      {metrics['f1']:.4f}")
    logger.info("\n" + classification_report(y_test, test_pred, target_names=["No Churn", "Churn"]))

    # 7. Сохранение
    model_path = models_dir / "churn_model.joblib"
    joblib.dump(final_pipe, model_path)
    logger.info(f"Модель сохранена: {model_path}")

    # Сохранение метрик
    metrics_path = output_dir / "metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    logger.info(f"Метрики сохранены: {metrics_path}")

    # 8. SHAP summary plot (опционально)
    try:
        logger.info("Построение SHAP summary plot...")
        fe = final_pipe.named_steps["fe"]
        prep = final_pipe.named_steps["preprocessor"]
        clf = final_pipe.named_steps["classifier"]

        X_test_fe = fe.transform(X_test)
        X_test_tr = prep.transform(X_test_fe)
        feature_names = list(prep.get_feature_names_out())

        explainer = shap.TreeExplainer(clf)
        shap_values = explainer.shap_values(X_test_tr)
        if isinstance(shap_values, list):
            shap_values = shap_values[1]

        shap.summary_plot(shap_values, X_test_tr, feature_names=feature_names, show=False)
        import matplotlib.pyplot as plt
        plt.savefig(output_dir / "shap_summary.png", bbox_inches="tight")
        logger.info(f"SHAP plot сохранён: {output_dir / 'shap_summary.png'}")
    except Exception as e:
        logger.warning(f"Не удалось построить SHAP plot: {e}")

    logger.info("✅ Обучение завершено!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Обучение модели Churn Prediction")
    parser.add_argument("--data", type=str, default="data/WA_Fn-UseC_-Telco-Customer-Churn.csv",
                        help="Путь к CSV-файлу")
    parser.add_argument("--output", type=str, default=".", help="Директория для артефактов")
    parser.add_argument("--trials", type=int, default=50, help="Количество trials Optuna")
    args = parser.parse_args()

    train_model(args.data, args.output, n_trials=args.trials)
