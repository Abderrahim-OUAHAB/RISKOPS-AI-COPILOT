import json
import os
import subprocess
import sys
import warnings
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
BACKEND_ROOT = PROJECT_ROOT / "backend"
sys.path.append(str(BACKEND_ROOT))
sys.path.append(str(PROJECT_ROOT))
os.environ.setdefault("GIT_PYTHON_REFRESH", "quiet")
warnings.filterwarnings(
    "ignore",
    message="Hint: Inferred schema contains integer column",
)

try:
    import joblib
    import mlflow
    import mlflow.sklearn
    import pandas as pd
    from dotenv import load_dotenv
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        precision_score,
        recall_score,
        roc_auc_score,
    )
    from sklearn.model_selection import train_test_split
    from sqlalchemy import create_engine, text
    from xgboost import XGBClassifier
except ModuleNotFoundError:
    if os.getenv("RISKOPS_TRAINING_DOCKER_DELEGATE") == "1":
        raise

    result = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "-e",
            "RISKOPS_TRAINING_DOCKER_DELEGATE=1",
            "-e",
            "GIT_PYTHON_REFRESH=quiet",
            "backend",
            "python",
            "ml/training/train_churn_model.py",
        ],
        cwd=PROJECT_ROOT,
        check=False,
    )
    raise SystemExit(result.returncode)

from app.services.feature_engineering import FEATURE_COLUMNS, prepare_features  # noqa: E402

SAMPLE_PATH = PROJECT_ROOT / "data" / "sample" / "customers_sample.csv"
MODEL_DIR = PROJECT_ROOT / "ml" / "models"
MODEL_PATH = MODEL_DIR / "churn_model.pkl"
FEATURES_PATH = MODEL_DIR / "churn_features.json"


def main() -> None:
    load_dotenv(PROJECT_ROOT / ".env")
    dataframe = load_training_dataframe()
    X, y = prepare_features(dataframe, include_target=True)

    if len(dataframe) < 6:
        raise ValueError("Dataset is too small for a reliable train/test split.")
    if y.nunique() < 2:
        raise ValueError("Dataset must contain both churn classes: 0 and 1.")

    stratify = y if y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.3,
        random_state=42,
        stratify=stratify,
    )

    model = XGBClassifier(
        n_estimators=80,
        max_depth=3,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        random_state=42,
    )

    mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI", "file:./mlruns")
    experiment_name = os.getenv("MLFLOW_EXPERIMENT_NAME", "riskops-churn-model")
    mlflow.set_tracking_uri(mlflow_tracking_uri)
    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name="xgboost-churn-baseline"):
        model.fit(X_train, y_train)
        predictions = model.predict(X_test)
        probabilities = model.predict_proba(X_test)[:, 1]
        metrics = calculate_metrics(y_test, predictions, probabilities)

        mlflow.log_params(
            {
                "model_type": "XGBClassifier",
                "n_estimators": model.n_estimators,
                "max_depth": model.max_depth,
                "learning_rate": model.learning_rate,
                "feature_count": len(FEATURE_COLUMNS),
                "training_rows": len(X_train),
                "test_rows": len(X_test),
            }
        )
        for metric_name, metric_value in metrics.items():
            if metric_value is not None:
                mlflow.log_metric(metric_name, metric_value)

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        model_bundle = {"model": model, "features": FEATURE_COLUMNS}
        joblib.dump(model_bundle, MODEL_PATH)
        with FEATURES_PATH.open("w", encoding="utf-8") as features_file:
            json.dump({"features": FEATURE_COLUMNS}, features_file, indent=2)

        mlflow.sklearn.log_model(
            model,
            artifact_path="model",
            input_example=X_train.head(1),
        )
        mlflow.log_artifact(str(FEATURES_PATH))

    print(
        json.dumps(
            {
                "rows": len(dataframe),
                "features": FEATURE_COLUMNS,
                "metrics": metrics,
                "model_path": str(MODEL_PATH),
                "features_path": str(FEATURES_PATH),
            },
            indent=2,
        )
    )


def load_training_dataframe() -> pd.DataFrame:
    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        try:
            return load_from_postgres(database_url)
        except Exception as exc:
            print(f"PostgreSQL load failed, falling back to sample CSV: {exc}")

    return pd.read_csv(SAMPLE_PATH)


def load_from_postgres(database_url: str) -> pd.DataFrame:
    urls_to_try = [database_url]
    if "@postgres:" in database_url:
        urls_to_try.append(database_url.replace("@postgres:", "@localhost:"))

    last_error: Exception | None = None
    query = text(
        """
        SELECT
            customer_external_id AS customer_id,
            name,
            tenure,
            monthly_charges,
            total_charges,
            contract_type,
            support_tickets,
            late_payments,
            churn
        FROM customers
        WHERE churn IS NOT NULL
        """
    )
    for url in urls_to_try:
        try:
            engine = create_engine(url)
            dataframe = pd.read_sql(query, engine)
            if dataframe.empty:
                raise ValueError("No labeled customers found in PostgreSQL.")
            return dataframe
        except Exception as exc:
            last_error = exc

    raise RuntimeError(last_error)


def calculate_metrics(y_test, predictions, probabilities) -> dict[str, float | None]:
    metrics = {
        "accuracy": accuracy_score(y_test, predictions),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "f1_score": f1_score(y_test, predictions, zero_division=0),
        "roc_auc": None,
    }
    if len(set(y_test)) > 1:
        metrics["roc_auc"] = roc_auc_score(y_test, probabilities)

    return {key: round(value, 4) if value is not None else None for key, value in metrics.items()}


if __name__ == "__main__":
    main()
