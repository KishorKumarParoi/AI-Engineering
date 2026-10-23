"""Unit tests for ML inference pipelines and feature generation."""

import pandas as pd
from mlops.feature_store.feature_pipeline import FeaturePipeline


def test_feature_pipeline_transformation():
    pipeline = FeaturePipeline()
    sample_data = pd.DataFrame([{
        "restaurant_lat": 12.9352,
        "restaurant_lng": 77.6245,
        "customer_lat": 12.9716,
        "customer_lng": 77.5946,
        "order_amount": 450.0,
        "delivery_fee": 35.0,
        "item_count": 3,
        "cuisine": "Biryani",
        "order_hour": 19,
        "day_of_week": 5
    }])

    transformed = pipeline.transform(sample_data)
    assert not transformed.empty
    assert "delivery_distance_km" in transformed.columns
    assert transformed["delivery_distance_km"].iloc[0] > 0.0
    assert transformed["prep_complexity_score"].iloc[0] == 1.45 # Biryani complexity multiplier
    assert transformed["is_peak_rush"].iloc[0] in [0, 1]
