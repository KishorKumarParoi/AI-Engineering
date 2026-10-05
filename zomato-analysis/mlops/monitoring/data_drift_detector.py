"""
Data Drift Detector for Zomato Delivery ETA Features.
Implements Population Stability Index (PSI) and distribution checks.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd


class DataDriftDetector:
    """
    Monitors feature distribution drift between training reference and live inference batches.
    
    PSI Rule of Thumb:
      • PSI < 0.10: No significant shift (Healthy)
      • 0.10 <= PSI < 0.25: Moderate shift (Monitor / Warning)
      • PSI >= 0.25: Significant drift (Trigger Automatic Retraining)
    """

    @staticmethod
    def calculate_psi(reference: np.ndarray, current: np.ndarray, num_buckets: int = 10) -> float:
        """
        Calculates Population Stability Index (PSI) across numeric distributions.
        """
        ref = reference[~np.isnan(reference)]
        curr = current[~np.isnan(current)]

        if len(ref) == 0 or len(curr) == 0:
            return 0.0

        # Create quantile buckets based on reference distribution
        quantiles = np.linspace(0, 100, num_buckets + 1)
        bins = np.percentile(ref, quantiles)
        bins[0] = -np.inf
        bins[-1] = np.inf
        bins = np.unique(bins)

        if len(bins) <= 1:
            return 0.0

        ref_counts, _ = np.histogram(ref, bins=bins)
        curr_counts, _ = np.histogram(curr, bins=bins)

        # Convert to percentages with epsilon smoothing to prevent div by 0
        eps = 1e-4
        ref_pct = (ref_counts / len(ref)) + eps
        curr_pct = (curr_counts / len(curr)) + eps

        # Re-normalize
        ref_pct /= ref_pct.sum()
        curr_pct /= curr_pct.sum()

        psi_val = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))
        return float(np.round(psi_val, 4))

    def evaluate_features_drift(
        self, baseline_df: pd.DataFrame, live_df: pd.DataFrame, feature_cols: List[str]
    ) -> Dict[str, Any]:
        """
        Audits all feature columns and returns comprehensive drift metrics.
        """
        report = {}
        max_psi = 0.0
        retraining_recommended = False

        for col in feature_cols:
            if col in baseline_df.columns and col in live_df.columns:
                ref_vals = pd.to_numeric(baseline_df[col], errors="coerce").values
                curr_vals = pd.to_numeric(live_df[col], errors="coerce").values
                psi = self.calculate_psi(ref_vals, curr_vals)

                if psi >= 0.25:
                    status = "CRITICAL_DRIFT"
                    retraining_recommended = True
                elif psi >= 0.10:
                    status = "MODERATE_SHIFT"
                else:
                    status = "STABLE"

                report[col] = {
                    "psi": psi,
                    "status": status
                }
                max_psi = max(max_psi, psi)

        return {
            "features": report,
            "max_psi": max_psi,
            "overall_status": "RETRAIN_TRIGGERED" if retraining_recommended else "HEALTHY",
            "retraining_recommended": retraining_recommended
        }
