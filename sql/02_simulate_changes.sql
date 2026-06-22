-- Simulate change-data-capture so the dbt snapshot records SCD2 history.
-- Changes city + status and bumps last_updated for 5,000 customers.
-- Run between the first and second `dbt snapshot`:
--   PGPASSWORD=kali psql -h localhost -U pipeline_user -d pipeline_db -f sql/02_simulate_changes.sql

UPDATE customers
SET city = (ARRAY['Nairobi','Mombasa','Kisumu','Nakuru','Eldoret'])[1 + (customer_id % 5)],
    status = CASE WHEN status = 'active' THEN 'inactive' ELSE 'active' END,
    last_updated = TIMESTAMP '2026-06-23 09:00:00'
WHERE customer_id <= 5000;

SELECT count(*) AS changed_rows
FROM customers
WHERE last_updated = TIMESTAMP '2026-06-23 09:00:00';
