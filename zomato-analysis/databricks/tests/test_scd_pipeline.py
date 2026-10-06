"""
Zomato Enterprise Lakehouse: Comprehensive Test Suite for Metadata-Driven PySpark & SCD
Tests Metadata Parsing, Data Quality Quarantine, SCD Type 1, and SCD Type 2.
"""

import os
import shutil
import pytest
from pathlib import Path
from pyspark.sql import functions as F

from databricks.engine.spark_session import get_spark_session
from databricks.engine.metadata_parser import MetadataRegistry
from databricks.engine.data_quality import DataQualityEngine
from databricks.engine.scd_processor import SCDProcessor
from databricks.engine.pipeline_runner import MetadataPipelineRunner
from delta.tables import DeltaTable

@pytest.fixture(scope="session")
def spark():
    session = get_spark_session("Zomato-SCD-TestSuite")
    yield session

@pytest.fixture(scope="session")
def registry():
    return MetadataRegistry()

def test_metadata_registry_loading(registry):
    assert "dim_restaurants" in registry.entities
    assert "dim_customers" in registry.entities
    assert "dim_food" in registry.entities
    assert "fct_orders_stream" in registry.entities

    rest_cfg = registry.get_entity("dim_restaurants")
    assert rest_cfg.scd_config.scd_type == "SCD_TYPE_2"
    assert "rating" in rest_cfg.scd_config.tracked_columns
    assert rest_cfg.target.format == "delta"

    food_cfg = registry.get_entity("dim_food")
    assert food_cfg.scd_config.scd_type == "SCD_TYPE_1"

def test_data_quality_quarantine(spark, registry):
    entity_cfg = registry.get_entity("dim_restaurants")

    records = [
        (101, "Valid Burger Hub", 4.5, 100, 300.0, "Burgers", "Street 1", "Mumbai"),
        (None, "Invalid Null PK", 4.0, 50, 200.0, "Fast Food", "Street 2", "Delhi"),  # Fails NOT_NULL on ID
        (102, "Invalid Negative Cost", 3.8, 40, -50.0, "Snacks", "Street 3", "Pune"), # Fails GREATER_THAN on cost
        (103, "Invalid Rating Out of Bounds", 9.9, 10, 400.0, "Desserts", "Street 4", "Bangalore") # Fails BETWEEN 0..5
    ]
    schema = ["restaurant_id", "restaurant_name", "rating", "rating_count", "cost_for_two", "cuisine", "address", "city"]
    df = spark.createDataFrame(records, schema)

    clean_df, quarantined_df = DataQualityEngine.evaluate(df, entity_cfg)

    assert clean_df.count() == 1
    assert clean_df.first()["restaurant_id"] == 101
    assert quarantined_df.count() == 3

def test_scd_type_1_in_place_overwrite(spark, registry, tmp_path):
    entity_cfg = registry.get_entity("dim_food")
    # Redirect to isolated temp path
    test_target_path = str(tmp_path / "dim_food_scd1_test")
    entity_cfg.target.path = test_target_path

    # Initial batch
    day1_records = [
        ("fd01", "Aloo Burger", 65.0, "Burgers", "Veg"),
        ("fd02", "Chicken Biryani", 240.0, "Biryani", "Non-Veg"),
    ]
    schema = ["food_id", "food_name", "price", "category", "veg_or_non_veg"]
    df_day1 = spark.createDataFrame(day1_records, schema)

    res1 = SCDProcessor.apply_scd_type_1(spark, df_day1, entity_cfg)
    assert res1["status"] == "INITIALIZED"

    dt = DeltaTable.forPath(spark, test_target_path)
    assert dt.toDF().count() == 2

    # Update price on fd01 and add new item fd03
    day2_records = [
        ("fd01", "Aloo Burger", 85.0, "Burgers", "Veg"),       # Price changed from 65 to 85
        ("fd02", "Chicken Biryani", 240.0, "Biryani", "Non-Veg"), # Unchanged
        ("fd03", "Cold Coffee", 110.0, "Beverages", "Veg"),    # New item
    ]
    df_day2 = spark.createDataFrame(day2_records, schema)

    res2 = SCDProcessor.apply_scd_type_1(spark, df_day2, entity_cfg)
    assert res2["status"] == "MERGED_SCD1"

    # SCD Type 1 should maintain exactly 3 unique rows with latest prices
    result_df = dt.toDF().orderBy("food_id")
    assert result_df.count() == 3
    row_fd01 = result_df.filter(F.col("food_id") == "fd01").first()
    assert row_fd01["price"] == 85.0  # Overwritten in place

def test_scd_type_2_history_tracking(spark, registry, tmp_path):
    entity_cfg = registry.get_entity("dim_restaurants")
    test_target_path = str(tmp_path / "dim_restaurants_scd2_test")
    entity_cfg.target.path = test_target_path

    # Day 1: 2 records
    day1_records = [
        (1001, "Burger King", 4.1, 500, 350.0, "Burgers", "Connaught Place", "Delhi"),
        (1002, "Karim's", 4.6, 2200, 700.0, "Mughlai", "Jama Masjid", "Delhi"),
    ]
    schema = ["restaurant_id", "restaurant_name", "rating", "rating_count", "cost_for_two", "cuisine", "address", "city"]
    df_day1 = spark.createDataFrame(day1_records, schema)

    res1 = SCDProcessor.apply_scd_type_2(spark, df_day1, entity_cfg)
    assert res1["status"] == "INITIALIZED_SCD2"

    dt = DeltaTable.forPath(spark, test_target_path)
    assert dt.toDF().filter(F.col("is_current") == True).count() == 2

    # Day 2: 1001 changes rating & cost, 1002 is unchanged, 1003 is new
    day2_records = [
        (1001, "Burger King", 4.5, 750, 420.0, "Burgers", "Connaught Place", "Delhi"),  # Changed
        (1002, "Karim's", 4.6, 2200, 700.0, "Mughlai", "Jama Masjid", "Delhi"),          # Unchanged
        (1003, "Saravana Bhavan", 4.7, 3100, 400.0, "South Indian", "Janpath", "Delhi"), # New
    ]
    df_day2 = spark.createDataFrame(day2_records, schema)

    res2 = SCDProcessor.apply_scd_type_2(spark, df_day2, entity_cfg)
    assert res2["status"] == "MERGED_SCD2"

    final_df = dt.toDF()
    # Total rows should be: 1 (closed) + 1 (new version of 1001) + 1 (1002) + 1 (1003) = 4 rows
    assert final_df.count() == 4
    assert final_df.filter(F.col("is_current") == True).count() == 3
    assert final_df.filter(F.col("is_current") == False).count() == 1

    # Check that 1001 has exactly 2 versions: one active and one retired
    v_closed = final_df.filter((F.col("restaurant_id") == 1001) & (F.col("is_current") == False)).first()
    v_active = final_df.filter((F.col("restaurant_id") == 1001) & (F.col("is_current") == True)).first()

    assert v_closed["rating"] == 4.1
    assert v_active["rating"] == 4.5
    assert v_closed["valid_to"] == v_active["valid_from"]
    assert str(v_active["valid_to"]).startswith("9999-12-31")
