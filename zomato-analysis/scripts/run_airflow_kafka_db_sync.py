#!/usr/bin/env python3
"""
Zomato Enterprise Lakehouse: Kafka-to-Snowflake Medallion Ingestion Script
Principal Data Engineer Standard

This script is invoked by Airflow Cronjobs (dags/kafka_to_snowflake_sync_dag.py)
or on-demand via the Web UI / CLI to consume Kafka events and update Snowflake:
  1. Consumes buffered events from Kafka / local event buffer.
  2. Deduplicates by order_id.
  3. Executes UPSERT (MERGE INTO) into ZOMATO.RAW.KAFKA_ORDER_EVENTS.
  4. Records sync metrics and audit timestamps.
"""

import os
import sys
import json
import glob
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

try:
    import snowflake.connector
    HAS_SNOWFLAKE = True
except ImportError:
    HAS_SNOWFLAKE = False

candidate_buffers = [
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "kafka_order_events.jsonl")),
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "kafka_order_events.jsonl")),
    "/app/data/kafka_order_events.jsonl",
    "/usr/local/airflow/data/kafka_order_events.jsonl"
]
BUFFER_FILE = next((p for p in candidate_buffers if os.path.exists(p)), candidate_buffers[0])

def get_snowflake_connection():
    if not HAS_SNOWFLAKE:
        return None
    user = os.getenv("SNOWFLAKE_USER") or os.getenv("SNOWFLAKE_USERNAME")
    password = os.getenv("SNOWFLAKE_PASSWORD")
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    warehouse = os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH")
    database = os.getenv("SNOWFLAKE_DATABASE", "ZOMATO")
    role = os.getenv("SNOWFLAKE_ROLE", "DBT_ROLE")

    if not (user and password and account):
        print("[!] Snowflake credentials missing in environment.")
        return None

    try:
        conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            warehouse=warehouse,
            database=database,
            schema="RAW",
            role=role
        )
        return conn
    except Exception as e:
        print(f"[!] Snowflake connection error: {e}")
        return None

