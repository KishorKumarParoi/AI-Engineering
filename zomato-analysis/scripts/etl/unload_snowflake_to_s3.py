#!/usr/bin/env python3
"""
Zomato Enterprise Lakehouse: Snowflake to AWS S3 Data Unload Utility
Exports verified Kafka order events from ZOMATO.RAW.KAFKA_ORDER_EVENTS 
directly into s3://zomato-dataset-kkp/export/kafka_events/ as Parquet.

Scheduled via Airflow cronjob every 4 hours (`0 */4 * * *`).
"""

import os
import sys
import json
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

try:
    import snowflake.connector
    HAS_SNOWFLAKE = True
except ImportError:
    HAS_SNOWFLAKE = False

def export_snowflake_to_s3(s3_path="s3://zomato-dataset-kkp/export/kafka_events/"):
    if not HAS_SNOWFLAKE:
        print("Error: snowflake-connector-python is not installed.")
        sys.exit(1)

    user = os.getenv("SNOWFLAKE_USERNAME") or os.getenv("SNOWFLAKE_USER")
    pwd = os.getenv("SNOWFLAKE_PASSWORD")
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    wh = os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH")
    db = os.getenv("SNOWFLAKE_DATABASE", "ZOMATO")
    schema = os.getenv("SNOWFLAKE_SCHEMA", "RAW")

    if not (user and pwd and account):
        print("Error: Snowflake credentials missing in environment.")
        sys.exit(1)

    print("=" * 70)
    print("🚀 SNOWFLAKE -> AWS S3 PARQUET EXPORT (AIRFLOW 4-HOUR CRONJOB)")
    print(f"   Source Table:    {db}.{schema}.KAFKA_ORDER_EVENTS")
    print(f"   Target S3 URI:   {s3_path}")
    print(f"   Format:          PARQUET (SNAPPY COMPRESSION)")
    print("=" * 70)

    conn = snowflake.connector.connect(
        user=user,
        password=pwd,
        account=account,
        warehouse=wh,
        database=db,
        schema=schema
    )
    cur = conn.cursor()

    unload_sql = f"""
    COPY INTO '{s3_path}'
    FROM (
        SELECT 
            ORDER_ID,
            CUSTOMER_ID,
            RESTAURANT_ID,
            RESTAURANT_NAME,
            FOOD_ID,
            FOOD_NAME,
            CUISINE,
            CITY,
            ORDER_STATUS,
            ORDER_AMOUNT,
            DELIVERY_FEE,
            ITEM_COUNT,
            PAYMENT_METHOD,
            DISTANCE_KM,
            PREDICTED_ETA_MINS,
            RESTAURANT_LAT,
            RESTAURANT_LNG,
            DELIVERY_LAT,
            DELIVERY_LNG,
            EVENT_TIMESTAMP::TIMESTAMP_NTZ AS EVENT_TIMESTAMP,
            INGESTED_AT::TIMESTAMP_NTZ AS INGESTED_AT
        FROM {db}.{schema}.KAFKA_ORDER_EVENTS
    )
    STORAGE_INTEGRATION = ZOMATO_S3_INT
    FILE_FORMAT = (TYPE = 'PARQUET' COMPRESSION = 'SNAPPY')
    HEADER = TRUE
    OVERWRITE = TRUE;
    """

    try:
        cur.execute(unload_sql)
        results = cur.fetchall()
        total_rows = sum(r[0] for r in results)
        total_bytes = sum(r[2] for r in results if len(r) > 2 and isinstance(r[2], (int, float)))
        file_count = len(results)

        print(f"\n[✓] Export Successful!")
        print(f"    • Total Rows Unloaded: {total_rows:,}")
        print(f"    • Total Parquet Files: {file_count}")
        print(f"    • Target Location:     {s3_path}")
        print(f"    • Timestamp:           {datetime.now(timezone.utc).isoformat()}")

        cur.close()
        conn.close()

        result_payload = {
            "status": "SUCCESS",
            "rows_unloaded": total_rows,
            "files_written": file_count,
            "s3_destination": s3_path,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        return result_payload

    except Exception as e:
        print(f"\n[!] Error unloading to AWS S3: {e}")
        cur.close()
        conn.close()
        sys.exit(1)

if __name__ == "__main__":
    res = export_snowflake_to_s3()
    print(json.dumps(res, indent=2))
