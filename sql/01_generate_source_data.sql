-- Generate the 100k-customer + 300k-order source dataset in PostgreSQL.
-- Run as the pipeline user against pipeline_db:
--   PGPASSWORD=kali psql -h localhost -U pipeline_user -d pipeline_db -f sql/01_generate_source_data.sql

TRUNCATE customers RESTART IDENTITY CASCADE;

INSERT INTO customers (customer_id, name, email, city, registration_date, status, last_updated)
SELECT
    g,
    (ARRAY['Alice','Bob','Carol','David','Eve','Frank','Grace','Henry','Irene','John',
           'Karen','Leo','Mary','Nina','Oscar','Paul','Quinn','Rita','Sam','Tina'])[1 + (g % 20)]
      || ' ' ||
    (ARRAY['Johnson','Smith','Davis','Wilson','Brown','Otieno','Kamau','Wanjiru','Mwangi','Achieng',
           'Kiptoo','Hassan','Njoroge','Omar','Cheruiyot','Ali','Mutua','Owino','Korir','Wafula'])[1 + ((g/20) % 20)],
    'cust' || g || '@email.com',
    (ARRAY['Nairobi','Mombasa','Kisumu','Nakuru','Eldoret','Thika','Nyeri','Machakos','Kakamega','Kericho'])[1 + (g % 10)],
    DATE '2020-01-01' + (floor(random()*1825))::int,
    CASE WHEN random() < 0.85 THEN 'active' ELSE 'inactive' END,
    TIMESTAMP '2026-01-01 00:00:00'
FROM generate_series(1, 100000) AS g;

INSERT INTO orders (order_id, customer_id, order_date, amount, status, last_updated)
SELECT
    g,
    1 + (floor(random()*100000))::int,
    DATE '2024-01-01' + (floor(random()*730))::int,
    round((random()*490 + 10)::numeric, 2),
    (ARRAY['completed','completed','completed','pending','cancelled'])[1 + (floor(random()*5))::int],
    TIMESTAMP '2026-01-01 00:00:00'
FROM generate_series(1, 300000) AS g;

SELECT (SELECT count(*) FROM customers) AS customers,
       (SELECT count(*) FROM orders)    AS orders;
