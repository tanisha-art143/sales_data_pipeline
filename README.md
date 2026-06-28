# sales_data_pipeline
# RetailMart Data Pipeline

Data engineering pipeline that ingests, cleans, transforms, and loads
RetailMart's daily sales data into SQLite — then auto-generates an
interactive HTML dashboard and charts.

## Setup (2 commands)

```bash
pip install -r requirements.txt
python sample_data.py   # sample CSV files generate karo (sirf ek baar)
python pipeline.py      # poora pipeline run karo
```

## Project structure

```
retailmart_pipeline/
├── data/
│   ├── sales_data.csv      ← daily transactions (messy, intentional)
│   ├── products.csv        ← product catalog
│   └── stores.csv          ← store info
├── reports/                ← auto-generated outputs
│   ├── dashboard.html      ← interactive Chart.js dashboard (browser mein open karo)
│   └── revenue_dashboard.png ← 4-panel matplotlib chart
├── logs/
│   └── pipeline.log        ← full execution log with timestamps
├── config.py               ← all paths and business rules
├── utils.py                ← logging, validation, report helpers
├── pipeline.py             ← main pipeline (Tasks 1-14)
├── sample_data.py          ← sample CSV generator
└── requirements.txt
```

## What the pipeline does

| Task | What happens |
|------|-------------|
| 1 | Load 3 CSVs, print shape + null summary |
| 2 | Remove duplicates, fill/drop nulls, fix dtypes |
| 3 | Merge DataFrames, add total_revenue, group by city |
| 4 | Load to SQLite, top-3 products SQL query |
| 5 | Store-day revenue SQL, business summary KPIs |
| 6 | Single run_pipeline() with specific error handling |
| BONUS | Data quality validation (negative qty, future dates, outliers) |
| BONUS | 4-panel matplotlib PNG dashboard |
| BONUS | Interactive HTML dashboard with Chart.js (no extra install needed) |

## Outputs after running

- `retail_sales.db` — cleaned, merged SQLite table
- `reports/dashboard.html` — open in browser for interactive charts
- `reports/revenue_dashboard.png` — shareable chart image
- `logs/pipeline.log` — detailed execution log

