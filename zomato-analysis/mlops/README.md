# Zomato & Uber MLOps Platform (MLflow & Kubeflow)

This directory houses the production Machine Learning Operations (MLOps) architecture, designed for distributed experiment tracking, feature engineering, real-time/batch inference, drift monitoring, and Kubernetes-native workflow orchestration.

---

## Architecture Overview

```
                      [ Raw Data Sources ]
           Snowflake RAW / Azure Event Hubs / Lakehouse
                               │
                               ▼
        ┌──────────────────────────────────────────────┐
        │        1. MLOps Feature Store                │
        │  • mlops/feature_store/spatial_features.py   │
        │  • mlops/feature_store/temporal_features.py  │
        │  • mlops/feature_store/feature_pipeline.py   │
        └──────────────────────┬───────────────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌──────────────────────────────┐     ┌──────────────────────────────┐
│  2. MLflow Training Pipeline │     │ 3. Kubeflow Orchestration    │
│  • train_eta_mlflow.py       │     │ • components.py              │
│  • Autologging & Metrics     │     │ • pipeline.py                │
│  • Model Signature & Skops   │     │ • compile_pipeline.py        │
│  • Model Registry Promotion  │     │ • kfp_pipeline.yaml          │
└──────────────┬───────────────┘     └──────────────┬───────────────┘
               │                                    │
               └─────────────────┬──────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Inference & Monitoring                                   │
│  • mlops/inference/batch_predictor.py (Snowflake / S3)      │
│  • ai/databricks_eventhub_ml_stream.py (Spark Streaming)    │
│  • mlops/monitoring/data_drift_detector.py (PSI Auditing)   │
└─────────────────────────────────────────────────────────────┘
```

---

## Quickstart Commands

### 1. Train Model with MLflow Experiment Tracking
```bash
# Run training on local lakehouse data with MLflow tracking
python mlops/training/train_eta_mlflow.py

# Ingest live from Snowflake RAW:
python mlops/training/train_eta_mlflow.py --snowflake
```

### 2. Launch MLflow Tracking UI
```bash
mlflow ui --backend-store-uri sqlite:///mlops/mlflow.db --port 5001
```
Navigate to `http://localhost:5001` to view runs, parameters, metrics (RMSE, MAE, R²), and registered model artifacts.

### 3. Run Batch Scoring with Champion Model
```bash
python -c "
import pandas as pd
from mlops.inference.batch_predictor import BatchPredictor
predictor = BatchPredictor()
df = pd.read_json('data/kafka_order_events.jsonl', lines=True).head(10)
scored = predictor.predict(df)
print(scored[['order_id', 'predicted_delivery_eta_mins', 'eta_confidence_score']])
"
```

### 4. Monitor Feature Drift (PSI)
```bash
python -c "
import pandas as pd
from mlops.monitoring.data_drift_detector import DataDriftDetector
from mlops.feature_store.feature_pipeline import FeaturePipeline

df = pd.read_json('data/kafka_order_events.jsonl', lines=True)
p = FeaturePipeline()
feat = p.transform(df)
detector = DataDriftDetector()
report = detector.evaluate_features_drift(feat, feat, FeaturePipeline.FEATURE_COLUMNS)
print('Drift Status:', report['overall_status'])
"
```

### 5. Compile Kubeflow Pipeline (KFP v2)
```bash
python mlops/pipelines/kubeflow/compile_pipeline.py
```
Output: `mlops/pipelines/kubeflow/kfp_zomato_eta_pipeline.yaml` (Ready for upload to Kubeflow UI or Argo).
