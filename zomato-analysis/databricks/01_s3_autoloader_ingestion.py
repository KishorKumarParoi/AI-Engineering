"""
Zomato Enterprise Lakehouse: Databricks Auto Loader S3 Ingestion
Principal Data Engineer Standard

Architecture:
  - AWS S3 Landing Bucket (raw JSON / CSV dumps)
  - Auto Loader (`cloudFiles`) with AWS SQS File Notification Mode
  - Schema Evolution ('addNewColumns') & Schema Inference
  - Data Quality Guard: Rescued Data Column ('_rescued_data')
  - Delta Lake ACID Bronze Target: 'zomato_catalog.bronze.orders_raw'
"""

import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def create_spark_session() -> SparkSession:
    """Initialize or retrieve Databricks SparkSession with Delta Lake support."""
    return SparkSession.builder \
        .appName("Zomato-AutoLoader-S3-Ingestion") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

def run_s3_autoloader(
    s3_raw_path: str,
    checkpoint_base: str,
    schema_base: str,
    target_table: str,
    file_format: str = "json",
    is_continuous: bool = False
):
    spark = create_spark_session()
    print(f"[*] Initializing Databricks Auto Loader from S3: {s3_raw_path}")
    print(f"[*] Target Bronze Delta Table: {target_table}")

    schema_location = f"{schema_base}/{target_table.split('.')[-1]}"
    checkpoint_location = f"{checkpoint_base}/{target_table.split('.')[-1]}"

    # Auto Loader Stream Configuration
    autoloader_stream = (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", file_format)
        .option("cloudFiles.schemaLocation", schema_location)
        .option("cloudFiles.schemaEvolutionMode", "addNewColumns")
        .option("cloudFiles.inferColumnTypes", "true")
        # In AWS production, enables SQS queue notification for instantaneous, zero-list ingestion
        .option("cloudFiles.useNotifications", "true")
        .load(s3_raw_path)
        .withColumn("_ingested_at", F.current_timestamp())
        .withColumn("_source_file", F.col("_metadata.file_name"))
        .withColumn("_source_file_size", F.col("_metadata.file_size"))
    )

    # Delta Lake Write Stream
    writer = (
        autoloader_stream.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_location)
        .option("mergeSchema", "true")
    )

    if is_continuous:
        print("[+] Starting continuous 24/7 Auto Loader stream...")
        query = writer.trigger(processingTime="10 seconds").toTable(target_table)
    else:
        print("[+] Starting batch-streaming Auto Loader with Trigger.AvailableNow...")
        query = writer.trigger(availableNow=True).toTable(target_table)

    query.awaitTermination()
    print(f"[✓] Auto Loader batch completed successfully for {target_table}.")

if __name__ == "__main__":
    S3_BASE = "s3://zomato-enterprise-datalake/raw"
    CHECKPOINT_BASE = "s3://zomato-enterprise-datalake/checkpoints/autoloader"
    SCHEMA_BASE = "s3://zomato-enterprise-datalake/schemas/autoloader"

    # Ingest Orders Landing
    run_s3_autoloader(
        s3_raw_path=f"{S3_BASE}/orders/",
        checkpoint_base=CHECKPOINT_BASE,
        schema_base=SCHEMA_BASE,
        target_table="zomato_catalog.bronze.orders_raw",
        file_format="json",
        is_continuous=False
    )
