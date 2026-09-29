"""
Nexus-AI: Silver Layer — Data Cleaning, Type Casting & Enrichment
===================================================================
Silver layer responsibilities:
1. TYPE CASTING:    Convert strings to proper types (float, int, bool, datetime)
2. NULL HANDLING:   Impute or flag missing values
3. STRING CLEANING: Strip whitespace, normalize casing
4. DEDUPLICATION:   Remove duplicate rows using _raw_hash
5. ENRICHMENT:      Derived columns (hour_of_day, geohash, delivery_speed)
6. VALIDATION:      Data quality assertions before promoting to Silver

Design Decision: Silver is the "single source of truth" — the first layer
where data is queryable with correct types. All downstream consumers
(Gold aggregates, ML models, Agent queries) read from Silver.
"""

from datetime import datetime

import pandas as pd


def transform_restaurants(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and type-cast restaurant data.

    Transformations:
    - Strip and title-case restaurant names
    - Cast numeric columns (lat, lng, cost, rating)
    - Cast boolean columns
    - Deduplicate by _raw_hash
    - Add price_tier derived column
    """
    out = df.copy()

    # Dedup by raw hash
    out = out.drop_duplicates(subset=["_raw_hash"], keep="first")

    # String cleaning
    out["name"] = out["name"].str.strip().str.title()
    out["city"] = out["city"].str.strip().str.title()
    out["area"] = out["area"].str.strip()
    out["cuisine_type"] = out["cuisine_type"].str.strip()

    # Type casting
    out["latitude"] = pd.to_numeric(out["latitude"], errors="coerce")
    out["longitude"] = pd.to_numeric(out["longitude"], errors="coerce")
    out["avg_cost_for_two"] = pd.to_numeric(out["avg_cost_for_two"], errors="coerce").fillna(0).astype(int)
    out["rating"] = pd.to_numeric(out["rating"], errors="coerce").clip(1.0, 5.0)
    out["total_reviews"] = pd.to_numeric(out["total_reviews"], errors="coerce").fillna(0).astype(int)

    # Boolean casting
    for col in ["is_premium", "has_online_delivery", "has_table_booking", "is_active"]:
        out[col] = out[col].astype(str).str.lower().map({"true": True, "false": False, "1": True, "0": False}).fillna(False)

    # Derived: price tier
    out["price_tier"] = pd.cut(
        out["avg_cost_for_two"],
        bins=[0, 200, 500, 1000, float("inf")],
        labels=["Budget", "Mid-Range", "Premium", "Luxury"],
        right=True,
    ).astype(str)

    # Drop audit columns (Silver has its own lineage)
    audit_cols = [c for c in out.columns if c.startswith("_")]
    out = out.drop(columns=audit_cols, errors="ignore")

    return out


def transform_orders(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and type-cast order data.

    Transformations:
    - Parse order_time and delivery_time to datetime
    - Cast monetary columns to float
    - Extract hour_of_day, day_of_week, is_weekend
    - Validate order_status values
    - Deduplicate by _raw_hash
    """
    out = df.copy()
    out = out.drop_duplicates(subset=["_raw_hash"], keep="first")

    # Datetime parsing
    out["order_time"] = pd.to_datetime(out["order_time"], errors="coerce")
    out["delivery_time"] = pd.to_datetime(out["delivery_time"], errors="coerce")

    # Monetary columns
    for col in ["total_amount", "discount_amount", "tax_amount", "net_amount", "platform_fee", "delivery_fee"]:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).round(2)

    # Integer columns
    out["items_count"] = pd.to_numeric(out["items_count"], errors="coerce").fillna(1).astype(int)

    # Boolean
    out["is_first_order"] = out["is_first_order"].astype(str).str.lower().map({"true": True, "false": False}).fillna(False)

    # Validate order_status
    valid_statuses = {"Delivered", "Cancelled", "Returned", "In Transit", "Preparing"}
    out["order_status"] = out["order_status"].where(out["order_status"].isin(valid_statuses), "Unknown")

    # Derived time features
    out["hour_of_day"] = out["order_time"].dt.hour
    out["day_of_week"] = out["order_time"].dt.day_name()
    out["is_weekend"] = out["order_time"].dt.dayofweek.isin([5, 6])
    out["order_month"] = out["order_time"].dt.to_period("M").astype(str)

    # Delivery duration (minutes)
    out["delivery_duration_min"] = (
        (out["delivery_time"] - out["order_time"]).dt.total_seconds() / 60
    ).round(1)

    # Drop audit columns
    audit_cols = [c for c in out.columns if c.startswith("_")]
    out = out.drop(columns=audit_cols, errors="ignore")

    return out


