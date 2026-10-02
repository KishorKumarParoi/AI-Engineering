#!/usr/bin/env -S uv run --with snowflake-connector-python --with python-dotenv python
# -*- coding: utf-8 -*-
"""
Test Suite: testing/data-engineering/test_snowflake_connection.py
Purpose: Snowflake Warehouse, Database, Role & Schema Verification
Tier: Senior Staff / Lead Data Engineer Standard

Validates:
  1. Snowflake Credentials & Connectivity
  2. Active Session Context (User, Role, Warehouse, Database)
  3. Medallion Schemas Existence (RAW, STAGING, MARTS, SNAPSHOTS, AI)
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
    print(f"{RED}[ERROR] snowflake-connector-python is required to run connection tests.{NC}")
    sys.exit(1)

def print_header(title):
    print(f"\n{CYAN}{BOLD}=========================================================={NC}")
    print(f"{CYAN}{BOLD}  {title}{NC}")
    print(f"{CYAN}{BOLD}=========================================================={NC}")

def run_tests():
    print_header("SNOWFLAKE CONNECTION & ENVIRONMENT VERIFICATION")

    user = os.getenv("SNOWFLAKE_USER") or os.getenv("SNOWFLAKE_USERNAME")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH")
    database = os.getenv("SNOWFLAKE_DATABASE", "ZOMATO")
    role = os.getenv("SNOWFLAKE_ROLE", "DBT_ROLE")

    print(f"{BLUE}[INFO]{NC} Establishing connection to account: {BOLD}{account}{NC} as user: {BOLD}{user}{NC} (Role: {role})...")

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
        print(f"{YELLOW}[WARN] Could not connect directly with role '{role}': {e}{NC}")
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

    # Check active session context
    cur.execute("SELECT CURRENT_USER(), CURRENT_ROLE(), CURRENT_WAREHOUSE(), CURRENT_DATABASE();")
    s_user, s_role, s_wh, s_db = cur.fetchone()
    print(f"{GREEN}[PASS]{NC} Session Context:")
    print(f"  - Active User:      {BOLD}{s_user}{NC}")
    print(f"  - Active Role:      {BOLD}{s_role}{NC}")
    print(f"  - Active Warehouse: {BOLD}{s_wh}{NC}")
    print(f"  - Active Database:  {BOLD}{s_db}{NC}")

    # Validate Medallion Schemas
    print(f"\n{BLUE}[INFO]{NC} Verifying Medallion Schemas in database '{database}'...")
    cur.execute(f"SHOW SCHEMAS IN DATABASE {database};")
    schemas = [row[1].upper() for row in cur.fetchall()]

    required_schemas = ["RAW", "STAGING", "MARTS", "SNAPSHOTS", "AI"]
    all_schemas_exist = True
    for s in required_schemas:
        if s in schemas:
            print(f"  {GREEN}[PASS]{NC} Schema {BOLD}{database}.{s}{NC} exists")
        else:
            print(f"  {RED}[FAIL]{NC} Schema {BOLD}{database}.{s}{NC} is MISSING!")
            all_schemas_exist = False

    conn.close()

    print_header("CONNECTION TEST SUMMARY")
    if all_schemas_exist:
        print(f"{GREEN}{BOLD}ALL SNOWFLAKE CONNECTION & SCHEMA CHECKS PASSED (100%)!{NC}")
        return True
    else:
        print(f"{RED}{BOLD}SOME SCHEMA CHECKS FAILED{NC}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
