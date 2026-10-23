"""Custom telemetry metrics recorder for Logfire and LangSmith."""

import time
import logfire


class LatencyTracker:
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = None

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.perf_counter() - self.start_time) * 1000
        status = "error" if exc_type else "success"
        logfire.info(
            f"⏱️ {self.operation_name} completed in {duration_ms:.2f}ms | status={status}",
            duration_ms=duration_ms,
            operation=self.operation_name,
            status=status,
        )
