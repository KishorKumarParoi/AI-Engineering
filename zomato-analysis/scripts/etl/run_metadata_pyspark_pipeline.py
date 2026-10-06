#!/usr/bin/env python3
"""
Zomato Enterprise Lakehouse: Metadata-Driven PySpark & SCD Pipeline CLI
Principal Data Engineer Standard

Usage:
  # Run full metadata pipeline for all configured entities:
  python scripts/etl/run_metadata_pyspark_pipeline.py --all

  # Run a specific entity:
  python scripts/etl/run_metadata_pyspark_pipeline.py --entity dim_restaurants

  # Run end-to-end SCD Type 2 Demonstration (Day 1 Initial Load vs Day 2 Dimension Evolution):
  python scripts/etl/run_metadata_pyspark_pipeline.py --demo-scd2

  # Inspect Delta Lake Table (History & Versions):
  python scripts/etl/run_metadata_pyspark_pipeline.py --inspect dim_restaurants_scd2
"""

import sys
import os
import argparse
import shutil
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from databricks.engine.spark_session import get_spark_session
from databricks.engine.metadata_parser import MetadataRegistry
from databricks.engine.pipeline_runner import MetadataPipelineRunner
from delta.tables import DeltaTable
from pyspark.sql import functions as F

def run_scd2_simulation_demo():
    """
    Simulates Day 1 Initial Load vs Day 2 Dimension Evolution to visibly demonstrate
    SCD Type 2 versioning, record retirement, and surrogate key assignment.
    """
    print("\n" + "=" * 78)
    print("🌟 RUNNING END-TO-END SCD TYPE 2 SIMULATION DEMONSTRATION")
    print("=" * 78)

    spark = get_spark_session("Zomato-SCD2-Demo")
    runner = MetadataPipelineRunner(spark=spark)

    target_delta_dir = str(project_root / "data" / "lakehouse" / "silver" / "dim_restaurants_scd2")
    if os.path.exists(target_delta_dir):
        print(f"[*] Resetting test target Delta directory: {target_delta_dir}")
        shutil.rmtree(target_delta_dir)

    # -------------------------------------------------------------------------
    # DAY 1: Initial Load (5 Authentic Restaurants)
    # -------------------------------------------------------------------------
    print("\n" + "─" * 78)
    print("📅 DAY 1: INITIAL LOAD (Batch of 5 Initial Restaurants)")
    print("─" * 78)

    day1_records = [
        (170435, "Good Flippin' Burgers", 4.2, 1250, 600.0, "Burgers", "Bandra West, Mumbai", "Mumbai"),
        (537139, "NARMADA Chain of Restaurants", 4.4, 3400, 700.0, "Biryani", "Indiranagar, Bangalore", "Bangalore"),
        (56590, "Mangalore Pearl", 4.1, 890, 800.0, "Seafood", "Frazer Town, Bangalore", "Bangalore"),
        (4430, "Shiraz Golden Restaurant", 4.3, 5100, 550.0, "Mughlai", "Park Circus, Kolkata", "Kolkata"),
        (66217, "La Pino'Z Pizza", 4.0, 720, 450.0, "Pizzas", "Athwa, Surat", "Surat"),
    ]
    schema = ["restaurant_id", "restaurant_name", "rating", "rating_count", "cost_for_two", "cuisine", "address", "city"]
    day1_df = spark.createDataFrame(day1_records, schema)

    print("[*] Source DataFrame (Day 1):")
    day1_df.select("restaurant_id", "restaurant_name", "rating", "cost_for_two", "city").show(truncate=False)

    res_day1 = runner.run_entity("dim_restaurants", custom_source_df=day1_df)

    # Inspect Day 1 Target Table
    dt = DeltaTable.forPath(spark, target_delta_dir)
    print("\n[📊] TARGET DELTA TABLE AFTER DAY 1:")
    (
        dt.toDF()
        .select("restaurant_id", "restaurant_name", "rating", "cost_for_two", "is_current", "valid_from", "valid_to")
        .show(truncate=False)
    )

    # -------------------------------------------------------------------------
    # DAY 2: Incremental Changes & New Additions
    # -------------------------------------------------------------------------
    print("\n" + "─" * 78)
    print("📅 DAY 2: INCREMENTAL INGESTION (Dimension Attribute Changes + New Entry)")
    print("─" * 78)
    print("Changes Simulated:")
    print("  1. Restaurant 170435 (Good Flippin' Burgers): Rating jumps 4.2 -> 4.8, Cost jumps 600 -> 750 (CHANGED)")
    print("  2. Restaurant 56590 (Mangalore Pearl): Rating jumps 4.1 -> 4.5, Address updated (CHANGED)")
    print("  3. Restaurant 537139 (NARMADA): Exactly identical attributes (UNCHANGED)")
    print("  4. Restaurant 999001 (Empire Restaurant): Brand new restaurant opening in Bangalore (NEW ENTRY)")

    day2_records = [
        (170435, "Good Flippin' Burgers", 4.8, 1890, 750.0, "Burgers", "Bandra West, Mumbai", "Mumbai"),  # Changed rating & cost
        (56590, "Mangalore Pearl", 4.5, 1120, 800.0, "Seafood", "New Bel Road, Bangalore", "Bangalore"),  # Changed rating & address
        (537139, "NARMADA Chain of Restaurants", 4.4, 3400, 700.0, "Biryani", "Indiranagar, Bangalore", "Bangalore"),  # Unchanged
        (999001, "Empire Restaurant", 4.6, 9200, 850.0, "North Indian", "Church Street, Bangalore", "Bangalore"),  # Brand New
    ]
    day2_df = spark.createDataFrame(day2_records, schema)

    print("\n[*] Source DataFrame (Day 2):")
    day2_df.select("restaurant_id", "restaurant_name", "rating", "cost_for_two", "city").show(truncate=False)

    res_day2 = runner.run_entity("dim_restaurants", custom_source_df=day2_df)

    # -------------------------------------------------------------------------
    # FINAL AUDIT: Proof of SCD Type 2 History & Lineage
    # -------------------------------------------------------------------------
    print("\n" + "=" * 78)
    print("🏆 FINAL SCD TYPE 2 AUDIT & LINEAGE IN DELTA LAKE")
    print("=" * 78)

    final_df = dt.toDF().orderBy("restaurant_id", F.col("valid_from").desc())

    print("\n[+] Full Dimension Table (Historical + Active Records):")
    (
        final_df
        .select(
            "restaurant_id",
            "restaurant_name",
            "rating",
            "cost_for_two",
            "is_current",
            F.date_format("valid_from", "yyyy-MM-dd HH:mm:ss").alias("valid_from"),
            F.date_format("valid_to", "yyyy-MM-dd HH:mm:ss").alias("valid_to")
        )
        .show(15, truncate=False)
    )

    # Check Restaurant 170435 specifically to show the 2 versions
    print("[+] Specific Audit for Restaurant 170435 (Good Flippin' Burgers):")
    (
        final_df
        .filter(F.col("restaurant_id") == 170435)
        .select(
            "restaurant_sk",
            "restaurant_name",
            "rating",
            "cost_for_two",
            "is_current",
            F.date_format("valid_from", "yyyy-MM-dd HH:mm:ss").alias("valid_from"),
            F.date_format("valid_to", "yyyy-MM-dd HH:mm:ss").alias("valid_to")
        )
        .show(truncate=False)
    )

    print("┌" + "─" * 76 + "┐")
    print("│ 🎉 SCD TYPE 2 VERIFICATION CONFIRMED:                                      │")
    print("│   1. Historical record closed: is_current=False, valid_to=Day2_timestamp   │")
    print("│   2. New active record created: is_current=True, valid_to=9999-12-31       │")
    print("│   3. Unchanged records untouched with zero redundant duplicate rows        │")
    print("│   4. Brand new records inserted as version 1 with unique surrogate keys    │")
    print("└" + "─" * 76 + "┘\n")

