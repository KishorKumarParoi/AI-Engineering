"""
Unified Feature Pipeline for Zomato Delivery ETA Prediction.
Consistently transforms raw lakehouse or streaming payloads into model-ready feature matrices.
"""

from typing import Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from mlops.feature_store.spatial_features import calculate_haversine_distance_vectorized
from mlops.feature_store.temporal_features import extract_temporal_features


class FeaturePipeline:
    """
    Production-grade Feature Pipeline for Delivery ETA modeling.
    Guarantees deterministic feature schemas across:
      - Historical training runs (Snowflake / S3 Parquet)
      - Batch scoring jobs (Airflow / Cron)
      - Streaming inference (Azure Event Hubs / Kafka)
    """

    CUISINE_COMPLEXITY_MAP = {
        "Biryani": 1.45,
        "Mughlai": 1.40,
        "North Indian": 1.30,
        "Continental": 1.25,
        "Chinese": 1.15,
        "Italian": 1.20,
        "Pizzas": 1.10,
        "Burgers": 1.05,
        "Fast Food": 0.95,
        "Street Food": 0.85,
        "Desserts": 0.75,
        "Beverages": 0.65,
    }

    FEATURE_COLUMNS = [
        "delivery_distance_km",
        "prep_complexity_score",
        "order_amount",
        "delivery_fee",
        "item_count",
        "is_peak_rush",
        "is_weekend",
        "hour_sin",
        "hour_cos"
    ]

    def __init__(self):
        self.feature_names = self.FEATURE_COLUMNS

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transforms raw DataFrame into model-ready features.
        """
        data = df.copy()

        # 1. Spatial Feature (Haversine Distance)
        if "delivery_distance_km" not in data.columns or data["delivery_distance_km"].isnull().all():
            lat1 = data.get("restaurant_lat", pd.Series(dtype=float))
            lon1 = data.get("restaurant_lng", pd.Series(dtype=float))
            lat2 = data.get("delivery_lat", pd.Series(dtype=float))
            lon2 = data.get("delivery_lng", pd.Series(dtype=float))
            data["delivery_distance_km"] = calculate_haversine_distance_vectorized(lat1, lon1, lat2, lon2)
        else:
            data["delivery_distance_km"] = data["delivery_distance_km"].fillna(3.5)

        # 2. Cuisine Prep Complexity
        cuisine_series = data.get("cuisine", pd.Series(dtype=str)).fillna("Fast Food")
        data["prep_complexity_score"] = cuisine_series.map(self.CUISINE_COMPLEXITY_MAP).fillna(1.0).astype(np.float64)

        # 3. Numeric Fillers & Safe Casts
        data["delivery_distance_km"] = data["delivery_distance_km"].astype(np.float64)
        data["order_amount"] = pd.to_numeric(data.get("order_amount", 450.0), errors="coerce").fillna(450.0).astype(np.float64)
        data["delivery_fee"] = pd.to_numeric(data.get("delivery_fee", 40.0), errors="coerce").fillna(40.0).astype(np.float64)
        data["item_count"] = pd.to_numeric(data.get("item_count", 2), errors="coerce").fillna(2).astype(np.int64)

        # 4. Temporal Features
        time_col = None
        for candidate in ["event_timestamp", "order_timestamp", "kafka_arrival_time", "created_at"]:
            if candidate in data.columns:
                time_col = data[candidate]
                break
        
        if time_col is None:
            time_col = pd.Series(pd.Timestamp.now(), index=data.index)

        temp_df = extract_temporal_features(time_col)
        for col_name in temp_df.columns:
            data[col_name] = temp_df[col_name].astype(np.float64)

        return data[self.FEATURE_COLUMNS]

    def create_synthetic_ground_truth(self, features_df: pd.DataFrame) -> pd.Series:
        """
        Calculates ground truth actual delivery time (in minutes) with realistic physical latency:
          Base time (12 min kitchen overhead)
          + (Distance * 4.2 min/km)
          + (Prep Complexity * 8.0 min)
          + (Peak Rush * 6.5 min traffic delay)
          + (Item Count * 1.2 min)
          + Gaussian stochastic noise N(0, 1.5)
        """
        np.random.seed(42)
        base = 12.0
        dist_factor = features_df["delivery_distance_km"] * 4.2
        prep_factor = features_df["prep_complexity_score"] * 8.0
        rush_factor = features_df["is_peak_rush"] * 6.5
        item_factor = features_df["item_count"] * 1.2
        noise = np.random.normal(0, 1.5, size=len(features_df))

        eta = base + dist_factor + prep_factor + rush_factor + item_factor + noise
        return eta.clip(lower=10.0, upper=95.0).round(1)
