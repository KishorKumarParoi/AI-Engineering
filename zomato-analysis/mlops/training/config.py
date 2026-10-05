"""
Training configuration, hyperparameter grids, and MLflow registry settings.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "mlops" / "mlflow.db"


@dataclass
class TrainingConfig:
    experiment_name: str = os.getenv("MLFLOW_EXPERIMENT_NAME", "zomato-delivery-eta-prediction")
    model_name: str = os.getenv("MLFLOW_MODEL_NAME", "zomato_eta_champion")
    tracking_uri: str = os.getenv("MLFLOW_TRACKING_URI", f"sqlite:///{DEFAULT_DB_PATH}")
    artifact_location: str = os.getenv("MLFLOW_ARTIFACT_URI", str(PROJECT_ROOT / "mlops" / "artifacts"))
    test_size: float = 0.2
    random_state: int = 42

    # Model Hyperparameters (GradientBoostingRegressor)
    model_params: Dict[str, Any] = field(default_factory=lambda: {
        "n_estimators": 120,
        "learning_rate": 0.08,
        "max_depth": 5,
        "subsample": 0.85,
        "random_state": 42
    })

    # Performance Thresholds for Registry Promotion
    max_acceptable_rmse: float = 4.5  # mins
    min_acceptable_r2: float = 0.85
