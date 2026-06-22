"""
Render a polished, high-resolution system-architecture diagram for the README.
Output: dashboard/img/architecture.png
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "dashboard", "img", "architecture.png")

# lane theme: (header color, light panel fill, box border)
LANES = {
    "postgres": ("#336791", "#eaf1f8", "#336791"),
    "spark":    ("#e25a1c", "#fdeee4", "#e25a1c"),
    "dbt":      ("#16a34a", "#e7f7ec", "#16a34a"),
    "gold":     ("#7c3aed", "#f2e9fc", "#7c3aed"),
}

fig, ax = plt.subplots(figsize=(17, 9.5))
ax.set_xlim(0, 17); ax.set_ylim(0, 10); ax.axis("off")
fig.patch.set_facecolor("white")


def box(x, y, w, h, text, fc, ec, tc="#0f172a", fs=12, bold=False, r=0.06):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle=f"round,pad=0.02,rounding_size={r}",
        linewidth=1.8, edgecolor=ec, facecolor=fc, zorder=3))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fs, color=tc, zorder=4,
            fontweight="bold" if bold else "normal", wrap=True)


def lane(cx, key, title, subtitle):
    hc, panel, _ = LANES[key]
    w = 3.7
    x = cx - w / 2
    # panel
    ax.add_patch(FancyBboxPatch(
        (x, 0.5), w, 8.4, boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=2, edgecolor=hc, facecolor=panel, zorder=1, alpha=0.9))
    # header band
    ax.add_patch(FancyBboxPatch(
        (x, 8.0), w, 0.95, boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=0, facecolor=hc, zorder=2))
    ax.text(cx, 8.62, title, ha="center", va="center", fontsize=15,
            color="white", fontweight="bold", zorder=4)
    ax.text(cx, 8.22, subtitle, ha="center", va="center", fontsize=9.5,
            color="white", zorder=4, alpha=0.95)
    return x, w


def stage_arrow(x0, x1, y, label):
    ax.add_patch(FancyArrowPatch(
        (x0, y), (x1, y), arrowstyle="-|>", mutation_scale=26,
        linewidth=3.4, color="#334155", zorder=7))
    ax.text((x0 + x1) / 2, y, label, ha="center", va="center",
            fontsize=10.5, color="#1e293b", fontweight="bold", zorder=8,
            bbox=dict(boxstyle="round,pad=0.3", facecolor="white",
                      edgecolor="#334155", linewidth=1.2))


# Title
ax.text(8.5, 9.55, "Customer Analytics Pipeline — System Architecture",
        ha="center", va="center", fontsize=21, fontweight="bold",
        color="#0f172a")
ax.text(8.5, 9.18, "PostgreSQL  →  Spark + Delta Lake  →  dbt (SCD2)  →  Dashboard / BI",
        ha="center", va="center", fontsize=12.5, color="#64748b")

cx = {"postgres": 2.3, "spark": 6.4, "dbt": 10.6, "gold": 14.7}

# ---- Lane 1: PostgreSQL ----
lane(cx["postgres"], "postgres", "1 · PostgreSQL", "source · pipeline_db")
hc, _, ec = LANES["postgres"]
box(cx["postgres"]-1.5, 6.3, 3.0, 1.0, "customers\n100,000 rows", "white", ec, fs=12, bold=True)
box(cx["postgres"]-1.5, 4.9, 3.0, 1.0, "orders\n300,000 rows", "white", ec, fs=12, bold=True)
box(cx["postgres"]-1.5, 2.6, 3.0, 1.4,
    "CDC change\n5,000 customers update\ncity / status\n(last_updated bumped)",
    "#fff7ed", "#f59e0b", tc="#9a3412", fs=9.5)

# ---- Lane 2: Spark ----
lane(cx["spark"], "spark", "2 · Spark + Delta", "JDBC ingestion · 4.1.1")
hc, _, ec = LANES["spark"]
box(cx["spark"]-1.6, 6.5, 3.2, 1.1,
    "ingest_postgres_to_spark.py\nJDBC read → managed tables", "white", ec, fs=10.5, bold=True)
box(cx["spark"]-1.6, 5.1, 1.5, 0.9, "customers", "white", ec, fs=11)
box(cx["spark"]+0.1, 5.1, 1.5, 0.9, "orders", "white", ec, fs=11)
box(cx["spark"]-1.6, 2.9, 3.2, 1.6,
    "Delta Lake\n• transactional tables\n• MERGE / UPDATE\nenables SCD2 snapshots",
    "#fff1e9", ec, tc="#9a3412", fs=9.8, bold=False)

# ---- Lane 3: dbt ----
lane(cx["dbt"], "dbt", "3 · dbt-spark", "method: session")
hc, _, ec = LANES["dbt"]
box(cx["dbt"]-1.6, 6.9, 3.2, 0.85, "staging views\nstg_customers · stg_orders", "white", ec, fs=10)
box(cx["dbt"]-1.6, 5.55, 3.2, 1.0,
    "customers_snapshot\nSCD2 history (Delta MERGE)", "#dcfce7", ec, tc="#14532d", fs=10.5, bold=True)
box(cx["dbt"]-1.6, 4.35, 3.2, 0.85, "dim_customers  (SCD2)", "white", ec, fs=10.5)
box(cx["dbt"]-1.6, 3.35, 3.2, 0.8, "dim_customers_current", "white", ec, fs=10.5)
box(cx["dbt"]-1.6, 2.35, 3.2, 0.8, "fact_orders", "white", ec, fs=10.5)
# internal flow hints
for y0, y1 in [(6.9, 6.55), (5.55, 5.2), (4.35, 4.15), (3.35, 3.15)]:
    ax.add_patch(FancyArrowPatch((cx["dbt"], y0), (cx["dbt"], y1),
                 arrowstyle="-|>", mutation_scale=12, color="#94a3b8", zorder=4))

# ---- Lane 4: Gold ----
lane(cx["gold"], "gold", "4 · Gold / Serving", "BI-ready outputs")
hc, _, ec = LANES["gold"]
box(cx["gold"]-1.6, 6.4, 3.2, 1.0, "PostgreSQL  gold.*\nlive Power BI source", "white", ec, fs=10.5, bold=True)
box(cx["gold"]-1.6, 5.0, 3.2, 1.0, "powerbi_export/*.csv\nportable extracts", "white", ec, fs=10.5, bold=True)
box(cx["gold"]-1.6, 3.2, 3.2, 1.4,
    "Dashboard\nPlotly HTML + PNG charts\n(SCD2 + sales analytics)",
    "#f3e8ff", ec, tc="#5b21b6", fs=10.5, bold=True)

# ---- stage arrows between lanes ----
stage_arrow(cx["postgres"]+1.55, cx["spark"]-1.75, 6.8, "JDBC")
stage_arrow(cx["spark"]+1.65, cx["dbt"]-1.75, 6.8, "transform")
stage_arrow(cx["dbt"]+1.65, cx["gold"]-1.75, 6.8, "publish")

# footnote
ax.text(8.5, 0.15,
        "Embedded Derby metastore → one JVM at a time: every stage runs in a process that exits before the next begins.",
        ha="center", va="center", fontsize=9.5, color="#64748b", style="italic")

plt.savefig(OUT, dpi=150, bbox_inches="tight", facecolor="white")
print(f"wrote {OUT}")
