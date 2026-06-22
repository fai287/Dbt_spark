# LinkedIn Post — Curated Package

Everything you need to publish this project on LinkedIn: the post copy (with a
viral hook), the artifacts to attach (in order), and posting tips.

---

## 🎯 Primary post (copy–paste)

> 🧠 Most data pipelines have amnesia. Mine doesn't.
>
> When a customer changes from "active" to "inactive," most systems just
> overwrite the old value. The history? Gone forever.
>
> So I built an end-to-end pipeline that never forgets — full Slowly Changing
> Dimension (SCD Type 2) history on 100,000 customers. Here's the breakdown 👇
>
> 🏗️ The stack — PostgreSQL → Spark → dbt → Dashboard
> • PostgreSQL as the source of truth (100K customers + 300K orders)
> • Apache Spark ingests it over JDBC
> • dbt snapshots model SCD2 history on Delta Lake
> • Results served back to PostgreSQL + CSV + an interactive dashboard
>
> 🔁 How the SCD2 history actually works:
> 1️⃣ Load 100K customers → run the dbt snapshot
> 2️⃣ Change 5,000 of them (city + status)
> 3️⃣ Re-run the snapshot
> → dbt automatically CLOSES the old versions and OPENS new ones.
>
> 📊 Result: 105,000 rows = 100,000 current + 5,000 historical. Zero history
> lost. Every change is auditable with valid_from / valid_to timestamps.
>
> 🧩 The hard parts nobody warns you about:
> • dbt snapshots need a transactional table format — plain Parquet can't UPDATE
>   rows. Fixed it with Delta Lake on Spark.
> • Spark's embedded Derby metastore allows only ONE process at a time — a
>   leftover PySpark shell was silently locking dbt out of the whole pipeline.
> • Had to pin PySpark to 4.1.1 to stay compatible with Delta 4.3.0.
>
> ✅ Quality gates: 16 dbt tests on every key — uniqueness, not-null, referential
> integrity — all green.
>
> 📈 And since Power BI doesn't run on Linux 😅, I built the dashboard in Plotly:
> SCD2 history + sales analytics, fully portable.
>
> It's all open source — ingestion, SCD2 modeling, testing, serving, and
> visualization, with diagrams and a one-command pipeline 👇
> 🔗 github.com/fai287/Dbt_spark
>
> If you're learning data engineering, this is a full runnable reference.
> What would you add to it? 👇
>
> #DataEngineering #dbt #ApacheSpark #SCD2 #DeltaLake #PostgreSQL #ELT
> #DataPipeline #Analytics #OpenSource

---

## 🪝 Alternative hooks (swap the first line to A/B test)

- "Your database forgets. Mine remembers every change. Here's how 👇"
- "I changed 5,000 customer records and lost exactly zero history. Here's the pipeline."
- "Overwriting data is easy. Keeping its full history is a discipline. I built the discipline 👇"
- "100,000 customers. 300,000 orders. 1 pipeline that never loses the past."

---

## 🖼️ Artifacts to attach (LinkedIn carousel / multi-image — in this order)

Post as a **document/carousel** (image posts get higher reach than link-only posts).
Put the GitHub link in the **first comment**, not the body, to maximize reach.

| # | File | Why it's the slide |
|---|------|--------------------|
| 1 | `dashboard/img/architecture.png` | The hook visual — the whole system at a glance |
| 2 | `dashboard/img/05_scd2_versions.png` | The "105K = 100K current + 5K historical" headline |
| 3 | `dashboard/img/06_scd2_example.png` | Proof: one customer's active→inactive history with valid_from/valid_to |
| 4 | `dashboard/img/01_sales_by_city.png` | Shows it's not just modeling — real analytics |
| 5 | `dashboard/img/02_revenue_over_time.png` | Time-series depth |
| 6 | `dashboard/img/03_order_status.png` *(optional)* | Rounds out the dashboard story |

> Tip: a 3–6 image carousel tends to outperform a single image. Slides 1–3 carry
> the story; 4–6 add credibility.

---

## 🧵 Optional: turn it into a short carousel (slide captions)

1. **Most pipelines forget. This one doesn't.** — system architecture
2. **SCD Type 2 = full history.** — 100K current + 5K historical versions
3. **Watch one record change.** — active → inactive, old version closed, new one opened
4. **It's a real analytics product.** — sales by city
5. **…with time-series depth.** — monthly revenue
6. **16 dbt tests. All green. Open source →** github.com/fai287/Dbt_spark

---

## 💡 Posting tips

- **First 2 lines are everything** — they're all that shows before "…see more".
- **Native images > external links** in the body. Drop the repo link in the
  first comment and/or the last line.
- **Post Tue–Thu, mid-morning** for B2B/tech reach.
- **Reply to every comment** in the first hour — engagement compounds reach.
- Keep **hashtags to 5–10**, mixing broad (#DataEngineering) and niche (#SCD2).
- Consider tagging **#dbt**, Databricks/Delta, and any data community you're in.
