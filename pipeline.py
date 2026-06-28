
import sqlite3
import time
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")  
import matplotlib.pyplot as plt

from config import (
    SALES_PATH, PRODUCTS_PATH, STORES_PATH,
    DB_PATH, TABLE_NAME, CHART_PATH, REPORTS_DIR
)
from utils import log, validate_data, print_df_info, print_execution_report



def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Teeno CSV files load karo.
    Shape, first 5 rows aur missing value summary print karo.
    """
    log.info("TASK 1 — Loading CSV files...")
    REPORTS_DIR.mkdir(exist_ok=True)

    sales    = pd.read_csv(SALES_PATH)
    products = pd.read_csv(PRODUCTS_PATH)
    stores   = pd.read_csv(STORES_PATH)

    print_df_info("sales_data", sales)
    print_df_info("products", products)
    print_df_info("stores", stores)

    log.info(f"Loaded → sales:{sales.shape}, products:{products.shape}, stores:{stores.shape}")
    return sales, products, stores






def clean_sales(df: pd.DataFrame) -> tuple[pd.DataFrame, int, int]:
    """
    Duplicates remove, nulls fix, data types correct karo.
    Returns: (cleaned_df, duplicates_removed, nulls_dropped)
    """
    log.info("TASK 2 — Cleaning sales data...")

    
    before_dedup = len(df)
    df = df.drop_duplicates()
    duplicates_removed = before_dedup - len(df)
    log.info(f"Duplicates removed: {duplicates_removed}")
    print(f"\n  [Clean] Duplicates removed : {duplicates_removed}")

    
    before_null = len(df)
    df["quantity"] = df["quantity"].fillna(0)
    df = df.dropna(subset=["amount"])
    nulls_dropped = before_null - len(df)
    log.info(f"Rows dropped (null amount): {nulls_dropped}")
    print(f"  [Clean] Null amount rows dropped : {nulls_dropped}")
    print(f"  [Clean] Shape after cleaning     : {df.shape}")

    
    df["sale_date"] = pd.to_datetime(df["sale_date"])
    df["amount"]    = df["amount"].astype(float)
    df["quantity"]  = df["quantity"].astype(int)
    log.info("Data types corrected: sale_date→datetime, amount→float, quantity→int")

    return df, duplicates_removed, nulls_dropped






def transform_data(
    sales: pd.DataFrame,
    products: pd.DataFrame,
    stores: pd.DataFrame,
) -> pd.DataFrame:
    """
    Teeno DataFrames merge karo, total_revenue add karo,
    city-wise summary print karo.
    """
    log.info("TASK 3 — Transforming data...")

    
    merged = (
        sales
        .merge(stores,   on="store_id",   how="left")
        .merge(products, on="product_id", how="left")
    )
    print(f"\n  [Transform] Merged DataFrame shape: {merged.shape}")
    print(merged.head(3).to_string(index=False))

    
    merged["total_revenue"] = (merged["quantity"] * merged["price"]).round(2)
    rev = merged["total_revenue"]
    print(f"\n  [Transform] total_revenue stats:")
    print(f"    Mean : Rs {np.mean(rev):>12,.2f}")
    print(f"    Max  : Rs {np.max(rev):>12,.2f}")
    print(f"    Min  : Rs {np.min(rev):>12,.2f}")

    city_revenue = (
        merged.groupby("city")["total_revenue"]
              .sum()
              .sort_values(ascending=False)
              .reset_index()
              .rename(columns={"total_revenue": "city_revenue"})
    )
    print("\n  [Transform] Revenue by city:")
    print(city_revenue.to_string(index=False))
    log.info("Transformation complete")
    return merged





def load_to_db(df: pd.DataFrame) -> None:
    """
    Merged DataFrame ko SQLite mein load karo.
    Top 3 products by quantity bhi print karo.
    """

    df_db = df.copy()
    df_db["sale_date"] = df_db["sale_date"].dt.strftime("%Y-%m-%d")

    with sqlite3.connect(DB_PATH) as conn:
        df_db.to_sql(TABLE_NAME, conn, if_exists="replace", index=False)
        log.info(f"Table '{TABLE_NAME}' written — {len(df_db)} rows")

        
        q_top3 = f"""
            SELECT   product_name,
                     category,
                     SUM(quantity)     AS total_qty_sold,
                     SUM(total_revenue) AS total_revenue
            FROM     {TABLE_NAME}
            GROUP BY product_name, category
            ORDER BY total_qty_sold DESC
            LIMIT    3
        """
        top3 = pd.read_sql_query(q_top3, conn)
        print("\n  [DB] Top 3 best-selling products by quantity:")
        print(top3.to_string(index=False))

    log.info(f"Database saved at: {DB_PATH}")





def generate_report() -> dict:
    """
    SQL queries se business insights nikalo.
    Summary report print karo.
    Returns dict of KPIs (dashboard ke liye use hoga).
    """
    log.info("TASK 5 — Generating business report...")
    kpis = {}

    with sqlite3.connect(DB_PATH) as conn:

        
        q_store_day = f"""
            SELECT   store_name,
                     city,
                     sale_date,
                     COUNT(*)          AS transactions,
                     SUM(quantity)     AS total_qty,
                     ROUND(SUM(total_revenue), 2) AS daily_revenue
            FROM     {TABLE_NAME}
            GROUP BY store_name, city, sale_date
            ORDER BY daily_revenue DESC
        """
        store_day_df = pd.read_sql_query(q_store_day, conn)
        print("\n  [Report] Revenue per store per day:")
        print(store_day_df.to_string(index=False))

        
        kpis["total_transactions"] = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE_NAME}"
        ).fetchone()[0]

        kpis["total_revenue"] = conn.execute(
            f"SELECT ROUND(SUM(total_revenue), 2) FROM {TABLE_NAME}"
        ).fetchone()[0]

        kpis["top_city"] = conn.execute(
            f"""SELECT city FROM {TABLE_NAME}
                GROUP BY city ORDER BY SUM(total_revenue) DESC LIMIT 1"""
        ).fetchone()[0]

        kpis["top_product"] = conn.execute(
            f"""SELECT product_name FROM {TABLE_NAME}
                GROUP BY product_name ORDER BY SUM(quantity) DESC LIMIT 1"""
        ).fetchone()[0]

        kpis["top_category"] = conn.execute(
            f"""SELECT category FROM {TABLE_NAME}
                GROUP BY category ORDER BY SUM(total_revenue) DESC LIMIT 1"""
        ).fetchone()[0]

        
        city_rev_rows = conn.execute(
            f"""SELECT city, ROUND(SUM(total_revenue),2) AS rev
                FROM {TABLE_NAME} GROUP BY city ORDER BY rev DESC"""
        ).fetchall()
        kpis["city_revenue"] = city_rev_rows

        
        prod_rows = conn.execute(
            f"""SELECT product_name, SUM(quantity) AS qty
                FROM {TABLE_NAME} GROUP BY product_name
                ORDER BY qty DESC LIMIT 7"""
        ).fetchall()
        kpis["top_products"] = prod_rows

        
        daily_rows = conn.execute(
            f"""SELECT sale_date, ROUND(SUM(total_revenue),2) AS rev
                FROM {TABLE_NAME} GROUP BY sale_date ORDER BY sale_date"""
        ).fetchall()
        kpis["daily_trend"] = daily_rows

      
        region_rows = conn.execute(
            f"""SELECT region, ROUND(SUM(total_revenue),2) AS rev
                FROM {TABLE_NAME} GROUP BY region ORDER BY rev DESC"""
        ).fetchall()
        kpis["region_revenue"] = region_rows

        kpis["store_day_df"] = store_day_df

    
    print("\n" + "═" * 50)
    print("       RETAILMART BUSINESS SUMMARY")
    print("═" * 50)
    print(f"  Total Transactions : {kpis['total_transactions']}")
    print(f"  Total Revenue      : Rs {kpis['total_revenue']:>12,.2f}")
    print(f"  Top Selling City   : {kpis['top_city']}")
    print(f"  Top Selling Product: {kpis['top_product']}")
    print(f"  Top Category       : {kpis['top_category']}")
    print("═" * 50)

    log.info(f"KPIs — Revenue: Rs {kpis['total_revenue']:,} | Top city: {kpis['top_city']} | Top product: {kpis['top_product']}")
    return kpis





def save_charts(kpis: dict) -> None:
    """2x2 matplotlib dashboard PNG save karo."""
    log.info("Generating matplotlib charts...")
    REPORTS_DIR.mkdir(exist_ok=True)

    cities   = [r[0] for r in kpis["city_revenue"]]
    city_rev = [r[1] for r in kpis["city_revenue"]]
    prods    = [r[0].split()[0] for r in kpis["top_products"]]   # first word only
    prod_qty = [r[1] for r in kpis["top_products"]]
    dates    = [r[0] for r in kpis["daily_trend"]]
    daily_r  = [r[1] for r in kpis["daily_trend"]]
    regions  = [r[0] for r in kpis["region_revenue"]]
    reg_rev  = [r[1] for r in kpis["region_revenue"]]

    COLORS = ["#4A90D9", "#50C878", "#FF6B6B", "#FFD93D",
              "#A29BFE", "#FD79A8", "#00CEC9", "#FDCB6E"]

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("RetailMart Sales Dashboard", fontsize=16,
                 fontweight="bold", y=0.98, color="#2d3436")
    fig.patch.set_facecolor("#f8f9fa")

    
    ax = axes[0, 0]
    ax.set_facecolor("#ffffff")
    bars = ax.bar(cities, city_rev, color=COLORS[:len(cities)], edgecolor="white", linewidth=0.8)
    ax.bar_label(bars, labels=[f"Rs {v/1000:.0f}K" for v in city_rev],
                 padding=3, fontsize=8, color="#636e72")
    ax.set_title("Revenue by City", fontweight="bold", fontsize=11)
    ax.set_xlabel("City"); ax.set_ylabel("Revenue (Rs)")
    ax.tick_params(axis="x", rotation=30, labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)

    
    ax = axes[0, 1]
    ax.set_facecolor("#ffffff")
    hbars = ax.barh(prods[::-1], prod_qty[::-1], color="#50C878", edgecolor="white")
    ax.bar_label(hbars, padding=4, fontsize=8, color="#636e72")
    ax.set_title("Top Products by Quantity Sold", fontweight="bold", fontsize=11)
    ax.set_xlabel("Quantity Sold")
    ax.spines[["top", "right"]].set_visible(False)

    
    ax = axes[1, 0]
    ax.set_facecolor("#ffffff")
    ax.plot(dates, daily_r, marker="o", color="#4A90D9",
            linewidth=2, markersize=6, markerfacecolor="white",
            markeredgewidth=2)
    ax.fill_between(range(len(dates)), daily_r, alpha=0.1, color="#4A90D9")
    ax.set_xticks(range(len(dates)))
    ax.set_xticklabels([d[5:] for d in dates], fontsize=8, rotation=30)
    ax.set_title("Daily Revenue Trend", fontweight="bold", fontsize=11)
    ax.set_ylabel("Revenue (Rs)")
    ax.spines[["top", "right"]].set_visible(False)

    
    ax = axes[1, 1]
    ax.set_facecolor("#ffffff")
    wedges, texts, autotexts = ax.pie(
        reg_rev, labels=regions,
        autopct="%1.1f%%", startangle=90,
        colors=COLORS[:len(regions)],
        wedgeprops={"edgecolor": "white", "linewidth": 1.5}
    )
    for t in autotexts: t.set_fontsize(9)
    ax.set_title("Revenue by Region", fontweight="bold", fontsize=11)

    plt.tight_layout(rect=[0, 0, 1, 0.96])
    plt.savefig(CHART_PATH, dpi=150, bbox_inches="tight",
                facecolor="#f8f9fa")
    plt.close()
    log.info(f"Charts saved: {CHART_PATH}")
    print(f"\n  [Charts] Saved to: {CHART_PATH}")




def generate_html_dashboard(kpis: dict) -> None:
    """
    Pure Python se HTML dashboard generate karo.
    Browser mein open karo — Chart.js charts, summary cards sab.
    Koi extra library nahi chahiye.
    """
    log.info("Generating HTML dashboard...")
    REPORTS_DIR.mkdir(exist_ok=True)

    city_labels  = str([r[0] for r in kpis["city_revenue"]])
    city_data    = str([r[1] for r in kpis["city_revenue"]])
    prod_labels  = str([r[0] for r in kpis["top_products"]])
    prod_data    = str([r[1] for r in kpis["top_products"]])
    date_labels  = str([r[0] for r in kpis["daily_trend"]])
    date_data    = str([r[1] for r in kpis["daily_trend"]])
    reg_labels   = str([r[0] for r in kpis["region_revenue"]])
    reg_data     = str([r[1] for r in kpis["region_revenue"]])

    
    store_rows = ""
    for _, row in kpis["store_day_df"].iterrows():
        store_rows += f"""
        <tr>
          <td>{row['store_name']}</td>
          <td>{row['city']}</td>
          <td>{row['sale_date']}</td>
          <td style="text-align:center">{int(row['transactions'])}</td>
          <td style="text-align:right">Rs {float(row['daily_revenue']):,.0f}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>RetailMart Sales Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
          background: #f0f2f5; color: #2d3436; min-height: 100vh; }}
  header {{ background: linear-gradient(135deg, #1a73e8, #0d47a1);
            color: white; padding: 20px 32px;
            display: flex; align-items: center; gap: 16px; }}
  header h1 {{ font-size: 22px; font-weight: 700; letter-spacing: -0.3px; }}
  header p  {{ font-size: 13px; opacity: 0.8; margin-top: 2px; }}
  .badge    {{ background: rgba(255,255,255,0.2); border-radius: 20px;
               padding: 4px 12px; font-size: 12px; font-weight: 600; }}
  .main  {{ padding: 24px 32px; max-width: 1400px; margin: 0 auto; }}
  .kpi-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
               margin-bottom: 24px; }}
  .kpi-card {{ background: white; border-radius: 12px;
               padding: 20px; border: 1px solid #e9ecef;
               box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
  .kpi-card .label {{ font-size: 12px; color: #868e96;
                      text-transform: uppercase; letter-spacing: 0.5px;
                      margin-bottom: 6px; }}
  .kpi-card .value {{ font-size: 24px; font-weight: 700; color: #1a73e8; }}
  .kpi-card .sub   {{ font-size: 12px; color: #868e96; margin-top: 4px; }}
  .chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px;
                 margin-bottom: 24px; }}
  .chart-card {{ background: white; border-radius: 12px; padding: 20px;
                 border: 1px solid #e9ecef;
                 box-shadow: 0 1px 4px rgba(0,0,0,0.06); }}
  .chart-card h3 {{ font-size: 14px; font-weight: 600; color: #495057;
                    margin-bottom: 16px; padding-bottom: 12px;
                    border-bottom: 1px solid #f1f3f5; }}
  .chart-wrap {{ position: relative; height: 240px; }}
  .table-card {{ background: white; border-radius: 12px; padding: 20px;
                 border: 1px solid #e9ecef;
                 box-shadow: 0 1px 4px rgba(0,0,0,0.06);
                 margin-bottom: 24px; }}
  .table-card h3 {{ font-size: 14px; font-weight: 600; color: #495057;
                    margin-bottom: 16px; padding-bottom: 12px;
                    border-bottom: 1px solid #f1f3f5; }}
  table {{ width: 100%; border-collapse: collapse; font-size: 13px; }}
  th {{ background: #f8f9fa; padding: 10px 12px; text-align: left;
        font-weight: 600; color: #495057; border-bottom: 2px solid #dee2e6; }}
  td {{ padding: 9px 12px; border-bottom: 1px solid #f1f3f5; color: #495057; }}
  tr:hover td {{ background: #f8f9fa; }}
  footer {{ text-align: center; padding: 20px; color: #adb5bd; font-size: 12px; }}
</style>
</head>
<body>

<header>
  <div>
    <h1>RetailMart Sales Dashboard</h1>
    <p>Data Engineering Pipeline — Auto-generated report</p>
  </div>
  <div style="margin-left:auto">
    <span class="badge">Live from SQLite DB</span>
  </div>
</header>

<div class="main">

  <!-- KPI Cards -->
  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="label">Total Transactions</div>
      <div class="value">{kpis['total_transactions']}</div>
      <div class="sub">across all stores</div>
    </div>
    <div class="kpi-card">
      <div class="label">Total Revenue</div>
      <div class="value">Rs {kpis['total_revenue']:,.0f}</div>
      <div class="sub">net sales value</div>
    </div>
    <div class="kpi-card">
      <div class="label">Top Selling City</div>
      <div class="value" style="font-size:20px">{kpis['top_city']}</div>
      <div class="sub">highest revenue city</div>
    </div>
    <div class="kpi-card">
      <div class="label">Top Product</div>
      <div class="value" style="font-size:14px;padding-top:6px">{kpis['top_product']}</div>
      <div class="sub">by units sold</div>
    </div>
  </div>

  <!-- Charts row 1 -->
  <div class="chart-grid">
    <div class="chart-card">
      <h3>Revenue by City</h3>
      <div class="chart-wrap"><canvas id="cityChart"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>Top Products by Quantity Sold</h3>
      <div class="chart-wrap"><canvas id="prodChart"></canvas></div>
    </div>
  </div>

  <!-- Charts row 2 -->
  <div class="chart-grid">
    <div class="chart-card">
      <h3>Daily Revenue Trend</h3>
      <div class="chart-wrap"><canvas id="trendChart"></canvas></div>
    </div>
    <div class="chart-card">
      <h3>Revenue by Region</h3>
      <div class="chart-wrap"><canvas id="regionChart"></canvas></div>
    </div>
  </div>

  <!-- Store daily table -->
  <div class="table-card">
    <h3>Revenue per Store per Day</h3>
    <table>
      <thead>
        <tr>
          <th>Store</th><th>City</th><th>Date</th>
          <th style="text-align:center">Transactions</th>
          <th style="text-align:right">Revenue</th>
        </tr>
      </thead>
      <tbody>
        {store_rows}
      </tbody>
    </table>
  </div>

</div>

<footer>Generated by Tanisha  &nbsp;|&nbsp; Data source: retail_sales.db</footer>

<script>
const COLORS = ['#4A90D9','#50C878','#FF6B6B','#FFD93D','#A29BFE','#FD79A8','#00CEC9','#FDCB6E'];
const OPTS   = {{ responsive:true, maintainAspectRatio:false,
                  plugins:{{ legend:{{ display:false }} }},
                  scales:{{ x:{{ grid:{{ display:false }} }}, y:{{ grid:{{ color:'#f1f3f5' }} }} }} }};

new Chart(document.getElementById('cityChart'), {{
  type:'bar',
  data:{{ labels:{city_labels}, datasets:[{{ data:{city_data},
    backgroundColor:COLORS, borderRadius:6, borderSkipped:false }}] }},
  options:{{ ...OPTS, plugins:{{ legend:{{ display:false }},
    tooltip:{{ callbacks:{{ label: c=>'Rs '+c.raw.toLocaleString('en-IN') }} }} }} }}
}});

new Chart(document.getElementById('prodChart'), {{
  type:'bar',
  data:{{ labels:{prod_labels}, datasets:[{{ data:{prod_data},
    backgroundColor:'#50C878', borderRadius:6, borderSkipped:false }}] }},
  options:{{ ...OPTS, indexAxis:'y',
    plugins:{{ legend:{{ display:false }} }} }}
}});

new Chart(document.getElementById('trendChart'), {{
  type:'line',
  data:{{ labels:{date_labels}, datasets:[{{ data:{date_data},
    borderColor:'#4A90D9', backgroundColor:'rgba(74,144,217,0.08)',
    borderWidth:2.5, pointRadius:5, pointBackgroundColor:'white',
    pointBorderWidth:2, fill:true, tension:0.3 }}] }},
  options:{{ ...OPTS, plugins:{{ legend:{{ display:false }},
    tooltip:{{ callbacks:{{ label: c=>'Rs '+c.raw.toLocaleString('en-IN') }} }} }} }}
}});

new Chart(document.getElementById('regionChart'), {{
  type:'doughnut',
  data:{{ labels:{reg_labels}, datasets:[{{ data:{reg_data},
    backgroundColor:COLORS, borderWidth:2, borderColor:'white' }}] }},
  options:{{ responsive:true, maintainAspectRatio:false,
    plugins:{{ legend:{{ position:'bottom', labels:{{ boxWidth:12, font:{{ size:12 }} }} }},
      tooltip:{{ callbacks:{{ label: c=>c.label+': Rs '+c.raw.toLocaleString('en-IN') }} }} }} }}
}});
</script>
</body>
</html>"""

    from config import DASHBOARD_PATH
    DASHBOARD_PATH.write_text(html, encoding="utf-8")
    log.info(f"HTML Dashboard saved: {DASHBOARD_PATH}")
    print(f"  [Dashboard] Saved to: {DASHBOARD_PATH}")
    print(f"  [Dashboard] Browser mein open karo: open reports/dashboard.html")




def run_pipeline() -> None:
    """
    Task 13: Ek function mein poora pipeline chalaao.
    Task 14: Try/except se proper error handling.
    """
    start_time = time.time()
    all_warnings: list[str] = []
    rows_in = 0

    log.info("=" * 56)
    log.info("  RETAILMART DATA PIPELINE — START")
    log.info("=" * 56)

    try:
        
        sales, products, stores = load_data()
        rows_in = len(sales)

        
        sales, w1 = validate_data(sales, "sales")
        products, w2 = validate_data(products, "products")
        all_warnings.extend(w1 + w2)

        
        sales, dup_removed, nulls_dropped = clean_sales(sales)

        
        merged = transform_data(sales, products, stores)

        
        load_to_db(merged)

        
        kpis = generate_report()

        
        save_charts(kpis)
        generate_html_dashboard(kpis)

        
        print_execution_report(
            start_time, all_warnings,
            rows_in, len(merged),
            dup_removed, nulls_dropped
        )
        log.info("PIPELINE COMPLETED SUCCESSFULLY")

    
    except FileNotFoundError as e:
        log.error(f"FILE NOT FOUND: {e}")
        log.error("Check karein ki data/ folder mein teeno CSV files hain.")
        print(f"\n  ERROR: {e}\n  Tip: 'python sample_data.py' run karo pehle.")

    except pd.errors.EmptyDataError as e:
        log.error(f"EMPTY CSV: {e}")
        print(f"\n  ERROR: CSV file empty hai — {e}")

    except pd.errors.ParserError as e:
        log.error(f"CSV PARSE ERROR: {e}")
        print(f"\n  ERROR: CSV format galat hai — {e}")

    except sqlite3.Error as e:
        log.error(f"DATABASE ERROR: {e}")
        print(f"\n  ERROR: SQLite issue — {e}")

    except PermissionError as e:
        log.error(f"PERMISSION ERROR: {e}")
        print(f"\n  ERROR: File access denied — {e}")

    except Exception as e:
        log.error(f"UNEXPECTED ERROR: {e}", exc_info=True)
        print(f"\n  UNEXPECTED ERROR: {e}")
        raise


if __name__ == "__main__":
    run_pipeline()
