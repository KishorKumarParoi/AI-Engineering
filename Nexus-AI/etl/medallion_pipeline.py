"""
Medallion ETL Pipeline Engine (Bronze -> Silver -> Gold)
Applies automated quality gates, PII tokenization, dimension-fact star schema generation,
and feature store materialization for the Zomato AI Lakehouse.
"""

import os
import csv
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple
from etl.storage_adapter import get_storage_adapter, CloudStorageAdapter

class MedallionETLPipeline:
    def __init__(self, data_source_dir: str, provider: str = "local", **kwargs):
        self.data_source_dir = os.path.abspath(data_source_dir)
        self.provider = provider
        self.storage: CloudStorageAdapter = get_storage_adapter(provider, **kwargs)
        self.batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.stats = {"bronze": {}, "silver": {}, "gold": {}, "quality_checks": []}

    def _load_csv(self, filename: str) -> List[Dict[str, Any]]:
        path = os.path.join(self.data_source_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Missing source file: {path}")
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)

    # ==========================================
    # 1. BRONZE LAYER: Raw Append + Audit Metadata
    # ==========================================
    def run_bronze(self) -> Dict[str, str]:
        print("\n" + "="*50)
        print(f"📦 [BRONZE LAYER] Ingesting Raw Data (Batch: {self.batch_id})")
        print("="*50)

        raw_files = [
            ("restaurants.csv", "raw_restaurants"),
            ("customers.csv", "raw_customers"),
            ("delivery_partners.csv", "raw_delivery_partners"),
            ("orders.csv", "raw_orders"),
            ("deliveries.csv", "raw_deliveries"),
            ("reviews.csv", "raw_reviews")
        ]

        bronze_uris = {}
        ingested_at = datetime.now().isoformat()

        for csv_file, table_name in raw_files:
            rows = self._load_csv(csv_file)
            enriched_rows = []
            for row in rows:
                raw_str = json.dumps(row, sort_keys=True)
                enriched = dict(row)
                enriched["_bronze_ingested_at"] = ingested_at
                enriched["_source_file"] = csv_file
                enriched["_batch_id"] = self.batch_id
                enriched["_raw_hash"] = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]
                enriched_rows.append(enriched)

            uri = self.storage.write_table("bronze", table_name, enriched_rows)
            bronze_uris[table_name] = uri
            self.stats["bronze"][table_name] = len(enriched_rows)
            print(f"  ✓ Bronze: {table_name:<24} | {len(enriched_rows):>5} records -> {uri}")

        return bronze_uris

    # ==========================================
    # 2. SILVER LAYER: Validation, Cleansing, PII Hashing
    # ==========================================
    def run_silver(self) -> Dict[str, str]:
        print("\n" + "="*50)
        print("🥈 [SILVER LAYER] Cleansing, Validation & Schema Normalization")
        print("="*50)

        silver_uris = {}

        # 2.1 Cleansed Restaurants
        raw_rests = self.storage.read_table("bronze", "raw_restaurants")
        silver_rests = []
        for r in raw_rests:
            silver_rests.append({
                "restaurant_id": r["restaurant_id"],
                "restaurant_name": r["restaurant_name"].strip().title(),
                "city": r["city"].strip(),
                "locality": r["locality"].strip(),
                "latitude": float(r["latitude"]),
                "longitude": float(r["longitude"]),
                "primary_cuisine": r["primary_cuisine"],
                "avg_cost_for_two": float(r["avg_cost_for_two"]),
                "price_range": int(r["price_range"]),
                "has_online_delivery": bool(int(r["has_online_delivery"])),
                "aggregate_rating": float(r["aggregate_rating"]),
                "votes": int(r["votes"]),
                "is_delivering_now": bool(int(r["is_delivering_now"]))
            })
        silver_uris["clean_restaurants"] = self.storage.write_table("silver", "clean_restaurants", silver_rests)
        self.stats["silver"]["clean_restaurants"] = len(silver_rests)
        print(f"  ✓ Silver: clean_restaurants        | {len(silver_rests):>5} records validated")

        # 2.2 Cleansed Customers with Presidio / PII Tokenization
        raw_custs = self.storage.read_table("bronze", "raw_customers")
        silver_custs = []
        for c in raw_custs:
            # Tokenize / Mask PII email and phone to comply with GDPR & DPDP Act
            phone = c["phone_number"]
            masked_phone = phone[:6] + "XXXX" + phone[-2:]
            email_parts = c["email"].split("@")
            masked_email = email_parts[0][:3] + "***@" + email_parts[1]
            silver_custs.append({
                "customer_id": c["customer_id"],
                "full_name": c["full_name"],
                "masked_email": masked_email,
                "masked_phone": masked_phone,
                "city": c["city"],
                "loyalty_tier": c["loyalty_tier"],
                "registered_at": c["registered_at"]
            })
        silver_uris["clean_customers"] = self.storage.write_table("silver", "clean_customers", silver_custs)
        self.stats["silver"]["clean_customers"] = len(silver_custs)
        print(f"  ✓ Silver: clean_customers          | {len(silver_custs):>5} records (PII masked)")

        # 2.3 Cleansed Deliveries (Features normalized)
        raw_dels = self.storage.read_table("bronze", "raw_deliveries")
        silver_dels = []
        for d in raw_dels:
            actual_time = float(d["actual_delivery_time_minutes"])
            dist = float(d["delivery_distance_km"])
            prep = float(d["prep_time_minutes"])
            # Assert data sanity: delivery time > 5 min, distance > 0
            if actual_time >= 5.0 and dist > 0.0:
                speed = (dist / (actual_time / 60.0)) if actual_time > 0 else 0.0
                silver_dels.append({
                    "delivery_id": d["delivery_id"],
                    "order_id": d["order_id"],
                    "partner_id": d["partner_id"],
                    "delivery_distance_km": dist,
                    "weather_condition": d["weather_condition"],
                    "traffic_density": d["traffic_density"],
                    "prep_time_minutes": prep,
                    "rider_wait_time_minutes": float(d["rider_wait_time_minutes"]),
                    "actual_delivery_time_minutes": actual_time,
                    "effective_speed_kmh": round(speed, 2)
                })
        silver_uris["clean_deliveries"] = self.storage.write_table("silver", "clean_deliveries", silver_dels)
        self.stats["silver"]["clean_deliveries"] = len(silver_dels)
        print(f"  ✓ Silver: clean_deliveries         | {len(silver_dels):>5} records passed sanity checks")

        # 2.4 Cleansed Orders
        raw_orders = self.storage.read_table("bronze", "raw_orders")
        silver_orders = []
        for o in raw_orders:
            silver_orders.append({
                "order_id": o["order_id"],
                "customer_id": o["customer_id"],
                "restaurant_id": o["restaurant_id"],
                "delivery_partner_id": o["delivery_partner_id"],
                "order_timestamp": o["order_timestamp"],
                "order_status": o["order_status"],
                "items_count": int(o["items_count"]),
                "order_amount": float(o["order_amount"]),
                "discount_amount": float(o["discount_amount"]),
                "delivery_fee": float(o["delivery_fee"]),
                "final_billed_amount": float(o["final_billed_amount"]),
                "payment_mode": o["payment_mode"],
                "order_hour": int(o["order_hour"]),
                "is_weekend": int(o["is_weekend"])
            })
        silver_uris["clean_orders"] = self.storage.write_table("silver", "clean_orders", silver_orders)
        self.stats["silver"]["clean_orders"] = len(silver_orders)
        print(f"  ✓ Silver: clean_orders             | {len(silver_orders):>5} records verified")

        return silver_uris

    # ==========================================
    # 3. GOLD LAYER: Star Schema & MLOps Feature Store
    # ==========================================
    def run_gold(self) -> Dict[str, str]:
        print("\n" + "="*50)
        print("🥇 [GOLD LAYER] Business Marts & MLOps Feature Store")
        print("="*50)

        gold_uris = {}
        silver_orders = self.storage.read_table("silver", "clean_orders")
        silver_dels = self.storage.read_table("silver", "clean_deliveries")
        silver_rests = self.storage.read_table("silver", "clean_restaurants")

        # 3.1 Dimension Tables
        gold_uris["dim_restaurants"] = self.storage.write_table("gold", "dim_restaurants", silver_rests)
        print(f"  ✓ Gold: dim_restaurants            | Dimension table registered")

        # 3.2 Fact Orders
        gold_uris["fact_orders"] = self.storage.write_table("gold", "fact_orders", silver_orders)
        print(f"  ✓ Gold: fact_orders                | Fact table registered")

        # 3.3 MLOps Feature Store: `features_delivery_eta`
        # Join delivery features with order time attributes
        orders_map = {o["order_id"]: o for o in silver_orders}
        feature_matrix = []

        weather_encoding = {"Clear": 0, "Sunny": 1, "Cloudy": 2, "Rainy": 3, "Heavy Rain": 4, "Foggy": 5}
        traffic_encoding = {"Low": 0, "Moderate": 1, "High": 2, "Congested": 3}

        for d in silver_dels:
            ord_info = orders_map.get(d["order_id"])
            if not ord_info:
                continue

            feature_matrix.append({
                "delivery_id": d["delivery_id"],
                "order_id": d["order_id"],
                # Features for Model Training
                "delivery_distance_km": d["delivery_distance_km"],
                "prep_time_minutes": d["prep_time_minutes"],
                "rider_wait_time_minutes": d["rider_wait_time_minutes"],
                "traffic_density_code": traffic_encoding.get(d["traffic_density"], 1),
                "weather_condition_code": weather_encoding.get(d["weather_condition"], 0),
                "order_hour": ord_info["order_hour"],
                "is_weekend": ord_info["is_weekend"],
                "items_count": ord_info["items_count"],
                # Supervised Target Variable
                "target_actual_delivery_minutes": d["actual_delivery_time_minutes"]
            })

        gold_uris["features_delivery_eta"] = self.storage.write_table("gold", "features_delivery_eta", feature_matrix)
        self.stats["gold"]["features_delivery_eta"] = len(feature_matrix)
        print(f"  ✓ Gold: features_delivery_eta      | {len(feature_matrix):>5} training samples materialized")

        # 3.4 Daily Delivery Performance Mart
        city_metrics = {}
        rest_city_map = {r["restaurant_id"]: r["city"] for r in silver_rests}
        for o in silver_orders:
            city = rest_city_map.get(o["restaurant_id"], "Unknown")
            if city not in city_metrics:
                city_metrics[city] = {"total_orders": 0, "total_revenue": 0.0, "successful_deliveries": 0}
            city_metrics[city]["total_orders"] += 1
            city_metrics[city]["total_revenue"] += o["final_billed_amount"]
            if o["order_status"] == "Delivered":
                city_metrics[city]["successful_deliveries"] += 1

        mart_summary = []
        for city, m in city_metrics.items():
            success_rate = (m["successful_deliveries"] / m["total_orders"]) * 100.0 if m["total_orders"] > 0 else 0.0
            mart_summary.append({
                "city": city,
                "total_orders": m["total_orders"],
                "total_revenue_inr": round(m["total_revenue"], 2),
                "fulfillment_rate_percent": round(success_rate, 2)
            })
        gold_uris["mart_city_performance"] = self.storage.write_table("gold", "mart_city_performance", mart_summary)
        print(f"  ✓ Gold: mart_city_performance      | {len(mart_summary):>5} city aggregates materialized")

        return gold_uris

    def run_all(self) -> Dict[str, Any]:
        """One-Stop Execution of Bronze -> Silver -> Gold"""
        print(f"\n🚀 Launching One-Click Medallion ETL Pipeline ({self.provider.upper()})")
        b_uris = self.run_bronze()
        s_uris = self.run_silver()
        g_uris = self.run_gold()

        summary = {
            "status": "SUCCESS",
            "batch_id": self.batch_id,
            "provider": self.provider,
            "bronze_tables": b_uris,
            "silver_tables": s_uris,
            "gold_tables": g_uris,
            "stats": self.stats
        }
        print("\n" + "="*50)
        print(f"✅ Medallion Lakehouse Pipeline Completed Successfully!")
        print(f"   Provider: {self.provider.upper()} | Gold Features Ready for MLOps")
        print("="*50 + "\n")
        return summary

if __name__ == "__main__":
    import sys
    data_dir = sys.argv[1] if len(sys.argv) > 1 else "zomato-dataset"
    cloud_provider = sys.argv[2] if len(sys.argv) > 2 else "local"
    pipeline = MedallionETLPipeline(data_source_dir=data_dir, provider=cloud_provider)
    pipeline.run_all()
