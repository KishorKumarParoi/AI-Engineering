#!/usr/bin/env python3
"""
SageMaker Training Step Script.

This script acts as the entrypoint for the SageMaker SKLearn Estimator.
It adheres strictly to the SageMaker Training Toolkit environment specifications:
- SM_CHANNEL_TRAIN: Path to the training dataset.
- SM_CHANNEL_VALIDATION: Path to the validation dataset (optional).
- SM_MODEL_DIR: Target directory for saving the serialized model (auto-packaged into model.tar.gz).
- Hyperparameters passed as CLI flags.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("sagemaker-train")

TARGET_COLUMN = "price_range"
TARGET_CLASSES = {
    0: "Low Cost",
    1: "Medium Cost",
    2: "High Cost",
    3: "Very High Cost"
}


def load_dataset_from_channel(channel_dir: str, file_name: str = "train.csv") -> pd.DataFrame:
    """Load dataset from a SageMaker input channel directory or exact file."""
    if not os.path.exists(channel_dir):
        raise FileNotFoundError(f"Channel path does not exist: {channel_dir}")

    if os.path.isfile(channel_dir):
        return pd.read_csv(channel_dir)

    # Search for specified file or fallback to first CSV
    target_path = os.path.join(channel_dir, file_name)
    if os.path.exists(target_path):
        return pd.read_csv(target_path)

    csv_files = [f for f in os.listdir(channel_dir) if f.endswith(".csv")]
    if not csv_files:
        raise FileNotFoundError(f"No CSV file found in channel directory: {channel_dir}")

    chosen_file = os.path.join(channel_dir, csv_files[0])
    logger.info("Found CSV file in channel: %s", chosen_file)
    return pd.read_csv(chosen_file)


def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    n_estimators: int = 150,
    max_depth: int = 15,
    min_samples_split: int = 4,
    min_samples_leaf: int = 2,
    random_state: int = 42,
    n_jobs: int = -1,
) -> RandomForestClassifier:
    """Instantiate and fit RandomForestClassifier."""
    logger.info(
        "Training RandomForestClassifier (n_estimators=%d, max_depth=%d, min_samples_split=%d, min_samples_leaf=%d)",
        n_estimators, max_depth, min_samples_split, min_samples_leaf
    )

    clf = RandomForestClassifier(
        n_estimators=n_estimators,
        max_depth=max_depth,
        min_samples_split=min_samples_split,
        min_samples_leaf=min_samples_leaf,
        random_state=random_state,
        n_jobs=n_jobs,
        verbose=1,
    )
    clf.fit(X_train, y_train)
    return clf


def evaluate_dataset(
    model: RandomForestClassifier,
    X: pd.DataFrame,
    y: pd.Series,
    prefix: str = "validation"
) -> Dict[str, float]:
    """Calculate and log metrics formatted for CloudWatch regex capture."""
    preds = model.predict(X)
    acc = accuracy_score(y, preds)
    f1_macro = f1_score(y, preds, average="macro")
    precision_macro = precision_score(y, preds, average="macro")
    recall_macro = recall_score(y, preds, average="macro")

    # CloudWatch Metric Filter Emission Formats
    logger.info("%s:accuracy = %0.4f", prefix, acc)
    logger.info("%s:f1 = %0.4f", prefix, f1_macro)
    logger.info("%s:precision = %0.4f", prefix, precision_macro)
    logger.info("%s:recall = %0.4f", prefix, recall_macro)

    return {
        f"{prefix}_accuracy": float(acc),
        f"{prefix}_f1_macro": float(f1_macro),
        f"{prefix}_precision_macro": float(precision_macro),
        f"{prefix}_recall_macro": float(recall_macro),
    }


def main():
    parser = argparse.ArgumentParser(description="SageMaker Mobile Price Classifier Training")

    # Hyperparameters
    parser.add_argument("--n_estimators", type=int, default=150)
    parser.add_argument("--max_depth", type=int, default=15)
    parser.add_argument("--min_samples_split", type=int, default=4)
    parser.add_argument("--min_samples_leaf", type=int, default=2)
    parser.add_argument("--random_state", type=int, default=42)

    # SageMaker Environment Variables / CLI arguments
    parser.add_argument(
        "--model-dir",
        type=str,
        default=os.environ.get("SM_MODEL_DIR", "./artifacts/model"),
        help="Directory to save the trained model",
    )
    parser.add_argument(
        "--train",
        type=str,
        default=os.environ.get("SM_CHANNEL_TRAIN", "./data/processed/train"),
        help="Directory containing training data",
    )
    parser.add_argument(
        "--validation",
        type=str,
        default=os.environ.get("SM_CHANNEL_VALIDATION", "./data/processed/validation"),
        help="Directory containing validation data",
    )
    parser.add_argument("--train-file", type=str, default="train.csv")
    parser.add_argument("--val-file", type=str, default="validation.csv")

    args, unknown = parser.parse_known_args()
    if unknown:
        logger.warning("Unrecognized arguments received: %s", unknown)

    logger.info("Initializing Training Execution...")
    logger.info("SM_MODEL_DIR: %s", args.model_dir)
    logger.info("SM_CHANNEL_TRAIN: %s", args.train)
    logger.info("SM_CHANNEL_VALIDATION: %s", args.validation)

    # 1. Load Data
    train_df = load_dataset_from_channel(args.train, args.train_file)
    logger.info("Loaded training data with shape: %s", train_df.shape)

    features = [c for c in train_df.columns if c != TARGET_COLUMN]
    X_train = train_df[features]
    y_train = train_df[TARGET_COLUMN]

    # 2. Train Model
    model = train_model(
        X_train=X_train,
        y_train=y_train,
        n_estimators=args.n_estimators,
        max_depth=args.max_depth,
        min_samples_split=args.min_samples_split,
        min_samples_leaf=args.min_samples_leaf,
        random_state=args.random_state,
    )

    # 3. Evaluate on Training Data
    train_metrics = evaluate_dataset(model, X_train, y_train, prefix="train")

    # 4. Evaluate on Validation Data (if provided)
    val_metrics = {}
    if args.validation and os.path.exists(args.validation):
        try:
            val_df = load_dataset_from_channel(args.validation, args.val_file)
            X_val = val_df[features]
            y_val = val_df[TARGET_COLUMN]
            val_metrics = evaluate_dataset(model, X_val, y_val, prefix="validation")

            logger.info("Validation Classification Report:\n%s", classification_report(y_val, model.predict(X_val)))
        except Exception as e:
            logger.warning("Skipping validation dataset evaluation due to: %s", e)

    # 5. Save Model and Metadata
    os.makedirs(args.model_dir, exist_ok=True)
    model_save_path = os.path.join(args.model_dir, "model.joblib")
    joblib.dump(model, model_save_path)
    logger.info("Model serialized and saved to: %s", model_save_path)

    metadata = {
        "model_type": "RandomForestClassifier",
        "features": features,
        "target_column": TARGET_COLUMN,
        "target_classes": TARGET_CLASSES,
        "hyperparameters": {
            "n_estimators": args.n_estimators,
            "max_depth": args.max_depth,
            "min_samples_split": args.min_samples_split,
            "min_samples_leaf": args.min_samples_leaf,
            "random_state": args.random_state,
        },
        "metrics": {**train_metrics, **val_metrics},
    }

    metadata_path = os.path.join(args.model_dir, "metadata.json")
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    logger.info("Model metadata saved to: %s", metadata_path)
    logger.info("Training completed successfully.")


if __name__ == "__main__":
    main()