def transform_deliveries(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and type-cast delivery data — the core ML training dataset.

    Transformations:
    - Cast distance, ETA, timing columns to float
    - Compute delivery_speed_kmh derived feature
    - Compute eta_error (actual - estimated) for drift monitoring
    - Encode weather/traffic as ordinal features
    - Validate ranges (distance > 0, ETA > 0)
    """
    out = df.copy()
    out = out.drop_duplicates(subset=["_raw_hash"], keep="first")

    # Numeric casting
    for col in ["distance_km", "estimated_eta_min", "actual_eta_min", "preparation_time_min", "delivery_rating"]:
        out[col] = pd.to_numeric(out[col], errors="coerce")

    # Boolean
    out["is_late"] = out["is_late"].astype(str).str.lower().map({"true": True, "false": False}).fillna(False)

    # Datetime parsing
    out["pickup_time"] = pd.to_datetime(out["pickup_time"], errors="coerce")
    out["delivery_time"] = pd.to_datetime(out["delivery_time"], errors="coerce")

    # Filter invalid rows (distance must be positive, ETA must be positive)
    out = out[(out["distance_km"] > 0) & (out["actual_eta_min"] > 0)]

    # Derived: delivery speed (km/h)
    travel_time_hours = (out["actual_eta_min"] - out["preparation_time_min"]).clip(lower=1) / 60
    out["delivery_speed_kmh"] = (out["distance_km"] / travel_time_hours).round(2)

    # Derived: ETA error (positive = slower than estimated)
    out["eta_error_min"] = (out["actual_eta_min"] - out["estimated_eta_min"]).round(1)

    # Ordinal encoding for categorical features
    weather_map = {
        "Clear": 0, "Cloudy": 1, "Rain": 2, "Heavy Rain": 3, "Storm": 4, "Fog": 5,
    }
    traffic_map = {"Low": 0, "Medium": 1, "High": 2, "Jam": 3}

    out["weather_code"] = out["weather_condition"].map(weather_map).fillna(0).astype(int)
    out["traffic_code"] = out["traffic_level"].map(traffic_map).fillna(1).astype(int)

    # Drop audit columns
    audit_cols = [c for c in out.columns if c.startswith("_")]
    out = out.drop(columns=audit_cols, errors="ignore")

    return out


def transform_reviews(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and type-cast review data.

    Transformations:
    - Cast rating to float, clip to [1.0, 5.0]
    - Clean review text (strip, handle empty)
    - Cast helpful_votes to int
    - Validate sentiment values
    """
    out = df.copy()
    out = out.drop_duplicates(subset=["_raw_hash"], keep="first")

    # Numeric
    out["rating"] = pd.to_numeric(out["rating"], errors="coerce").clip(1.0, 5.0)
    out["helpful_votes"] = pd.to_numeric(out["helpful_votes"], errors="coerce").fillna(0).astype(int)

    # Boolean
    out["is_verified_purchase"] = out["is_verified_purchase"].astype(str).str.lower().map(
        {"true": True, "false": False}
    ).fillna(False)

    # Text cleaning
    out["review_text"] = out["review_text"].fillna("").str.strip()

    # Datetime
    out["review_date"] = pd.to_datetime(out["review_date"], errors="coerce")

    # Validate sentiment columns
    valid_sentiments = {"positive", "neutral", "negative"}
    for col in ["food_quality_sentiment", "delivery_speed_sentiment", "packaging_sentiment",
                "value_for_money_sentiment", "portion_size_sentiment"]:
        out[col] = out[col].str.lower().where(out[col].str.lower().isin(valid_sentiments), "neutral")

    # Derived: sentiment score (positive=1, neutral=0, negative=-1)
    sentiment_score_map = {"positive": 1, "neutral": 0, "negative": -1}
    out["overall_sentiment_score"] = out["food_quality_sentiment"].map(sentiment_score_map).fillna(0).astype(int)

    # Drop audit columns
    audit_cols = [c for c in out.columns if c.startswith("_")]
    out = out.drop(columns=audit_cols, errors="ignore")

    return out


# ── Unified Transform Dispatcher ─────────────────────────────────────────

TRANSFORM_FUNCTIONS = {
    "raw_restaurants": ("clean_restaurants", transform_restaurants),
    "raw_orders": ("clean_orders", transform_orders),
    "raw_deliveries": ("clean_deliveries", transform_deliveries),
    "raw_reviews": ("clean_reviews", transform_reviews),
}


def run_silver_transforms(storage_adapter) -> dict[str, dict]:
    """
    Run all Silver layer transformations.

    Reads each Bronze table, applies cleaning/type-casting/enrichment,
    writes to Silver layer via the storage adapter.

    Returns:
        Dict mapping silver_table_name -> {rows, columns, path, dropped_rows}
    """
    results = {}

    print(f"\n{'='*60}")
    print(f"🥈 [SILVER LAYER] Cleaning, Validation & Enrichment")
    print(f"{'='*60}")

    for bronze_name, (silver_name, transform_fn) in TRANSFORM_FUNCTIONS.items():
        try:
            # Read from Bronze
            bronze_df = storage_adapter.read_table("bronze", bronze_name)
            bronze_rows = len(bronze_df)

            # Apply transformation
            silver_df = transform_fn(bronze_df)
            silver_rows = len(silver_df)
            dropped = bronze_rows - silver_rows

            # Write to Silver
            path = storage_adapter.write_dataframe(silver_df, "silver", silver_name)

            results[silver_name] = {
                "status": "transformed",
                "bronze_rows": bronze_rows,
                "silver_rows": silver_rows,
                "dropped_rows": dropped,
                "columns": list(silver_df.columns),
                "path": path,
            }

            drop_info = f" (dropped {dropped})" if dropped > 0 else ""
            print(f"  ✅ {bronze_name:<20s} → {silver_name:<22s} │ {silver_rows:>7,} rows{drop_info}")

        except FileNotFoundError:
            print(f"  ⚠️  Skipping {bronze_name} (not found in Bronze)")
            results[silver_name] = {"status": "skipped", "reason": "bronze_not_found"}

    total_silver = sum(r.get("silver_rows", 0) for r in results.values())
    print(f"\n  📊 Silver Total: {total_silver:,} rows across {len([r for r in results.values() if r.get('status') == 'transformed'])} tables")

    return results
