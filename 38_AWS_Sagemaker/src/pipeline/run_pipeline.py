#!/usr/bin/env python3
"""
CLI runner and orchestrator for SageMaker Pipeline.

Supports:
1. --build-only: Compiles the pipeline DAG and exports JSON schema (works offline!).
2. --upsert: Creates or updates the pipeline in AWS SageMaker.
3. --execute: Starts execution of the pipeline on AWS.
4. --local-simulation: Runs preprocessing, training, and evaluation sequentially locally.
"""

import argparse
import json
import logging
import os
import sys
import subprocess
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("run-pipeline")


def build_pipeline_definition(output_file: str = "artifacts/pipeline_definition.json"):
    """Compile pipeline definition to JSON without requiring AWS infrastructure."""
    logger.info("Compiling SageMaker Pipeline definition...")

    # Set mock AWS environment variables so SageMaker SDK does not fail if no AWS config exists
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
    os.environ.setdefault("SAGEMAKER_SUPPRESS_V2_WARNING", "1")

    from src.pipeline.sagemaker_pipeline import get_pipeline
    from src.config import load_app_config, load_model_config

    app_cfg = load_app_config()
    model_cfg = load_model_config()

    pipeline = get_pipeline(app_config=app_cfg, model_config=model_cfg)
    definition_json = pipeline.definition()

    # Pretty print JSON
    parsed = json.loads(definition_json)
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2)

    logger.info("Pipeline compiled successfully!")
    logger.info("Total steps in pipeline DAG: %d", len(parsed.get("Steps", [])))
    for step in parsed.get("Steps", []):
        logger.info("  - Step [%s]: Type=%s", step.get("Name"), step.get("Type"))
    logger.info("Exported JSON definition to: %s", output_file)
    return parsed


def upsert_and_execute_pipeline(execute: bool = False):
    """Upsert pipeline definition to AWS and optionally trigger execution."""
    logger.info("Connecting to AWS SageMaker to upsert pipeline...")
    from src.pipeline.sagemaker_pipeline import get_pipeline
    from src.config import load_app_config

    app_cfg = load_app_config()
    if not app_cfg.aws.role_arn:
        raise ValueError(
            "SAGEMAKER_ROLE_ARN must be set in environment or config.yaml to upsert/execute on AWS."
        )

    pipeline = get_pipeline(app_config=app_cfg)
    response = pipeline.upsert(role_arn=app_cfg.aws.role_arn)
    logger.info("Pipeline upserted successfully: %s", response["PipelineArn"])

    if execute:
        logger.info("Triggering pipeline execution on AWS SageMaker...")
        execution = pipeline.start()
        logger.info("Pipeline execution started: %s", execution.arn)
        return execution
    return response


def run_local_simulation():
    """Simulate the end-to-end ML lifecycle on local machine."""
    logger.info("=== STARTING LOCAL MLOPS PIPELINE SIMULATION ===")
    python_exe = sys.executable

    # 1. Preprocessing
    logger.info("Step 1/3: Running Preprocessing...")
    cmd_prep = [
        python_exe, "src/processing/preprocess.py",
        "--input-data", "data/raw/mob_price_classification_train.csv",
        "--train-dir", "data/processed/train",
        "--val-dir", "data/processed/validation",
        "--test-dir", "data/processed/test",
        "--baseline-dir", "data/baseline",
    ]
    subprocess.run(cmd_prep, check=True)

    # 2. Training
    logger.info("Step 2/3: Running Model Training...")
    cmd_train = [
        python_exe, "src/training/train.py",
        "--train", "data/processed/train",
        "--validation", "data/processed/validation",
        "--model-dir", "artifacts/model",
    ]
    subprocess.run(cmd_train, check=True)

    # 3. Evaluation
    logger.info("Step 3/3: Running Model Evaluation...")
    cmd_eval = [
        python_exe, "src/evaluation/evaluate.py",
        "--model-path", "artifacts/model/model.joblib",
        "--test-data", "data/processed/test/test.csv",
        "--output-dir", "artifacts/evaluation",
    ]
    subprocess.run(cmd_eval, check=True)

    # 4. Gating Check
    eval_file = "artifacts/evaluation/evaluation.json"
    with open(eval_file, "r", encoding="utf-8") as f:
        metrics = json.load(f)

    accuracy = metrics["multiclass_classification_metrics"]["accuracy"]["value"]
    logger.info("Evaluation Complete. Model Holdout Accuracy: %0.4f", accuracy)

    threshold = 0.85
    if accuracy >= threshold:
        logger.info(">>> QUALITY GATE PASSED (Accuracy %0.4f >= Threshold %0.4f). Model approved for deployment!", accuracy, threshold)
    else:
        logger.warning(">>> QUALITY GATE FAILED (Accuracy %0.4f < Threshold %0.4f). Model rejected.", accuracy, threshold)


def main():
    parser = argparse.ArgumentParser(description="SageMaker Pipeline Orchestrator CLI")
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="Compile pipeline DAG and export definition JSON without AWS credentials",
    )
    parser.add_argument(
        "--upsert",
        action="store_true",
        help="Upload/update pipeline definition to AWS SageMaker",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Start execution of pipeline on AWS SageMaker",
    )
    parser.add_argument(
        "--local-simulation",
        action="store_true",
        help="Run preprocessing, training, and evaluation locally",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="artifacts/pipeline_definition.json",
        help="Output path for compiled pipeline JSON",
    )

    args = parser.parse_args()

    if args.local_simulation:
        run_local_simulation()
    elif args.upsert or args.execute:
        upsert_and_execute_pipeline(execute=args.execute)
    else:
        # Default action: build only
        build_pipeline_definition(output_file=args.output)


if __name__ == "__main__":
    main()
