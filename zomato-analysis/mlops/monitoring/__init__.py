"""
Model and Data Drift Monitoring Package.
Monitors population stability and feature drift between training baseline and production inference.
"""

from mlops.monitoring.data_drift_detector import DataDriftDetector

__all__ = ["DataDriftDetector"]
