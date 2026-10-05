"""
MLOps Training package for Zomato Delivery ETA Prediction.
Contains model training scripts, MLflow tracking, and experiment orchestration.
"""

from mlops.training.train_eta_mlflow import train_model

__all__ = ["train_model"]
