
import logging
import time
from pathlib import Path

import pandas as pd
import numpy as np

from config import LOG_DIR, LOG_FILE, MAX_VALID_AMOUNT, MAX_VALID_QUANTITY, MIN_VALID_QUANTITY



def setup_logger(name: str = "retailmart") -> logging.Logger:
    """File + console dono pe log karo."""
    LOG_DIR.mkdir(exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)-8s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)

    
    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)

    if not logger.handlers:
        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger


log = setup_logger()



def validate_data(df: pd.DataFrame, source_name: str) -> tuple[pd.DataFrame, list[str]]:
    """
    Business logic validation — sirf technical cleaning nahi,
    actual data quality rules check karta hai.

    Args:
        df: Input DataFrame
        source_name: "sales", "products", ya "stores"

    Returns:
        (cleaned_df, list of warning strings)
    """
    warnings: list[str] = []
    original_len = len(df)

    if source_name == "sales":
        
        mask_neg = df["quantity"].notna() & (df["quantity"] < MIN_VALID_QUANTITY)
        if mask_neg.any():
            count = mask_neg.sum()
            warnings.append(f"{count} row(s) with negative quantity — corrected to 0")
            log.warning(f"[VALIDATION] {count} negative quantity row(s) found and fixed")
            df.loc[mask_neg, "quantity"] = 0

        
        mask_outlier = df["amount"].notna() & (df["amount"] > MAX_VALID_AMOUNT)
        if mask_outlier.any():
            count = mask_outlier.sum()
            warnings.append(f"{count} row(s) with amount > Rs {MAX_VALID_AMOUNT:,} — flagged as outlier")
            log.warning(f"[VALIDATION] {count} outlier amount row(s) found: {df.loc[mask_outlier, 'amount'].tolist()}")

        
        mask_large = df["quantity"].notna() & (df["quantity"] > MAX_VALID_QUANTITY)
        if mask_large.any():
            count = mask_large.sum()
            warnings.append(f"{count} row(s) with quantity > {MAX_VALID_QUANTITY} — check source data")
            log.warning(f"[VALIDATION] {count} unreasonably large quantity row(s)")

        
        today = pd.Timestamp.today().normalize()
        if "sale_date" in df.columns:
            df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
            mask_future = df["sale_date"] > today
            if mask_future.any():
                count = mask_future.sum()
                warnings.append(f"{count} row(s) with future sale_date — check source system")
                log.warning(f"[VALIDATION] {count} future-dated sale(s) detected")

    if source_name == "products":
        
        mask_neg_price = df["price"] <= 0
        if mask_neg_price.any():
            count = mask_neg_price.sum()
            warnings.append(f"{count} product(s) with zero/negative price")
            log.warning(f"[VALIDATION] {count} invalid price(s) in products")

    log.debug(f"[VALIDATION] {source_name}: {original_len} rows in, {len(df)} rows out, {len(warnings)} warning(s)")
    return df, warnings



def print_execution_report(
    start_time: float,
    warnings: list[str],
    rows_in: int,
    rows_out: int,
    duplicates_removed: int,
    nulls_dropped: int,
) -> None:
    """Pipeline ke end mein ek clean professional summary print karo."""
    duration = round(time.time() - start_time, 2)
    status = "SUCCESS" if not any("ERROR" in w.upper() for w in warnings) else "SUCCESS WITH WARNINGS"

    print("\n" + "━" * 56)
    print("      RETAILMART PIPELINE — EXECUTION REPORT")
    print("━" * 56)
    print(f"  Status              : {status}")
    print(f"  Total time          : {duration}s")
    print(f"  Rows ingested       : {rows_in}")
    print(f"  Duplicates removed  : {duplicates_removed}")
    print(f"  Nulls dropped       : {nulls_dropped}")
    print(f"  Rows after cleaning : {rows_out}")
    print(f"  Warnings            : {len(warnings)}")
    if warnings:
        for w in warnings:
            print(f"    ⚠  {w}")
    print(f"  Output DB           : retail_sales.db")
    print(f"  Dashboard           : reports/dashboard.html")
    print(f"  Charts              : reports/revenue_dashboard.png")
    print(f"  Logs                : logs/pipeline.log")
    print("━" * 56 + "\n")



def print_df_info(name: str, df: pd.DataFrame) -> None:
    """Shape aur first 5 rows print karo (Task 1 requirement)."""
    print(f"\n{'═'*50}")
    print(f"  {name.upper()} — shape: {df.shape}")
    print(f"{'═'*50}")
    print(df.head().to_string(index=False))
    null_summary = df.isnull().sum()
    null_cols = null_summary[null_summary > 0]
    if not null_cols.empty:
        print(f"\n  Missing values:")
        for col, cnt in null_cols.items():
            pct = round(cnt / len(df) * 100, 1)
            print(f"    {col}: {cnt} ({pct}%)")
    else:
        print("\n  No missing values.")
