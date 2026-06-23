with source_customers as (
    select *
    from {{ source('riskops', 'customers') }}
    where customer_external_id is not null
      and trim(customer_external_id) <> ''
)

select
    trim(customer_external_id) as customer_id,
    nullif(trim(name), '') as name,
    coalesce(tenure, 0)::integer as tenure,
    coalesce(monthly_charges, 0)::numeric(12, 2) as monthly_charges,
    coalesce(total_charges, 0)::numeric(12, 2) as total_charges,
    case
        when contract_type is null or trim(contract_type) = '' then 'unknown'
        else lower(replace(replace(trim(contract_type), '-', '_'), ' ', '_'))
    end as contract_type,
    coalesce(support_tickets, 0)::integer as support_tickets,
    coalesce(late_payments, 0)::integer as late_payments,
    churn::integer as churn
from source_customers
