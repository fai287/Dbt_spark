"""
Build the analytics dashboard from the exported gold CSVs.

Outputs:
  dashboard/img/*.png   -> static charts embedded in the GitHub README
  dashboard/index.html  -> self-contained interactive dashboard (open in a browser)

Run after the pipeline has produced ./powerbi_export/*.csv:
  python build_dashboard.py
"""
import os
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from plotly.io import to_html

BASE = os.path.dirname(os.path.abspath(__file__))
EXPORT = os.path.join(BASE, "powerbi_export")
IMG = os.path.join(BASE, "dashboard", "img")
os.makedirs(IMG, exist_ok=True)

PALETTE = ["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed",
           "#0891b2", "#db2777", "#65a30d", "#ea580c", "#475569"]
plt.rcParams.update({"figure.facecolor": "white", "axes.grid": True,
                     "grid.alpha": 0.3, "axes.spines.top": False,
                     "axes.spines.right": False, "font.size": 11})


def load():
    dim = pd.read_csv(os.path.join(EXPORT, "gold_dim_customers.csv"))
    cur = pd.read_csv(os.path.join(EXPORT, "gold_dim_customers_current.csv"))
    fct = pd.read_csv(os.path.join(EXPORT, "gold_fact_orders.csv"))
    fct["order_date"] = pd.to_datetime(fct["order_date"])
    return dim, cur, fct


def savefig(fig, name):
    path = os.path.join(IMG, name)
    fig.savefig(path, dpi=110, bbox_inches="tight")
    plt.close(fig)
    print(f"[dashboard] wrote {path}")


