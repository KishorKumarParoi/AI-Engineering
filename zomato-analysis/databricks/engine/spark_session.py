"""
Zomato Enterprise Lakehouse: Centralized SparkSession Provider
Supports local Delta Lake operations and Azure ADLS Gen2 / Databricks deployment.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure Java 17 and Python worker paths are configured
java_temurin_17 = "/Library/Java/JavaVirtualMachines/temurin-17.jdk/Contents/Home"
if os.path.exists(java_temurin_17) and "JAVA_HOME" not in os.environ:
    os.environ["JAVA_HOME"] = java_temurin_17

# Ensure driver and worker Python use the project .venv
project_root = Path(__file__).resolve().parents[2]
venv_python = str(project_root / ".venv" / "bin" / "python")
if os.path.exists(venv_python):
    os.environ.setdefault("PYSPARK_PYTHON", venv_python)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", venv_python)

from pyspark.sql import SparkSession
from delta import configure_spark_with_delta_pip

_spark_instance: SparkSession | None = None

def get_spark_session(app_name: str = "Zomato-Metadata-PySpark-Engine") -> SparkSession:
    """
    Returns or creates a high-performance SparkSession pre-configured for Delta Lake ACID operations.
    """
    global _spark_instance
    if _spark_instance is not None:
        try:
            if not _spark_instance.sparkContext._jsc.sc().isStopped():
                return _spark_instance
        except Exception:
            pass

    load_dotenv(project_root / ".env")

    builder = SparkSession.builder \
        .appName(app_name) \
        .master("local[2]") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.sql.shuffle.partitions", "4") \
        .config("spark.default.parallelism", "4") \
        .config("spark.databricks.delta.schema.autoMerge.enabled", "true") \
        .config("spark.sql.parquet.compression.codec", "snappy")

    # Configure Azure ADLS Gen2 connector if credentials exist
    storage_account = os.getenv("AZURE_STORAGE_ACCOUNT") or os.getenv("STORAGE_ACCOUNT_NAME")
    storage_key = os.getenv("AZURE_STORAGE_KEY") or os.getenv("STORAGE_ACCOUNT_KEY")
    if storage_account and storage_key:
        builder = builder.config(
            f"fs.azure.account.key.{storage_account}.dfs.core.windows.net",
            storage_key
        )

    _spark_instance = configure_spark_with_delta_pip(builder).getOrCreate()
    _spark_instance.sparkContext.setLogLevel("WARN")
    return _spark_instance
