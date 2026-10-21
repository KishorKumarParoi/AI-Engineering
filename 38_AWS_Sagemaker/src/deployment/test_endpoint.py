#!/usr/bin/env python3
"""
SageMaker Live Endpoint Testing and Benchmark Script.

Sends single and batch test payloads to the deployed endpoint and
computes latency percentiles (p50, p95).
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import List

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import boto3
import numpy as np
import pandas as pd

from src.config import load_app_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("test-endpoint")

SAMPLE_PAYLOAD = {
    "instances": [
        {
            "battery_power": 842, "blue": 0, "clock_speed": 2.2, "dual_sim": 0,
            "fc": 1, "four_g": 0, "int_memory": 7, "m_dep": 0.6, "mobile_wt": 188,
            "n_cores": 2, "pc": 2, "px_height": 20, "px_width": 756, "ram": 2549,
            "sc_h": 9, "sc_w": 7, "talk_time": 19, "three_g": 0, "touch_screen": 0, "wifi": 1
        },
        {
            "battery_power": 1821, "blue": 1, "clock_speed": 1.2, "dual_sim": 0,
            "fc": 13, "four_g": 1, "int_memory": 44, "m_dep": 0.8, "mobile_wt": 141,
            "n_cores": 6, "pc": 14, "px_height": 1208, "px_width": 1212, "ram": 3911,
            "sc_h": 8, "sc_w": 6, "talk_time": 15, "three_g": 1, "touch_screen": 1, "wifi": 0
        }
    ]
}


def invoke_endpoint(endpoint_name: str, payload: dict, region: str = "us-east-1"):
    """Invoke endpoint using boto3 sagemaker-runtime client."""
    client = boto3.client("sagemaker-runtime", region_name=region)

    body_bytes = json.dumps(payload).encode("utf-8")

    start_time = time.perf_counter()
    response = client.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="application/json",
        Accept="application/json",
        Body=body_bytes,
    )
    latency_ms = (time.perf_counter() - start_time) * 1000

    response_body = response["Body"].read().decode("utf-8")
    result = json.loads(response_body)
    return result, latency_ms


def run_benchmark(endpoint_name: str, iterations: int = 10, region: str = "us-east-1"):
    """Benchmark endpoint latency."""
    logger.info("Benchmarking endpoint '%s' with %d requests...", endpoint_name, iterations)
    latencies = []

    for i in range(iterations):
        result, latency_ms = invoke_endpoint(endpoint_name, SAMPLE_PAYLOAD, region)
        latencies.append(latency_ms)
        logger.info("Request #%d: Latency=%0.2f ms | Predictions: %s", i + 1, latency_ms, result.get("labels"))

    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    mean_lat = np.mean(latencies)

    logger.info("==========================================")
    logger.info("BENCHMARK SUMMARY (%d requests):", iterations)
    logger.info("  Mean Latency: %0.2f ms", mean_lat)
    logger.info("  p50 Latency:  %0.2f ms", p50)
    logger.info("  p95 Latency:  %0.2f ms", p95)
    logger.info("==========================================")


def main():
    parser = argparse.ArgumentParser(description="Test and Benchmark SageMaker Live Endpoint")
    parser.add_argument("--endpoint-name", type=str, required=True, help="Name of deployed endpoint")
    parser.add_argument("--iterations", type=int, default=5, help="Number of test iterations")
    parser.add_argument("--region", type=str, default="us-east-1", help="AWS region")

    args = parser.parse_args()
    run_benchmark(endpoint_name=args.endpoint_name, iterations=args.iterations, region=args.region)


if __name__ == "__main__":
    main()
