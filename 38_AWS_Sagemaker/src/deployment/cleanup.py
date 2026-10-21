#!/usr/bin/env python3
"""
SageMaker Endpoint and Resource Teardown Script.

Prevents unnecessary AWS cloud bills by cleanly terminating:
1. SageMaker Endpoints
2. SageMaker Endpoint Configurations
3. SageMaker Models
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("cleanup")


def cleanup_endpoint(endpoint_name: str, region: str = "us-east-1"):
    """Delete endpoint, endpoint config, and matching model from AWS."""
    sm_client = boto3.client("sagemaker", region_name=region)
    logger.info("Initiating teardown for endpoint: %s in %s...", endpoint_name, region)

    # 1. Delete Endpoint
    try:
        sm_client.delete_endpoint(EndpointName=endpoint_name)
        logger.info("Successfully deleted Endpoint: %s", endpoint_name)
    except ClientError as e:
        logger.warning("Endpoint deletion error: %s", e)

    # 2. Delete Endpoint Config
    try:
        sm_client.delete_endpoint_config(EndpointConfigName=endpoint_name)
        logger.info("Successfully deleted EndpointConfig: %s", endpoint_name)
    except ClientError as e:
        logger.warning("EndpointConfig deletion error: %s", e)

    # 3. Delete Model (if matching name)
    try:
        sm_client.delete_model(ModelName=endpoint_name)
        logger.info("Successfully deleted Model: %s", endpoint_name)
    except ClientError as e:
        logger.warning("Model deletion error: %s", e)

    logger.info("Cleanup process finished.")


def main():
    parser = argparse.ArgumentParser(description="Clean up SageMaker Endpoint resources")
    parser.add_argument("--endpoint-name", type=str, required=True, help="Endpoint name to delete")
    parser.add_argument("--region", type=str, default="us-east-1", help="AWS Region")

    args = parser.parse_args()
    cleanup_endpoint(endpoint_name=args.endpoint_name, region=args.region)


if __name__ == "__main__":
    main()
