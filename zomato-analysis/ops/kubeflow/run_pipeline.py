#!/usr/bin/env python3
"""
Kubeflow Pipeline Runner: Submits or executes the Colorectal Cancer Survival pipeline.
Supports remote cluster submission via KFP Client and local DAG simulation runner.
"""

import os
import sys
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ops.kubeflow.pipeline import run_local_pipeline_execution
from ops.kubeflow.compile_pipeline import compile_pipeline, OUTPUT_YAML


def submit_to_kfp_cluster(endpoint: str, experiment_name: str = "colorectal-cancer-survival"):
    """
    Submits compiled pipeline YAML to an active Kubeflow Pipelines cluster.
    """
    try:
        import kfp
        client = kfp.Client(host=endpoint)
        print(f"[*] Connecting to Kubeflow Pipelines at: {endpoint}")

        if not OUTPUT_YAML.exists():
            compile_pipeline()

        run = client.create_run_from_pipeline_package(
            pipeline_file=str(OUTPUT_YAML),
            arguments={
                "raw-data-path": "/pipeline/data/data.csv",
                "n-estimators": "100",
                "learning-rate": "0.1",
                "max-depth": "3"
            },
            run_name="colorectal-cancer-kfp-run",
            experiment_name=experiment_name
        )
        print(f"[✓] Pipeline Run submitted successfully! Run ID: {run.run_id}")
        return run
    except ImportError:
        print("[!] 'kfp' Python package not installed. Running local pipeline simulation instead...")
        return run_local_pipeline_execution()
    except Exception as e:
        print(f"[!] Cluster submission failed ({e}). Falling back to local pipeline execution...")
        return run_local_pipeline_execution()


def main():
    parser = argparse.ArgumentParser(description="Run or submit Colorectal Cancer Survival MLOps Pipeline")
    parser.add_argument("--remote", action="store_true", help="Submit to remote Kubeflow cluster")
    parser.add_argument("--endpoint", default=os.getenv("KFP_ENDPOINT", "http://localhost:8080"), help="KFP cluster endpoint")
    parser.add_argument("--compile-only", action="store_true", help="Only compile pipeline YAML")
    args = parser.parse_args()

    if args.compile_only:
        compile_pipeline()
        return

    if args.remote:
        submit_to_kfp_cluster(args.endpoint)
    else:
        # Default: execute complete local pipeline run
        raw_data = PROJECT_ROOT / "1. ALL MATERIAL - 5 - NEW" / "DATA" / "data.csv"
        run_local_pipeline_execution(
            raw_data_path=str(raw_data),
            artifacts_dir=str(PROJECT_ROOT / "ops" / "artifacts")
        )


if __name__ == "__main__":
    main()
