"""
Kubeflow Pipeline Components: Colorectal Cancer Survival Prediction
Modular, container-ready component definitions matching MLOps Project 5.
"""

import os
import json
from pathlib import Path

def preprocess_and_select_features(
    raw_data_path: str,
    output_processed_dir: str,
    max_rows: int = None
) -> dict:
    """
    KFP Component 1: Ingestion, Label Encoding, and Chi-Square Feature Selection.
    """
    import os
    import pandas as pd
    import numpy as np
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import LabelEncoder
    from sklearn.feature_selection import SelectKBest, chi2

    os.makedirs(output_processed_dir, exist_ok=True)
    print(f"[*] Ingesting raw dataset from: {raw_data_path} (max_rows: {max_rows or 'ALL'})")
    df = pd.read_csv(raw_data_path, nrows=max_rows)

    if "Patient_ID" in df.columns:
        df = df.drop(columns=["Patient_ID"])

    X = df.drop(columns=["Survival_Prediction"])
    y = df["Survival_Prediction"]

    # Encode categorical columns
    categorical_cols = X.select_dtypes(include=["object"]).columns
    label_encoders = {}
    for col in categorical_cols:
        le = LabelEncoder()
        X[col] = le.fit_transform(X[col])
        label_encoders[col] = le

    # Stratified split for chi2 feature selection
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=42)
    numeric_features = X_train.select_dtypes(include=["int64", "float64"])

    chi2_selector = SelectKBest(score_func=chi2, k="all")
    chi2_selector.fit(numeric_features, y_train)

    chi2_scores = pd.DataFrame({
        "Feature": numeric_features.columns,
        "Score": chi2_selector.scores_
    }).sort_values(by="Score", ascending=False)

    top_features = chi2_scores.head(5)["Feature"].tolist()
    print(f"[✓] Selected Top 5 Chi-Square Features: {top_features}")

    selected_X = X[top_features]
    processed_df = selected_X.copy()
    processed_df["Survival_Prediction"] = y.values

    processed_file = os.path.join(output_processed_dir, "processed_selected.csv")
    processed_df.to_csv(processed_file, index=False)

    return {
        "status": "success",
        "processed_file": processed_file,
        "selected_features": top_features,
        "total_records": len(processed_df)
    }


