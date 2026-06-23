select
    customer_id,
    name,
    tenure,
    monthly_charges,
    total_charges,
    support_tickets,
    late_payments,
    churn,
    support_risk_flag,
    payment_risk_flag,
    low_tenure_flag,
    high_value_customer_flag
from {{ ref('int_customer_risk_features') }}