def collect_unconsumed_events():
    """Reads events from the shared buffer and returns unique events."""
    events = []
    seen_ids = set()

    if os.path.exists(BUFFER_FILE):
        with open(BUFFER_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    oid = ev.get("order_id")
                    if oid and oid not in seen_ids:
                        seen_ids.add(oid)
                        events.append(ev)
                except json.JSONDecodeError:
                    continue

    # Also check /tmp for any ephemeral event streams
    tmp_buffer = "/tmp/zomato_kafka_events.jsonl"
    if os.path.exists(tmp_buffer):
        with open(tmp_buffer, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    oid = ev.get("order_id")
                    if oid and oid not in seen_ids:
                        seen_ids.add(oid)
                        events.append(ev)
                except json.JSONDecodeError:
                    continue

    return events

def sync_events_to_snowflake(events=None):
    """Upserts collected order events into ZOMATO.RAW.KAFKA_ORDER_EVENTS."""
    if events is None:
        events = collect_unconsumed_events()

    if not events:
        print("[*] No unconsumed Kafka order events found in buffer. (Queue clean)")
        return {"status": "NO_OP", "rows_ingested": 0, "message": "Buffer empty"}

    print(f"[*] Processing {len(events)} Kafka order events for Snowflake ingestion...")
    conn = get_snowflake_connection()
    if not conn:
        print("[!] Operating in simulated database update mode (Snowflake connector unavailable).")
        return {
            "status": "SIMULATED",
            "rows_ingested": len(events),
            "message": f"Processed {len(events)} events in offline simulated mode."
        }

    cur = conn.cursor()
    cur.execute("USE SCHEMA ZOMATO.RAW")
    
    # Ensure destination table exists
    cur.execute("""
    CREATE TABLE IF NOT EXISTS ZOMATO.RAW.KAFKA_ORDER_EVENTS (
        order_id VARCHAR(64) PRIMARY KEY,
        customer_id VARCHAR(64),
        restaurant_id NUMBER(38,0),
        restaurant_name VARCHAR(256),
        food_id VARCHAR(64),
        food_name VARCHAR(256),
        cuisine VARCHAR(128),
        city VARCHAR(64),
        order_status VARCHAR(32),
        order_amount NUMBER(10,2),
        delivery_fee NUMBER(10,2),
        item_count NUMBER(38,0),
        payment_method VARCHAR(64),
        distance_km NUMBER(6,2),
        predicted_eta_mins NUMBER(6,1),
        restaurant_lat NUMBER(9,6),
        restaurant_lng NUMBER(9,6),
        delivery_lat NUMBER(9,6),
        delivery_lng NUMBER(9,6),
        event_timestamp TIMESTAMP_TZ,
        ingested_at TIMESTAMP_TZ DEFAULT CURRENT_TIMESTAMP()
    )
    """)

    # Merge each event into Snowflake
    merge_sql = """
    MERGE INTO ZOMATO.RAW.KAFKA_ORDER_EVENTS target
    USING (
        SELECT 
            %s AS order_id, %s AS customer_id, %s AS restaurant_id, %s AS restaurant_name,
            %s AS food_id, %s AS food_name, %s AS cuisine, %s AS city,
            %s AS order_status, %s AS order_amount, %s AS delivery_fee, %s AS item_count,
            %s AS payment_method, %s AS distance_km, %s AS predicted_eta_mins,
            %s AS restaurant_lat, %s AS restaurant_lng, %s AS delivery_lat, %s AS delivery_lng,
            %s::TIMESTAMP_TZ AS event_timestamp
    ) src
    ON target.order_id = src.order_id
    WHEN MATCHED THEN
        UPDATE SET 
            order_status = src.order_status,
            order_amount = src.order_amount,
            delivery_fee = src.delivery_fee,
            ingested_at = CURRENT_TIMESTAMP()
    WHEN NOT MATCHED THEN
        INSERT (
            order_id, customer_id, restaurant_id, restaurant_name,
            food_id, food_name, cuisine, city,
            order_status, order_amount, delivery_fee, item_count,
            payment_method, distance_km, predicted_eta_mins,
            restaurant_lat, restaurant_lng, delivery_lat, delivery_lng,
            event_timestamp, ingested_at
        ) VALUES (
            src.order_id, src.customer_id, src.restaurant_id, src.restaurant_name,
            src.food_id, src.food_name, src.cuisine, src.city,
            src.order_status, src.order_amount, src.delivery_fee, src.item_count,
            src.payment_method, src.distance_km, src.predicted_eta_mins,
            src.restaurant_lat, src.restaurant_lng, src.delivery_lat, src.delivery_lng,
            src.event_timestamp, CURRENT_TIMESTAMP()
        )
    """

    ingested_count = 0
    for ev in events:
        params = (
            str(ev.get("order_id")),
            str(ev.get("customer_id", "CUST-UNKNOWN")),
            int(ev.get("restaurant_id", 0)),
            str(ev.get("restaurant_name", "Unknown")),
            str(ev.get("food_id", "fd0")),
            str(ev.get("food_name", "Unknown Item")),
            str(ev.get("cuisine", "General")),
            str(ev.get("city", "Bangalore")),
            str(ev.get("order_status", "PLACED")),
            float(ev.get("order_amount", 0.0)),
            float(ev.get("delivery_fee", 0.0)),
            int(ev.get("item_count", 1)),
            str(ev.get("payment_method", "UPI")),
            float(ev.get("distance_km", 3.0)),
            float(ev.get("predicted_eta_mins", 25.0)),
            float(ev.get("restaurant_lat", 12.97)),
            float(ev.get("restaurant_lng", 77.59)),
            float(ev.get("delivery_lat", 12.95)),
            float(ev.get("delivery_lng", 77.61)),
            str(ev.get("event_timestamp", datetime.now(timezone.utc).isoformat()))
        )
        cur.execute(merge_sql, params)
        ingested_count += 1

    conn.commit()

    # Query updated table count
    cur.execute("SELECT COUNT(*) FROM ZOMATO.RAW.KAFKA_ORDER_EVENTS")
    total_in_db = cur.fetchone()[0]

    cur.close()
    conn.close()

    print(f"[✓] Airflow Cronjob Sync Complete: Successfully merged {ingested_count} events into ZOMATO.RAW.KAFKA_ORDER_EVENTS. Total rows in Snowflake: {total_in_db}")

    return {
        "status": "SUCCESS",
        "rows_ingested": ingested_count,
        "total_in_snowflake": total_in_db,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

if __name__ == "__main__":
    result = sync_events_to_snowflake()
    print(json.dumps(result, indent=2))
