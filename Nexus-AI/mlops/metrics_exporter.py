"""
Nexus-AI: Prometheus Metrics Exporter
=======================================
Exports ML model metrics in Prometheus text exposition format.
These metrics are scraped by Prometheus and visualized in Grafana.

Metrics exported:
- nexus_delivery_eta_rmse            (gauge)
- nexus_delivery_eta_mae             (gauge)
- nexus_delivery_eta_r2              (gauge)
- nexus_delivery_eta_mape            (gauge)
- nexus_model_drift_psi              (gauge)
- nexus_model_inference_latency_ms   (histogram)
- nexus_feature_null_rate            (gauge)
- nexus_model_predictions_total      (counter)

Design Decision: We export both static training metrics and runtime
inference metrics. Training metrics update per training run.
Inference metrics update per prediction request.
"""

import time
from pathlib import Path


def export_training_metrics(
    metrics: dict,
    params: dict,
    artifacts_dir: str = "mlops/artifacts",
) -> Path:
    """
    Export training metrics in Prometheus text exposition format.

    Args:
        metrics: Dict of evaluation metrics
        params: Dict of model hyperparameters
        artifacts_dir: Directory to save the .prom file

    Returns:
        Path to the generated metrics file
    """
    output_path = Path(artifacts_dir) / "prometheus_metrics.prom"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    model_type = params.get("model_type", "unknown")
    version = f"v{int(time.time())}"

    lines = []

    # ── Model Performance Metrics ────────────────────────────────────
    lines.append("# HELP nexus_delivery_eta_rmse Root Mean Squared Error of delivery ETA prediction (minutes)")
    lines.append("# TYPE nexus_delivery_eta_rmse gauge")
    lines.append(f'nexus_delivery_eta_rmse{{model="{model_type}",version="{version}"}} {metrics.get("rmse", 0)}')
    lines.append("")

    lines.append("# HELP nexus_delivery_eta_mae Mean Absolute Error of delivery ETA prediction (minutes)")
    lines.append("# TYPE nexus_delivery_eta_mae gauge")
    lines.append(f'nexus_delivery_eta_mae{{model="{model_type}",version="{version}"}} {metrics.get("mae", 0)}')
    lines.append("")

    lines.append("# HELP nexus_delivery_eta_r2 R-squared score of delivery ETA model")
    lines.append("# TYPE nexus_delivery_eta_r2 gauge")
    lines.append(f'nexus_delivery_eta_r2{{model="{model_type}",version="{version}"}} {metrics.get("r2_score", 0)}')
    lines.append("")

    lines.append("# HELP nexus_delivery_eta_mape Mean Absolute Percentage Error (%)")
    lines.append("# TYPE nexus_delivery_eta_mape gauge")
    lines.append(f'nexus_delivery_eta_mape{{model="{model_type}",version="{version}"}} {metrics.get("mape", 0)}')
    lines.append("")

    lines.append("# HELP nexus_delivery_eta_within_5min Percentage of predictions within 5 minutes of actual")
    lines.append("# TYPE nexus_delivery_eta_within_5min gauge")
    lines.append(f'nexus_delivery_eta_within_5min{{model="{model_type}"}} {metrics.get("within_5min_pct", 0)}')
    lines.append("")

    lines.append("# HELP nexus_delivery_eta_within_10min Percentage of predictions within 10 minutes of actual")
    lines.append("# TYPE nexus_delivery_eta_within_10min gauge")
    lines.append(f'nexus_delivery_eta_within_10min{{model="{model_type}"}} {metrics.get("within_10min_pct", 0)}')
    lines.append("")

    lines.append("# HELP nexus_delivery_eta_p95_error 95th percentile absolute error (minutes)")
    lines.append("# TYPE nexus_delivery_eta_p95_error gauge")
    lines.append(f'nexus_delivery_eta_p95_error{{model="{model_type}"}} {metrics.get("p95_error", 0)}')
    lines.append("")

    # ── Drift Metrics ────────────────────────────────────────────────
    lines.append("# HELP nexus_model_drift_psi Population Stability Index for prediction drift")
    lines.append("# TYPE nexus_model_drift_psi gauge")
    lines.append(f'nexus_model_drift_psi{{model="{model_type}",version="{version}"}} {metrics.get("drift_psi", 0)}')
    lines.append("")

    # ── Model Info ───────────────────────────────────────────────────
    lines.append("# HELP nexus_model_info Metadata about the active model")
    lines.append("# TYPE nexus_model_info gauge")
    n_est = params.get("n_estimators", 0)
    lr = params.get("learning_rate", 0)
    depth = params.get("max_depth", 0)
    lines.append(f'nexus_model_info{{model="{model_type}",n_estimators="{n_est}",learning_rate="{lr}",max_depth="{depth}"}} 1')
    lines.append("")

    # ── Runtime Placeholder Metrics ──────────────────────────────────
    lines.append("# HELP nexus_model_predictions_total Total number of inference predictions made")
    lines.append("# TYPE nexus_model_predictions_total counter")
    lines.append(f'nexus_model_predictions_total{{model="{model_type}"}} 0')
    lines.append("")

    lines.append("# HELP nexus_model_inference_latency_seconds Inference latency in seconds")
    lines.append("# TYPE nexus_model_inference_latency_seconds histogram")
    lines.append(f'nexus_model_inference_latency_seconds_bucket{{model="{model_type}",le="0.01"}} 0')
    lines.append(f'nexus_model_inference_latency_seconds_bucket{{model="{model_type}",le="0.05"}} 0')
    lines.append(f'nexus_model_inference_latency_seconds_bucket{{model="{model_type}",le="0.1"}} 0')
    lines.append(f'nexus_model_inference_latency_seconds_bucket{{model="{model_type}",le="0.5"}} 0')
    lines.append(f'nexus_model_inference_latency_seconds_bucket{{model="{model_type}",le="1.0"}} 0')
    lines.append(f'nexus_model_inference_latency_seconds_bucket{{model="{model_type}",le="+Inf"}} 0')
    lines.append(f'nexus_model_inference_latency_seconds_sum{{model="{model_type}"}} 0')
    lines.append(f'nexus_model_inference_latency_seconds_count{{model="{model_type}"}} 0')
    lines.append("")

    content = "\n".join(lines) + "\n"
    output_path.write_text(content)

    return output_path
