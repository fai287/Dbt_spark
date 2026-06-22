-- Staging view over the raw orders table ingested from PostgreSQL.
select
    order_id,
    customer_id,
    order_date,
    cast(amount as decimal(10,2)) as amount,
    status,
    last_updated
from {{ source('raw', 'orders') }}
