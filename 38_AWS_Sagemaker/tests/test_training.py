import os
import pytest
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

from src.training.train import train_model, evaluate_dataset, TARGET_COLUMN


def test_train_model_fit(sample_raw_dataframe):
    """Test that train_model fits a RandomForestClassifier."""
    features = [c for c in sample_raw_dataframe.columns if c != TARGET_COLUMN]
    X_train = sample_raw_dataframe[features]
    y_train = sample_raw_dataframe[TARGET_COLUMN]

    model = train_model(
        X_train=X_train,
        y_train=y_train,
        n_estimators=10,
        max_depth=5,
        random_state=42,
    )

    assert isinstance(model, RandomForestClassifier)
    assert hasattr(model, "classes_")
    assert len(model.classes_) == 4


def test_evaluate_dataset_metrics(sample_raw_dataframe):
    """Test that evaluate_dataset returns valid metric dictionary."""
    features = [c for c in sample_raw_dataframe.columns if c != TARGET_COLUMN]
    X = sample_raw_dataframe[features]
    y = sample_raw_dataframe[TARGET_COLUMN]

    model = train_model(X, y, n_estimators=10, max_depth=5, random_state=42)
    metrics = evaluate_dataset(model, X, y, prefix="test")

    assert "test_accuracy" in metrics
    assert "test_f1_macro" in metrics
    assert 0.0 <= metrics["test_accuracy"] <= 1.0
    assert 0.0 <= metrics["test_f1_macro"] <= 1.0
