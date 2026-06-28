
from pathlib import Path


BASE_DIR      = Path(__file__).parent
DATA_DIR      = BASE_DIR / "data"
REPORTS_DIR   = BASE_DIR / "reports"
LOG_DIR       = BASE_DIR / "logs"


SALES_PATH    = DATA_DIR / "sales_data.csv"
PRODUCTS_PATH = DATA_DIR / "products.csv"
STORES_PATH   = DATA_DIR / "stores.csv"


DB_PATH        = BASE_DIR / "retail_sales.db"
TABLE_NAME     = "retail_sales"
DASHBOARD_PATH = REPORTS_DIR / "dashboard.html"
CHART_PATH     = REPORTS_DIR / "revenue_dashboard.png"
LOG_FILE       = LOG_DIR / "pipeline.log"


MAX_VALID_AMOUNT   = 500_000   
MAX_VALID_QUANTITY = 10_000    
MIN_VALID_QUANTITY = 0
