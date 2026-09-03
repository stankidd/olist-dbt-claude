"""
Olist DuckDB Loader
Downloads and loads the Olist Brazilian e-commerce dataset into DuckDB.

Usage:
    python scripts/load_data.py

Requirements:
    pip install duckdb kaggle
    kaggle.json in ~/.kaggle/

The dataset will be downloaded to data/raw/ and loaded into data/olist.duckdb
"""
import os
import duckdb
import subprocess
from pathlib import Path

# Paths
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "olist.duckdb"

# Create directories
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Download from Kaggle
print("Downloading Olist dataset from Kaggle...")
subprocess.run([
    "kaggle", "datasets", "download",
    "-d", "olistbr/brazilian-ecommerce",
    "--unzip", "-p", str(RAW_DIR)
], check=True)

# Load into DuckDB
print(f"\nLoading into DuckDB at {DB_PATH}...")
conn = duckdb.connect(str(DB_PATH))
conn.execute("CREATE SCHEMA IF NOT EXISTS raw")

tables = {
    "customers":    "olist_customers_dataset.csv",
    "geolocation":  "olist_geolocation_dataset.csv",
    "orders":       "olist_orders_dataset.csv",
    "order_items":  "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "products":     "olist_products_dataset.csv",
    "sellers":      "olist_sellers_dataset.csv",
    "product_category_name_translation": "product_category_name_translation.csv",
}

for table, filename in tables.items():
    path = RAW_DIR / filename
    print(f"  Loading {table}...")
    conn.execute(f"""
        CREATE OR REPLACE TABLE raw.{table} AS
        SELECT * FROM read_csv_auto('{path.as_posix()}')
    """)
    count = conn.execute(f"SELECT COUNT(*) FROM raw.{table}").fetchone()[0]
    print(f"    {table}: {count:,} rows")

conn.close()
print(f"\nDone! Database created at {DB_PATH}")
print("Next: dbt build --profiles-dir .")