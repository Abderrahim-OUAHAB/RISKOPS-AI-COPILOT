import json
from pathlib import Path

import joblib
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Customer
from app.services.feature_engineering import (
    FEATURE_COLUMNS,
    customer_to_feature_frame,
    risk_level_from_score,
    risk_reasons,
)


class ModelNotTrainedError(Exception):
    pass


class ModelPredictionError(Exception):
    pass


def predict_customer_risk(db: Session, customer: Customer) -> dict:
    probability = predict_churn_probability(customer)
    risk_score = int(round(probability * 100))
    risk_level = risk_level_from_score(risk_score)
    reasons = risk_reasons(customer)

    customer.churn_probability = probability
    customer.risk_score = risk_score
    customer.risk_level = risk_level
    db.commit()
    db.refresh(customer)

    return {
        "customer_id": customer.customer_external_id,
        "churn_probability": round(probability, 4),
        "risk_score": risk_score,
        "risk_level": risk_level,
        "reasons": reasons,
    }


def predict_churn_probability(customer: Customer) -> float:
    model_path = Path(settings.churn_model_path)
    features_path = Path(settings.churn_features_path)
    if not model_path.exists() or not features_path.exists():
        raise ModelNotTrainedError(
            "Churn model is not trained yet. Run ml/training/train_churn_model.py."
        )

    try:
        model_bundle = joblib.load(model_path)
        with features_path.open("r", encoding="utf-8") as features_file:
            feature_columns = json.load(features_file)["features"]
    except Exception as exc:
        raise ModelPredictionError("Could not load the churn model artifacts.") from exc

    if feature_columns != FEATURE_COLUMNS:
        raise ModelPredictionError(
            "Model features are incompatible with current feature engineering."
        )

    try:
        feature_frame = customer_to_feature_frame(customer)[feature_columns]
        model = model_bundle["model"] if isinstance(model_bundle, dict) else model_bundle
        probability = float(model.predict_proba(feature_frame)[0][1])
    except Exception as exc:
        raise ModelPredictionError("Could not predict churn risk for this customer.") from exc

    return probability
