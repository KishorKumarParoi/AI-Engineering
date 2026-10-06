#!/usr/bin/env -S uv run python
# -*- coding: utf-8 -*-
"""
Test Suite: testing/data-engineering/test_pyspark_scd.py
Purpose: Metadata-Driven PySpark Engine & Delta Lake SCD Type 1 & 2 Verification
Tier: Senior Staff / Lead Data Engineer Standard

Validates:
  1. Declarative YAML Metadata Registry Loading & Entity Parsing
  2. Data Quality Rules Engine & Automated Quarantine Isolation
  3. Delta Lake SCD Type 1 In-Place Atomic MERGE
  4. Delta Lake SCD Type 2 Timeline History Tracking (valid_from, valid_to, is_current)
"""

import os
import sys
import time
import shutil
from pathlib import Path

# Enforce Java 17 for PySpark Delta compatibility on macOS
temurin_17 = "/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home"
if os.path.isdir(temurin_17):
    os.environ["JAVA_HOME"] = temurin_17

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Enforce virtual environment python for worker subprocesses
venv_python = PROJECT_ROOT / ".venv" / "bin" / "python"
if venv_python.exists():
    os.environ["PYSPARK_PYTHON"] = str(venv_python)
    os.environ["PYSPARK_DRIVER_PYTHON"] = str(venv_python)

GREEN = "\033[0;32m"
BLUE = "\033[0;34m"
CYAN = "\033[0;36m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
BOLD = "\033[1m"
NC = "\033[0m"

def print_header(title: str):
    print(f"\n{CYAN}{BOLD}=========================================================={NC}")
    print(f"{CYAN}{BOLD}  {title}{NC}")
    print(f"{CYAN}{BOLD}=========================================================={NC}")

