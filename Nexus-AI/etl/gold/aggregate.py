"""
Nexus-AI: Gold Layer — Dimension Tables, Fact Tables & Aggregated Marts
=========================================================================
Gold layer creates business-ready, queryable data:

1. DIMENSION TABLES: dim_restaurants, dim_cuisines, dim_delivery_partners
2. FACT TABLES:      fact_orders, fact_daily_delivery_performance
3. BUSINESS MARTS:   mart_city_revenue, mart_cuisine_trends, mart_hourly_demand

Design Decision: Star schema enables both SQL analytics (for Agent queries)
and fast dimensional joins for dashboards. Fact tables use surrogate keys
and pre-computed metrics to avoid runtime joins.
"""

import pandas as pd


def build_dim_restaurants(storage_adapter) -> pd.DataFrame:
    """Build dim_restaurants from Silver clean_restaurants."""
    df = storage_adapter.read_table("silver", "clean_restaurants")

    dim = df[[
        "restaurant_id", "name", "cuisine_type", "city", "area",
        "latitude", "longitude", "avg_cost_for_two", "rating",
        "total_reviews", "is_premium", "has_online_delivery",
        "has_table_booking", "is_active", "price_tier",
    ]].copy()

    storage_adapter.write_dataframe(dim, "gold", "dim_restaurants")
    return dim


def build_dim_cuisines(storage_adapter) -> pd.DataFrame:
    """Build dim_cuisines — unique cuisine types with aggregated stats."""
    restaurants = storage_adapter.read_table("silver", "clean_restaurants")

    dim = (
        restaurants.groupby("cuisine_type")
        .agg(
            restaurant_count=("restaurant_id", "count"),
            avg_rating=("rating", "mean"),
            avg_cost=("avg_cost_for_two", "mean"),
            premium_count=("is_premium", "sum"),
        )
        .reset_index()
    )
    dim["avg_rating"] = dim["avg_rating"].round(2)
    dim["avg_cost"] = dim["avg_cost"].round(0).astype(int)
    dim["cuisine_id"] = range(1, len(dim) + 1)

    storage_adapter.write_dataframe(dim, "gold", "dim_cuisines")
    return dim


def build_dim_delivery_partners(storage_adapter) -> pd.DataFrame:
    """Build dim_delivery_partners from Silver deliveries."""
    deliveries = storage_adapter.read_table("silver", "clean_deliveries")

    dim = (
        deliveries.groupby("partner_id")
        .agg(
            partner_tier=("partner_tier", "first"),
            total_deliveries=("delivery_id", "count"),
            avg_rating=("delivery_rating", "mean"),
            avg_speed_kmh=("delivery_speed_kmh", "mean"),
            late_delivery_count=("is_late", "sum"),
            avg_eta_error_min=("eta_error_min", "mean"),
        )
        .reset_index()
    )
    dim["avg_rating"] = dim["avg_rating"].round(2)
    dim["avg_speed_kmh"] = dim["avg_speed_kmh"].round(1)
    dim["avg_eta_error_min"] = dim["avg_eta_error_min"].round(1)
    dim["on_time_rate"] = ((dim["total_deliveries"] - dim["late_delivery_count"]) / dim["total_deliveries"] * 100).round(1)

    storage_adapter.write_dataframe(dim, "gold", "dim_delivery_partners")
    return dim


def build_fact_orders(storage_adapter) -> pd.DataFrame:
    """Build fact_orders — enriched order fact table with pre-joined dimensions."""
    orders = storage_adapter.read_table("silver", "clean_orders")
    restaurants = storage_adapter.read_table("silver", "clean_restaurants")

    fact = orders.merge(
        restaurants[["restaurant_id", "name", "cuisine_type", "city", "price_tier"]],
        on="restaurant_id",
        how="left",
        suffixes=("", "_restaurant"),
    )

    fact = fact.rename(columns={"name": "restaurant_name"})

    storage_adapter.write_dataframe(fact, "gold", "fact_orders")
    return fact


