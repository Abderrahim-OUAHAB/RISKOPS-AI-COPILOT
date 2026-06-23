from typing import Iterable

import pandas as pd

from app.models import Customer

FEATURE_COLUMNS = [
    "tenure",
    "monthly_charges",
    "total_charges",
    "support_tickets",
    "late_payments",
    "contract_type_month_to_month",
    "contract_type_one_year",
    "contract_type_two_year",
    "average_monthly_value",
    "payment_risk_flag",
    "support_risk_flag",
]


class FeatureEngineeringError(Exception):
    pass


def customers_to_dataframe(customers: Iterable[Customer]) -> pd.DataFrame:
    rows = []
    for customer in customers:
        rows.append(
            {
                "customer_id": customer.customer_external_id,
                "name": customer.name,
                "tenure": customer.tenure,
                "monthly_charges": customer.monthly_charges,
                "total_charges": customer.total_charges,
                "contract_type": customer.contract_type,
                "support_tickets": customer.support_tickets,
                "late_payments": customer.late_payments,
                "churn": customer.churn,
            }
        )
    return pd.DataFrame(rows)


def prepare_features(
    dataframe: pd.DataFrame,
    include_target: bool = True,
) -> tuple[pd.DataFrame, pd.Series | None]:
    missing_columns = {
        "tenure",
        "monthly_charges",
        "total_charges",
        "contract_type",
        "support_tickets",
        "late_payments",
    }.difference(dataframe.columns)
    if include_target:
        missing_columns = missing_columns.union({"churn"}.difference(dataframe.columns))

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise FeatureEngineeringError(f"Missing feature columns: {missing}.")

    features = dataframe.copy()
    numeric_columns = [
        "tenure",
        "monthly_charges",
        "total_charges",
        "support_tickets",
        "late_payments",
    ]
    if include_target:
        numeric_columns.append("churn")

    for column in numeric_columns:
        features[column] = pd.to_numeric(features[column], errors="coerce")

    required_columns = numeric_columns + ["contract_type"]
    if features[required_columns].isna().any().any():
        raise FeatureEngineeringError("Invalid or missing values found in ML features.")

    contract_type = features["contract_type"].map(_normalize_contract_type)
    engineered = pd.DataFrame(index=features.index)
    engineered["tenure"] = features["tenure"].astype(float)
    engineered["monthly_charges"] = features["monthly_charges"].astype(float)
    engineered["total_charges"] = features["total_charges"].astype(float)
    engineered["support_tickets"] = features["support_tickets"].astype(float)
    engineered["late_payments"] = features["late_payments"].astype(float)
    engineered["contract_type_month_to_month"] = (
        contract_type == "month_to_month"
    ).astype(int)
    engineered["contract_type_one_year"] = (contract_type == "one_year").astype(int)
    engineered["contract_type_two_year"] = (contract_type == "two_year").astype(int)
    engineered["average_monthly_value"] = engineered["total_charges"] / engineered[
        "tenure"
    ].clip(lower=1)
    engineered["payment_risk_flag"] = (engineered["late_payments"] >= 2).astype(int)
    engineered["support_risk_flag"] = (engineered["support_tickets"] >= 5).astype(int)

    engineered = engineered[FEATURE_COLUMNS].astype(float)
    target = features["churn"].astype(int) if include_target else None
    return engineered, target


def customer_to_feature_frame(customer: Customer) -> pd.DataFrame:
    dataframe = customers_to_dataframe([customer])
    features, _ = prepare_features(dataframe, include_target=False)
    return features


def risk_reasons(customer: Customer) -> list[str]:
    reasons = []
    if (customer.support_tickets or 0) >= 5:
        reasons.append("Many support tickets")
    if (customer.late_payments or 0) > 0:
        reasons.append("Late payments detected")
    if customer.tenure is not None and customer.tenure < 12:
        reasons.append("Short customer tenure")
    if _normalize_contract_type(customer.contract_type) == "month_to_month":
        reasons.append("Month-to-month contract")
    if not reasons:
        reasons.append("No major risk driver detected")
    return reasons


def risk_level_from_score(risk_score: int) -> str:
    if risk_score >= 70:
        return "high"
    if risk_score >= 40:
        return "medium"
    return "low"


def _normalize_contract_type(value: object) -> str:
    normalized = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "monthly": "month_to_month",
        "month": "month_to_month",
        "month_to_month": "month_to_month",
        "one_year": "one_year",
        "1_year": "one_year",
        "annual": "one_year",
        "two_year": "two_year",
        "2_year": "two_year",
        "biannual": "two_year",
    }
    return aliases.get(normalized, normalized)
