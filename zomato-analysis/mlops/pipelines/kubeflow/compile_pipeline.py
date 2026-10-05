#!/usr/bin/env python3
"""
Kubeflow Pipeline Compiler
Compiles the Zomato Delivery ETA MLOps workflow into a production KFP v2 pipeline YAML specification.
"""

import sys
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUTPUT_YAML = Path(__file__).resolve().parent / "kfp_zomato_eta_pipeline.yaml"


def generate_kfp_pipeline_spec() -> dict:
    """
    Constructs the declarative Kubeflow Pipelines v2 DAG specification.
    """
    pipeline_spec = {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "Workflow",
        "metadata": {
            "generateName": "zomato-eta-training-pipeline-",
            "annotations": {
                "pipelines.kubeflow.org/pipeline_name": "zomato-delivery-eta-mlops",
                "pipelines.kubeflow.org/pipeline_version": "2.4.0",
                "mlflow.tracking.uri": "http://mlflow.internal:5000"
            },
            "labels": {
                "tier": "principal-mlops",
                "app": "zomato-eta-prediction",
                "engine": "kubeflow-pipelines"
            }
        },
        "spec": {
            "entrypoint": "zomato-eta-dag",
            "serviceAccountName": "pipeline-runner",
            "templates": [
                {
                    "name": "zomato-eta-dag",
                    "dag": {
                        "tasks": [
                            {
                                "name": "extract-features",
                                "template": "extract-features-step"
                            },
                            {
                                "name": "train-and-evaluate",
                                "template": "train-eval-step",
                                "dependencies": ["extract-features"]
                            },
                            {
                                "name": "validate-model-gate",
                                "template": "validate-gate-step",
                                "dependencies": ["train-and-evaluate"]
                            },
                            {
                                "name": "deploy-or-register",
                                "template": "deploy-step",
                                "dependencies": ["validate-model-gate"]
                            }
                        ]
                    }
                },
                {
                    "name": "extract-features-step",
                    "container": {
                        "image": "zomato-mlops:latest",
                        "command": ["python", "-m", "mlops.pipelines.kubeflow.components"],
                        "args": ["--action", "extract_features"],
                        "resources": {
                            "requests": {"cpu": "2000m", "memory": "4Gi"},
                            "limits": {"cpu": "4000m", "memory": "8Gi"}
                        }
                    }
                },
                {
                    "name": "train-eval-step",
                    "container": {
                        "image": "zomato-mlops:latest",
                        "command": ["python", "-m", "mlops.training.train_eta_mlflow"],
                        "args": ["--snowflake"],
                        "resources": {
                            "requests": {"cpu": "4000m", "memory": "8Gi"},
                            "limits": {"cpu": "8000m", "memory": "16Gi"}
                        },
                        "env": [
                            {"name": "MLFLOW_TRACKING_URI", "value": "http://mlflow-service.mlflow:5000"},
                            {"name": "MLFLOW_EXPERIMENT_NAME", "value": "zomato-kfp-eta-pipeline"}
                        ]
                    }
                },
                {
                    "name": "validate-gate-step",
                    "container": {
                        "image": "zomato-mlops:latest",
                        "command": ["python", "-m", "mlops.pipelines.kubeflow.components"],
                        "args": ["--action", "validate_gate"],
                        "resources": {
                            "requests": {"cpu": "1000m", "memory": "2Gi"},
                            "limits": {"cpu": "2000m", "memory": "4Gi"}
                        }
                    }
                },
                {
                    "name": "deploy-step",
                    "container": {
                        "image": "zomato-mlops:latest",
                        "command": ["python", "-m", "mlops.inference.batch_predictor"],
                        "resources": {
                            "requests": {"cpu": "2000m", "memory": "4Gi"},
                            "limits": {"cpu": "4000m", "memory": "8Gi"}
                        }
                    }
                }
            ]
        }
    }
    return pipeline_spec


def main():
    print(f"[*] Compiling Kubeflow Pipeline (KFP v2) to: {OUTPUT_YAML}...")
    spec = generate_kfp_pipeline_spec()
    with open(OUTPUT_YAML, "w") as f:
        yaml.dump(spec, f, sort_keys=False, default_flow_style=False)
    print(f"[✓] Kubeflow Pipeline successfully compiled: {OUTPUT_YAML}")
    print(f"    • DAG Steps: extract-features -> train-and-evaluate -> validate-model-gate -> deploy-or-register")
    print(f"    • Ready for deployment via Kubeflow UI, kfp CLI, or Argo Workflows.")


if __name__ == "__main__":
    main()
