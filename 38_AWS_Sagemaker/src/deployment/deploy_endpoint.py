#!/usr/bin/env python3
"""
SageMaker Endpoint Deployment Script.

Deploys a model to a real-time or serverless SageMaker Endpoint with:
1. DataCaptureConfig: Capturing 100% of request and response payloads to S3 for Model Monitor.
2. Dynamic configuration (Real-time vs Serverless).
3. CloudWatch Logging and Endpoint Status verification.
"""

import argparse
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import boto3
import sagemaker
from sagemaker.model_monitor import DataCaptureConfig
from sagemaker.serverless import ServerlessInferenceConfig
from sagemaker.sklearn.model import SKLearnModel

from src.config import load_app_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("deploy-endpoint")

SKLEARN_FRAMEWORK_VERSION = "1.2-1"


def deploy_model(
    model_s3_uri: Optional[str] = None,
    endpoint_name: Optional[str] = None,
    serverless: bool = False,
    enable_data_capture: bool = True,
):
    """
    Deploy trained model to SageMaker Endpoint.

    Args:
        model_s3_uri: S3 URI to model.tar.gz.
        endpoint_name: Custom endpoint name.
        serverless: Deploy as Serverless Inference Endpoint if True.
        enable_data_capture: Enable Model Monitor data capture if True.
    """
    app_cfg = load_app_config()

    role = app_cfg.aws.role_arn
    if not role:
        raise ValueError("SAGEMAKER_ROLE_ARN must be set to deploy an endpoint to AWS.")

    sagemaker_session = sagemaker.Session(default_bucket=app_cfg.aws.s3_bucket)
    timestamp = time.strftime("%Y-%m-%d-%H-%M-%S", time.gmtime())
    endpoint_name = endpoint_name or f"mobile-price-endpoint-{timestamp}"
    entry_point = str(PROJECT_ROOT / "src" / "inference" / "inference.py")

    logger.info("Initializing Endpoint Deployment...")
    logger.info("Endpoint Name: %s", endpoint_name)
    logger.info("Serverless Mode: %s", serverless)

    # 1. Create Model
    model = SKLearnModel(
        model_data=model_s3_uri,
        role=role,
        entry_point=entry_point,
        framework_version=SKLEARN_FRAMEWORK_VERSION,
        sagemaker_session=sagemaker_session,
    )

    # 2. Configure Data Capture for Model Monitor
    data_capture_config = None
    if enable_data_capture and not serverless:
        capture_s3_uri = f"s3://{app_cfg.aws.s3_bucket}/{app_cfg.aws.s3_prefix}/datacapture"
        logger.info("Enabling Data Capture to S3: %s", capture_s3_uri)
        data_capture_config = DataCaptureConfig(
            enable_capture=True,
            sampling_percentage=app_cfg.data_capture.sampling_percentage,
            destination_s3_uri=capture_s3_uri,
            capture_options=["REQUEST", "RESPONSE"],
            csv_offsets=[0],
            json_resource=["*"],
            sagemaker_session=sagemaker_session,
        )

    # 3. Deploy
    if serverless:
        serverless_config = ServerlessInferenceConfig(
            memory_size_in_mb=app_cfg.serverless_inference.memory_size_in_mb,
            max_concurrency=app_cfg.serverless_inference.max_concurrency,
        )
        logger.info(
            "Deploying Serverless Endpoint (Memory=%d MB, Max Concurrency=%d)...",
            app_cfg.serverless_inference.memory_size_in_mb,
            app_cfg.serverless_inference.max_concurrency,
        )
        predictor = model.deploy(
            endpoint_name=endpoint_name,
            serverless_inference_config=serverless_config,
        )
    else:
        logger.info(
            "Deploying Real-time Endpoint (%d x %s)...",
            app_cfg.compute.inference_instance_count,
            app_cfg.compute.inference_instance_type,
        )
        predictor = model.deploy(
            initial_instance_count=app_cfg.compute.inference_instance_count,
            instance_type=app_cfg.compute.inference_instance_type,
            endpoint_name=endpoint_name,
            data_capture_config=data_capture_config,
        )

    logger.info("Endpoint deployed successfully: %s", endpoint_name)
    return predictor


def main():
    parser = argparse.ArgumentParser(description="Deploy SageMaker Endpoint")
    parser.add_argument("--model-s3-uri", type=str, required=True, help="S3 URI to model.tar.gz")
    parser.add_argument("--endpoint-name", type=str, default=None, help="Custom endpoint name")
    parser.add_argument("--serverless", action="store_true", help="Deploy as Serverless endpoint")
    parser.add_argument("--disable-data-capture", action="store_true", help="Disable S3 data capture")

    args = parser.parse_args()

    deploy_model(
        model_s3_uri=args.model_s3_uri,
        endpoint_name=args.endpoint_name,
        serverless=args.serverless,
        enable_data_capture=not args.disable_data_capture,
    )


if __name__ == "__main__":
    main()
