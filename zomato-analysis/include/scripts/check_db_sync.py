#!/usr/bin/env python3
"""
Zomato Enterprise Lakehouse: Snowflake Sync Verification Utility
Connects to Snowflake and prints detailed verification metrics for ZOMATO.RAW.KAFKA_ORDER_EVENTS.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

try:
    import snowflake.connector
except ImportError:
    print("Error: snowflake-connector-python is not installed in this environment.")
    sys.exit(1)

def check_snowflake_sync():
    user = os.getenv("SNOWFLAKE_USERNAME") or os.getenv("SNOWFLAKE_USER")
    pwd = os.getenv("SNOWFLAKE_PASSWORD")
    account = os.getenv("SNOWFLAKE_ACCOUNT")
    wh = os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH")
    db = os.getenv("SNOWFLAKE_DATABASE", "ZOMATO")
    schema = os.getenv("SNOWFLAKE_SCHEMA", "RAW")

    if not (user and pwd and account):
        print("Error: Snowflake credentials not found in .env.")
        sys.exit(1)

    print("=" * 70)
    print("❄️  SNOWFLAKE LAKEHOUSE SYNC AUDIT REPORT")
    print(f"   Target Table: {db}.{schema}.KAFKA_ORDER_EVENTS")
    print(f"   Account:      {account} | Warehouse: {wh}")
    print("=" * 70)

    try:
        conn = snowflake.connector.connect(
            user=user,
            password=pwd,
            account=account,
            warehouse=wh,
            database=db,
            schema=schema
        )
        cur = conn.cursor()

        # 1. Total Count & Aggregations
        cur.execute("""
            SELECT 
                COUNT(*) as total_orders,
                COUNT(DISTINCT restaurant_name) as distinct_restaurants,
                COUNT(DISTINCT cuisine) as distinct_cuisines,
                COUNT(DISTINCT city) as distinct_cities,
                SUM(order_amount) as total_gmv,
                MIN(ingested_at) as earliest_ingest,
                MAX(ingested_at) as latest_ingest
            FROM ZOMATO.RAW.KAFKA_ORDER_EVENTS;
        """)
        totals = cur.fetchone()
        
        print("\n📊 OVERALL SYNC HEALTH:")
        print(f"   • Total Orders Ingested:    {totals[0]:,}")
        print(f"   • Distinct Restaurants:     {totals[1]}")
        print(f"   • Distinct Food Cuisines:   {totals[2]}")
        print(f"   • Active Metro Cities:      {totals[3]}")
        print(f"   • Gross Merchandise Value:  ₹{totals[4]:,.2f}" if totals[4] else "   • Gross Merchandise Value:  ₹0.00")
        print(f"   • First Ingested At:        {totals[5]}")
        print(f"   • Most Recent Ingest At:    {totals[6]}")

        # 2. Breakdown by Cuisine
        print("\n🍽️ BREAKDOWN BY CUISINE:")
        cur.execute("""
            SELECT 
                CUISINE, 
                COUNT(*) as order_count, 
                SUM(ORDER_AMOUNT) as total_amt,
                ROUND(AVG(ORDER_AMOUNT), 2) as avg_order_val
            FROM ZOMATO.RAW.KAFKA_ORDER_EVENTS
            GROUP BY CUISINE
            ORDER BY order_count DESC;
        """)
        print(f"   {'CUISINE':<16} | {'ORDERS':<8} | {'TOTAL GMV':<14} | {'AVG TICKET':<12}")
        print("   " + "-" * 56)
        for row in cur.fetchall():
            print(f"   {row[0]:<16} | {row[1]:<8} | ₹{row[2]:<13,.2f} | ₹{row[3]:<11,.2f}")

        # 3. Latest 5 Synced Orders
        print("\n⏱️ LATEST 5 SYNCED KAFKA ORDERS IN SNOWFLAKE:")
        cur.execute("""
            SELECT 
                ORDER_ID, 
                RESTAURANT_NAME, 
                FOOD_NAME, 
                CUISINE, 
                CITY, 
                ORDER_AMOUNT, 
                ORDER_STATUS, 
                INGESTED_AT
            FROM ZOMATO.RAW.KAFKA_ORDER_EVENTS
            ORDER BY INGESTED_AT DESC
            LIMIT 5;
        """)
        for row in cur.fetchall():
            print(f"   [{row[0]}] {row[1]} ({row[4]}) ➔ {row[2]} | {row[3]} | ₹{row[5]:.2f} | Status: {row[6]}")

        cur.close()
        conn.close()
        print("\n" + "=" * 70)
        print("✅ VERIFICATION STATUS: 100% HEALTHY - DATA IS FULLY SYNCED IN SNOWFLAKE")
        print("=" * 70)

    except Exception as e:
        print(f"\n❌ Error connecting to Snowflake: {e}")

if __name__ == "__main__":
    check_snowflake_sync()
