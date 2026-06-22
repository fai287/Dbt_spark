# Customer Analytics Pipeline — PostgreSQL → Spark → dbt (SCD2) → Dashboard

An end-to-end data-engineering project that ingests source data from
**PostgreSQL** into **Apache Spark** via JDBC, models a **Slowly Changing
Dimension Type 2 (SCD2)** customer dimension using **dbt snapshots** on **Delta
Lake**, builds a star schema, and publishes the results to an analytics
**dashboard** (and Power-BI-ready outputs).

![dbt](https://img.shields.io/badge/dbt--core-1.11-orange)
![spark](https://img.shields.io/badge/Spark-4.1.1-e25a1c)
![delta](https://img.shields.io/badge/Delta_Lake-4.3.0-00add8)
![postgres](https://img.shields.io/badge/PostgreSQL-source-336791)

---

## 1. System Architecture

![System architecture](dashboard/img/architecture.png)

The whole flow runs as a single orchestrated script (`run_pipeline.sh`). Because
local Spark uses an embedded **Derby** metastore that only **one JVM** may open
at a time, every stage runs in a process that exits before the next begins.

<details>
<summary>Mermaid source (editable diagram)</summary>

```mermaid
flowchart LR
    subgraph SRC["PostgreSQL  (source: pipeline_db)"]
        C[(customers<br/>100k rows)]
        O[(orders<br/>300k rows)]
    end

    subgraph SPARK["Apache Spark 4.1.1 + Delta Lake 4.3.0"]
        ING["ingest_postgres_to_spark.py<br/>JDBC read → managed tables"]
        RC[customers]
        RO[orders]
        ING --> RC
        ING --> RO
    end

    subgraph DBT["dbt-spark  (method: session)"]
        STG["staging views<br/>stg_customers / stg_orders"]
        SNAP["snapshot: customers_snapshot<br/>SCD2 via Delta MERGE"]
        DIM["dim_customers (SCD2 history)"]
        DIMC["dim_customers_current"]
        FACT["fact_orders"]
    end

    subgraph GOLD["Gold / Serving"]
        CSV["powerbi_export/*.csv"]
        PG[("PostgreSQL schema: gold")]
        DASH["dashboard/index.html + PNGs"]
    end

    C -- JDBC --> ING
    O -- JDBC --> ING
    RC --> STG
    RO --> STG
    RC --> SNAP
    SNAP --> DIM --> DIMC
    STG --> FACT
    DIMC --> FACT
    DIM --> CSV & PG
    FACT --> CSV & PG
    CSV --> DASH

    classDef src fill:#dbeafe,stroke:#2563eb;
    classDef spark fill:#fde68a,stroke:#d97706;
    classDef dbt fill:#dcfce7,stroke:#16a34a;
    classDef gold fill:#f3e8ff,stroke:#7c3aed;
    class SRC,C,O src
    class SPARK,ING,RC,RO spark
    class DBT,STG,SNAP,DIM,DIMC,FACT dbt
    class GOLD,CSV,PG,DASH gold
```

</details>

---

## 2. The Dashboard

> Power BI Desktop is Windows-only, so this repo ships a portable dashboard
> (`dashboard/index.html`, interactive Plotly) plus the static charts below.
> The same data is also published as CSV and to a PostgreSQL `gold` schema for a
> live Power BI connection — see [Section 6](#6-connecting-power-bi).

### SCD Type 2 — the headline

| Dimension versions | Example change history |
|---|---|
| ![scd2 versions](dashboard/img/05_scd2_versions.png) | ![scd2 example](dashboard/img/06_scd2_example.png) |

100,000 current customer versions + 5,000 historical (closed) versions =
**105,000 rows** of full audit history. The right-hand table shows one customer
whose `status` changed from `active` to `inactive`: the old version was closed
(`valid_to` stamped) and a new current version opened.

### Business analytics (from `fact_orders` + `dim_customers`)

| | |
|---|---|
| ![sales by city](dashboard/img/01_sales_by_city.png) | ![revenue over time](dashboard/img/02_revenue_over_time.png) |
| ![order status](dashboard/img/03_order_status.png) | ![customer status](dashboard/img/04_customer_status.png) |

---

## 3. How SCD2 is implemented

SCD Type 2 keeps **full history**: when a tracked attribute changes, the current
row is *closed* (an end-timestamp is written) and a *new* current row is
inserted — the old value is never overwritten.

This is modeled with a **dbt snapshot** (`snapshots/customers_snapshot.sql`)
using the **timestamp strategy** on the source `last_updated` column with
`unique_key = customer_id`. dbt maintains the bookkeeping columns:

| column           | meaning                                            |
|------------------|----------------------------------------------------|
| `dbt_valid_from` | when this version became effective                 |
| `dbt_valid_to`   | when it was superseded (`NULL` = current)          |
| `dbt_scd_id`     | surrogate key, unique per version                  |

```mermaid
sequenceDiagram
    participant PG as PostgreSQL
    participant SP as Spark
    participant SN as customers_snapshot (Delta)
    Note over PG,SN: Run 1 — initial load
    PG->>SP: ingest 100k customers (last_updated = 2026-01-01)
    SP->>SN: dbt snapshot → 100,000 current rows (valid_to = NULL)
    Note over PG,SN: Source change (CDC)
    PG->>PG: 5,000 customers change city/status, last_updated = 2026-06-23
    Note over PG,SN: Run 2 — capture history
    PG->>SP: re-ingest changed rows
    SP->>SN: dbt snapshot → MERGE:<br/>close 5,000 old versions (set valid_to)<br/>insert 5,000 new current versions
    Note over SN: 105,000 versions = 100,000 current + 5,000 historical
```

### Why Delta Lake?
A dbt snapshot must **UPDATE** rows to close old versions, which plain
Hive/Parquet on Spark cannot do. Snapshots therefore require a transactional
table format — here **Delta Lake** (supports `MERGE`/`UPDATE`). It is configured
once in `spark_conf/spark-defaults.conf` and picked up by both the ingestion
script and dbt's in-process session via `SPARK_CONF_DIR`.

> `delta-spark 4.3.0` supports `pyspark <= 4.1.1`, so PySpark was pinned from
> 4.1.2 down to **4.1.1**.

---

## 4. Data model (star schema)

```mermaid
erDiagram
    DIM_CUSTOMERS_CURRENT ||--o{ FACT_ORDERS : "customer_id"
    DIM_CUSTOMERS ||--|{ DIM_CUSTOMERS_CURRENT : "is_current = true"

    DIM_CUSTOMERS {
        string customer_key PK "dbt_scd_id (per version)"
        int customer_id "business key"
        string name
        string email
        string city
        string status
        timestamp valid_from
        timestamp valid_to "NULL = current"
        boolean is_current
    }
    DIM_CUSTOMERS_CURRENT {
        string customer_key PK
        int customer_id "unique"
        string name
        string city
        string status
    }
    FACT_ORDERS {
        int order_id PK
        int customer_id FK
        string customer_city
        date order_date
        decimal amount
        string order_status
    }
```

| object                          | type        | grain / purpose                                   |
|---------------------------------|-------------|---------------------------------------------------|
| `stg_customers`, `stg_orders`   | view        | light staging over the raw ingested tables        |
| `customers_snapshot`            | snapshot    | **SCD2 history** (Delta)                           |
| `dim_customers`                 | table       | SCD2 dimension — one row per customer **version**  |
| `dim_customers_current`         | view        | current version only — one row per `customer_id`   |
| `fact_orders`                   | table       | order grain, conformed to the current customer     |

---

## 5. Data quality tests

dbt tests guard the keys that make the SCD2 model and star schema correct
(`snapshots/_snapshots.yml`, `models/marts/_marts.yml`). Run with `dbt test`
— **16 tests, all passing**:

| object                  | column         | tests                                  |
|-------------------------|----------------|----------------------------------------|
| `customers_snapshot`    | `dbt_scd_id`   | `unique`, `not_null` (one row per version) |
| `customers_snapshot`    | `customer_id`  | `not_null`                             |
| `customers_snapshot`    | `dbt_valid_from`, `dbt_updated_at` | `not_null`         |
| `dim_customers`         | `customer_key` | `unique`, `not_null`                   |
| `dim_customers_current` | `customer_id`  | `unique`, `not_null` (current grain)   |
| `fact_orders`           | `order_id`     | `unique`, `not_null`                   |
| `fact_orders`           | `customer_id`  | `not_null`, `relationships` → `dim_customers_current` |

The `unique` test on `dbt_scd_id` proves the snapshot produces exactly one row
per customer version; `unique` on `dim_customers_current.customer_id` proves the
current view collapses SCD2 history to one live row per customer.

## 6. How to run

**Prerequisites:** PostgreSQL running with database `pipeline_db`, user
`pipeline_user` (see note on credentials below), and a Python virtualenv at
`../venv` with `dbt-core`, `dbt-spark`, `pyspark==4.1.1`, `delta-spark==4.3.0`,
`pandas`, `matplotlib`, `plotly`.

```bash
cd my_dbt_project
./run_pipeline.sh             # generate data + SCD2 demo + build models + publish
python build_dashboard.py     # build dashboard from the published gold CSVs
```

Re-run models only (keep current source data): `./run_pipeline.sh --no-gen`.

Run a single stage (always export the Spark conf dir first):

```bash
export SPARK_CONF_DIR="$(pwd)/spark_conf"
python ingest_postgres_to_spark.py   # PostgreSQL -> Spark
dbt snapshot                         # build/update SCD2 history
dbt run                              # build marts
python export_for_powerbi.py         # publish CSV + Postgres gold
```

### The Derby metastore gotcha
Local Spark (`method: session`) uses an embedded **Derby** Hive metastore at
`./metastore_db` that **only one JVM can open at a time**. If you see
`Unable to instantiate SessionHiveMetaStoreClient` / Derby `XSDB6: Another
instance ... already booted the database`, a Spark/PySpark process is still
holding the lock — **never leave a `pyspark` shell open while running dbt**.

---

## 7. Connecting Power BI

The pipeline produces two Power-BI-ready sources:

- **CSV (portable):** `powerbi_export/*.csv` → Power BI → *Get Data → Text/CSV*.
- **Live PostgreSQL (serving layer):** schema `gold` in `pipeline_db`
  (`gold.gold_dim_customers`, `gold.gold_dim_customers_current`,
  `gold.gold_fact_orders`) → Power BI → *Get Data → PostgreSQL database*.

**Suggested model:** relate `gold_fact_orders[customer_id]` →
`gold_dim_customers_current[customer_id]` (many-to-one); use `gold_dim_customers`
for as-was / historical analysis via `valid_from` / `valid_to` / `is_current`.

---

## 8. Repository layout

```
my_dbt_project/
├── run_pipeline.sh                 # one-command end-to-end orchestrator
├── ingest_postgres_to_spark.py     # JDBC ingestion: PostgreSQL -> Spark tables
├── export_for_powerbi.py           # publish gold tables -> CSV + Postgres 'gold'
├── build_dashboard.py              # build dashboard (PNGs + interactive HTML)
├── spark_conf/spark-defaults.conf  # Delta + JDBC config (via SPARK_CONF_DIR)
├── sql/
│   ├── 01_generate_source_data.sql # 100k customers + 300k orders
│   └── 02_simulate_changes.sql     # 5k changes to demonstrate SCD2
├── snapshots/customers_snapshot.sql# SCD2 snapshot (Delta, timestamp strategy)
├── models/
│   ├── staging/{_sources.yml, stg_customers.sql, stg_orders.sql}
│   └── marts/{dim_customers.sql, dim_customers_current.sql, fact_orders.sql}
├── dashboard/{index.html, img/*.png}
└── powerbi_export/                 # generated CSVs (git-ignored)
```

## 9. Tech stack

PostgreSQL · PySpark **4.1.1** · Delta Lake **4.3.0** · PostgreSQL JDBC **42.7.3**
· dbt-core **1.11** · dbt-spark **1.10** (`type: spark, method: session`)
· pandas / matplotlib / plotly (dashboard)

> **Credentials note:** the scripts default to a local throwaway dev credential
> (`pipeline_user` / `kali`) for a PostgreSQL instance that only runs on the
> developer's machine. Override any of `DB_HOST`, `DB_PORT`, `DB_NAME`,
> `DB_USER`, `DB_PASSWORD` via environment variables for any other environment.
