"""
Prometheus & OpenTelemetry Metrics for Zomato Streaming & Lakehouse Systems.
"""

from prometheus_client import Counter, Histogram, Gauge

# Orders & Ingestion
ORDERS_PROCESSED = Counter(
    "zomato_orders_processed_total",
    "Total orders processed across stream and lakehouse",
    ["city", "status"]
)

ORDER_LATENCY = Histogram(
    "zomato_order_latency_seconds",
    "End-to-end processing latency for orders",
    buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0]
)

FEATURE_FRESHNESS = Gauge(
    "zomato_feature_freshness_seconds",
    "Time delta between feature event occurrence and online store ingestion",
    ["feature_view"]
)

DATA_CONTRACT_VIOLATIONS = Counter(
    "zomato_data_contract_violations_total",
    "Total dropped payloads failing schema data contracts",
    ["source_topic", "violation_type"]
)

DISPUTES_RESOLVED = Counter(
    "zomato_disputes_auto_resolved_total",
    "Total multimodal vision disputes resolved",
    ["decision", "category"]
)
