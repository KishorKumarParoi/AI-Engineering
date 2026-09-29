"""
Nexus-AI: Agent 3 — MLOps Agent
==================================
Autonomous MLOps supervisor that:
- Monitors model registry and health
- Checks drift metrics (PSI)
- Triggers retraining when drift exceeds threshold
- Manages model staging transitions
- Reports Prometheus telemetry status
"""

import json
from pathlib import Path
from typing import Any

import numpy as np


def inspect_model_health(artifacts_dir: str = "mlops/artifacts") -> dict[str, Any]:
    """Comprehensive model health inspection."""
    artifacts = Path(artifacts_dir)

    # Load model registry
    registry_path = artifacts / "model_registry.json"
    if not registry_path.exists():
        return {
            "agent": "MLOpsAgent",
            "status": "NO_MODEL",
            "message": "No model registered. Run: python -m mlops.train",
            "action": "TRAIN_INITIAL",
        }

    with open(registry_path) as f:
        registry = json.load(f)

    # Load baseline distributions
    baseline_path = artifacts / "baseline_distributions.json"
    baseline_info = {}
    if baseline_path.exists():
        with open(baseline_path) as f:
            baseline = json.load(f)
        baseline_info = {
            "training_samples": baseline.get("n_training_samples"),
            "prediction_mean": baseline.get("prediction_stats", {}).get("mean"),
            "prediction_std": baseline.get("prediction_stats", {}).get("std"),
            "features_tracked": len(baseline.get("feature_stats", {})),
        }

    # Load Prometheus metrics
    prom_path = artifacts / "prometheus_metrics.prom"
    prom_metrics = {}
    if prom_path.exists():
        with open(prom_path) as f:
            for line in f:
                if line.startswith("nexus_") and "{" in line:
                    parts = line.split("}")
                    if len(parts) >= 2:
                        metric_name = parts[0].split("{")[0].strip()
                        value = parts[1].strip()
                        try:
                            prom_metrics[metric_name] = float(value)
                        except ValueError:
                            pass

    # Determine health status
    metrics = registry.get("metrics", {})
    psi = metrics.get("drift_psi", 0)
    rmse = metrics.get("rmse", 999)
    r2 = metrics.get("r2_score", 0)

    health_checks = []
    overall_status = "HEALTHY"

    # Check R²
    if r2 >= 0.9:
        health_checks.append({"check": "r2_score", "status": "PASS", "value": r2, "threshold": "≥0.9"})
    elif r2 >= 0.8:
        health_checks.append({"check": "r2_score", "status": "WARN", "value": r2, "threshold": "≥0.9"})
        overall_status = "DEGRADED"
    else:
        health_checks.append({"check": "r2_score", "status": "FAIL", "value": r2, "threshold": "≥0.9"})
        overall_status = "CRITICAL"

    # Check RMSE
    if rmse <= 5:
        health_checks.append({"check": "rmse", "status": "PASS", "value": rmse, "threshold": "≤5 min"})
    elif rmse <= 10:
        health_checks.append({"check": "rmse", "status": "WARN", "value": rmse, "threshold": "≤5 min"})
    else:
        health_checks.append({"check": "rmse", "status": "FAIL", "value": rmse, "threshold": "≤5 min"})
        overall_status = "CRITICAL"

    # Check drift PSI
    if psi < 0.10:
        health_checks.append({"check": "drift_psi", "status": "PASS", "value": psi, "threshold": "<0.10"})
    elif psi < 0.25:
        health_checks.append({"check": "drift_psi", "status": "WARN", "value": psi, "threshold": "<0.10"})
        if overall_status == "HEALTHY":
            overall_status = "DEGRADED"
    else:
        health_checks.append({"check": "drift_psi", "status": "FAIL", "value": psi, "threshold": "<0.10"})
        overall_status = "CRITICAL"

    # Determine action
    if overall_status == "CRITICAL":
        action = "TRIGGER_RETRAINING"
        action_detail = "Model performance degraded or significant drift detected. Automated retraining recommended."
    elif overall_status == "DEGRADED":
        action = "MONITOR_CLOSELY"
        action_detail = "Some metrics approaching thresholds. Increase monitoring frequency."
    else:
        action = "MAINTAIN"
        action_detail = "All metrics healthy. Model performing within expected parameters."

    return {
        "agent": "MLOpsAgent",
        "type": "health_report",
        "overall_status": overall_status,
        "model_type": registry.get("model_type", "unknown"),
        "model_stage": registry.get("model_stage", "unknown"),
        "timestamp": registry.get("timestamp"),
        "metrics": metrics,
        "health_checks": health_checks,
        "baseline": baseline_info,
        "prometheus_metrics": prom_metrics,
        "action": action,
        "action_detail": action_detail,
    }


def analyze_query(query: str, artifacts_dir: str = "mlops/artifacts") -> dict[str, Any]:
    """Route MLOps queries to the appropriate handler."""
    q = query.lower()

    if any(kw in q for kw in ["health", "status", "check", "monitor"]):
        return inspect_model_health(artifacts_dir)

    elif any(kw in q for kw in ["drift", "psi", "distribution"]):
        report = inspect_model_health(artifacts_dir)
        # Focus on drift-specific info
        return {
            "agent": "MLOpsAgent",
            "type": "drift_report",
            "psi_score": report["metrics"].get("drift_psi", 0),
            "status": report["overall_status"],
            "baseline": report.get("baseline", {}),
            "message": report["action_detail"],
        }

    elif any(kw in q for kw in ["retrain", "train", "update"]):
        report = inspect_model_health(artifacts_dir)
        return {
            "agent": "MLOpsAgent",
            "type": "retrain_recommendation",
            "current_status": report["overall_status"],
            "should_retrain": report["overall_status"] in ("CRITICAL", "DEGRADED"),
            "command": "python -m mlops.train --data-dir=data",
            "message": report["action_detail"],
        }

    else:
        return inspect_model_health(artifacts_dir)
