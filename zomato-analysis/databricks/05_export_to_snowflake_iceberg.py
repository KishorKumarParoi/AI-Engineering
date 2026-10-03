"""
Zomato Enterprise Lakehouse: Databricks to Snowflake Iceberg Bridge
Principal Data Engineer Standard

Bridge Mechanisms:
  1. Delta Lake Universal Format (UniForm):
      - Emits Apache Iceberg metadata on top of Delta Parquet files in S3.
      - Snowflake queries Delta tables as native Iceberg External Tables with ZERO data copying!
  2. Fallback / Standard Bridge:
      - Exports partitioned Snappy-compressed Parquet files directly to S3 Stage for Snowflake COPY INTO or External Tables.
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

def create_spark_session() -> SparkSession:
    return SparkSession.builder \
        .appName("Zomato-Databricks-Snowflake-Bridge") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

def export_delta_to_snowflake_stage(
    source_table: str,
    s3_export_path: str,
    partition_cols: list = None
):
    spark = create_spark_session()
    print(f"[*] Reading Databricks ML Enriched Table: {source_table}")
    print(f"[*] Target S3 Snowflake Stage Path: {s3_export_path}")

    # Read enriched orders with ML ETA predictions
    df = spark.table(source_table)

    # 1. Option A: Enable Delta UniForm (Iceberg compatibility on Delta)
    try:
        print("[+] Configuring Delta Lake UniForm (Universal Format Iceberg metadata)...")
        spark.sql(f"""
            ALTER TABLE {source_table} 
            SET TBLPROPERTIES (
                'delta.universalFormat.enabledFormats' = 'iceberg'
            )
        """)
        print("[✓] UniForm Iceberg metadata enabled successfully.")
    except Exception as e:
        print(f"[i] UniForm requires Databricks Runtime 14.3+ (Notice: {e}). Proceeding with high-speed Parquet export.")

    # 2. Option B: High-Performance Parquet Export to S3 Stage
    writer = (
        df.write
        .format("parquet")
        .option("compression", "snappy")
        .mode("overwrite")
    )

    if partition_cols:
        writer = writer.partitionBy(*partition_cols)

    writer.save(s3_export_path)
    print(f"[✓] Successfully exported {df.count()} rows to {s3_export_path} for Snowflake ingestion.")

if __name__ == "__main__":
    SOURCE = "zomato_catalog.silver.orders_with_eta_predictions"
    S3_STAGE = "s3://zomato-enterprise-datalake/export/snowflake_ml_eta/"
    
    export_delta_to_snowflake_stage(
        source_table=SOURCE,
        s3_export_path=S3_STAGE,
        partition_cols=["order_hour"]
    )
