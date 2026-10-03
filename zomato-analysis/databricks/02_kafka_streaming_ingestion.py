"""
Zomato Enterprise Lakehouse: Databricks Kafka Streaming & Batch Ingestion
Principal Data Engineer Standard

Architecture:
  - Kafka Topics:
      1. `zomato.order_events` (Live high-frequency orders: ~50k events/sec)
      2. `zomato.rider_telemetry` (Live rider GPS lat/lng & speed)
  - Spark Structured Streaming (`spark-sql-kafka-0-10`)
  - Schema Deserialization & Event Watermarking (Handles late arrivals up to 15 mins)
  - Execution Modes:
      * Real-Time Stream: .trigger(processingTime="5 seconds")
      * Batch Stream    : .trigger(availableNow=True) [Airflow / Cost-Optimized]
  - Target: Delta Lake Bronze Table `zomato_catalog.bronze.kafka_order_events`
"""

import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    IntegerType, TimestampType, BooleanType
)

def create_spark_session() -> SparkSession:
    """Initialize Databricks SparkSession with Kafka and Delta Lake connectors."""
    return SparkSession.builder \
        .appName("Zomato-Kafka-Structured-Streaming") \
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        .config("spark.sql.streaming.forceDeleteTempCheckpointLocation", "true") \
        .getOrCreate()

# Schema for incoming Kafka order events
ORDER_EVENT_SCHEMA = StructType([
    StructField("order_id", StringType(), False),
    StructField("customer_id", StringType(), False),
    StructField("restaurant_id", StringType(), False),
    StructField("rider_id", StringType(), True),
    StructField("order_status", StringType(), False), # PLACED, ACCEPTED, PREPARING, PICKED_UP, DELIVERED
    StructField("order_amount", DoubleType(), False),
    StructField("delivery_fee", DoubleType(), True),
    StructField("item_count", IntegerType(), True),
    StructField("payment_method", StringType(), True),
    StructField("restaurant_lat", DoubleType(), True),
    StructField("restaurant_lng", DoubleType(), True),
    StructField("delivery_lat", DoubleType(), True),
    StructField("delivery_lng", DoubleType(), True),
    StructField("event_timestamp", TimestampType(), False),
])

def run_kafka_stream(
    kafka_bootstrap_servers: str,
    topic_name: str,
    checkpoint_location: str,
    target_table: str,
    trigger_mode: str = "available_now", # "available_now" or "real_time"
    starting_offsets: str = "latest"
):
    spark = create_spark_session()
    print(f"[*] Initializing Kafka Structured Streaming from {kafka_bootstrap_servers} on topic [{topic_name}]")
    print(f"[*] Trigger Mode: {trigger_mode.upper()} | Starting Offsets: {starting_offsets}")

    # 1. Read Raw Binary Stream from Kafka
    raw_kafka_df = (
        spark.readStream
        .format("kafka")
        .option("kafka.bootstrap.servers", kafka_bootstrap_servers)
        .option("subscribe", topic_name)
        .option("startingOffsets", starting_offsets)
        .option("failOnDataLoss", "false")
        .option("maxOffsetsPerTrigger", 100000) # Prevents OOM under burst conditions (50k/sec)
        .load()
    )

    # 2. Deserialize Binary Payload & Apply Watermarking for Late Data
    parsed_events = (
        raw_kafka_df
        .selectExpr(
            "CAST(key AS STRING) AS kafka_key",
            "CAST(value AS STRING) AS json_payload",
            "topic AS kafka_topic",
            "partition AS kafka_partition",
            "offset AS kafka_offset",
            "timestamp AS kafka_ingest_timestamp"
        )
        .withColumn("data", F.from_json(F.col("json_payload"), ORDER_EVENT_SCHEMA))
        .select(
            "kafka_key",
            "kafka_topic",
            "kafka_partition",
            "kafka_offset",
            "kafka_ingest_timestamp",
            "data.*"
        )
        # Watermark allows Spark state store to drop duplicate events older than 15 minutes
        .withWatermark("event_timestamp", "15 minutes")
        .dropDuplicates(["order_id", "order_status", "event_timestamp"])
        .withColumn("_ingested_to_bronze_at", F.current_timestamp())
    )

    # 3. Write Stream to Delta Lake
    writer = (
        parsed_events.writeStream
        .format("delta")
        .outputMode("append")
        .option("checkpointLocation", checkpoint_location)
        .option("mergeSchema", "true")
    )

    if trigger_mode == "real_time":
        print("[+] Launching continuous low-latency stream (5s micro-batch)...")
        query = writer.trigger(processingTime="5 seconds").toTable(target_table)
    else:
        print("[+] Launching cost-optimized batch stream (Trigger.AvailableNow)...")
        query = writer.trigger(availableNow=True).toTable(target_table)

    query.awaitTermination()
    print(f"[✓] Kafka ingestion finished writing into {target_table}.")

if __name__ == "__main__":
    KAFKA_BROKERS = "localhost:9092" # Or AWS MSK / Confluent Cloud endpoint
    CHECKPOINT_DIR = "/tmp/delta/checkpoints/kafka_orders"
    TARGET_DELTA_TABLE = "zomato_catalog.bronze.kafka_order_events"

    run_kafka_stream(
        kafka_bootstrap_servers=KAFKA_BROKERS,
        topic_name="zomato.order_events",
        checkpoint_location=CHECKPOINT_DIR,
        target_table=TARGET_DELTA_TABLE,
        trigger_mode="available_now"
    )
