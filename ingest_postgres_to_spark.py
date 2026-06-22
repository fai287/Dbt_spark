"""
Spark JDBC ingestion: PostgreSQL (source)  ->  Spark managed tables.

This is step 2 of the pipeline:
    PostgreSQL (source)
      -> Spark (JDBC ingestion + table creation)   <-- this script
      -> dbt-spark (transformations)

It writes Spark managed tables into the SAME local Hive metastore
(./metastore_db) and warehouse (./spark-warehouse) that dbt-spark uses
with `method: session`. Because embedded Derby allows only ONE JVM at a
time, this script starts Spark, ingests, and then EXITS, releasing the
metastore lock so `dbt run` can start its own session afterwards.

Run from the dbt project directory:
    python ingest_postgres_to_spark.py
"""
import os
from pyspark.sql import SparkSession

# --- Source connection (override via env vars if needed) -------------------
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pipeline_db")
DB_USER = os.getenv("DB_USER", "pipeline_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "kali")

JDBC_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Source tables in PostgreSQL -> target Spark table names (default schema).
TABLES = ["customers", "orders"]


def main():
    # Spark/Delta/JDBC config (jars, delta extensions, warehouse) is supplied by
    # spark_conf/spark-defaults.conf via the SPARK_CONF_DIR env var, so that this
    # script and dbt's in-process session use an identical Spark setup.
    spark = (
        SparkSession.builder
        .appName("postgres_jdbc_ingestion")
        .enableHiveSupport()  # share the Derby/Hive metastore with dbt-spark
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("WARN")

    for table in TABLES:
        print(f"[ingest] reading PostgreSQL table '{table}' ...")
        df = (
            spark.read.format("jdbc")
            .option("url", JDBC_URL)
            .option("dbtable", table)
            .option("user", DB_USER)
            .option("password", DB_PASSWORD)
            .option("driver", "org.postgresql.Driver")
            .load()
        )
        count = df.count()
        # Overwrite so the run is idempotent; registers a managed table in
        # the metastore that dbt reads via `FROM customers`.
        df.write.mode("overwrite").saveAsTable(table)
        print(f"[ingest] wrote Spark table '{table}' ({count} rows)")

    print("[ingest] tables now visible to Spark/dbt:")
    spark.sql("SHOW TABLES").show(truncate=False)
    spark.stop()
    print("[ingest] done; Spark stopped and metastore lock released.")


if __name__ == "__main__":
    main()
