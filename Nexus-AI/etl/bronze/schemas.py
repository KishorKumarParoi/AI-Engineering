"""
Nexus-AI: Bronze Layer Schema Definitions
===========================================
Expected column schemas for Bronze layer validation.
Bronze schemas are LENIENT — they only verify expected columns exist.
No type enforcement at Bronze level (that's Silver's job).
"""


# Expected columns for each raw dataset (excluding audit columns)
BRONZE_SCHEMAS: dict[str, list[str]] = {
    "restaurants": [
        "restaurant_id",
        "name",
        "cuisine_type",
        "city",
        "area",
        "latitude",
        "longitude",
        "avg_cost_for_two",
        "rating",
        "total_reviews",
        "is_premium",
        "has_online_delivery",
        "has_table_booking",
        "is_active",
    ],
    "orders": [
        "order_id",
        "restaurant_id",
        "customer_id",
        "order_time",
        "delivery_time",
        "total_amount",
        "discount_amount",
        "tax_amount",
        "net_amount",
        "payment_method",
        "order_status",
        "items_count",
        "is_first_order",
        "platform_fee",
        "delivery_fee",
    ],
    "deliveries": [
        "delivery_id",
        "order_id",
        "restaurant_id",
        "partner_id",
        "partner_tier",
        "vehicle_type",
        "distance_km",
        "estimated_eta_min",
        "actual_eta_min",
        "pickup_time",
        "delivery_time",
        "weather_condition",
        "traffic_level",
        "preparation_time_min",
        "delivery_rating",
        "is_late",
    ],
    "reviews": [
        "review_id",
        "order_id",
        "restaurant_id",
        "customer_id",
        "rating",
        "review_text",
        "review_date",
        "is_verified_purchase",
        "helpful_votes",
        "food_quality_sentiment",
        "delivery_speed_sentiment",
        "packaging_sentiment",
        "value_for_money_sentiment",
        "portion_size_sentiment",
    ],
}

# Audit columns added during Bronze ingestion
AUDIT_COLUMNS = ["_ingested_at", "_source_file", "_batch_id", "_raw_hash"]


def validate_bronze_schema(df, schema_name: str) -> dict:
    """
    Validate that a DataFrame has the expected Bronze columns.

    Args:
        df: DataFrame to validate
        schema_name: Key into BRONZE_SCHEMAS

    Returns:
        {"valid": bool, "issues": list[str], "missing": list[str], "extra": list[str]}
    """
    if schema_name not in BRONZE_SCHEMAS:
        return {"valid": True, "issues": [], "missing": [], "extra": []}

    expected = set(BRONZE_SCHEMAS[schema_name])
    actual = set(df.columns) - set(AUDIT_COLUMNS)

    missing = expected - actual
    extra = actual - expected

    issues = []
    if missing:
        issues.append(f"Missing columns: {sorted(missing)}")
    if extra:
        issues.append(f"Extra columns: {sorted(extra)}")

    return {
        "valid": len(missing) == 0,
        "issues": issues,
        "missing": sorted(missing),
        "extra": sorted(extra),
    }