def build_fact_daily_delivery_performance(storage_adapter) -> pd.DataFrame:
    """
    Build fact_daily_delivery_performance — daily aggregated delivery metrics.

    Metrics:
    - total_deliveries, avg_eta_min, avg_distance_km
    - late_delivery_count, late_delivery_rate
    - avg_delivery_rating, avg_delivery_speed
    """
    deliveries = storage_adapter.read_table("silver", "clean_deliveries")

    deliveries["delivery_date"] = pd.to_datetime(deliveries["delivery_time"]).dt.date.astype(str)

    fact = (
        deliveries.groupby("delivery_date")
        .agg(
            total_deliveries=("delivery_id", "count"),
            avg_actual_eta_min=("actual_eta_min", "mean"),
            avg_estimated_eta_min=("estimated_eta_min", "mean"),
            avg_distance_km=("distance_km", "mean"),
            avg_delivery_rating=("delivery_rating", "mean"),
            avg_delivery_speed_kmh=("delivery_speed_kmh", "mean"),
            late_count=("is_late", "sum"),
            avg_eta_error_min=("eta_error_min", "mean"),
        )
        .reset_index()
    )

    # Round metrics
    for col in ["avg_actual_eta_min", "avg_estimated_eta_min", "avg_distance_km",
                "avg_delivery_rating", "avg_delivery_speed_kmh", "avg_eta_error_min"]:
        fact[col] = fact[col].round(2)

    fact["late_delivery_rate"] = (fact["late_count"] / fact["total_deliveries"] * 100).round(1)

    storage_adapter.write_dataframe(fact, "gold", "fact_daily_delivery_performance")
    return fact


def build_mart_city_revenue(storage_adapter) -> pd.DataFrame:
    """Build mart_city_revenue — revenue and order analytics by city."""
    try:
        fact_orders = storage_adapter.read_table("gold", "fact_orders")
    except FileNotFoundError:
        fact_orders = build_fact_orders(storage_adapter)

    mart = (
        fact_orders.groupby("city")
        .agg(
            total_orders=("order_id", "count"),
            total_revenue=("net_amount", "sum"),
            avg_order_value=("net_amount", "mean"),
            total_discount_given=("discount_amount", "sum"),
            delivered_orders=("order_status", lambda x: (x == "Delivered").sum()),
            cancelled_orders=("order_status", lambda x: (x == "Cancelled").sum()),
            unique_restaurants=("restaurant_id", "nunique"),
            unique_customers=("customer_id", "nunique"),
        )
        .reset_index()
    )

    mart["total_revenue"] = mart["total_revenue"].round(2)
    mart["avg_order_value"] = mart["avg_order_value"].round(2)
    mart["fulfillment_rate"] = (mart["delivered_orders"] / mart["total_orders"] * 100).round(1)

    storage_adapter.write_dataframe(mart, "gold", "mart_city_revenue")
    return mart


def build_mart_hourly_demand(storage_adapter) -> pd.DataFrame:
    """Build mart_hourly_demand — order volume patterns by hour and day."""
    try:
        fact_orders = storage_adapter.read_table("gold", "fact_orders")
    except FileNotFoundError:
        fact_orders = build_fact_orders(storage_adapter)

    mart = (
        fact_orders.groupby(["hour_of_day", "is_weekend"])
        .agg(
            order_count=("order_id", "count"),
            avg_order_value=("net_amount", "mean"),
            avg_items=("items_count", "mean"),
        )
        .reset_index()
    )
    mart["avg_order_value"] = mart["avg_order_value"].round(2)
    mart["avg_items"] = mart["avg_items"].round(1)

    storage_adapter.write_dataframe(mart, "gold", "mart_hourly_demand")
    return mart


# ── Gold Layer Orchestrator ──────────────────────────────────────────────

def run_gold_aggregations(storage_adapter) -> dict[str, dict]:
    """
    Build all Gold layer tables: Dimensions, Facts, and Business Marts.

    Returns:
        Dict mapping table_name -> {rows, columns, path}
    """
    results = {}

    print(f"\n{'='*60}")
    print(f"🥇 [GOLD LAYER] Dimensions, Facts & Business Marts")
    print(f"{'='*60}")

    builders = [
        ("dim_restaurants", build_dim_restaurants),
        ("dim_cuisines", build_dim_cuisines),
        ("dim_delivery_partners", build_dim_delivery_partners),
        ("fact_orders", build_fact_orders),
        ("fact_daily_delivery_performance", build_fact_daily_delivery_performance),
        ("mart_city_revenue", build_mart_city_revenue),
        ("mart_hourly_demand", build_mart_hourly_demand),
    ]

    for table_name, builder_fn in builders:
        try:
            df = builder_fn(storage_adapter)
            results[table_name] = {
                "status": "built",
                "rows": len(df),
                "columns": list(df.columns),
            }

            # Classify table type
            if table_name.startswith("dim_"):
                icon = "📐"
                label = "Dimension"
            elif table_name.startswith("fact_"):
                icon = "📊"
                label = "Fact"
            else:
                icon = "📈"
                label = "Mart"

            print(f"  {icon} {label}: {table_name:<38s} │ {len(df):>7,} rows │ {len(df.columns)} cols")

        except Exception as e:
            print(f"  ❌ Failed: {table_name}: {e}")
            results[table_name] = {"status": "failed", "error": str(e)}

    total = sum(r.get("rows", 0) for r in results.values())
    print(f"\n  📊 Gold Total: {total:,} rows across {len([r for r in results.values() if r.get('status') == 'built'])} tables")

    return results
