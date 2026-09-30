#!/usr/bin/env -S uv run --with snowflake-connector-python --with python-dotenv python
# -*- coding: utf-8 -*-
"""
Snowflake Database & Population Health Check Script
Verifies:
  1. Connection & Session details
  2. Database & Schema verification
  3. External S3 Stage & file availability
  4. Raw Table existence, row counts & population status
  5. Staging and Marts layer status
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ANSI Color formatting
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
    print(f"{RED}[ERROR] snowflake-connector-python is not installed.{NC}")
    sys.exit(1)

def print_header(title):
    print(f"\n{CYAN}{BOLD}=========================================================={NC}")
    print(f"{CYAN}{BOLD}  {title}{NC}")
    print(f"{CYAN}{BOLD}=========================================================={NC}")

def main():
    print_header("SNOWFLAKE HEALTH & DATA POPULATION CHECK")

    # 1. Establish Snowflake Connection
    user = os.getenv("SNOWFLAKE_USERNAME")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH")
    database = os.getenv("SNOWFLAKE_DATABASE", "ZOMATO")
    schema = os.getenv("SNOWFLAKE_SCHEMA", "RAW")
    role = os.getenv("SNOWFLAKE_ROLE", "ACCOUNTADMIN")

    print(f"{BLUE}[INFO]{NC} Connecting to Snowflake account: {BOLD}{account}{NC} as {BOLD}{user}{NC}...")

    try:
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            role=role,
            warehouse=warehouse,
            database=database,
            schema=schema,
            login_timeout=15
        )
        cur = conn.cursor()
    except Exception as e:
        print(f"{RED}[ERROR] Connection failed: {e}{NC}")
        sys.exit(1)

    # 2. Connection & Session Info
    cur.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_REGION(), CURRENT_WAREHOUSE(), CURRENT_DATABASE(), CURRENT_SCHEMA();")
    s_user, s_role, s_region, s_wh, s_db, s_schema = cur.fetchone()
    print(f"{GREEN}[OK] Connected successfully!{NC}")
    print(f"  • User:      {BOLD}{s_user}{NC}")
    print(f"  • Role:      {BOLD}{s_role}{NC}")
    print(f"  • Region:    {BOLD}{s_region}{NC}")
    print(f"  • Warehouse: {BOLD}{s_wh}{NC}")
    print(f"  • Database:  {BOLD}{s_db}{NC}")
    print(f"  • Schema:    {BOLD}{s_schema}{NC}")

    # 3. Check Schemas in Database
    print_header("1. DATABASE SCHEMAS (MEDALLION LAYERS)")
    cur.execute(f"SHOW SCHEMAS IN DATABASE {database};")
    schemas = [s[1] for s in cur.fetchall()]
    print(f"{BLUE}[INFO]{NC} Found {len(schemas)} schemas in database '{database}':")
    for sch in schemas:
        print(f"  • {sch}")

    # 4. Check S3 External Stage & Files
    print_header("2. S3 STAGE & RAW FILES (LAKE INGESTION)")
    stage_name = f"@{database}.{schema}.ZOMATO_RAW_STAGE"
    try:
        cur.execute(f"LIST {stage_name};")
        files = cur.fetchall()
        print(f"{GREEN}[OK]{NC} External Stage '{stage_name}' is accessible!")
        print(f"{BLUE}[INFO]{NC} Found {len(files)} files staged in S3:")
        total_size_bytes = 0
        for f in files:
            file_name = f[0]
            size_mb = round(f[1] / (1024 * 1024), 2)
            total_size_bytes += f[1]
            print(f"  • {file_name} ({size_mb} MB)")
        total_mb = round(total_size_bytes / (1024 * 1024), 2)
        print(f"  --> Total Staged Data: {BOLD}{total_mb} MB{NC}")
    except Exception as e:
        print(f"{YELLOW}[WARN] Could not list stage {stage_name}: {e}{NC}")

    # 5. Check Raw Tables & Row Counts (Data Population)
    print_header("3. RAW TABLES & DATA POPULATION STATUS (BRONZE LAYER)")
    cur.execute(f"SHOW TABLES IN SCHEMA {database}.{schema};")
    raw_tables = cur.fetchall()

    if not raw_tables:
        print(f"{YELLOW}[WARN] No tables found in schema {database}.{schema}. Run 'snowflake/04_raw_tables.sql' first.{NC}")
    else:
        print(f"{BLUE}[INFO]{NC} Checking population status for {len(raw_tables)} tables in '{database}.{schema}':\n")
        print(f"  {'TABLE NAME':<20} | {'ROW COUNT':<15} | {'STATUS':<30}")
        print(f"  {'-'*20}-+-{'-'*15}-+-{'-'*30}")

        total_rows = 0
        for t in raw_tables:
            table_name = t[1]
            cur.execute(f"SELECT COUNT(*) FROM {database}.{schema}.{table_name};")
            row_count = cur.fetchone()[0]
            total_rows += row_count

            if row_count > 0:
                status = f"{GREEN}[POPULATED]{NC}"
                formatted_count = f"{row_count:,}"
            else:
                status = f"{YELLOW}[EMPTY - Run 05_copy_into.sql]{NC}"
                formatted_count = "0"

            print(f"  {table_name:<20} | {formatted_count:<15} | {status}")

        print(f"  {'-'*20}-+-{'-'*15}-+-{'-'*30}")
        print(f"  {'TOTAL ROWS':<20} | {total_rows:<15,}")

    # 6. Sample Preview if data exists
    if total_rows > 0:
        print_header("4. SAMPLE PREVIEW (FIRST POPULATED TABLE)")
        for t in raw_tables:
            table_name = t[1]
            cur.execute(f"SELECT COUNT(*) FROM {database}.{schema}.{table_name};")
            if cur.fetchone()[0] > 0:
                print(f"{BLUE}[INFO]{NC} Previewing top 2 rows from {table_name}:")
                cur.execute(f"SELECT * FROM {database}.{schema}.{table_name} LIMIT 2;")
                cols = [desc[0] for desc in cur.description]
                print(f"  Columns: {cols[:8]}...")
                for row in cur.fetchall():
                    print(f"  Row: {row[:8]}...")
                break

    # 7. Next Steps Guidance
    print_header("NEXT STEPS SUMMARY")
    if total_rows == 0:
        print(f"{YELLOW}• All raw tables are currently empty.{NC}")
        print(f"• Run {BOLD}snowflake/05_copy_into.sql{NC} in Snowsight to load the 1.4 GB of S3 CSVs into Snowflake.")
    else:
        print(f"{GREEN}• Tables are successfully populated!{NC}")
        print(f"• You can now run dbt models: {BOLD}dbt build{NC} to build the STAGING and MARTS layers.")

    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
