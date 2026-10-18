import pytest
import pandas as pd
import numpy as np

from src.processing.preprocess import (
    EXPECTED_FEATURES,
    TARGET_COLUMN,
    split_data,
    validate_schema,
)


def test_validate_schema_valid_data(sample_raw_dataframe):
    """Test that schema validation passes for valid dataset."""
    validate_schema(sample_raw_dataframe)


def test_validate_schema_missing_column(sample_raw_dataframe):
    """Test that schema validation fails when a feature is missing."""
    corrupted_df = sample_raw_dataframe.drop(columns=["battery_power"])
    with pytest.raises(ValueError, match="missing expected feature columns"):
        validate_schema(corrupted_df)


def test_validate_schema_missing_target(sample_raw_dataframe):
    """Test that schema validation fails when target column is missing."""
    corrupted_df = sample_raw_dataframe.drop(columns=[TARGET_COLUMN])
    with pytest.raises(ValueError, match="missing target column"):
        validate_schema(corrupted_df)


def test_split_data_proportions(sample_raw_dataframe):
    """Test that split_data splits data according to specified ratios."""
    train_df, val_df, test_df = split_data(
        sample_raw_dataframe,
        train_ratio=0.70,
        val_ratio=0.15,
        test_ratio=0.15,
        random_state=42,
    )

    total_len = len(sample_raw_dataframe)
    assert len(train_df) == int(total_len * 0.70)
    assert len(val_df) + len(test_df) == total_len - len(train_df)
    assert set(train_df.index).isdisjoint(set(val_df.index))
    assert set(train_df.index).isdisjoint(set(test_df.index))
    assert set(val_df.index).isdisjoint(set(test_df.index))


def test_split_data_stratification(sample_raw_dataframe):
    """Test that split maintains class distribution."""
    train_df, val_df, test_df = split_data(sample_raw_dataframe, random_state=42)
    # Check that each class 0, 1, 2, 3 exists in train, val, test
    for c in range(4):
        assert (train_df[TARGET_COLUMN] == c).sum() > 0
        assert (val_df[TARGET_COLUMN] == c).sum() > 0
        assert (test_df[TARGET_COLUMN] == c).sum() > 0
