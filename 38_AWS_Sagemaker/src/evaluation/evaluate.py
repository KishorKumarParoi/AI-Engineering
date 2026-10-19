#!/usr/bin/env python3
"""
SageMaker Evaluation Step Script.

Evaluates the trained model against the holdout test dataset.
Generates an evaluation.json report following SageMaker standard metrics schema,
enabling automated quality gating in SageMaker Pipelines ConditionStep.
"""

import argparse
import json
import logging
import os
import sys
import tarfile
from pathlib import Path
from typing import Dict, Any

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
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
logger = logging.getLogger("evaluate")

TARGET_COLUMN = "price_range"


def extract_and_load_model(model_input_path: str):
    """
    Load model from either a directory, a joblib file, or a model.tar.gz archive.
    SageMaker TrainingStep outputs model.tar.gz into S3, which is mounted into the
    Processing container as /opt/ml/processing/model/model.tar.gz.
    """
    logger.info("Resolving model from: %s", model_input_path)

    if os.path.isdir(model_input_path):
        tar_path = os.path.join(model_input_path, "model.tar.gz")
        joblib_path = os.path.join(model_input_path, "model.joblib")

        if os.path.exists(tar_path):
            logger.info("Extracting model.tar.gz from directory: %s", model_input_path)
            with tarfile.open(tar_path, "r:gz") as tar:
                tar.extractall(path=model_input_path)
            return joblib.load(joblib_path)
        elif os.path.exists(joblib_path):
            return joblib.load(joblib_path)
        else:
            raise FileNotFoundError(f"Neither model.tar.gz nor model.joblib found in {model_input_path}")

    elif model_input_path.endswith(".tar.gz"):
        extract_dir = os.path.dirname(model_input_path)
        logger.info("Extracting archive: %s to %s", model_input_path, extract_dir)
        with tarfile.open(model_input_path, "r:gz") as tar:
            tar.extractall(path=extract_dir)
        joblib_path = os.path.join(extract_dir, "model.joblib")
        return joblib.load(joblib_path)

    elif model_input_path.endswith(".joblib"):
        return joblib.load(model_input_path)

    raise ValueError(f"Unsupported model input format: {model_input_path}")


def load_test_data(test_data_path: str, test_file_name: str = "test.csv") -> pd.DataFrame:
    """Load test dataset from path or directory."""
    if os.path.isdir(test_data_path):
        target_file = os.path.join(test_data_path, test_file_name)
        if os.path.exists(target_file):
            return pd.read_csv(target_file)
        csv_files = [f for f in os.listdir(test_data_path) if f.endswith(".csv")]
        if not csv_files:
            raise FileNotFoundError(f"No CSV file found in test directory: {test_data_path}")
        return pd.read_csv(os.path.join(test_data_path, csv_files[0]))
    return pd.read_csv(test_data_path)


def run_evaluation(model_path: str, test_data_path: str, output_eval_dir: str) -> Dict[str, Any]:
    """Execute evaluation and serialize evaluation.json report."""
    logger.info("Starting Model Evaluation Step...")

    # 1. Load Model
    model = extract_and_load_model(model_path)
    logger.info("Model successfully loaded.")

    # 2. Load Test Data
    test_df = load_test_data(test_data_path)
    logger.info("Test dataset loaded with shape: %s", test_df.shape)

    features = [c for c in test_df.columns if c != TARGET_COLUMN]
    X_test = test_df[features]
    y_test = test_df[TARGET_COLUMN]

    # 3. Predict & Compute Metrics
    y_pred = model.predict(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    f1_macro = float(f1_score(y_test, y_pred, average="macro"))
    f1_weighted = float(f1_score(y_test, y_pred, average="weighted"))
    prec_macro = float(precision_score(y_test, y_pred, average="macro"))
    rec_macro = float(recall_score(y_test, y_pred, average="macro"))

    cm = confusion_matrix(y_test, y_pred)
    cm_dict = {str(i): {str(j): int(cm[i, j]) for j in range(cm.shape[1])} for i in range(cm.shape[0])}

    logger.info("==========================================")
    logger.info("EVALUATION RESULTS ON HOLDOUT TEST SET:")
    logger.info("Accuracy:             %0.4f", acc)
    logger.info("Macro F1-Score:       %0.4f", f1_macro)
    logger.info("Weighted F1-Score:    %0.4f", f1_weighted)
    logger.info("Macro Precision:      %0.4f", prec_macro)
    logger.info("Macro Recall:         %0.4f", rec_macro)
    logger.info("==========================================")
    logger.info("\nFull Classification Report:\n%s", classification_report(y_test, y_pred))

    # Format JSON strictly matching SageMaker Model Quality Specification
    eval_report = {
        "multiclass_classification_metrics": {
            "accuracy": {"value": acc, "standard_deviation": "NaN"},
            "f1_score": {"value": f1_macro, "standard_deviation": "NaN"},
            "precision": {"value": prec_macro, "standard_deviation": "NaN"},
            "recall": {"value": rec_macro, "standard_deviation": "NaN"},
            "weighted_f1_score": {"value": f1_weighted, "standard_deviation": "NaN"},
        },
        "confusion_matrix": cm_dict,
        "sample_count": len(y_test),
    }

    os.makedirs(output_eval_dir, exist_ok=True)
    report_file_path = os.path.join(output_eval_dir, "evaluation.json")
    with open(report_file_path, "w", encoding="utf-8") as f:
        json.dump(eval_report, f, indent=2)

    logger.info("Saved evaluation report to: %s", report_file_path)
    return eval_report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SageMaker Evaluation Step")
    parser.add_argument(
        "--model-path",
        type=str,
        default="/opt/ml/processing/model",
        help="Path to directory containing model.tar.gz or model.joblib",
    )
    parser.add_argument(
        "--test-data",
        type=str,
        default="/opt/ml/processing/test",
        help="Path to directory or file containing holdout test data",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="/opt/ml/processing/evaluation",
        help="Path to directory where evaluation.json will be saved",
    )

    args = parser.parse_args()

    run_evaluation(
        model_path=args.model_path,
        test_data_path=args.test_data,
        output_eval_dir=args.output_dir,
    )
