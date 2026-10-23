"""Prometheus metrics endpoint exporter."""

import time

_START_TIME = time.time()

def get_system_metrics() -> str:
    """Format basic uptime metrics in Prometheus text exposition format."""
    uptime_sec = time.time() - _START_TIME
    return f"""# HELP app_uptime_seconds Total application uptime in seconds
# TYPE app_uptime_seconds counter
app_uptime_seconds {uptime_sec:.2f}
# HELP app_status Current application status (1 = healthy)
# TYPE app_status gauge
app_status 1.0
"""
