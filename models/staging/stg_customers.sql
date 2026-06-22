-- Staging view over the raw customers table ingested from PostgreSQL.
select
    customer_id,
    name,
    email,
    city,
    registration_date,
    status,
    last_updated
from {{ source('raw', 'customers') }}
