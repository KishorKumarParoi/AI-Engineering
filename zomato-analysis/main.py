#!/usr/bin/env -S uv run python
# -*- coding: utf-8 -*-
"""
Executive CLI Entrypoint: main.py
System: Zomato AI Data Platform
Architecture: S3 Lakehouse -> Snowflake Medallion (Bronze/Silver/Gold) -> Airflow -> OpenAI LLM/RAG
Tier: Senior Staff / Lead Data Engineer Standard
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
load_dotenv(PROJECT_ROOT / ".env")

GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

def print_banner():
    print(rf"""{CYAN}{BOLD}
========================================================================
   ____ ____  __  __    _  _____ ___      _    ___   ____  _        _   
  |_  // () \|  \/  |  / \|_   _/ () \    / \  |_ _| | () \| |      / \  
  /__/\____/|_|\/|_| /_/ \_\|_| \____/   /_/ \_||___|| __/ |_|____/_/ \_
                                                     |_|                 
      Enterprise AI Lakehouse & Real-Time Analytical Intelligence       
========================================================================{NC}""")

def cmd_info(args):
    print_banner()
    account = os.getenv("SNOWFLAKE_ACCOUNT", "Not set")
    user = os.getenv("SNOWFLAKE_USER") or os.getenv("SNOWFLAKE_USERNAME", "Not set")
    role = os.getenv("SNOWFLAKE_ROLE", "DBT_ROLE")
    wh = os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH")
    db = os.getenv("SNOWFLAKE_DATABASE", "ZOMATO")
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    print(f"{BOLD}Architecture & Storage Topology:{NC}")
    print("  Lakehouse Ingestion  : AWS S3 (zomato-dataset-kkp/raw-data) -> External Stage")
    print("  Snowflake Database   : " + db)
    print("  Data Warehouse       : " + wh)
    print("  Access Role / User   : " + f"{role} / {user}")
    print(f"  Medallion Layers     : Bronze (RAW) -> Silver (STAGING) -> Gold (MARTS) -> Snapshots (SCD2)")
    print(f"  AI & LLM Services    : OpenAI gpt-4o-mini & text-embedding-3-small (Active: {has_openai})")
    print(f"  Orchestration Engine : Apache Airflow on Astronomer Runtime 3.3-8")
    print("")
    print(f"{BOLD}Quick Execution Commands:{NC}")
    print("  ./run.sh             - Run Data Engineering pipeline & see full logs")
    print("  ./run.sh check       - Validate platform scripts")
    print("  ./test_connection.py - Execute master verification matrix with live logs")
    print("  make de              - Run full dbt medallion pipeline")
    print("  make ai              - Run LLM enrichment & vector indexing")
    print("  make sql             - Launch Text-to-SQL UI")
    print("  make rag             - Launch Semantic Reviews RAG UI")
    print("")

def cmd_check(args):
    subprocess.run(["./run.sh", "check"], cwd=str(PROJECT_ROOT))

def cmd_test(args):
    suite_arg = ["--suite", args.suite] if args.suite else []
    subprocess.run(["./test_connection.py"] + suite_arg, cwd=str(PROJECT_ROOT))

def cmd_pipeline(args):
    subprocess.run(["./scripts/data-engineering/data_engineering.sh", args.target], cwd=str(PROJECT_ROOT))

def cmd_enrich(args):
    subprocess.run(["./scripts/data-engineering/ai_pipeline.sh", "all"], cwd=str(PROJECT_ROOT))

def cmd_serve(args):
    subprocess.run(["./scripts/data-engineering/serve_apps.sh", args.app], cwd=str(PROJECT_ROOT))

def main():
    parser = argparse.ArgumentParser(
        description="Zomato AI Data Platform - Executive CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", help="Platform operations")

    # info
    subparsers.add_parser("info", help="Display platform architecture, configurations and endpoints")

    # check
    subparsers.add_parser("check", help="Verify all automation scripts in scripts/")

    # test
    test_parser = subparsers.add_parser("test", help="Run master verification matrix")
    test_parser.add_argument("--suite", choices=["all", "de", "ai", "orch"], default="all", help="Target test suite")

    # pipeline
    pipe_parser = subparsers.add_parser("pipeline", help="Execute dbt medallion pipeline")
    pipe_parser.add_argument("target", choices=["all", "debug", "snapshot", "core", "ai"], default="all", nargs="?", help="Pipeline target")

    # enrich
    subparsers.add_parser("enrich", help="Run customer review LLM enrichment and vector embeddings")

    # serve
    serve_parser = subparsers.add_parser("serve", help="Launch interactive Streamlit applications")
    serve_parser.add_argument("app", choices=["sql", "rag"], default="sql", nargs="?", help="Application to launch")

    args = parser.parse_args()

    commands = {
        "info": cmd_info,
        "check": cmd_check,
        "test": cmd_test,
        "pipeline": cmd_pipeline,
        "enrich": cmd_enrich,
        "serve": cmd_serve,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        cmd_info(args)

if __name__ == "__main__":
    main()
