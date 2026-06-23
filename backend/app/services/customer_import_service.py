from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.models import Customer

REQUIRED_CUSTOMER_COLUMNS = {
    "customer_id",
    "name",
    "tenure",
    "monthly_charges",
    "total_charges",
    "contract_type",
    "support_tickets",
    "late_payments",
    "churn",
}


class CustomerImportError(Exception):
    pass


def import_customers_from_csv(file_obj: Any, db: Session) -> int:
    try:
        dataframe = pd.read_csv(file_obj)
    except pd.errors.EmptyDataError as exc:
        raise CustomerImportError("The CSV file is empty.") from exc
    except Exception as exc:
        raise CustomerImportError("Could not read the CSV file.") from exc

    if dataframe.empty:
        raise CustomerImportError("The CSV file is empty.")

    dataframe.columns = [str(column).strip() for column in dataframe.columns]
    missing_columns = REQUIRED_CUSTOMER_COLUMNS.difference(dataframe.columns)
    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise CustomerImportError(f"Missing required columns: {missing}.")

    dataframe = dataframe.copy()
    numeric_columns = [
        "tenure",
        "monthly_charges",
        "total_charges",
        "support_tickets",
        "late_payments",
        "churn",
    ]
    for column in numeric_columns:
        dataframe[column] = pd.to_numeric(dataframe[column], errors="coerce")

    invalid_rows = dataframe[dataframe[numeric_columns].isna().any(axis=1)]
    if not invalid_rows.empty:
        row_numbers = [str(index + 2) for index in invalid_rows.index.tolist()]
        raise CustomerImportError(
            "Invalid numeric values found on CSV rows: " + ", ".join(row_numbers)
        )

    imported_count = 0
    for _, row in dataframe.iterrows():
        external_id = str(row["customer_id"]).strip()
        if not external_id:
            raise CustomerImportError("customer_id cannot be empty.")

        customer = (
            db.query(Customer)
            .filter(Customer.customer_external_id == external_id)
            .one_or_none()
        )
        if customer is None:
            customer = Customer(customer_external_id=external_id)
            db.add(customer)

        support_tickets = int(row["support_tickets"])
        late_payments = int(row["late_payments"])
        monthly_charges = float(row["monthly_charges"])

        customer.name = str(row["name"]).strip()
        customer.segment = str(row.get("segment", "")).strip() or None
        customer.monthly_spend = monthly_charges
        customer.tenure = int(row["tenure"])
        customer.monthly_charges = monthly_charges
        customer.total_charges = float(row["total_charges"])
        customer.contract_type = str(row["contract_type"]).strip()
        customer.support_tickets = support_tickets
        customer.late_payments = late_payments
        customer.churn = int(row["churn"])
        customer.support_ticket_count = support_tickets
        customer.unpaid_invoice_count = late_payments
        imported_count += 1

    db.commit()
    return imported_count
