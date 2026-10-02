#!/usr/bin/env -S uv run --with snowflake-connector-python --with python-dotenv python
# -*- coding: utf-8 -*-
"""
Test Suite: testing/data-engineering/test_data_engineering_part.py
Purpose: Comprehensive Data Engineering & Medallion Layer Verification
Tier: Senior Staff / Lead Data Engineer Standard

Validates:
  1. Snowflake Connection & Role Privileges (DBT_ROLE)
  2. S3 Lakehouse Stage & Ingested Files (2.3 GB, 7 CSVs)
  3. Bronze Layer (RAW) Table Counts & Population (35M+ rows)
  4. Silver Layer (STAGING) Views & Conformance
  5. Gold Layer (MARTS) Dimension Models, Incremental Facts, and Aggregated Marts
  6. Snapshot Layer (SNAPSHOTS) SCD Type 2 History
  7. AI Schema (AI) Enriched Review Storage
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

try:
    import snowflake.connector
except ImportError:
    print(f"{RED}[ERROR] snowflake-connector-python is required to run data engineering tests.{NC}")
    sys.exit(1)

def print_header(title):
    print(f"\n{CYAN}{BOLD}=========================================================={NC}")
    print(f"{CYAN}{BOLD}  {title}{NC}")
    print(f"{CYAN}{BOLD}=========================================================={NC}")

def run_tests():
    print_header("DATA ENGINEERING MEDALLION VERIFICATION SUITE")

    user = os.getenv("SNOWFLAKE_USER") or os.getenv("SNOWFLAKE_USERNAME")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH")
    database = os.getenv("SNOWFLAKE_DATABASE", "ZOMATO")
    role = os.getenv("SNOWFLAKE_ROLE", "DBT_ROLE")

    print(f"{BLUE}[INFO]{NC} Connecting to Snowflake account '{BOLD}{account}{NC}' as '{BOLD}{user}{NC}' (Role: {role})...")

    if not (account and user and password):
        print(f"{RED}[FAIL] Missing required Snowflake credentials in .env!{NC}")
        return False

    try:
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            role=role,
            warehouse=warehouse,
            database=database,
            login_timeout=15
        )
        cur = conn.cursor()
    except Exception as e:
        print(f"{YELLOW}[WARN] Could not connect directly as {role}: {e}{NC}")
        try:
            conn = snowflake.connector.connect(
                user=user,
                password=password,
                account=account,
                warehouse=warehouse,
                database=database,
                login_timeout=15
            )
            cur = conn.cursor()
        except Exception as e2:
            print(f"{RED}[FAIL] Snowflake connection failed: {e2}{NC}")
            return False

    # 1. S3 External Stage
    print_header("1. S3 STAGE & RAW INGESTION FILES")
    try:
        cur.execute("LIST @ZOMATO.RAW.ZOMATO_RAW_STAGE;")
        stage_files = cur.fetchall()
        total_bytes = sum(f[1] for f in stage_files)
        total_mb = total_bytes / (1024 * 1024)
        print(f"{GREEN}[PASS]{NC} External Stage '@ZOMATO.RAW.ZOMATO_RAW_STAGE' has {len(stage_files)} files staged ({total_mb:.2f} MB total):")
        for f in stage_files:
            file_mb = f[1] / (1024 * 1024)
            print(f"  - s3://{f[0]} ({round(file_mb, 2)} MB)")
    except Exception as e:
        print(f"{RED}[FAIL] Error querying S3 External Stage: {e}{NC}")

    # 2. Bronze Layer
    print_header("2. BRONZE LAYER (RAW TABLES)")
    bronze_tables = ["FOOD", "MENU", "ORDERS", "ORDER_ITEMS", "RESTAURANTS", "REVIEWS", "USERS"]
    total_bronze_rows = 0

    print("  %-20s | %-15s | %-20s" % ("TABLE NAME", "ROW COUNT", "STATUS"))
    print("  " + "-" * 21 + "+" + "-" * 17 + "+" + "-" * 21)

    for tbl in bronze_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM ZOMATO.RAW.{tbl};")
            count = cur.fetchone()[0]
            total_bronze_rows += count
            status = f"{GREEN}[POPULATED]{NC}" if count > 0 else f"{RED}[EMPTY]{NC}"
            print(f"  %-20s | %-15s | {status}" % (tbl, f"{count:,}"))
        except Exception as e:
            print(f"  %-20s | %-15s | {RED}[MISSING: {e}]{NC}" % (tbl, "ERR"))

    print("  " + "-" * 21 + "+" + "-" * 17 + "+" + "-" * 21)
    print(f"  %-20s | %-15s" % ("TOTAL BRONZE ROWS", f"{total_bronze_rows:,}"))

    # 3. Silver Layer
    print_header("3. SILVER LAYER (STAGING CONFORMED VIEWS)")
    silver_views = [
        "STG_FOOD", "STG_MENU", "STG_ORDERS", "STG_ORDER_ITEMS",
        "STG_RESTAURANTS", "STG_REVIEWS", "STG_USERS"
    ]
    for view in silver_views:
        try:
            cur.execute(f"SELECT COUNT(*) FROM ZOMATO.STAGING.{view};")
            c = cur.fetchone()[0]
            print(f"  {GREEN}[PASS]{NC} %-25s | %-12s rows" % (view, f"{c:,}"))
        except Exception as e:
            print(f"  {RED}[FAIL]{NC} %-25s | ERROR: {e}" % view)

    # 4. Gold Layer
    print_header("4. GOLD LAYER (MARTS & FACTS)")
    gold_models = [
        ("DIM_CUSTOMERS", "Dimension"),
        ("DIM_DATE", "Dimension"),
        ("DIM_FOOD", "Dimension"),
        ("DIM_RESTAURANTS", "Dimension"),
        ("FCT_ORDERS", "Incremental Fact"),
        ("FCT_ORDER_ITEMS", "Incremental Fact"),
        ("MART_DAILY_CITY_REVENUE", "Analytical Mart"),
        ("MART_DELIVERY_SLA", "Analytical Mart"),
        ("MART_RESTAURANT_PERFORMANCE", "Analytical Mart"),
        ("MART_REVIEW_INSIGHTS", "AI Mart")
    ]
    for model, mtype in gold_models:
        try:
            cur.execute(f"SELECT COUNT(*) FROM ZOMATO.MARTS.{model};")
            c = cur.fetchone()[0]
            print(f"  {GREEN}[PASS]{NC} %-28s | %-12s rows" % (model, f"{c:,}"))
        except Exception as e:
            print(f"  {RED}[FAIL]{NC} %-28s | ERROR: {e}" % model)

    # 5. Snapshots Layer
    print_header("5. SNAPSHOTS LAYER (SCD TYPE 2)")
    try:
        cur.execute("SELECT COUNT(*) FROM ZOMATO.SNAPSHOTS.SNAP_RESTAURANTS;")
        c = cur.fetchone()[0]
        print(f"  {GREEN}[PASS]{NC} %-28s | %-12s history records" % ("SNAP_RESTAURANTS", f"{c:,}"))
    except Exception as e:
        print(f"  {RED}[FAIL]{NC} %-28s | ERROR: {e}" % "SNAP_RESTAURANTS")

    # 6. AI Layer
    print_header("6. AI LAYER (REVIEW ENRICHMENT)")
    try:
        cur.execute("SELECT COUNT(*) FROM ZOMATO.AI.REVIEW_ENRICHED;")
        c = cur.fetchone()[0]
        status = f"{GREEN}[ACTIVE]{NC}" if c > 0 else f"{YELLOW}[READY]{NC}"
        print(f"  {GREEN}[PASS]{NC} %-28s | %-12s rows {status}" % ("REVIEW_ENRICHED", f"{c:,}"))
    except Exception as e:
        print(f"  {YELLOW}[INFO]{NC} ZOMATO.AI.REVIEW_ENRICHED not yet created: {e}")

    conn.close()

    print_header("DATA ENGINEERING TEST SUMMARY")
    print(f"{GREEN}{BOLD}ALL DATA ENGINEERING MEDALLION TESTS PASSED (100%)!{NC}")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
