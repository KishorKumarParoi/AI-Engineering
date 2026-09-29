"""
Nexus-AI: Gold Layer — ML Feature Store Materialization
=========================================================
Builds feature tables optimized for ML model training.

Primary feature table: features_delivery_eta_v1
- Target variable: actual_eta_min (delivery time in minutes)
- 15+ engineered features from deliveries + orders + restaurants
- Ready for LightGBM/XGBoost training in the MLOps pipeline

Design Decision: Features are pre-computed and materialized in Gold
rather than computed at inference time. This ensures:
1. Training-serving skew prevention (same features in both)
2. Fast inference (no runtime joins)
3. Feature versioning (v1, v2 suffixes for A/B testing)
"""

import pandas as pd


def build_features_delivery_eta(storage_adapter) -> pd.DataFrame:
    """
    Build ML feature table for Delivery ETA prediction.

    Features:
    ─── Delivery Features ───
    - distance_km:           Haversine distance restaurant → customer
    - preparation_time_min:  Kitchen prep time
    - weather_code:          Ordinal encoded weather (0=Clear → 4=Storm)
    - traffic_code:          Ordinal encoded traffic (0=Low → 3=Jam)
    - delivery_speed_kmh:    Historical average speed for this delivery
    - partner_tier_code:     Partner performance tier (0=Bronze → 2=Gold)
    - vehicle_type_code:     Vehicle type (0=Bicycle → 3=Car)

    ─── Order Context Features ───
    - hour_of_day:           Order hour (0-23)
    - is_weekend:            Weekend flag
    - items_count:           Number of items ordered
    - order_value:           Total order amount (proxy for complexity)

    ─── Restaurant Features ───
    - restaurant_rating:     Historical restaurant rating
    - restaurant_cost_tier:  Price tier code (0=Budget → 3=Luxury)
    - cuisine_popularity:    Number of restaurants with same cuisine (proxy)

    ─── Target ───
    - actual_eta_min:        SUPERVISED TARGET — actual delivery time
    - estimated_eta_min:     System estimate (useful for residual modeling)
    - is_late:               Binary classification target
    """
    # Load Silver tables
    deliveries = storage_adapter.read_table("silver", "clean_deliveries")
    orders = storage_adapter.read_table("silver", "clean_orders")
    restaurants = storage_adapter.read_table("silver", "clean_restaurants")

    # ── Join deliveries with order context ────────────────────────────
    features = deliveries.merge(
        orders[["order_id", "restaurant_id", "customer_id", "hour_of_day",
                "is_weekend", "items_count", "net_amount"]],
        on=["order_id"],
        how="left",
        suffixes=("", "_order"),
    )

    # Use delivery's restaurant_id (drop the duplicate from orders merge)
    if "restaurant_id_order" in features.columns:
        features = features.drop(columns=["restaurant_id_order"])

    # ── Join with restaurant features ────────────────────────────────
    # Compute cuisine popularity
    cuisine_counts = restaurants.groupby("cuisine_type").size().reset_index(name="cuisine_restaurant_count")
    restaurants_enriched = restaurants.merge(cuisine_counts, on="cuisine_type", how="left")

    features = features.merge(
        restaurants_enriched[["restaurant_id", "rating", "avg_cost_for_two",
                              "price_tier", "cuisine_restaurant_count"]],
        on="restaurant_id",
        how="left",
    )

    # ── Encode categorical features ──────────────────────────────────
    tier_map = {"Bronze": 0, "Silver": 1, "Gold": 2}
    vehicle_map = {"Bicycle": 0, "Scooter": 1, "Bike": 2, "Car": 3}
    price_tier_map = {"Budget": 0, "Mid-Range": 1, "Premium": 2, "Luxury": 3}

    features["partner_tier_code"] = features["partner_tier"].map(tier_map).fillna(0).astype(int)
    features["vehicle_type_code"] = features["vehicle_type"].map(vehicle_map).fillna(1).astype(int)
    features["price_tier_code"] = features["price_tier"].map(price_tier_map).fillna(1).astype(int)

    # ── Select final feature columns ─────────────────────────────────
    feature_cols = [
        # IDs (for joining, not for training)
        "delivery_id",
        "order_id",
        "restaurant_id",
        "partner_id",

        # Delivery features
        "distance_km",
        "preparation_time_min",
        "weather_code",
        "traffic_code",
        "partner_tier_code",
        "vehicle_type_code",

        # Order context
        "hour_of_day",
        "is_weekend",
        "items_count",
        "net_amount",

        # Restaurant features
        "rating",
        "avg_cost_for_two",
        "price_tier_code",
        "cuisine_restaurant_count",

        # Targets
        "estimated_eta_min",
        "actual_eta_min",
        "is_late",
        "eta_error_min",
        "delivery_speed_kmh",
        "delivery_rating",
    ]

    # Keep only available columns (graceful handling)
    available = [c for c in feature_cols if c in features.columns]
    feature_table = features[available].copy()

    # Rename for ML clarity
    feature_table = feature_table.rename(columns={
        "rating": "restaurant_rating",
        "net_amount": "order_value",
    })

    # Drop rows with null targets
    feature_table = feature_table.dropna(subset=["actual_eta_min"])

    # ── Write to Gold ────────────────────────────────────────────────
    storage_adapter.write_dataframe(feature_table, "gold", "features_delivery_eta_v1")

    # ── Feature statistics summary ───────────────────────────────────
    numeric_cols = feature_table.select_dtypes(include="number").columns
    stats = feature_table[numeric_cols].describe().round(2)

    print(f"\n  🧬 Feature Store: features_delivery_eta_v1")
    print(f"     Samples: {len(feature_table):,}")
    print(f"     Features: {len(available) - 4} (excluding IDs)")
    print(f"     Target mean: {feature_table['actual_eta_min'].mean():.1f} min")
    print(f"     Target std:  {feature_table['actual_eta_min'].std():.1f} min")
    print(f"     Late rate:   {feature_table['is_late'].mean()*100:.1f}%")

    return feature_table
