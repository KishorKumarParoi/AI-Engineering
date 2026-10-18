#!/usr/bin/env python3
"""
SageMaker Processing Step Script.

This script runs inside an SKLearnProcessor container in SageMaker (or locally).
It handles:
1. Data ingestion from the specified input path.
2. Data validation and schema verification.
3. Stratified Train / Validation / Test split.
4. Exporting datasets for training, evaluation, and baseline monitoring.
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from typing import Tuple

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("preprocess")

EXPECTED_FEATURES = [
    "battery_power", "blue", "clock_speed", "dual_sim", "fc", "four_g",
    "int_memory", "m_dep", "mobile_wt", "n_cores", "pc", "px_height",
    "px_width", "ram", "sc_h", "sc_w", "talk_time", "three_g",
    "touch_screen", "wifi"
]
TARGET_COLUMN = "price_range"


def validate_schema(df: pd.DataFrame) -> None:
    """Validate that the dataset contains all expected features and target."""
    missing_cols = [col for col in EXPECTED_FEATURES if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Input data is missing expected feature columns: {missing_cols}")

    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Input data is missing target column: '{TARGET_COLUMN}'")

    # Check for null values
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        logger.warning("Dataset contains missing values. Imputing with median.")
        for col in EXPECTED_FEATURES:
            if df[col].isnull().sum() > 0:
                df[col] = df[col].fillna(df[col].median())


def split_data(
    df: pd.DataFrame,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified split into Train, Validation, and Test sets.
    Preserves multi-class target distribution across all splits.
    """
    if not np.isclose(train_ratio + val_ratio + test_ratio, 1.0):
        raise ValueError("Train, validation, and test ratios must sum to 1.0")

    # First split: Train vs Temp (Val + Test)
    temp_ratio = val_ratio + test_ratio
    train_df, temp_df = train_test_split(
        df,
        test_size=temp_ratio,
        random_state=random_state,
        stratify=df[TARGET_COLUMN],
    )

    # Second split: Validation vs Test
    relative_test_ratio = test_ratio / temp_ratio
    val_df, test_df = train_test_split(
        temp_df,
        test_size=relative_test_ratio,
        random_state=random_state,
        stratify=temp_df[TARGET_COLUMN],
    )

    return train_df, val_df, test_df


def run_preprocessing(
    input_data_path: str,
    output_train_dir: str,
    output_val_dir: str,
    output_test_dir: str,
    output_baseline_dir: str,
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_state: int = 42,
) -> None:
    """Execute end-to-end preprocessing pipeline."""
    logger.info("Starting SageMaker Preprocessing Step...")
    logger.info("Reading raw dataset from: %s", input_data_path)

    # Handle directory or file path
    if os.path.isdir(input_data_path):
        csv_files = [f for f in os.listdir(input_data_path) if f.endswith(".csv")]
        if not csv_files:
            raise FileNotFoundError(f"No CSV file found in input directory: {input_data_path}")
        file_path = os.path.join(input_data_path, csv_files[0])
    else:
        file_path = input_data_path

    df = pd.read_csv(file_path)
    logger.info("Raw dataset shape: %s", df.shape)

    # Validate Schema
    validate_schema(df)
    logger.info("Schema validation passed successfully.")

    # Split dataset
    train_df, val_df, test_df = split_data(
        df=df,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        random_state=random_state,
    )

    logger.info(
        "Data split summary: Train=%d, Val=%d, Test=%d (Total=%d)",
        len(train_df), len(val_df), len(test_df), len(df)
    )

    # Create baseline dataset (features only, without target) for SageMaker Model Monitor
    baseline_df = train_df[EXPECTED_FEATURES]

    # Ensure output directories exist
    os.makedirs(output_train_dir, exist_ok=True)
    os.makedirs(output_val_dir, exist_ok=True)
    os.makedirs(output_test_dir, exist_ok=True)
    os.makedirs(output_baseline_dir, exist_ok=True)

    # Save CSV files
    train_file = os.path.join(output_train_dir, "train.csv")
    val_file = os.path.join(output_val_dir, "validation.csv")
    test_file = os.path.join(output_test_dir, "test.csv")
    baseline_file = os.path.join(output_baseline_dir, "baseline.csv")

    train_df.to_csv(train_file, index=False)
    val_df.to_csv(val_file, index=False)
    test_df.to_csv(test_file, index=False)
    baseline_df.to_csv(baseline_file, index=False, header=False)

    logger.info("Saved train data to: %s", train_file)
    logger.info("Saved validation data to: %s", val_file)
    logger.info("Saved test data to: %s", test_file)
    logger.info("Saved drift baseline to: %s", baseline_file)
    logger.info("Preprocessing step completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SageMaker Preprocessing Step")

    # SageMaker container default paths vs custom CLI arguments
    parser.add_argument(
        "--input-data",
        type=str,
        default="/opt/ml/processing/input",
        help="Path to input raw data directory or file",
    )
    parser.add_argument(
        "--train-dir",
        type=str,
        default="/opt/ml/processing/train",
        help="Output directory for processed training data",
    )
    parser.add_argument(
        "--val-dir",
        type=str,
        default="/opt/ml/processing/validation",
        help="Output directory for processed validation data",
    )
    parser.add_argument(
        "--test-dir",
        type=str,
        default="/opt/ml/processing/test",
        help="Output directory for processed test data",
    )
    parser.add_argument(
        "--baseline-dir",
        type=str,
        default="/opt/ml/processing/baseline",
        help="Output directory for model monitor baseline data",
    )
    parser.add_argument("--train-ratio", type=float, default=0.70)
    parser.add_argument("--val-ratio", type=float, default=0.15)
    parser.add_argument("--test-ratio", type=float, default=0.15)
    parser.add_argument("--random-state", type=int, default=42)

    args = parser.parse_args()

    run_preprocessing(
        input_data_path=args.input_data,
        output_train_dir=args.train_dir,
        output_val_dir=args.val_dir,
        output_test_dir=args.test_dir,
        output_baseline_dir=args.baseline_dir,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        random_state=args.random_state,
    )
