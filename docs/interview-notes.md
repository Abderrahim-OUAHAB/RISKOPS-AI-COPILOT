# Interview Notes

## Churn

Churn means a customer is likely to leave or stop paying. In this project, churn prediction helps prioritize customers that need proactive action.

## Feature Engineering

Feature engineering transforms raw customer fields into model-ready signals. Examples include payment risk flags, support risk flags, contract type encoding and average monthly value.

## XGBoost

XGBoost is a gradient boosting algorithm based on decision trees. It works well for tabular business data because it captures non-linear patterns and feature interactions.

## Scikit-learn

Scikit-learn provides the training utilities around the model, such as train/test split and classification metrics.

## MLflow

MLflow tracks experiments, parameters, metrics and model artifacts. It makes model training reproducible and easier to compare across runs.

## Classification Metrics

Accuracy measures global correctness. Precision measures how many predicted churn customers were truly churn. Recall measures how many churn customers were found. F1 balances precision and recall. ROC AUC measures ranking quality when probabilities are available.

## Saved Model

The trained model is saved to `ml/models/churn_model.pkl`. The exact feature order is saved to `ml/models/churn_features.json` so prediction uses the same input contract as training.

## Prediction Endpoint

`POST /risk/predict` loads a customer from PostgreSQL, applies the same feature engineering, loads the saved model, predicts churn probability and returns a risk score, risk level and simple reasons.
