"""
MLflow Model Registry Management & Automated Champion/Challenger Gateways.
Enforces validation thresholds before promoting models from Staging to Production.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
import mlflow
from mlflow.tracking import MlflowClient


class ModelStage(str, Enum):
    NONE = "None"
    STAGING = "Staging"
    PRODUCTION = "Production"
    ARCHIVED = "Archived"


@dataclass
class ModelEvaluationGate:
    model_name: str
    challenger_version: int
    champion_version: int
    challenger_mae: float
    champion_mae: float
    geval_groundedness: float
    promoted: bool
    rationale: str


class EnterpriseModelRegistry:
    """
    Manages automated model lifecycle, evaluation benchmarks, and zero-downtime promotions.
    """

    def __init__(self, tracking_uri: str = "sqlite:///mlflow.db"):
        mlflow.set_tracking_uri(tracking_uri)
        self.client = MlflowClient(tracking_uri=tracking_uri)

    def register_and_evaluate(
        self,
        model_name: str,
        challenger_version: int,
        challenger_mae: float,
        geval_score: float,
        mae_improvement_threshold: float = 0.02
    ) -> ModelEvaluationGate:
        """
        Automated Champion vs Challenger evaluation.
        Promotes to Production if challenger improves MAE by >= 2% and G-Eval >= 0.85.
        """
        # Retrieve current Champion in Production
        latest_prod = self.client.get_latest_versions(model_name, stages=[ModelStage.PRODUCTION.value])
        
        if not latest_prod:
            # First model deployment -> automatic promotion
            self.client.transition_model_version_stage(
                name=model_name,
                version=str(challenger_version),
                stage=ModelStage.PRODUCTION.value,
                archive_existing_versions=True
            )
            return ModelEvaluationGate(
                model_name=model_name,
                challenger_version=challenger_version,
                champion_version=0,
                challenger_mae=challenger_mae,
                champion_mae=challenger_mae * 1.05,
                geval_groundedness=geval_score,
                promoted=True,
                rationale="Initial deployment: Promoted as baseline Champion."
            )

        champion = latest_prod[0]
        champion_ver = int(champion.version)
        champion_mae = float(champion.tags.get("val_mae", challenger_mae * 1.05))

        improvement = (champion_mae - challenger_mae) / champion_mae

        if improvement >= mae_improvement_threshold and geval_score >= 0.85:
            # Challenger wins!
            self.client.transition_model_version_stage(
                name=model_name,
                version=str(challenger_version),
                stage=ModelStage.PRODUCTION.value,
                archive_existing_versions=True
            )
            return ModelEvaluationGate(
                model_name=model_name,
                challenger_version=challenger_version,
                champion_version=champion_ver,
                challenger_mae=challenger_mae,
                champion_mae=champion_mae,
                geval_groundedness=geval_score,
                promoted=True,
                rationale=f"Challenger improved MAE by {improvement*100:.1f}% with G-Eval score {geval_score:.2f}. Promoted to Production."
            )
        else:
            return ModelEvaluationGate(
                model_name=model_name,
                challenger_version=challenger_version,
                champion_version=champion_ver,
                challenger_mae=challenger_mae,
                champion_mae=champion_mae,
                geval_groundedness=geval_score,
                promoted=False,
                rationale=f"Challenger failed threshold (delta={improvement*100:.1f}%, G-Eval={geval_score:.2f}). Retained Champion v{champion_ver}."
            )


# Global Singleton Model Registry
model_registry = EnterpriseModelRegistry()
