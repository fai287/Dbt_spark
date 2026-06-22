-- Order-grain fact table, conformed to the current customer dimension.
-- Carries the customer's current city/name (denormalized) so the table is
-- directly visualizable, and customer_id to relate to dim_customers_current.
select
    o.order_id,
    o.customer_id,
    c.customer_key,
    c.name        as customer_name,
    c.city        as customer_city,
    o.order_date,
    o.amount,
    o.status      as order_status
from {{ ref('stg_orders') }} o
left join {{ ref('dim_customers_current') }} c
    on o.customer_id = c.customer_id
