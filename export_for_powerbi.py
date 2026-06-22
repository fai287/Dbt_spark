"""
Publish the dbt gold tables to BI-consumable outputs:
  1. CSV files under ./powerbi_export   (portable, open anywhere)
  2. PostgreSQL schema `gold` in pipeline_db  (live Power BI connection)

Also prints SCD2 verification counts. Run after `dbt run`, from the project
dir, with SPARK_CONF_DIR pointing at ./spark_conf.
"""
import os
from pyspark.sql import SparkSession

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pipeline_db")
DB_USER = os.getenv("DB_USER", "pipeline_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "kali")
JDBC_URL = f"jdbc:postgresql://{DB_HOST}:{DB_PORT}/{DB_NAME}"

# dbt model/snapshot -> output name
EXPORTS = {
    "dim_customers": "gold_dim_customers",            # full SCD2 history
    "dim_customers_current": "gold_dim_customers_current",
    "fact_orders": "gold_fact_orders",
    "customers_snapshot": "gold_customers_snapshot",  # raw snapshot
}

CSV_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "powerbi_export")


def main():
    spark = (
        SparkSession.builder.appName("export_for_powerbi")
        .enableHiveSupport().getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")

    # ---- SCD2 verification ----
    snap = spark.table("customers_snapshot")
    total = snap.count()
    current = snap.filter("dbt_valid_to is null").count()
    historical = total - current
    print("\n================ SCD2 VERIFICATION ================")
    print(f"customers_snapshot total versions : {total}")
    print(f"  current versions (valid_to null) : {current}")
    print(f"  historical (closed) versions     : {historical}")
    print("Example customer with history (customer_id = 1):")
    snap.filter("customer_id = 1") \
        .select("customer_id", "city", "status", "dbt_valid_from", "dbt_valid_to") \
        .orderBy("dbt_valid_from").show(truncate=False)

    # ---- Publish ----
    for table, out in EXPORTS.items():
        df = spark.table(table)
        n = df.count()
        # CSV (single file)
        df.coalesce(1).write.mode("overwrite").option("header", "true") \
            .csv(os.path.join(CSV_DIR, out))
        # PostgreSQL gold schema
        df.write.format("jdbc").mode("overwrite") \
            .option("url", JDBC_URL).option("dbtable", f"gold.{out}") \
            .option("user", DB_USER).option("password", DB_PASSWORD) \
            .option("driver", "org.postgresql.Driver").save()
        print(f"[export] {table:24s} -> CSV + postgres gold.{out}  ({n} rows)")

    spark.stop()
    print("[export] done.")


if __name__ == "__main__":
    main()
