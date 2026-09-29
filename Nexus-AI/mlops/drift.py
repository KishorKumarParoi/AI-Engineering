"""
Nexus-AI: Model Drift Detection — Population Stability Index (PSI)
====================================================================
Detects distribution drift between training and production predictions
using PSI (Population Stability Index).

PSI Interpretation:
  PSI < 0.10  → No drift (stable)
  PSI 0.10-0.25 → Moderate drift (monitor closely)
  PSI > 0.25  → Significant drift (trigger retraining)

Design Decision: PSI is preferred over KS-test because:
1. Distribution-agnostic (works on any shape)
2. Symmetric and bounded (easy to set thresholds)
3. Industry standard at Uber, Spotify, Netflix for drift monitoring
4. Works well with small sample sizes (100+ predictions)
"""

import json
from pathlib import Path

import numpy as np


def compute_psi(
    baseline: np.ndarray,
    current: np.ndarray,
    n_bins: int = 10,
    eps: float = 1e-4,
) -> float:
    """
    Compute Population Stability Index (PSI) between two distributions.

    Args:
        baseline: Reference distribution (training predictions)
        current: Current distribution (production predictions)
        n_bins: Number of bins for histogram
        eps: Small constant to avoid log(0)

    Returns:
        PSI score (float)
    """
    baseline = np.asarray(baseline, dtype=np.float64)
    current = np.asarray(current, dtype=np.float64)

    if len(baseline) == 0 or len(current) == 0:
        return 0.0

    # Use baseline quantiles as bin edges for consistency
    breakpoints = np.percentile(baseline, np.linspace(0, 100, n_bins + 1))
    breakpoints[0] = -np.inf
    breakpoints[-1] = np.inf

    # Remove duplicate breakpoints
    breakpoints = np.unique(breakpoints)
    if len(breakpoints) < 3:
        return 0.0

    # Compute bin proportions
    baseline_counts = np.histogram(baseline, bins=breakpoints)[0]
    current_counts = np.histogram(current, bins=breakpoints)[0]

    baseline_pct = baseline_counts / len(baseline) + eps
    current_pct = current_counts / len(current) + eps

    # PSI formula: sum((current% - baseline%) * ln(current% / baseline%))
    psi = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))

    return float(psi)


def compute_feature_drift(
    baseline_features: np.ndarray,
    current_features: np.ndarray,
    feature_names: list[str],
    n_bins: int = 10,
) -> dict[str, float]:
    """
    Compute PSI for each feature column independently.

    Identifies WHICH features are drifting, not just the predictions.

    Args:
        baseline_features: Training feature matrix (n_samples, n_features)
        current_features: Current feature matrix
        feature_names: List of feature column names

    Returns:
        Dict mapping feature_name → PSI score
    """
    drift_scores = {}

    for i, name in enumerate(feature_names):
        if i < baseline_features.shape[1] and i < current_features.shape[1]:
            psi = compute_psi(baseline_features[:, i], current_features[:, i], n_bins)
            drift_scores[name] = round(psi, 6)

    return drift_scores


def save_baseline_distributions(
    X_train: np.ndarray,
    y_train: np.ndarray,
    train_preds: np.ndarray,
    feature_names: list[str],
    artifacts_dir: str = "mlops/artifacts",
) -> Path:
    """
    Save training distribution statistics for future drift comparison.

    Saves:
    - Feature means, stds, percentiles
    - Prediction distribution percentiles
    - Target distribution percentiles
    """
    output_path = Path(artifacts_dir) / "baseline_distributions.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    baseline = {
        "feature_stats": {},
        "prediction_stats": {},
        "target_stats": {},
        "n_training_samples": len(X_train),
    }

    # Feature distribution stats
    for i, name in enumerate(feature_names):
        if i < X_train.shape[1]:
            col = X_train[:, i]
            baseline["feature_stats"][name] = {
                "mean": float(np.mean(col)),
                "std": float(np.std(col)),
                "min": float(np.min(col)),
                "max": float(np.max(col)),
                "p25": float(np.percentile(col, 25)),
                "p50": float(np.percentile(col, 50)),
                "p75": float(np.percentile(col, 75)),
            }

    # Prediction distribution
    baseline["prediction_stats"] = {
        "mean": float(np.mean(train_preds)),
        "std": float(np.std(train_preds)),
        "min": float(np.min(train_preds)),
        "max": float(np.max(train_preds)),
        "p10": float(np.percentile(train_preds, 10)),
        "p50": float(np.percentile(train_preds, 50)),
        "p90": float(np.percentile(train_preds, 90)),
    }

    # Target distribution
    baseline["target_stats"] = {
        "mean": float(np.mean(y_train)),
        "std": float(np.std(y_train)),
        "min": float(np.min(y_train)),
        "max": float(np.max(y_train)),
        "p10": float(np.percentile(y_train, 10)),
        "p50": float(np.percentile(y_train, 50)),
        "p90": float(np.percentile(y_train, 90)),
    }

    with open(output_path, "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"  💾 Baseline distributions saved → {output_path}")
    return output_path


def check_drift(
    current_predictions: np.ndarray,
    artifacts_dir: str = "mlops/artifacts",
    threshold_moderate: float = 0.10,
    threshold_critical: float = 0.25,
) -> dict:
    """
    Check if current predictions have drifted from training baseline.

    Args:
        current_predictions: Array of recent predictions
        artifacts_dir: Directory containing baseline_distributions.json

    Returns:
        Drift status report with PSI score and recommended action
    """
    baseline_path = Path(artifacts_dir) / "baseline_distributions.json"
    if not baseline_path.exists():
        return {
            "status": "NO_BASELINE",
            "message": "No baseline distributions found. Run training first.",
            "action": "TRAIN",
        }

    with open(baseline_path) as f:
        baseline = json.load(f)

    # Reconstruct baseline prediction percentiles for PSI
    baseline_stats = baseline["prediction_stats"]

    # Generate synthetic baseline from percentiles for PSI calculation
    n_synthetic = 1000
    baseline_synthetic = np.random.normal(
        baseline_stats["mean"],
        baseline_stats["std"],
        size=n_synthetic,
    )

    psi = compute_psi(baseline_synthetic, current_predictions)

    if psi < threshold_moderate:
        status = "HEALTHY"
        action = "NONE"
        message = f"No significant drift detected (PSI={psi:.4f})"
    elif psi < threshold_critical:
        status = "MODERATE_DRIFT"
        action = "MONITOR"
        message = f"Moderate distribution drift detected (PSI={psi:.4f}). Monitor closely."
    else:
        status = "CRITICAL_DRIFT"
        action = "RETRAIN"
        message = f"Significant drift detected (PSI={psi:.4f}). Automated retraining recommended."

    return {
        "status": status,
        "psi_score": round(psi, 4),
        "message": message,
        "action": action,
        "threshold_moderate": threshold_moderate,
        "threshold_critical": threshold_critical,
        "baseline_mean": baseline_stats["mean"],
        "current_mean": float(np.mean(current_predictions)),
        "baseline_std": baseline_stats["std"],
        "current_std": float(np.std(current_predictions)),
    }
