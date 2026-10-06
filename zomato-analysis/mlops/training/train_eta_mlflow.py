#!/usr/bin/env python3
"""
Zomato & Uber Enterprise: MLflow Model Training Pipeline
Trains high-precision Dynamic ETA Regression models with MLflow Tracking & Model Registry.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
from sklearn.ensemble import GradientBoostingRegressor
import mlflow
import mlflow.sklearn
from mlflow.models.signature import infer_signature

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from mlops.feature_store.feature_pipeline import FeaturePipeline
from mlops.training.config import TrainingConfig


def load_dataset(use_snowflake: bool = False) -> pd.DataFrame:
    """
    Loads authentic order data from Snowflake or fallback local lakehouse file.
    """
    if use_snowflake:
        try:
            import snowflake.connector
            from dotenv import load_dotenv
            load_dotenv()

            user = os.getenv("SNOWFLAKE_USERNAME") or os.getenv("SNOWFLAKE_USER")
            pwd = os.getenv("SNOWFLAKE_PASSWORD")
            account = os.getenv("SNOWFLAKE_ACCOUNT")
            wh = os.getenv("SNOWFLAKE_WAREHOUSE", "ZOMATO_WH")
            db = os.getenv("SNOWFLAKE_DATABASE", "ZOMATO")

            if all([user, pwd, account]):
                print(f"[*] Connecting to Snowflake: {account} (DB: {db})...")
                ctx = snowflake.connector.connect(
                    user=user, password=pwd, account=account, warehouse=wh, database=db, schema="RAW"
                )
                query = """
                    SELECT 
                        ORDER_ID, CUSTOMER_ID, RESTAURANT_ID, RESTAURANT_NAME, 
                        FOOD_NAME, CUISINE, CITY, ORDER_AMOUNT, DELIVERY_FEE, 
                        ITEM_COUNT, RESTAURANT_LAT, RESTAURANT_LNG, 
                        DELIVERY_LAT, DELIVERY_LNG, EVENT_TIMESTAMP
                    FROM ZOMATO.RAW.KAFKA_ORDER_EVENTS
                    ORDER BY INGESTED_AT DESC
                    LIMIT 10000;
                """
                df = pd.read_sql(query, ctx)
                df.columns = [c.lower() for c in df.columns]
                ctx.close()
                if len(df) > 0:
                    print(f"[✓] Loaded {len(df)} authentic records from Snowflake RAW.")
                    return df
        except Exception as e:
            print(f"[!] Snowflake connection bypass: {e}")

    # Fallback to local lakehouse file
    local_path = PROJECT_ROOT / "data" / "kafka_order_events.jsonl"
    if local_path.exists():
        print(f"[*] Loading data from local event lakehouse: {local_path}...")
        records = []
        with open(local_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        if records:
            df = pd.DataFrame(records)
            print(f"[✓] Loaded {len(df)} records from {local_path}.")
            return df

    # Synthetic fallback bootstrap if no events exist yet
    print("[*] Generating bootstrap lakehouse records for model cold-start...")
    np.random.seed(42)
    cuisines = ["Biryani", "North Indian", "Chinese", "Continental", "Burgers", "Pizzas"]
    cities = ["Bangalore", "Mumbai", "Delhi", "Hyderabad"]
    data = []
    for i in range(500):
        c_lat, c_lng = 12.9716, 77.5946
        d_lat = c_lat + np.random.uniform(-0.08, 0.08)
        d_lng = c_lng + np.random.uniform(-0.08, 0.08)
        data.append({
            "order_id": f"ORD-BOOTSTRAP-{i:05d}",
            "cuisine": np.random.choice(cuisines),
            "city": np.random.choice(cities),
            "order_amount": float(np.random.randint(150, 1800)),
            "delivery_fee": float(np.random.choice([30.0, 45.0, 60.0])),
            "item_count": int(np.random.randint(1, 6)),
            "restaurant_lat": c_lat,
            "restaurant_lng": c_lng,
            "delivery_lat": d_lat,
            "delivery_lng": d_lng,
            "event_timestamp": pd.Timestamp.now().isoformat()
        })
    return pd.DataFrame(data)


def train_model(config: TrainingConfig = None, use_snowflake: bool = False):
    """
    Executes the end-to-end MLflow training, evaluation, and registry pipeline.
    """
    if config is None:
        config = TrainingConfig()

    # Initialize DagsHub remote tracking if configured
    user = os.getenv("DAGSHUB_USER_NAME")
    repo = os.getenv("DAGSHUB_REPO_NAME")
    token = os.getenv("DAGSHUB_TOKEN")
    if token:
        os.environ["MLFLOW_TRACKING_USERNAME"] = user or os.getenv("MLFLOW_TRACKING_USERNAME", "")
        os.environ["MLFLOW_TRACKING_PASSWORD"] = token

    if user and repo:
        try:
            import dagshub
            dagshub.init(repo_owner=user, repo_name=repo, mlflow=True)
            print(f"[✓] Connected to DagsHub remote tracking: https://dagshub.com/{user}/{repo}")
        except Exception as de:
            pass

    # Set MLflow Tracking URI and ensure experiment
    mlflow.set_tracking_uri(config.tracking_uri)
    
    exp = mlflow.get_experiment_by_name(config.experiment_name)
    if exp is None:
        if config.tracking_uri.startswith("http"):
            # Remote server (e.g. DagsHub) handles its own artifact location
            mlflow.create_experiment(name=config.experiment_name)
        else:
            Path(config.artifact_location).mkdir(parents=True, exist_ok=True)
            mlflow.create_experiment(
                name=config.experiment_name,
                artifact_location=f"file://{config.artifact_location}"
            )
    mlflow.set_experiment(config.experiment_name)

    print(f"\n========================================================")
    print(f"🚀 MLOps Training Pipeline: {config.experiment_name}")
    print(f"📍 Tracking URI: {config.tracking_uri}")
    print(f"========================================================\n")

    # 1. Ingest Data
    raw_df = load_dataset(use_snowflake=use_snowflake)

    # 2. Feature Engineering via Feature Store Pipeline
    pipeline = FeaturePipeline()
    X = pipeline.transform(raw_df)
    y = pipeline.create_synthetic_ground_truth(X)

    print(f"[*] Features Engineered: {list(X.columns)}")
    print(f"[*] Dataset Shape: {X.shape}, Target Range: [{y.min():.1f}m, {y.max():.1f}m]")

    # 3. Train-Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=config.test_size, random_state=config.random_state
    )

    # 4. Start MLflow Run
    with mlflow.start_run(run_name="gradient-boosted-trees-eta") as run:
        run_id = run.info.run_id
        print(f"[*] MLflow Run Started: ID={run_id}")

        # Log Hyperparameters
        mlflow.log_params(config.model_params)
        mlflow.log_param("test_size", config.test_size)
        mlflow.log_param("num_features", X.shape[1])
        mlflow.log_param("training_samples", len(X_train))

        # Train Gradient Boosting Regressor
        model = GradientBoostingRegressor(**config.model_params)
        model.fit(X_train, y_train)

        # Predictions
        preds = model.predict(X_test)

        # Calculate Industry-Standard Metrics
        rmse = float(np.sqrt(mean_squared_error(y_test, preds)))
        mae = float(mean_absolute_error(y_test, preds))
        r2 = float(r2_score(y_test, preds))
        mape = float(np.mean(np.abs((y_test - preds) / y_test)) * 100)

        # Log Metrics
        mlflow.log_metrics({
            "rmse": rmse,
            "mae": mae,
            "r2_score": r2,
            "mape_pct": mape
        })

        print(f"\n[✓] Evaluation Metrics:")
        print(f"    • RMSE    : {rmse:.3f} mins")
        print(f"    • MAE     : {mae:.3f} mins")
        print(f"    • R² Score: {r2:.4f}")
        print(f"    • MAPE    : {mape:.2f}%\n")

        # Feature Importance Logging
        importance = dict(zip(X.columns, model.feature_importances_.tolist()))
        mlflow.log_dict(importance, "feature_importance.json")

        # Infer Model Signature
        signature = infer_signature(X_train, preds)

        # Log Model with MLflow using standard cloudpickle serialization
        model_info = mlflow.sklearn.log_model(
            sk_model=model,
            artifact_path="eta_model",
            signature=signature,
            registered_model_name=config.model_name,
            serialization_format="cloudpickle"
        )

        print(f"[✓] Model logged: {model_info.model_uri}")

        # Check performance criteria for Production tagging
        is_champion = (rmse <= config.max_acceptable_rmse) and (r2 >= config.min_acceptable_r2)
        if is_champion:
            mlflow.set_tag("deployment_candidate", "true")
            mlflow.set_tag("model_tier", "champion")
            print(f"[★] Champion Performance Gate Passed: Eligible for Production deployment.")
        else:
            mlflow.set_tag("deployment_candidate", "false")
            mlflow.set_tag("model_tier", "challenger")

        return {
            "run_id": run_id,
            "rmse": rmse,
            "mae": mae,
            "r2": r2,
            "model_uri": model_info.model_uri,
            "is_champion": is_champion
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Zomato ETA Prediction Model with MLflow")
    parser.add_argument("--snowflake", action="store_true", help="Ingest training data live from Snowflake RAW")
    args = parser.parse_args()

    train_model(use_snowflake=args.snowflake)
