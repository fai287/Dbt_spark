-- SCD Type 2 customer dimension built from the dbt snapshot.
-- One row per customer *version*. `is_current` flags the live version;
-- valid_from / valid_to bound the period each version was in effect.
select
    dbt_scd_id                       as customer_key,   -- surrogate key (per version)
    customer_id,                                          -- natural/business key
    upper(name)                      as name,
    email,
    city,
    registration_date,
    status,
    valid_from,
    valid_to,
    case when valid_to is null then true else false end as is_current
from (
    select
        dbt_scd_id,
        customer_id,
        name,
        email,
        city,
        registration_date,
        status,
        dbt_valid_from as valid_from,
        dbt_valid_to   as valid_to
    from {{ ref('customers_snapshot') }}
)
