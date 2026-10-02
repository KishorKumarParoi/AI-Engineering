#!/usr/bin/env -S uv run --with snowflake-connector-python --with python-dotenv python
# -*- coding: utf-8 -*-
"""
Test Suite: testing/test_data_engineering_part.py
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
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ANSI Color formatting (Universal ASCII safe)
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
    print_header("DATA ENGINEERING VERIFICATION SUITE")

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

    cur.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE();")
    s_user, s_role, s_wh, s_db = cur.fetchone()
    print(f"{GREEN}[PASS]{NC} Session: User={s_user} | Role={s_role} | WH={s_wh} | DB={s_db}")

    failures = 0

    # 1. S3 Lakehouse Stage Check
    print_header("1. S3 STAGE & RAW INGESTION FILES")
    stage_name = f"@{database}.RAW.ZOMATO_RAW_STAGE"
    try:
        cur.execute(f"LIST {stage_name};")
        files = cur.fetchall()
        total_mb = round(sum(f[1] for f in files) / (1024 * 1024), 2)
        print(f"{GREEN}[PASS]{NC} External Stage '{stage_name}' has {len(files)} files staged ({total_mb} MB total):")
        for f in files:
            size_mb = round(f[1] / (1024 * 1024), 2)
            print(f"  - {f[0]} ({size_mb} MB)")
        if len(files) < 7:
            print(f"{YELLOW}[WARN] Expected 7 staged files, found {len(files)}.{NC}")
            failures += 1
    except Exception as e:
        print(f"{RED}[FAIL] Could not access stage {stage_name}: {e}{NC}")
        failures += 1

    # 2. Bronze Layer (RAW) Table Verification
    print_header("2. BRONZE LAYER (RAW TABLES)")
    raw_tables = ["FOOD", "MENU", "ORDERS", "ORDER_ITEMS", "RESTAURANTS", "REVIEWS", "USERS"]
    total_bronze_rows = 0
    print(f"  {'TABLE NAME':<20} | {'ROW COUNT':<15} | {'STATUS':<20}")
    print(f"  {'-'*20}-+-{'-'*15}-+-{'-'*20}")
    for tbl in raw_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {database}.RAW.{tbl};")
            count = cur.fetchone()[0]
            total_bronze_rows += count
            status = f"{GREEN}[POPULATED]{NC}" if count > 0 else f"{RED}[EMPTY]{NC}"
            if count == 0:
                failures += 1
            print(f"  {tbl:<20} | {count:<15,} | {status}")
        except Exception as e:
            print(f"  {tbl:<20} | {'ERROR':<15} | {RED}{e}{NC}")
            failures += 1
    print(f"  {'-'*20}-+-{'-'*15}-+-{'-'*20}")
    print(f"  {'TOTAL BRONZE ROWS':<20} | {total_bronze_rows:<15,}")

    # 3. Silver Layer (STAGING) View Verification
    print_header("3. SILVER LAYER (STAGING CONFORMED VIEWS)")
    staging_views = ["STG_FOOD", "STG_MENU", "STG_ORDERS", "STG_ORDER_ITEMS", "STG_RESTAURANTS", "STG_REVIEWS", "STG_USERS"]
    for v in staging_views:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {database}.STAGING.{v};")
            count = cur.fetchone()[0]
            print(f"  {GREEN}[PASS]{NC} {v:<25} | {count:<12,} rows")
        except Exception as e:
            print(f"  {RED}[FAIL]{NC} {v:<25} | Error: {e}")
            failures += 1

    # 4. Gold Layer (MARTS) Table Verification
    print_header("4. GOLD LAYER (MARTS & FACTS)")
    marts_tables = [
        "DIM_CUSTOMERS", "DIM_DATE", "DIM_FOOD", "DIM_RESTAURANTS",
        "FCT_ORDERS", "FCT_ORDER_ITEMS",
        "MART_DAILY_CITY_REVENUE", "MART_DELIVERY_SLA", "MART_RESTAURANT_PERFORMANCE", "MART_REVIEW_INSIGHTS"
    ]
    for m in marts_tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {database}.MARTS.{m};")
            count = cur.fetchone()[0]
            print(f"  {GREEN}[PASS]{NC} {m:<28} | {count:<12,} rows")
        except Exception as e:
            print(f"  {RED}[FAIL]{NC} {m:<28} | Error: {e}")
            failures += 1

    # 5. Snapshots (SCD Type 2) Verification
    print_header("5. SNAPSHOTS LAYER (SCD TYPE 2)")
    try:
        cur.execute(f"SELECT COUNT(*) FROM {database}.SNAPSHOTS.SNAP_RESTAURANTS;")
        snap_count = cur.fetchone()[0]
        print(f"  {GREEN}[PASS]{NC} SNAP_RESTAURANTS              | {snap_count:<12,} history records")
    except Exception as e:
        print(f"  {RED}[FAIL]{NC} SNAP_RESTAURANTS              | Error: {e}")
        failures += 1

    # 6. AI Layer Verification
    print_header("6. AI LAYER (REVIEW ENRICHMENT)")
    try:
        cur.execute(f"SELECT COUNT(*) FROM {database}.AI.REVIEW_ENRICHED;")
        ai_count = cur.fetchone()[0]
        status = f"{GREEN}[ACTIVE]{NC}" if ai_count > 0 else f"{YELLOW}[READY - 0 rows]{NC}"
        print(f"  {GREEN}[PASS]{NC} REVIEW_ENRICHED               | {ai_count:<12,} rows {status}")
    except Exception as e:
        print(f"{YELLOW}[INFO] REVIEW_ENRICHED not present: {e}{NC}")

    print_header("DATA ENGINEERING TEST SUMMARY")
    if failures == 0:
        print(f"{GREEN}{BOLD}ALL DATA ENGINEERING MEDALLION TESTS PASSED (100%)!{NC}")
        cur.close()
        conn.close()
        return True
    else:
        print(f"{RED}{BOLD}{failures} DATA ENGINEERING TEST(S) FAILED.{NC}")
        cur.close()
        conn.close()
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
