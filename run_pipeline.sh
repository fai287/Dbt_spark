#!/usr/bin/env bash
# End-to-end pipeline:
#   PostgreSQL  ->  Spark (JDBC ingestion)  ->  dbt-spark (SCD2 snapshot + marts)  ->  CSV + Postgres gold
#
# Usage:
#   ./run_pipeline.sh            # full run incl. data generation + SCD2 change simulation
#   ./run_pipeline.sh --no-gen   # skip regenerating source data (re-run models only)
#
# IMPORTANT: local Spark uses an embedded Derby metastore (./metastore_db) that
# only ONE JVM may open at a time. Each step below runs in a process that EXITS
# before the next starts. Never leave a `pyspark` shell open while dbt runs, or
# you'll hit: "Another instance of Derby may have already booted the database".
set -euo pipefail
cd "$(dirname "$0")"

export SPARK_CONF_DIR="$(pwd)/spark_conf"   # supplies Delta + JDBC jars to every Spark session
PG="PGPASSWORD=${DB_PASSWORD:-kali} psql -h ${DB_HOST:-localhost} -U ${DB_USER:-pipeline_user} -d ${DB_NAME:-pipeline_db}"

[ -f ../venv/bin/activate ] && source ../venv/bin/activate

unlock() { rm -f metastore_db/db.lck metastore_db/dbex.lck 2>/dev/null || true; }

if [ "${1:-}" != "--no-gen" ]; then
  echo ">>> [1/8] Generating 100k customers + 300k orders in PostgreSQL ..."
  eval "$PG -v ON_ERROR_STOP=1 -f sql/01_generate_source_data.sql"
fi

echo ">>> [2/8] Ingesting source tables PostgreSQL -> Spark (run 1) ..."
unlock; python ingest_postgres_to_spark.py

echo ">>> [3/8] dbt snapshot (SCD2 run 1 - initial load) ..."
unlock; dbt snapshot

if [ "${1:-}" != "--no-gen" ]; then
  echo ">>> [4/8] Simulating source changes for SCD2 history ..."
  eval "$PG -v ON_ERROR_STOP=1 -f sql/02_simulate_changes.sql"

  echo ">>> [5/8] Re-ingesting changed source -> Spark (run 2) ..."
  unlock; python ingest_postgres_to_spark.py

  echo ">>> [6/8] dbt snapshot (SCD2 run 2 - captures history) ..."
  unlock; dbt snapshot
fi

echo ">>> [7/8] Building dbt marts (dim + fact star schema) ..."
unlock; dbt run

echo ">>> [8/8] Publishing gold tables to CSV + PostgreSQL gold schema ..."
eval "$PG -c 'CREATE SCHEMA IF NOT EXISTS gold AUTHORIZATION ${DB_USER:-pipeline_user};'"
rm -rf powerbi_export
unlock; python export_for_powerbi.py
# flatten Spark CSV folders into single friendly files
for d in powerbi_export/*/; do
  name="$(basename "$d")"
  part="$(find "$d" -name 'part-*.csv' | head -1)"
  [ -n "$part" ] && cp "$part" "powerbi_export/${name}.csv"
done

echo ">>> Pipeline complete. Power BI sources: ./powerbi_export/*.csv  and  Postgres schema 'gold'."
