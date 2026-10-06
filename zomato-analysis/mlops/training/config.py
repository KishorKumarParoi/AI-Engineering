"""
Training configuration, hyperparameter grids, and MLflow registry settings.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DB_PATH = PROJECT_ROOT / "mlops" / "mlflow.db"


def resolve_tracking_uri() -> str:
    """
    Resolves the MLflow tracking URI with automatic DagsHub cloud detection.
    Precedence:
      1. Explicit MLFLOW_TRACKING_URI env var
      2. DagsHub cloud URI if DAGSHUB_USER_NAME & DAGSHUB_REPO_NAME are set
      3. Fallback to local SQLite database
    """
    if os.getenv("MLFLOW_TRACKING_URI"):
        return os.environ["MLFLOW_TRACKING_URI"]
    
    user = os.getenv("DAGSHUB_USER_NAME")
    repo = os.getenv("DAGSHUB_REPO_NAME")
    if user and repo:
        return f"https://dagshub.com/{user}/{repo}.mlflow"

    return f"sqlite:///{DEFAULT_DB_PATH}"


@dataclass
class TrainingConfig:
    experiment_name: str = os.getenv("MLFLOW_EXPERIMENT_NAME", "zomato-delivery-eta-prediction")
    model_name: str = os.getenv("MLFLOW_MODEL_NAME", "zomato_eta_champion")
    tracking_uri: str = resolve_tracking_uri()
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
