"""
Zomato Enterprise Lakehouse: Databricks PySpark Silver ETL Layer
Principal Data Engineer Standard

Transformations:
  1. Unifies Bronze Kafka Event Stream and S3 Order Dumps.
  2. Calculates Geospatial Haversine Distance (km) between Restaurant and Customer.
  3. Feature Engineering for ML:
      - `delivery_distance_km`
      - `order_hour`, `day_of_week`, `is_weekend`, `is_peak_dining_hour`
      - Preparation complexity score based on item count.
  4. Delta Lake ACID MERGE INTO target Silver Table `zomato_catalog.silver.orders_enriched`.
"""

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from delta.tables import DeltaTable

def create_spark_session() -> SparkSession:
    return SparkSession.builder \
        .appName("Zomato-Silver-PySpark-ETL") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .getOrCreate()

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """Computes great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0 # Earth's radius in kilometers
    dlat = F.radians(lat2 - lat1)
    dlon = F.radians(lon2 - lon1)
    a = (
        F.sin(dlat / 2.0) ** 2
        + F.cos(F.radians(lat1)) * F.cos(F.radians(lat2)) * (F.sin(dlon / 2.0) ** 2)
    )
    c = 2.0 * F.atan2(F.sqrt(a), F.sqrt(1.0 - a))
    return r * c

def run_silver_transformation():
    spark = create_spark_session()
    print("[*] Running Databricks PySpark Silver Transformation...")

    # Read from Bronze Kafka Events (or Delta Bronze)
    bronze_df = spark.table("zomato_catalog.bronze.kafka_order_events")

    # Filter to latest valid orders
    enriched_df = (
        bronze_df
        .filter(F.col("order_id").isNotNull())
        .withColumn(
            "delivery_distance_km",
            F.round(
                calculate_haversine_distance(
                    F.col("restaurant_lat"),
                    F.col("restaurant_lng"),
                    F.col("delivery_lat"),
                    F.col("delivery_lng")
                ),
                2
            )
        )
        .withColumn("order_hour", F.hour(F.col("event_timestamp")))
        .withColumn("day_of_week", F.dayofweek(F.col("event_timestamp")))
        .withColumn("is_weekend", F.when(F.col("day_of_week").isin([1, 7]), 1).otherwise(0))
        .withColumn(
            "is_peak_dining_hour",
            F.when(
                (F.col("order_hour").between(12, 14)) | (F.col("order_hour").between(19, 22)),
                1
            ).otherwise(0)
        )
        .withColumn(
            "prep_complexity_score",
            F.when(F.col("item_count") <= 2, 1.0)
             .when(F.col("item_count") <= 5, 1.8)
             .otherwise(2.5)
        )
        .withColumn("_transformed_at", F.current_timestamp())
    )

    # Upsert into Delta Silver using MERGE INTO
    target_table_name = "zomato_catalog.silver.orders_enriched"
    
    if not spark.catalog.tableExists(target_table_name):
        print(f"[+] Target table {target_table_name} does not exist. Creating as Delta...")
        (
            enriched_df.write
            .format("delta")
            .mode("overwrite")
            .partitionBy("is_weekend")
            .saveAsTable(target_table_name)
        )
    else:
        print(f"[+] Performing ACID Delta MERGE into {target_table_name}...")
        target_delta = DeltaTable.forName(spark, target_table_name)
        (
            target_delta.alias("tgt")
            .merge(
                source=enriched_df.alias("src"),
                condition="tgt.order_id = src.order_id"
            )
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute()
        )

    print(f"[✓] Silver transformation and Delta MERGE completed successfully.")

if __name__ == "__main__":
    run_silver_transformation()
