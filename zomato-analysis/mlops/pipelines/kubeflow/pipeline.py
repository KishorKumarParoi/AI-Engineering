"""
Kubeflow Pipeline DAG Definition for Zomato Delivery ETA.
Orchestrates: Ingest & Feature Extraction -> Model Train & MLflow Track -> Quality Gate Validation.
"""

from typing import Dict, Any


class KubeflowETAPipeline:
    """
    KFP v2 Representation of the Zomato Delivery ETA MLOps Pipeline.
    Can be run locally or compiled to Kubeflow / Vertex AI YAML.
    """

    def __init__(self, experiment_name: str = "zomato-kfp-eta-pipeline"):
        self.experiment_name = experiment_name

    def run_local_simulation(self) -> Dict[str, Any]:
        """
        Runs the components in order, simulating containerized pod execution.
        """
        from mlops.pipelines.kubeflow.components import (
            extract_features_component,
            train_and_evaluate_component,
            validate_and_register_component
        )

        print("\n========================================================")
        print("☸️ Executing Kubeflow Pipeline (KFP v2 Simulation)")
        print(f"Pipeline Name: {self.experiment_name}")
        print("========================================================\n")

        # Step 1: Feature Extraction
        feature_parquet = extract_features_component(
            source_type="lakehouse",
            limit=5000,
            output_feature_path="/tmp/kfp_features.parquet"
        )

        # Step 2: Training & MLflow Logging
        train_results = train_and_evaluate_component(
            feature_parquet_path=feature_parquet,
            n_estimators=100,
            learning_rate=0.08,
            max_depth=5,
            experiment_name=self.experiment_name
        )

        # Step 3: Gate Validation
        passed_gate = validate_and_register_component(
            metrics=train_results,
            max_acceptable_rmse=4.5,
            min_acceptable_r2=0.85
        )

        return {
            "pipeline_status": "COMPLETED",
            "feature_parquet": feature_parquet,
            "train_results": train_results,
            "passed_gate": passed_gate
        }


if __name__ == "__main__":
    pipeline = KubeflowETAPipeline()
    pipeline.run_local_simulation()
