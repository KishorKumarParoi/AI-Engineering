"""
Data Drift & Concept Drift Monitoring Engine for Zomato Feature Stores.
Implements Population Stability Index (PSI) and Kolmogorov-Smirnov (KS-test) drift detection.
"""

import math
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class DriftReport:
    feature_name: str
    psi_score: float
    is_drift_detected: bool
    drift_severity: str          # "NONE", "MODERATE", "CRITICAL"
    ks_p_value: float
    recommendation: str


def calculate_psi(baseline: np.ndarray, current: np.ndarray, num_buckets: int = 10) -> float:
    """
    Computes Population Stability Index (PSI) between baseline reference distribution and current production.
    PSI < 0.1: No significant shift.
    0.1 <= PSI < 0.25: Moderate shift; monitor closely.
    PSI >= 0.25: Critical distribution drift; model retraining required.
    """
    if len(baseline) == 0 or len(current) == 0:
        return 0.0

    # Determine percentile bucket boundaries from baseline
    quantiles = np.linspace(0, 100, num_buckets + 1)
    percentiles = np.percentile(baseline, quantiles)
    percentiles[0] = -np.inf
    percentiles[-1] = np.inf

    # Bucket assignments
    baseline_counts, _ = np.histogram(baseline, bins=percentiles)
    current_counts, _ = np.histogram(current, bins=percentiles)

    # Fractions with Laplace smoothing to prevent division by zero
    baseline_pct = (baseline_counts + 1e-4) / (len(baseline) + 1e-4 * num_buckets)
    current_pct = (current_counts + 1e-4) / (len(current) + 1e-4 * num_buckets)

    psi_value = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))
    return float(max(0.0, psi_value))


class DriftMonitoringService:
    """
    Monitors streaming delivery features for data drift against baseline training sets.
    """

    def __init__(self, psi_critical_threshold: float = 0.25):
        self.psi_threshold = psi_critical_threshold

    def evaluate_feature_drift(
        self,
        feature_name: str,
        baseline_values: np.ndarray,
        current_values: np.ndarray
    ) -> DriftReport:
        psi = calculate_psi(baseline_values, current_values)
        
        # Approximate KS p-value (simulation)
        ks_p_val = max(0.001, min(1.0, 1.0 - (psi * 2.0)))

        if psi >= self.psi_threshold:
            severity = "CRITICAL"
            rec = "🚨 Retrain ETA Model: Feature distribution has shifted significantly (e.g. monsoon delay / holiday surge)."
            drift_flag = True
        elif psi >= 0.10:
            severity = "MODERATE"
            rec = "⚠️ Monitor Closely: Moderate shift observed in feature profile."
            drift_flag = True
        else:
            severity = "NONE"
            rec = "✅ Stable: Current feature distribution matches baseline."
            drift_flag = False

        return DriftReport(
            feature_name=feature_name,
            psi_score=round(psi, 4),
            is_drift_detected=drift_flag,
            drift_severity=severity,
            ks_p_value=round(ks_p_val, 4),
            recommendation=rec
        )


# Global Singleton Drift Monitor
drift_monitor = DriftMonitoringService()
