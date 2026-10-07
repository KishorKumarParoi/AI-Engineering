#!/usr/bin/env python3
"""
Kubeflow Pipeline Compiler: Colorectal Cancer Survival Prediction
Compiles the end-to-end MLOps workflow into a production Kubeflow Pipelines v2 YAML specification.
"""

import sys
import yaml
from pathlib import Path

OUTPUT_YAML = Path(__file__).resolve().parent / "colorectal_cancer_pipeline.yaml"


def generate_declarative_pipeline_spec() -> dict:
    """
    Constructs the declarative Kubeflow Pipelines / Argo Workflow specification.
    """
    return {
        "apiVersion": "argoproj.io/v1alpha1",
        "kind": "Workflow",
        "metadata": {
            "generateName": "colorectal-cancer-survival-pipeline-",
            "annotations": {
                "pipelines.kubeflow.org/pipeline_name": "colorectal-cancer-survival-mlops",
                "pipelines.kubeflow.org/pipeline_version": "1.0.0",
                "mlflow.tracking.uri": "https://dagshub.com/kishorkumarparoi/AI-Engineering.mlflow"
            },
            "labels": {
                "tier": "mlops-pipeline",
                "app": "colorectal-cancer-survival",
                "engine": "kubeflow-pipelines"
            }
        },
        "spec": {
            "entrypoint": "colorectal-cancer-dag",
            "serviceAccountName": "pipeline-runner",
            "arguments": {
                "parameters": [
                    {
                        "name": "raw-data-path",
                        "value": "/app/data/data.csv"
                    },
                    {
                        "name": "n-estimators",
                        "value": "100"
                    },
                    {
                        "name": "learning-rate",
                        "value": "0.1"
                    },
                    {
                        "name": "max-depth",
                        "value": "3"
                    },
                    {
                        "name": "mlflow-tracking-uri",
                        "value": "https://dagshub.com/kishorkumarparoi/AI-Engineering.mlflow"
                    }
                ]
            },
            "templates": [
                {
                    "name": "colorectal-cancer-dag",
                    "dag": {
                        "tasks": [
                            {
                                "name": "data-processing-and-chi2",
                                "template": "data-processing-step",
                                "arguments": {
                                    "parameters": [
                                        {"name": "raw-data-path", "value": "{{workflow.parameters.raw-data-path}}"}
                                    ]
                                }
                            },
                            {
                                "name": "split-and-scale",
                                "template": "split-scale-step",
                                "dependencies": ["data-processing-and-chi2"]
                            },
                            {
                                "name": "train-and-log-mlflow",
                                "template": "train-step",
                                "dependencies": ["split-and-scale"],
                                "arguments": {
                                    "parameters": [
                                        {"name": "n-estimators", "value": "{{workflow.parameters.n-estimators}}"},
                                        {"name": "learning-rate", "value": "{{workflow.parameters.learning-rate}}"},
                                        {"name": "max-depth", "value": "{{workflow.parameters.max-depth}}"},
                                        {"name": "mlflow-tracking-uri", "value": "{{workflow.parameters.mlflow-tracking-uri}}"}
                                    ]
                                }
                            },
                            {
                                "name": "validate-production-gate",
                                "template": "gate-step",
                                "dependencies": ["train-and-log-mlflow"]
                            }
                        ]
                    }
                },
                {
                    "name": "data-processing-step",
                    "inputs": {
                        "parameters": [{"name": "raw-data-path"}]
                    },
                    "container": {
                        "image": "kishorkumarparoi/colorectal-cancer-pipeline:latest",
                        "command": ["python", "-c"],
                        "args": [
                            "from ops.kubeflow.components import preprocess_and_select_features; "
                            "preprocess_and_select_features('{{inputs.parameters.raw-data-path}}', '/pipeline/artifacts/processed')"
                        ],
                        "resources": {
                            "requests": {"cpu": "500m", "memory": "1Gi"},
                            "limits": {"cpu": "2000m", "memory": "4Gi"}
                        },
                        "volumeMounts": [
                            {"name": "artifacts", "mountPath": "/pipeline/artifacts"}
                        ]
                    }
                },
                {
                    "name": "split-scale-step",
                    "container": {
                        "image": "kishorkumarparoi/colorectal-cancer-pipeline:latest",
                        "command": ["python", "-c"],
                        "args": [
                            "from ops.kubeflow.components import split_and_scale_features; "
                            "split_and_scale_features('/pipeline/artifacts/processed/processed_selected.csv', '/pipeline/artifacts/split')"
                        ],
                        "resources": {
                            "requests": {"cpu": "500m", "memory": "1Gi"},
                            "limits": {"cpu": "1000m", "memory": "2Gi"}
                        },
                        "volumeMounts": [
                            {"name": "artifacts", "mountPath": "/pipeline/artifacts"}
                        ]
                    }
                },
                {
                    "name": "train-step",
                    "inputs": {
                        "parameters": [
                            {"name": "n-estimators"},
                            {"name": "learning-rate"},
                            {"name": "max-depth"},
                            {"name": "mlflow-tracking-uri"}
                        ]
                    },
                    "container": {
                        "image": "kishorkumarparoi/colorectal-cancer-pipeline:latest",
                        "command": ["python", "-c"],
                        "args": [
                            "from ops.kubeflow.components import train_gradient_boosting_model; "
                            "train_gradient_boosting_model("
                            "'/pipeline/artifacts/split', "
                            "'/pipeline/artifacts/models', "
                            "int('{{inputs.parameters.n-estimators}}'), "
                            "float('{{inputs.parameters.learning-rate}}'), "
                            "int('{{inputs.parameters.max-depth}}'), "
                            "'{{inputs.parameters.mlflow-tracking-uri}}')"
                        ],
                        "resources": {
                            "requests": {"cpu": "1000m", "memory": "2Gi"},
                            "limits": {"cpu": "4000m", "memory": "8Gi"}
                        },
                        "volumeMounts": [
                            {"name": "artifacts", "mountPath": "/pipeline/artifacts"}
                        ]
                    }
                },
                {
                    "name": "gate-step",
                    "container": {
                        "image": "kishorkumarparoi/colorectal-cancer-pipeline:latest",
                        "command": ["python", "-c"],
                        "args": [
                            "from ops.kubeflow.components import evaluate_and_production_gate; "
                            "res = evaluate_and_production_gate('/pipeline/artifacts/models'); "
                            "assert res['is_approved'], 'Pipeline Gate Failed: Model does not meet quality criteria!'"
                        ],
                        "volumeMounts": [
                            {"name": "artifacts", "mountPath": "/pipeline/artifacts"}
                        ]
                    }
                }
            ],
            "volumes": [
                {
                    "name": "artifacts",
                    "persistentVolumeClaim": {
                        "claimName": "mlops-artifacts-pvc"
                    }
                }
            ]
        }
    }


def compile_pipeline() -> Path:
    """
    Compiles and writes pipeline specification to YAML file.
    """
    spec = generate_declarative_pipeline_spec()
    with open(OUTPUT_YAML, "w") as f:
        yaml.dump(spec, f, sort_keys=False)
    print(f"[✓] Kubeflow Pipeline compiled successfully: {OUTPUT_YAML}")
    return OUTPUT_YAML


if __name__ == "__main__":
    compile_pipeline()
