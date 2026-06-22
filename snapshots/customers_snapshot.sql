{#
  SCD Type 2 snapshot of the customer dimension.

  dbt compares each incoming row against the stored version using the
  `last_updated` timestamp (timestamp strategy). When `last_updated`
  changes for a customer_id, dbt closes the previous version
  (sets dbt_valid_to) and inserts a new current version. This is the
  textbook Slowly Changing Dimension Type 2 pattern, maintained for us
  by dbt snapshots.

  Requires a transactional file format on Spark (delta) so dbt can MERGE
  updates into the existing snapshot table.
#}
{% snapshot customers_snapshot %}
{{
    config(
        target_schema='default',
        unique_key='customer_id',
        strategy='timestamp',
        updated_at='last_updated',
        file_format='delta',
        invalidate_hard_deletes=True
    )
}}

select
    customer_id,
    name,
    email,
    city,
    registration_date,
    status,
    last_updated
from {{ source('raw', 'customers') }}

{% endsnapshot %}
