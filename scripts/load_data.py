"""
Olist DuckDB Loader
Downloads and loads the Olist Brazilian e-commerce dataset into DuckDB.

Usage:
    python scripts/load_data.py

Requirements:
    pip install duckdb kaggle

Kaggle authentication (the installed kaggle CLI checks these in order,
so any one of them is enough):
    1. KAGGLE_API_TOKEN environment variable — the token itself, or a
       path to a file containing it. Set as a repo secret in CI (see
       .github/workflows/dbt_build.yml).
    2. ~/.kaggle/access_token — a file containing just the token, for
       local use.
    3. ~/.kaggle/kaggle.json — the legacy {"username": "...", "key": "..."}
       file, still supported for local use.

Get a token at https://www.kaggle.com/settings -> API -> Create New Token.

The dataset will be downloaded to data/raw/ and loaded into data/olist.duckdb
"""
import os
import sys
import duckdb
import subprocess
from pathlib import Path

# Paths
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
DB_PATH = DATA_DIR / "olist.duckdb"


def check_kaggle_credentials() -> None:
    """Fail fast with a clear message if no Kaggle credential source is present.

    Mirrors the precedence the installed kaggle CLI itself uses
    (kagglesdk.kaggle_env.get_access_token_from_env, then the legacy
    kaggle.json path): KAGGLE_API_TOKEN env var, then ~/.kaggle/access_token
    (or .txt), then ~/.kaggle/kaggle.json. This function only checks that a
    source is present — the kaggle CLI itself validates the credential.
    """
    if os.environ.get("KAGGLE_API_TOKEN"):
        return
    kaggle_dir = Path.home() / ".kaggle"
    if (kaggle_dir / "access_token").exists() or (kaggle_dir / "access_token.txt").exists():
        return
    if (kaggle_dir / "kaggle.json").exists():
        return
    print(
        "No Kaggle credentials found. Provide one of:\n"
        "  - KAGGLE_API_TOKEN environment variable\n"
        "  - ~/.kaggle/access_token (a file containing your token)\n"
        '  - ~/.kaggle/kaggle.json (the legacy {"username", "key"} file)\n'
        "Get a token at https://www.kaggle.com/settings -> API -> Create New Token.",
        file=sys.stderr,
    )
    sys.exit(1)


check_kaggle_credentials()

# Create directories
RAW_DIR.mkdir(parents=True, exist_ok=True)

# Download from Kaggle
# Invoked via `python -m kaggle` rather than the bare `kaggle` command so
# this doesn't depend on the kaggle console script being on PATH (it isn't,
# by default, in some local Windows installs).
print("Downloading Olist dataset from Kaggle...")
subprocess.run([
    sys.executable, "-m", "kaggle", "datasets", "download",
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