def test_pyspark_scd():
    print_header("METADATA-DRIVEN PYSPARK & DELTA LAKE SCD VERIFICATION")
    
    start_time = time.time()
    try:
        from databricks.engine.spark_session import get_spark_session
        from databricks.engine.metadata_parser import MetadataRegistry
        from databricks.engine.data_quality import DataQualityEngine
        from databricks.engine.scd_processor import SCDProcessor
        from delta.tables import DeltaTable
    except ImportError as e:
        print(f"{RED}[FAIL] Missing PySpark / Delta Lake dependencies: {e}{NC}")
        return False

    # 1. Test Metadata Registry
    print(f"{BLUE}[INFO] 1/4. Validating Declarative Metadata Registry (pipeline_metadata.yaml)...{NC}")
    registry = MetadataRegistry()
    entities = registry.entities
    expected_entities = ["dim_restaurants", "dim_customers", "dim_food", "fct_orders_stream"]
    for e in expected_entities:
        if e not in entities:
            print(f"{RED}[FAIL] Entity {e} not found in metadata registry!{NC}")
            return False
    print(f"  {GREEN}[PASS]{NC} Metadata Registry loaded {len(entities)} entities successfully:")
    for e, cfg in entities.items():
        print(f"    - {e}: format={cfg.target.format}, SCD={cfg.scd_config.scd_type if cfg.scd_config else 'APPEND_ONLY'}")

    # 2. Test Spark Session Initialization
    print(f"\n{BLUE}[INFO] 2/4. Initializing Apache Spark Session with Delta Lake 3.2.0...{NC}")
    spark = get_spark_session("Zomato-MasterRunner-Verification")
    print(f"  {GREEN}[PASS]{NC} Spark Session active (Version: {spark.version})")

    # 3. Test Data Quality Quarantine Engine
    print(f"\n{BLUE}[INFO] 3/4. Testing Data Quality & Quarantine Isolation Engine...{NC}")
    rest_cfg = registry.get_entity("dim_restaurants")
    sample_records = [
        (101, "Valid Burger Hub", 4.5, 100, 300.0, "Burgers", "Street 1", "Mumbai"),
        (None, "Invalid Null PK", 4.0, 50, 200.0, "Fast Food", "Street 2", "Delhi"),
        (102, "Invalid Negative Cost", 3.8, 40, -50.0, "Snacks", "Street 3", "Pune"),
        (103, "Invalid Rating Out of Bounds", 9.9, 10, 400.0, "Desserts", "Street 4", "Bangalore")
    ]
    schema = ["restaurant_id", "restaurant_name", "rating", "rating_count", "cost_for_two", "cuisine", "address", "city"]
    raw_df = spark.createDataFrame(sample_records, schema)
    clean_df, quarantined_df = DataQualityEngine.evaluate(raw_df, rest_cfg)

    clean_count = clean_df.count()
    quarantine_count = quarantined_df.count()
    if clean_count != 1 or quarantine_count != 3:
        print(f"{RED}[FAIL] DQ Engine unexpected counts: clean={clean_count}, quarantine={quarantine_count}{NC}")
        return False
    print(f"  {GREEN}[PASS]{NC} DQ Engine accurately isolated: {clean_count} clean record, {quarantine_count} quarantined records")

    # 4. Test SCD Type 1 & Type 2 Delta Merges in sandbox
    print(f"\n{BLUE}[INFO] 4/4. Testing Delta Lake SCD Type 1 & SCD Type 2 MERGE Operations...{NC}")
    sandbox_dir = PROJECT_ROOT / "data" / "lakehouse" / "test_sandbox"
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir, ignore_errors=True)

    try:
        # SCD 1 Test
        food_cfg = registry.get_entity("dim_food")
        scd1_dir = str(sandbox_dir / "dim_food")
        food_cfg.target.path = scd1_dir
        initial_food = [("fd01", "Burger", 100.0, "Burgers", "Veg")]
        f_schema = ["food_id", "food_name", "price", "category", "veg_or_non_veg"]
        SCDProcessor.apply_scd_type_1(spark, spark.createDataFrame(initial_food, f_schema), food_cfg)

        updated_food = [("fd01", "Burger", 150.0, "Burgers", "Veg")] # updated price
        SCDProcessor.apply_scd_type_1(spark, spark.createDataFrame(updated_food, f_schema), food_cfg)
        scd1_res = spark.read.format("delta").load(scd1_dir).collect()
        if len(scd1_res) != 1 or scd1_res[0]["price"] != 150.0:
            print(f"{RED}[FAIL] SCD-1 overwrite failed!{NC}")
            return False
        print(f"  {GREEN}[PASS]{NC} SCD Type 1 in-place atomic update verified (price 100.0 -> 150.0)")

        # SCD 2 Test
        rest_cfg = registry.get_entity("dim_restaurants")
        scd2_dir = str(sandbox_dir / "dim_restaurants")
        rest_cfg.target.path = scd2_dir
        initial_rest = [(201, "Pizza Bella", 4.2, 50, 400.0, "Italian", "Main Rd", "Pune")]
        r_schema = ["restaurant_id", "restaurant_name", "rating", "rating_count", "cost_for_two", "cuisine", "address", "city"]
        SCDProcessor.apply_scd_type_2(spark, spark.createDataFrame(initial_rest, r_schema), rest_cfg)

        updated_rest = [(201, "Pizza Bella", 4.8, 80, 400.0, "Italian", "Main Rd", "Pune")] # rating changed 4.2 -> 4.8
        SCDProcessor.apply_scd_type_2(spark, spark.createDataFrame(updated_rest, r_schema), rest_cfg)
        scd2_df = spark.read.format("delta").load(scd2_dir)
        scd2_records = scd2_df.collect()

        if len(scd2_records) != 2:
            print(f"{RED}[FAIL] SCD-2 expected 2 history versions, got {len(scd2_records)}{NC}")
            return False
        
        current_rec = [r for r in scd2_records if r["is_current"]][0]
        historical_rec = [r for r in scd2_records if not r["is_current"]][0]

        if current_rec["rating"] != 4.8 or historical_rec["rating"] != 4.2:
            print(f"{RED}[FAIL] SCD-2 version values do not match expected ratings!{NC}")
            return False

        print(f"  {GREEN}[PASS]{NC} SCD Type 2 timeline versioning verified:")
        print(f"    - Historical Record: rating={historical_rec['rating']}, is_current={historical_rec['is_current']}, valid_to={historical_rec['valid_to']}")
        print(f"    - Current Record:    rating={current_rec['rating']}, is_current={current_rec['is_current']}, valid_to={current_rec['valid_to']}")

    finally:
        if sandbox_dir.exists():
            shutil.rmtree(sandbox_dir, ignore_errors=True)

    elapsed = time.time() - start_time
    print(f"\n{CYAN}{BOLD}=========================================================={NC}")
    print(f"{GREEN}{BOLD}ALL METADATA PYSPARK & SCD CHECKS PASSED (100%) in {elapsed:.2f}s!{NC}")
    print(f"{CYAN}{BOLD}=========================================================={NC}")
    return True

if __name__ == "__main__":
    success = test_pyspark_scd()
    sys.exit(0 if success else 1)
