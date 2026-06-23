with customers as (
    select *
    from {{ ref('stg_customers') }}
)

select
    customer_id,
    name,
    tenure,
    monthly_charges,
    total_charges,
    contract_type,
    support_tickets,
    late_payments,
    churn,
    case when support_tickets >= 5 then 1 else 0 end as support_risk_flag,
    case when late_payments > 0 then 1 else 0 end as payment_risk_flag,
    case when tenure < 12 then 1 else 0 end as low_tenure_flag,
    case when total_charges >= 5000 then 1 else 0 end as high_value_customer_flag
from customers
