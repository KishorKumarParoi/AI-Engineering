#!/usr/bin/env -S uv run python
# -*- coding: utf-8 -*-
"""
Master Test Runner: test_connection.py
Purpose: Runs all verification suites in testing/data-engineering and streams full logs
Tier: Senior Staff / Lead Data Engineer Standard

Suites:
  1. testing/data-engineering/test_snowflake_connection.py (Warehouse, Roles, Schemas)
  2. testing/data-engineering/test_data_engineering_part.py (S3 Stage, Bronze, Silver, Gold, SCD2)
  3. testing/data-engineering/test_ai_layer.py (OpenAI Embeddings, RAG, Text-to-SQL Guardrails)
  4. testing/data-engineering/test_orchestration.py (Airflow DAG AST, Task Graphs, Astro Containers)
"""

import os
import sys
import time
import argparse
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
TEST_DIR = PROJECT_ROOT / "testing" / "data-engineering"

GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

# Enforce Java 17 for PySpark Delta compatibility on macOS
temurin_17 = "/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home"
if os.path.isdir(temurin_17):
    os.environ["JAVA_HOME"] = temurin_17

SUITES = [
    {
        "id": "conn",
        "name": "Snowflake Connection & Schemas",
        "file": "test_snowflake_connection.py",
        "scope": "Snowflake Session & Schemas"
    },
    {
        "id": "de",
        "name": "Data Engineering Medallion",
        "file": "test_data_engineering_part.py",
        "scope": "S3 / Bronze / Silver / Gold / SCD2"
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
        "scope": "DAG AST / Pipeline Graph / Astro"
    },
    {
        "id": "azure",
        "name": "Azure Event Hubs Streaming",
        "file": "test_azure_eventhub.py",
        "scope": "Azure AMQP / Real-Time Buffers"
    },
    {
        "id": "pyspark",
        "name": "Metadata PySpark & Delta SCD",
        "file": "test_pyspark_scd.py",
        "scope": "Delta Lake / SCD 1 & 2 / DQ"
    },
    {
        "id": "vision",
        "name": "Computer Vision & OCR Arbitration",
        "file": "test_vision_ocr.py",
        "scope": "CV / OCR / Fraud / Spillage"
    }
]

def print_banner():
    print(f"\n{CYAN}{BOLD}==========================================================")
    print("      ZOMATO AI PLATFORM - MASTER TEST RUNNER")
    print("      Executing all suites in testing/data-engineering/   ")
    print(f"=========================================================={NC}")

def get_python_interpreter() -> str:
    venv_py = PROJECT_ROOT / ".venv" / "bin" / "python"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable

def run_suite(suite_info: dict) -> tuple[bool, float]:
    suite_file = TEST_DIR / suite_info["file"]
    if not suite_file.exists():
        print(f"{RED}[ERROR] Test suite file missing: {suite_file}{NC}")
        return False, 0.0

    print(f"\n{BLUE}[START SUITE]{NC} {BOLD}{suite_info['name']}{NC} ({suite_file.name})")
    start_time = time.time()

    py_bin = get_python_interpreter()
    cmd = [py_bin, str(suite_file)]
    
    child_env = os.environ.copy()
    child_env["PYTHONPATH"] = str(PROJECT_ROOT)
    child_env["PYSPARK_PYTHON"] = py_bin
    child_env["PYSPARK_DRIVER_PYTHON"] = py_bin
    if os.path.isdir(temurin_17):
        child_env["JAVA_HOME"] = temurin_17

    # Run and stream output directly to stdout in real-time
    process = subprocess.Popen(
        cmd,
        cwd=str(PROJECT_ROOT),
        env=child_env,
        stdout=sys.stdout,
        stderr=sys.stderr
    )
    process.wait()
    success = (process.returncode == 0)

    duration = time.time() - start_time
    status_str = f"{GREEN}[PASS]{NC}" if success else f"{RED}[FAIL]{NC}"
    print(f"\n{status_str} Suite '{suite_info['name']}' finished in {duration:.2f}s")
    return success, duration

def main():
    parser = argparse.ArgumentParser(description="Master Platform Test Runner for Zomato AI")
    parser.add_argument(
        "--suite",
        choices=["all", "conn", "de", "ai", "orch", "azure", "pyspark", "vision"],
        default="all",
        help="Specify which test suite to run (default: all)"
    )
    args = parser.parse_args()

    print_banner()

    target_suites = SUITES if args.suite == "all" else [s for s in SUITES if s["id"] == args.suite]

    results = []
    total_start = time.time()

    for s in target_suites:
        success, duration = run_suite(s)
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

    # Executive Scorecard Matrix
    print(f"\n{CYAN}{BOLD}==========================================================")
    print("           MASTER PLATFORM TEST EXECUTION MATRIX")
    print(f"=========================================================={NC}")
    printf_fmt = "  %-32s | %-24s | %-10s | %-8s\n"
    print(printf_fmt % ("TEST SUITE", "SCOPE", "DURATION", "RESULT"))
    print("  " + "-" * 78)

    for r in results:
        res_str = f"{GREEN}PASS{NC}" if r["success"] else f"{RED}FAIL{NC}"
        print(printf_fmt % (r["name"], r["scope"], f"{r['duration']:.2f}s", res_str))

    print("  " + "-" * 78)
    print(f"  TOTAL: {total_suites} suites | PASSED: {passed_suites} | FAILED: {failed_suites} | DURATION: {total_duration:.2f}s")

    if failed_suites == 0:
        print(f"\n{GREEN}{BOLD}  SCORECARD: 100% PASS - ALL SYSTEMS OPERATIONAL (PRODUCTION READY){NC}\n")
        return 0
    else:
        print(f"\n{RED}{BOLD}  SCORECARD: {failed_suites} SUITE(S) FAILED - REVIEW LOGS ABOVE{NC}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
