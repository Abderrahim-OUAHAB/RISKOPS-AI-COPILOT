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

## Risk Score

The RiskOps score combines model output and business signals. Churn probability contributes most of the score, then late payments, support tickets, short tenure, contract type and high-value exposure adjust the final 0 to 100 score.

## Business Prioritization

Prioritization sorts customers by risk score so an operations team can focus on the most urgent accounts first instead of scanning raw churn probabilities.

## Recommended Actions

Recommended actions translate reasons into business next steps. For example, late payments trigger invoice review, repeated tickets trigger support escalation and high risk triggers customer contact within 48 hours.

## Prediction History

Every RiskOps analysis is stored in `risk_predictions`. This creates an audit trail of the score, reasons, actions, model version and timestamp.

## LangGraph

LangGraph models the agent workflow as explicit nodes and edges. This project uses it to route a question to a controlled tool rather than letting an agent freely choose arbitrary actions.

## Controlled AI Agent

The agent can analyze a specific customer, list priority customers, generate a weekly report or ask the RAG system. Unknown questions receive a controlled fallback response.

## Tool Routing

Tool routing means mapping user intent to a known capability. A question mentioning `CUST-001` routes to customer analysis, a weekly/report question routes to the report service and a top-risk question routes to priority customers.

## Human In The Loop

The system recommends actions but does not execute them automatically. A human operator still decides whether to contact a customer, escalate support or propose retention.
