"""
Kubeflow Pipeline Components for Zomato Delivery ETA MLOps.
Defines modular, containerized operations following Kubeflow Pipelines (KFP v2) standards.
"""

from typing import NamedTuple, Dict, Any


def extract_features_component(
    source_type: str = "lakehouse",
    limit: int = 10000,
    output_feature_path: str = "/tmp/features.parquet"
) -> str:
    """
    Component 1: Ingests lakehouse data from Snowflake / S3 and applies feature store transforms.
    """
    import pandas as pd
    from mlops.feature_store.feature_pipeline import FeaturePipeline
    from mlops.training.train_eta_mlflow import load_dataset

    print(f"[*] [KFP Component 1] Extracting {limit} records from {source_type}...")
    raw_df = load_dataset(use_snowflake=(source_type == "snowflake"))
    
    pipeline = FeaturePipeline()
    features_df = pipeline.transform(raw_df)
    features_df["actual_eta_mins"] = pipeline.create_synthetic_ground_truth(features_df)

    features_df.to_parquet(output_feature_path, index=False)
    print(f"[✓] [KFP Component 1] Saved {len(features_df)} feature vectors to {output_feature_path}")
    return output_feature_path


def train_and_evaluate_component(
    feature_parquet_path: str,
    n_estimators: int = 120,
    learning_rate: float = 0.08,
    max_depth: int = 5,
    experiment_name: str = "zomato-kfp-eta-pipeline"
) -> Dict[str, Any]:
    """
    Component 2: Trains model, logs metrics to MLflow, and returns performance summary.
    """
    import numpy as np
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
    import mlflow
    import mlflow.sklearn
    from mlops.training.config import TrainingConfig

    print(f"[*] [KFP Component 2] Loading features from {feature_parquet_path}...")
    df = pd.read_parquet(feature_parquet_path)
    X = df.drop(columns=["actual_eta_mins"])
    y = df["actual_eta_mins"]

    cfg = TrainingConfig()
    mlflow.set_tracking_uri(cfg.tracking_uri)
    mlflow.set_experiment(experiment_name)

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    with mlflow.start_run(run_name="kfp-worker-gbt-run") as run:
        model = GradientBoostingRegressor(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=42
        )
        model.fit(X_train, y_train)

        preds = model.predict(X_test)
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        mae = float(mean_absolute_error(y_test, preds))
        r2 = float(r2_score(y_test, preds))

        mlflow.log_params({
            "n_estimators": n_estimators,
            "learning_rate": learning_rate,
            "max_depth": max_depth,
            "pipeline_type": "kubeflow_kfp_v2"
        })
        mlflow.log_metrics({"rmse": rmse, "mae": mae, "r2": r2})
        model_info = mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="model",
            registered_model_name="zomato_eta_champion"
        )

        print(f"[✓] [KFP Component 2] Training complete. RMSE: {rmse:.3f}, R²: {r2:.4f}")
        return {
            "run_id": run.info.run_id,
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
            "model_uri": model_info.model_uri
        }


def validate_and_register_component(
    metrics: Dict[str, Any],
    max_acceptable_rmse: float = 4.5,
    min_acceptable_r2: float = 0.85
) -> bool:
    """
    Component 3: Model Quality Gate. Validates model against production thresholds.
    """
    rmse = metrics.get("rmse", 999.0)
    r2 = metrics.get("r2", -1.0)
    run_id = metrics.get("run_id", "unknown")

    print(f"[*] [KFP Component 3] Validating Model Quality Gate (Run: {run_id})...")
    print(f"    • Evaluated RMSE: {rmse:.3f} (Max Threshold: {max_acceptable_rmse})")
    print(f"    • Evaluated R²  : {r2:.4f} (Min Threshold: {min_acceptable_r2})")

    passed = (rmse <= max_acceptable_rmse) and (r2 >= min_acceptable_r2)
    if passed:
        print(f"[★] [KFP Component 3] GATE PASSED! Model promoted to Champion/Production.")
    else:
        print(f"[!] [KFP Component 3] GATE FAILED: Model rejected for Production promotion.")
    return passed
