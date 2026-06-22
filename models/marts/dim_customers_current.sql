-- Current-version-only customer dimension (one row per customer_id).
-- Convenient, conformed dimension for the Power BI star schema.
{{ config(materialized='view') }}

select
    customer_key,
    customer_id,
    name,
    email,
    city,
    registration_date,
    status,
    valid_from
from {{ ref('dim_customers') }}
where is_current = true
