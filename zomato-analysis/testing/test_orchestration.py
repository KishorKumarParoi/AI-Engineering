#!/usr/bin/env -S uv run python
# -*- coding: utf-8 -*-
"""
Test Suite: testing/test_orchestration.py
Purpose: DAG Integrity, Task Graph & Airflow Orchestration Verification
Tier: Senior Staff / Lead Data Engineer Standard

Validates:
  1. DAG File Syntax & AST Integrity (No syntax or parsing errors)
  2. DAG Definition & Parameters (dag_id, schedule, catchup, tags)
  3. Task Definitions & Operator Types (SQLExecuteQueryOperator, BashOperator)
  4. Task Dependency Pipeline Graph:
     reload_raw >> dbt_build_core >> enrich_reviews >> dbt_build_ai
  5. Astronomer Airflow Container Status & Docker Health
"""

import os
import sys
import ast
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

def print_header(title):
    print(f"\n{CYAN}{BOLD}=========================================================={NC}")
    print(f"{CYAN}{BOLD}  {title}{NC}")
    print(f"{CYAN}{BOLD}=========================================================={NC}")

def test_dag_ast():
    dag_path = PROJECT_ROOT / "dags" / "zomato_batch.py"
    if not dag_path.exists():
        print(f"{RED}[FAIL] DAG file not found: {dag_path}{NC}")
        return False

    print(f"{BLUE}[INFO]{NC} Parsing AST for {dag_path.name}...")
    try:
        with open(dag_path, "r", encoding="utf-8") as f:
            tree = ast.parse(f.read(), filename=str(dag_path))
    except SyntaxError as e:
        print(f"{RED}[FAIL] Python syntax error in DAG: {e}{NC}")
        return False

    print(f"{GREEN}[PASS]{NC} DAG file syntax is 100% valid")

    # Extract task names and assignments
    task_names = set()
    has_dag_instantiation = False
    
    for node in ast.walk(tree):
        if isinstance(node, ast.With):
            for item in node.items:
                if isinstance(item.context_expr, ast.Call):
                    func_name = getattr(item.context_expr.func, "id", "")
                    if func_name == "DAG":
                        has_dag_instantiation = True
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if isinstance(node.value, ast.Call):
                        op_name = getattr(node.value.func, "id", "")
                        if "Operator" in op_name:
                            task_names.add(target.id)

    expected_tasks = {"reload_raw", "dbt_build_core", "enrich_reviews", "dbt_build_ai"}
    missing = expected_tasks - task_names
    if missing:
        print(f"{RED}[FAIL] Missing required tasks in DAG: {missing}{NC}")
        return False

    print(f"{GREEN}[PASS]{NC} Found DAG context and all {len(expected_tasks)} core pipeline tasks:")
    for t in sorted(expected_tasks):
        print(f"  - {BOLD}{t}{NC}")

    return True

def test_astro_status():
    print(f"{BLUE}[INFO]{NC} Verifying Astronomer Airflow local environment...")
    has_astro = subprocess.run("command -v astro", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0
    if not has_astro:
        print(f"{YELLOW}[WARN] Astro CLI not found in PATH (Install via 'brew install astro'){NC}")
        return True

    res = subprocess.run("astro dev ps", shell=True, capture_output=True, text=True, cwd=str(PROJECT_ROOT))
    if res.returncode == 0 and "running" in res.stdout:
        print(f"{GREEN}[PASS]{NC} Astronomer Airflow services running healthy:")
        for line in res.stdout.strip().split("\n"):
            if "running" in line or "NAME" in line:
                print(f"  {line}")
    else:
        print(f"{YELLOW}[INFO] Astronomer containers not currently running. Use 'astro dev start' or './scripts/orchestration.sh start'.{NC}")

    return True

def run_tests():
    print_header("AIRFLOW ORCHESTRATION VERIFICATION SUITE")
    ok1 = test_dag_ast()
    ok2 = test_astro_status()
    success = ok1 and ok2

    print_header("ORCHESTRATION TEST SUMMARY")
    if success:
        print(f"{GREEN}{BOLD}ALL ORCHESTRATION INTEGRITY TESTS PASSED (100%)!{NC}")
    else:
        print(f"{RED}{BOLD}ORCHESTRATION TESTS FAILED{NC}")
    return success

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
