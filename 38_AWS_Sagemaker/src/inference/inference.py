#!/usr/bin/env python3
"""
SageMaker Inference Serving Script.

Implements the official SageMaker Inference Toolkit contracts:
1. model_fn(model_dir): Loads the model from disk upon container initialization.
2. input_fn(request_body, request_content_type): Deserializes and validates input.
3. predict_fn(input_data, model_bundle): Performs inference and probability calculations.
4. output_fn(prediction, accept): Serializes predictions to JSON or CSV.
"""

import io
import json
import logging
import os
import sys
from typing import Any, Dict, List, Union

import joblib
import numpy as np
import pandas as pd

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("sagemaker-inference")

DEFAULT_FEATURES = [
    "battery_power", "blue", "clock_speed", "dual_sim", "fc", "four_g",
    "int_memory", "m_dep", "mobile_wt", "n_cores", "pc", "px_height",
    "px_width", "ram", "sc_h", "sc_w", "talk_time", "three_g",
    "touch_screen", "wifi"
]

TARGET_CLASSES = {
    0: "Low Cost",
    1: "Medium Cost",
    2: "High Cost",
    3: "Very High Cost"
}


def model_fn(model_dir: str) -> Dict[str, Any]:
    """
    SageMaker container hook to load the trained model into memory.
    Runs once when the container is initialized.

    Args:
        model_dir: Directory where the uncompressed model artifacts reside.

    Returns:
        Dict containing the model object and metadata.
    """
    logger.info("Initializing model loading from model_dir: %s", model_dir)
    model_path = os.path.join(model_dir, "model.joblib")
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file 'model.joblib' not found in {model_dir}")

    model = joblib.load(model_path)
    logger.info("RandomForestClassifier model loaded successfully.")

    metadata = {}
    metadata_path = os.path.join(model_dir, "metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            logger.info("Loaded metadata: %s features defined.", len(metadata.get("features", [])))
        except Exception as e:
            logger.warning("Could not read metadata.json: %s", e)

    return {
        "model": model,
        "features": metadata.get("features", DEFAULT_FEATURES),
        "target_classes": metadata.get("target_classes", TARGET_CLASSES),
    }


def input_fn(request_body: Any, request_content_type: str = "application/json") -> pd.DataFrame:
    """
    Deserialize request payload into a validated pandas DataFrame.

    Supported content types:
    - application/json:
        - List of records: [{"battery_power": 842, ...}]
        - Instances payload: {"instances": [[...], [...]]}
        - 2D array: [[842, 0, 2.2, ...]]
    - text/csv:
        - CSV strings (comma-separated rows)

    Args:
        request_body: Raw request body.
        request_content_type: Content type header.

    Returns:
        pd.DataFrame formatted with expected columns.
    """
    logger.info("Received inference request with content_type: %s", request_content_type)

    if request_content_type == "application/json":
        if isinstance(request_body, (bytes, bytearray)):
            request_body = request_body.decode("utf-8")

        payload = json.loads(request_body) if isinstance(request_body, str) else request_body

        # Case 1: {"instances": [...]}
        if isinstance(payload, dict) and "instances" in payload:
            raw_instances = payload["instances"]
            if isinstance(raw_instances, list) and len(raw_instances) > 0 and isinstance(raw_instances[0], dict):
                df = pd.DataFrame(raw_instances)
            else:
                df = pd.DataFrame(raw_instances, columns=DEFAULT_FEATURES)

        # Case 2: [{"feature1": val, ...}]
        elif isinstance(payload, list) and len(payload) > 0 and isinstance(payload[0], dict):
            df = pd.DataFrame(payload)

        # Case 3: [[val1, val2, ...]]
        elif isinstance(payload, list):
            df = pd.DataFrame(payload, columns=DEFAULT_FEATURES)

        else:
            raise ValueError("Invalid JSON schema. Expected list of records, 2D array, or {'instances': [...]}")

    elif request_content_type == "text/csv":
        if isinstance(request_body, (bytes, bytearray)):
            request_body = request_body.decode("utf-8")

        df = pd.read_csv(io.StringIO(request_body), header=None)
        if df.shape[1] == len(DEFAULT_FEATURES):
            df.columns = DEFAULT_FEATURES
        else:
            raise ValueError(f"CSV payload column mismatch. Expected {len(DEFAULT_FEATURES)} cols, got {df.shape[1]}")

    else:
        raise ValueError(f"Unsupported content type: '{request_content_type}'. Must be application/json or text/csv.")

    # Validate column count
    if df.shape[1] != len(DEFAULT_FEATURES):
        raise ValueError(f"Expected {len(DEFAULT_FEATURES)} features, but received {df.shape[1]}")

    return df


def predict_fn(input_data: pd.DataFrame, model_bundle: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run prediction on the deserialized input data.

    Args:
        input_data: DataFrame with features.
        model_bundle: Dictionary returned by model_fn.

    Returns:
        Dictionary containing predictions, class labels, and probabilities.
    """
    model = model_bundle["model"]
    feature_order = model_bundle.get("features", DEFAULT_FEATURES)
    target_classes = model_bundle.get("target_classes", TARGET_CLASSES)

    # Ensure consistent column ordering
    if all(col in input_data.columns for col in feature_order):
        X = input_data[feature_order]
    else:
        X = input_data.values

    # Run predictions
    class_preds = model.predict(X).tolist()
    class_probabilities = model.predict_proba(X).tolist()

    results = []
    for idx, (pred_class, probs) in enumerate(zip(class_preds, class_probabilities)):
        class_str = str(pred_class)
        class_name = target_classes.get(pred_class, target_classes.get(class_str, f"Class {pred_class}"))
        results.append({
            "index": idx,
            "predicted_class": int(pred_class),
            "predicted_label": class_name,
            "confidence": float(max(probs)),
            "probabilities": {
                target_classes.get(i, target_classes.get(str(i), f"Class {i}")): float(prob)
                for i, prob in enumerate(probs)
            }
        })

    return {
        "predictions": results,
        "classes": [r["predicted_class"] for r in results],
        "labels": [r["predicted_label"] for r in results],
    }


def output_fn(prediction: Dict[str, Any], accept: str = "application/json") -> Union[str, bytes]:
    """
    Format prediction output based on requested Accept header.

    Args:
        prediction: Dictionary from predict_fn.
        accept: Target MIME type.

    Returns:
        Formatted response string or bytes.
    """
    if accept in ("application/json", "*/*"):
        return json.dumps(prediction, indent=2)

    elif accept == "text/csv":
        # Returns simple comma-separated predicted classes
        return ",".join(map(str, prediction.get("classes", [])))

    else:
        raise ValueError(f"Unsupported Accept header: '{accept}'. Expected application/json or text/csv.")
