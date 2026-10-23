"""
Feast Feature Store Definitions for Zomato AI Engineering.
Defines entities, feature views, and data sources for ETA prediction and fraud scoring.
"""

from datetime import timedelta
from feast import (
    Entity,
    FeatureView,
    Field,
    FileSource,
    ValueType,
)
from feast.types import Float32, Int64, String, Bool

# 1. Entities
restaurant_entity = Entity(
    name="restaurant_id",
    value_type=ValueType.STRING,
    description="Unique identifier for restaurant partner"
)

customer_entity = Entity(
    name="customer_id",
    value_type=ValueType.STRING,
    description="Unique identifier for customer"
)

delivery_partner_entity = Entity(
    name="partner_id",
    value_type=ValueType.STRING,
    description="Unique delivery partner identifier"
)

# 2. Offline Data Sources (Delta Lake / Parquet Gold Tables)
restaurant_source = FileSource(
    path="data/gold/restaurant_features.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp"
)

customer_source = FileSource(
    path="data/gold/customer_features.parquet",
    timestamp_field="event_timestamp",
    created_timestamp_column="created_timestamp"
)

# 3. Feature Views
restaurant_feature_view = FeatureView(
    name="restaurant_hourly_stats",
    entities=[restaurant_entity],
    ttl=timedelta(days=7),
    schema=[
        Field(name="avg_prep_time_minutes", dtype=Float32),
        Field(name="cancellation_rate_7d", dtype=Float32),
        Field(name="order_volume_trailing_1h", dtype=Int64),
        Field(name="cuisine_complexity_factor", dtype=Float32),
        Field(name="is_kitchen_overloaded", dtype=Bool),
    ],
    online=True,
    source=restaurant_source,
    tags={"team": "dispatch_eta", "tier": "gold"}
)

customer_feature_view = FeatureView(
    name="customer_risk_profile",
    entities=[customer_entity],
    ttl=timedelta(days=30),
    schema=[
        Field(name="lifetime_order_count", dtype=Int64),
        Field(name="dispute_refund_rate_90d", dtype=Float32),
        Field(name="avg_order_value_inr", dtype=Float32),
        Field(name="is_gold_member", dtype=Bool),
    ],
    online=True,
    source=customer_source,
    tags={"team": "fraud_prevention", "tier": "gold"}
)