def main():
    dim, cur, fct = load()

    # ---- aggregates ----
    sales_city = (fct.groupby("customer_city")["amount"].sum()
                  .sort_values(ascending=False))
    orders_month = (fct.set_index("order_date").resample("MS")["amount"]
                    .agg(["sum", "count"]).reset_index())
    status_dist = fct["order_status"].value_counts()
    cust_status = cur["status"].value_counts()
    scd_counts = pd.Series(
        {"Current versions": int((dim["is_current"] == True).sum()),
         "Historical versions": int((dim["is_current"] != True).sum())})

    # ===== matplotlib PNGs (for README) =====
    # 1. Sales by city
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(sales_city.index, sales_city.values / 1e6, color=PALETTE[0])
    ax.set_title("Total Sales by City"); ax.set_ylabel("Sales (millions)")
    ax.tick_params(axis="x", rotation=45)
    savefig(fig, "01_sales_by_city.png")

    # 2. Orders & revenue over time
    fig, ax = plt.subplots(figsize=(9, 4.2))
    ax.plot(orders_month["order_date"], orders_month["sum"] / 1e6,
            marker="o", color=PALETTE[1], label="Revenue (M)")
    ax.set_title("Monthly Revenue"); ax.set_ylabel("Revenue (millions)")
    ax.tick_params(axis="x", rotation=30)
    savefig(fig, "02_revenue_over_time.png")

    # 3. Order status
    fig, ax = plt.subplots(figsize=(5.5, 5.5))
    ax.pie(status_dist.values, labels=status_dist.index, autopct="%1.1f%%",
           colors=PALETTE, startangle=90, wedgeprops={"width": 0.45})
    ax.set_title("Order Status Distribution")
    savefig(fig, "03_order_status.png")

    # 4. Customer status (current dim)
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    ax.bar(cust_status.index, cust_status.values, color=[PALETTE[1], PALETTE[3]])
    ax.set_title("Active vs Inactive Customers (current)")
    ax.set_ylabel("customers")
    for i, v in enumerate(cust_status.values):
        ax.text(i, v, f"{v:,}", ha="center", va="bottom")
    savefig(fig, "04_customer_status.png")

    # 5. SCD2 versions (the headline SCD2 visual)
    fig, ax = plt.subplots(figsize=(6, 4.2))
    bars = ax.bar(scd_counts.index, scd_counts.values,
                  color=[PALETTE[0], PALETTE[2]])
    ax.set_title("SCD Type 2 — Customer Dimension Versions")
    ax.set_ylabel("rows")
    for b, v in zip(bars, scd_counts.values):
        ax.text(b.get_x() + b.get_width() / 2, v, f"{v:,}",
                ha="center", va="bottom")
    savefig(fig, "05_scd2_versions.png")

    # 6. SCD2 example timeline for one changed customer
    ex = (dim[dim["customer_id"] == 1]
          .sort_values("valid_from")
          [["customer_id", "city", "status", "valid_from", "valid_to", "is_current"]]
          .copy())
    # shorten ISO timestamps to 'YYYY-MM-DD'; mark the open (current) row
    ex["valid_from"] = ex["valid_from"].astype("string").str.slice(0, 10)
    ex["valid_to"] = (ex["valid_to"].astype("string").str.slice(0, 10)
                      .fillna("— (current)"))
    ex = ex.rename(columns={"customer_id": "cust_id"})
    fig, ax = plt.subplots(figsize=(10, 2.0)); ax.axis("off")
    tbl = ax.table(cellText=ex.values, colLabels=ex.columns,
                   loc="center", cellLoc="center")
    tbl.auto_set_font_size(False); tbl.set_fontsize(11)
    tbl.auto_set_column_width(col=list(range(len(ex.columns))))
    tbl.scale(1, 2.0)
    for j in range(len(ex.columns)):
        tbl[0, j].set_facecolor(PALETTE[0]); tbl[0, j].set_text_props(color="white")
    ax.set_title("SCD2 History — customer_id = 1 (status changed active → inactive)",
                 pad=14)
    savefig(fig, "06_scd2_example.png")

    # ===== interactive HTML dashboard =====
    fig = make_subplots(
        rows=3, cols=2,
        specs=[[{"type": "bar"}, {"type": "scatter"}],
               [{"type": "domain"}, {"type": "bar"}],
               [{"type": "bar"}, {"type": "table"}]],
        subplot_titles=("Total Sales by City", "Monthly Revenue",
                        "Order Status", "Active vs Inactive Customers",
                        "SCD2 — Dimension Versions",
                        "SCD2 History (customer_id = 1)"),
        vertical_spacing=0.09, horizontal_spacing=0.08)

    fig.add_trace(go.Bar(x=sales_city.index, y=sales_city.values,
                         marker_color=PALETTE[0], name="Sales"), 1, 1)
    fig.add_trace(go.Scatter(x=orders_month["order_date"], y=orders_month["sum"],
                             mode="lines+markers", line_color=PALETTE[1],
                             name="Revenue"), 1, 2)
    fig.add_trace(go.Pie(labels=status_dist.index, values=status_dist.values,
                         hole=0.45, marker_colors=PALETTE), 2, 1)
    fig.add_trace(go.Bar(x=cust_status.index, y=cust_status.values,
                         marker_color=[PALETTE[1], PALETTE[3]],
                         name="Customers"), 2, 2)
    fig.add_trace(go.Bar(x=scd_counts.index, y=scd_counts.values,
                         marker_color=[PALETTE[0], PALETTE[2]],
                         name="Versions"), 3, 1)
    fig.add_trace(go.Table(
        header=dict(values=list(ex.columns), fill_color=PALETTE[0],
                    font_color="white"),
        cells=dict(values=[ex[c].fillna("current").astype(str) for c in ex.columns])),
        3, 2)

    fig.update_layout(
        height=1200, showlegend=False, template="plotly_white",
        title_text="Customer Analytics — SCD2 Pipeline Dashboard "
                   "(PostgreSQL → Spark → dbt → Delta)",
        title_font_size=22)

    html_path = os.path.join(BASE, "dashboard", "index.html")
    with open(html_path, "w") as f:
        f.write(to_html(fig, include_plotlyjs="cdn", full_html=True))
    print(f"[dashboard] wrote {html_path}")
    print("[dashboard] done.")


if __name__ == "__main__":
    main()
