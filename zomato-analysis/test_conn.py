#!/usr/bin/env -S uv run python
# -*- coding: utf-8 -*-
"""
Master Test Runner: test_conn.py
Purpose: Discovers, executes, and aggregates all verification suites in testing/
Tier: Senior Staff / Lead Data Engineer Standard

Suites:
  1. testing/test_data_engineering_part.py (Snowflake Medallion, S3 Stage, Bronze, Silver, Gold, Snapshots)
  2. testing/test_ai_layer.py (OpenAI Embeddings, RAG Semantic Search, Text-to-SQL Guardrails)
  3. testing/test_orchestration.py (Airflow DAG Syntax, Task Graph, Docker Status)
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
TESTING_DIR = PROJECT_ROOT / "testing"

GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

SUITES = [
    {
        "id": "de",
        "name": "Data Engineering Medallion",
        "file": "test_data_engineering_part.py",
        "scope": "Snowflake / S3 / dbt"
    },
    {
        "id": "ai",
        "name": "AI & Intelligence Layer",
        "file": "test_ai_layer.py",
        "scope": "OpenAI / RAG / Text-to-SQL"
    },
    {
        "id": "orch",
        "name": "Airflow Orchestration",
        "file": "test_orchestration.py",
        "scope": "DAGs / Pipeline Graph / Astro"
    }
]

def print_banner():
    print(f"\n{CYAN}{BOLD}==========================================================")
    print("      ZOMATO AI PLATFORM - MASTER TEST RUNNER")
    print(f"=========================================================={NC}")

def run_suite(suite_info: dict, verbose: bool = True) -> tuple[bool, float]:
    suite_file = TESTING_DIR / suite_info["file"]
    if not suite_file.exists():
        print(f"{RED}[ERROR] Test suite file missing: {suite_file}{NC}")
        return False, 0.0

    print(f"\n{BLUE}[RUNNING]{NC} {BOLD}{suite_info['name']}{NC} ({suite_info['file']})...")
    start_time = time.time()

    cmd = ["uv", "run", "python", str(suite_file)]
    
    if verbose:
        res = subprocess.run(cmd, cwd=str(PROJECT_ROOT))
        success = (res.returncode == 0)
    else:
        res = subprocess.run(cmd, cwd=str(PROJECT_ROOT), capture_output=True, text=True)
        success = (res.returncode == 0)
        if not success:
            print(res.stdout)
            print(res.stderr)

    duration = time.time() - start_time
    status_str = f"{GREEN}[PASS]{NC}" if success else f"{RED}[FAIL]{NC}"
    print(f"{status_str} Completed in {duration:.2f}s")
    return success, duration

def main():
    parser = argparse.ArgumentParser(description="Master Platform Test Runner for Zomato AI")
    parser.add_argument(
        "--suite",
        choices=["all", "de", "ai", "orch"],
        default="all",
        help="Specify which test suite to run (default: all)"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress intermediate suite outputs unless an error occurs"
    )
    args = parser.parse_args()

    print_banner()

    target_suites = SUITES if args.suite == "all" else [s for s in SUITES if s["id"] == args.suite]

    results = []
    total_start = time.time()

    for s in target_suites:
        success, duration = run_suite(s, verbose=not args.quiet)
        results.append({
            "name": s["file"],
            "scope": s["scope"],
            "duration": duration,
            "success": success
        })

    total_duration = time.time() - total_start
    total_suites = len(results)
    passed_suites = sum(1 for r in results if r["success"])
    failed_suites = total_suites - passed_suites

    # Executive Scorecard
    print(f"\n{CYAN}{BOLD}==========================================================")
    print("           MASTER PLATFORM TEST EXECUTION MATRIX")
    print(f"=========================================================={NC}")
    printf_fmt = "  %-32s | %-22s | %-10s | %-8s\n"
    print(printf_fmt % ("TEST SUITE", "SCOPE", "DURATION", "RESULT"))
    print("  " + "-" * 75)

    for r in results:
        res_str = f"{GREEN}PASS{NC}" if r["success"] else f"{RED}FAIL{NC}"
        print(printf_fmt % (r["name"], r["scope"], f"{r['duration']:.2f}s", res_str))

    print("  " + "-" * 75)
    print(f"  TOTAL: {total_suites} suites | PASSED: {passed_suites} | FAILED: {failed_suites} | DURATION: {total_duration:.2f}s")

    if failed_suites == 0:
        print(f"\n{GREEN}{BOLD}  SCORECARD: 100% PASS - ALL SYSTEMS OPERATIONAL (PRODUCTION READY){NC}\n")
        return 0
    else:
        print(f"\n{RED}{BOLD}  SCORECARD: {failed_suites} SUITE(S) FAILED - REVIEW LOGS ABOVE{NC}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
