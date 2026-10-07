"""
Kubeflow Pipeline DAG: Colorectal Cancer Survival Prediction MLOps Workflow
Chains data ingestion, feature selection, scaling, model training, and gate validation.
"""

from ops.kubeflow.components import (
    preprocess_and_select_features,
    split_and_scale_features,
    train_gradient_boosting_model,
    evaluate_and_production_gate,
)

def run_local_pipeline_execution(
    raw_data_path: str = "1. ALL MATERIAL - 5 - NEW/DATA/data.csv",
    artifacts_dir: str = "ops/artifacts",
    n_estimators: int = 100,
    learning_rate: float = 0.1,
    max_depth: int = 3,
    mlflow_tracking_uri: str = "https://dagshub.com/kishorkumarparoi/AI-Engineering.mlflow",
    max_rows: int = 15000
) -> dict:
    """
    Executes the end-to-end pipeline locally following the exact Kubeflow DAG sequence.
    """
    import os

    processed_dir = os.path.join(artifacts_dir, "processed")
    split_dir = os.path.join(artifacts_dir, "split")
    models_dir = os.path.join(artifacts_dir, "models")

    os.makedirs(artifacts_dir, exist_ok=True)

    print("\n==========================================================")
    print("   KUBEFLOW PIPELINE EXECUTION: COLORECTAL SURVIVAL       ")
    print("==========================================================")

    # Step 1: Preprocess and Chi2 Feature Selection
    print("\n[STEP 1/4] Running Data Processing & Chi-Square Feature Selection...")
    step1_out = preprocess_and_select_features(raw_data_path, processed_dir, max_rows=max_rows)

    # Step 2: Split and Scale
    print("\n[STEP 2/4] Running Stratified Train/Test Split & StandardScaler...")
    step2_out = split_and_scale_features(step1_out["processed_file"], split_dir)

    # Step 3: Train GradientBoosting & Log to MLflow
    print("\n[STEP 3/4] Running GradientBoosting Training & MLflow Logging...")
    step3_out = train_gradient_boosting_model(
        split_dir=split_dir,
        model_output_dir=models_dir,
        n_estimators=n_estimators,
        learning_rate=learning_rate,
        max_depth=max_depth,
        mlflow_tracking_uri=mlflow_tracking_uri
    )

    # Step 4: Production Quality Gate
    print("\n[STEP 4/4] Validating Model against Production Quality Gate...")
    step4_out = evaluate_and_production_gate(models_dir)

    print("\n==========================================================")
    print(f"   PIPELINE COMPLETED: {step4_out['status']}")
    print("==========================================================\n")

    return {
        "step1": step1_out,
        "step2": step2_out,
        "step3": step3_out,
        "step4": step4_out
    }

if __name__ == "__main__":
    run_local_pipeline_execution()