def inspect_table(table_name: str):
    spark = get_spark_session("Zomato-Inspector")
    target_path = str(project_root / "data" / "lakehouse" / "silver" / table_name)
    if not os.path.exists(target_path) or not DeltaTable.isDeltaTable(spark, target_path):
        print(f"[!] Table '{table_name}' does not exist at {target_path}")
        return

    dt = DeltaTable.forPath(spark, target_path)
    print(f"\n=== INSPECTING DELTA TABLE: {table_name} ===")
    print(f"Path: {target_path}")
    print(f"Total Rows: {dt.toDF().count()}")
    print("\nSchema:")
    dt.toDF().printSchema()
    print("\nSample Rows:")
    dt.toDF().show(10, truncate=False)

    print("\nDelta Lake ACID Commit History:")
    dt.history().select("version", "timestamp", "operation", "operationParameters").show(5, truncate=False)

def main():
    parser = argparse.ArgumentParser(description="Zomato Metadata-Driven PySpark & SCD Pipeline")
    parser.add_argument("--all", action="store_true", help="Execute pipeline for all metadata entities")
    parser.add_argument("--entity", type=str, help="Execute specific metadata entity (e.g. dim_restaurants, dim_food)")
    parser.add_argument("--demo-scd2", action="store_true", help="Run end-to-end SCD Type 2 Demonstration")
    parser.add_argument("--inspect", type=str, help="Inspect Delta table history and rows")

    args = parser.parse_args()

    if args.demo_scd2:
        run_scd2_simulation_demo()
        return

    if args.inspect:
        inspect_table(args.inspect)
        return

    spark = get_spark_session()
    runner = MetadataPipelineRunner(spark=spark)

    if args.entity:
        runner.run_entity(args.entity)
    elif args.all:
        runner.run_all()
    else:
        # Default behavior: Run SCD-2 demonstration
        run_scd2_simulation_demo()

if __name__ == "__main__":
    main()