def split_and_scale_features(
    processed_file: str,
    output_dir: str,
    test_size: float = 0.2,
    random_state: int = 42
) -> dict:
    """
    KFP Component 2: Stratified Train-Test Split and StandardScaler Transformation.
    """
    import os
    import joblib
    import pandas as pd
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    os.makedirs(output_dir, exist_ok=True)
    df = pd.read_csv(processed_file)

    X = df.drop(columns=["Survival_Prediction"])
    y = df["Survival_Prediction"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Save artifacts
    joblib.dump(X_train_scaled, os.path.join(output_dir, "X_train.pkl"))
    joblib.dump(X_test_scaled, os.path.join(output_dir, "X_test.pkl"))
    joblib.dump(y_train, os.path.join(output_dir, "y_train.pkl"))
    joblib.dump(y_test, os.path.join(output_dir, "y_test.pkl"))
    joblib.dump(scaler, os.path.join(output_dir, "scaler.pkl"))

    print(f"[✓] Data split & scaling complete: Train={len(X_train)}, Test={len(X_test)}")
    return {
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "scaler_path": os.path.join(output_dir, "scaler.pkl")
    }


def train_gradient_boosting_model(
    split_dir: str,
    model_output_dir: str,
    n_estimators: int = 100,
    learning_rate: float = 0.1,
    max_depth: int = 3,
    mlflow_tracking_uri: str = "https://dagshub.com/kishorkumarparoi/AI-Engineering.mlflow"
) -> dict:
    """
    KFP Component 3: GradientBoosting Classifier Training & MLflow Experiment Tracking.
    """
    import os
    import joblib
    from sklearn.ensemble import GradientBoostingClassifier
    from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
    import mlflow
    import mlflow.sklearn

    os.makedirs(model_output_dir, exist_ok=True)
    X_train = joblib.load(os.path.join(split_dir, "X_train.pkl"))
    X_test = joblib.load(os.path.join(split_dir, "X_test.pkl"))
    y_train = joblib.load(os.path.join(split_dir, "y_train.pkl"))
    y_test = joblib.load(os.path.join(split_dir, "y_test.pkl"))

    # Resilient MLflow Tracking: Remote DagsHub or Local SQLite Fallback
    try:
        if mlflow_tracking_uri and not mlflow_tracking_uri.startswith("sqlite"):
            mlflow.set_tracking_uri(mlflow_tracking_uri)
            mlflow.set_experiment("colorectal-cancer-survival-prediction")
            print(f"[*] Connected to MLflow Tracking Server: {mlflow_tracking_uri}")
        else:
            raise ValueError("Using local tracking store")
    except Exception as e:
        local_db = os.path.abspath(os.path.join(model_output_dir, "..", "mlflow.db"))
        mlflow.set_tracking_uri(f"sqlite:///{local_db}")
        mlflow.set_experiment("colorectal-cancer-survival-prediction")
        print(f"[*] MLflow Tracking initialized with local store: sqlite:///{local_db}")

    with mlflow.start_run(run_name="kubeflow-kfp-training") as run:
        # Log Hyperparameters
        mlflow.log_params({
            "n_estimators": n_estimators,
            "learning_rate": learning_rate,
            "max_depth": max_depth,
            "random_state": 42
        })

        model = GradientBoostingClassifier(
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            max_depth=max_depth,
            random_state=42
        )
        model.fit(X_train, y_train)

        # Predictions & Metrics
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1] if len(set(y_test)) == 2 else None

        accuracy = float(accuracy_score(y_test, y_pred))
        precision = float(precision_score(y_test, y_pred, average="weighted", zero_division=0))
        recall = float(recall_score(y_test, y_pred, average="weighted", zero_division=0))
        f1 = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

        mlflow.log_metric("accuracy", accuracy)
        mlflow.log_metric("precision", precision)
        mlflow.log_metric("recall", recall)
        mlflow.log_metric("f1_score", f1)

        metrics = {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1_score": f1
        }

        if y_proba is not None:
            roc_auc = float(roc_auc_score(y_test, y_proba))
            mlflow.log_metric("roc_auc", roc_auc)
            metrics["roc_auc"] = roc_auc

        model_path = os.path.join(model_output_dir, "model.pkl")
        joblib.dump(model, model_path)
        mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="gradient_boosting_model",
            serialization_format="cloudpickle"
        )

        metrics_path = os.path.join(model_output_dir, "metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=2)

        print(f"[✓] Model trained and saved to: {model_path}")
        print(f"    Metrics: Accuracy={accuracy:.4f}, F1={f1:.4f}")

        return {
            "run_id": run.info.run_id,
            "model_path": model_path,
            "metrics": metrics
        }


def evaluate_and_production_gate(
    model_output_dir: str,
    min_accuracy: float = 0.70,
    min_f1: float = 0.65
) -> dict:
    """
    KFP Component 4: Production Quality Gate Verification.
    """
    import os
    import json

    metrics_file = os.path.join(model_output_dir, "metrics.json")
    with open(metrics_file, "r") as f:
        metrics = json.load(f)

    acc = metrics.get("accuracy", 0.0)
    f1 = metrics.get("f1_score", 0.0)

    passed = (acc >= min_accuracy) and (f1 >= min_f1)
    status = "APPROVED_FOR_PRODUCTION" if passed else "REJECTED_BELOW_GATE"

    gate_result = {
        "status": status,
        "is_approved": passed,
        "gate_criteria": {
            "min_accuracy": min_accuracy,
            "min_f1": min_f1
        },
        "achieved_metrics": metrics
    }

    gate_file = os.path.join(model_output_dir, "production_gate.json")
    with open(gate_file, "w") as f:
        json.dump(gate_result, f, indent=2)

    print(f"[★] Gate Evaluation: {status} (Acc: {acc:.4f}, F1: {f1:.4f})")
    return gate_result
