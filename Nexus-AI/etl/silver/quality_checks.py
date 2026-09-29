"""
Nexus-AI: Silver Layer — Data Quality Checks
===============================================
Automated quality assertions for Silver layer data.
Inspired by Great Expectations but implemented as lightweight,
dependency-free checks that run as part of the ETL pipeline.

Each check returns:
    {"check": str, "table": str, "passed": bool, "details": str}

Design Decision: We use lightweight custom checks instead of full
Great Expectations to keep the local demo zero-dependency and fast.
In production, these would map to Great Expectations Expectations.
"""

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class QualityCheckResult:
    """Result of a single quality check."""

    check_name: str
    table_name: str
    passed: bool
    details: str
    metric_value: Any = None
    threshold: Any = None


def check_null_rate(df: pd.DataFrame, column: str, max_null_pct: float = 5.0) -> QualityCheckResult:
    """Assert that null rate for a column is below threshold."""
    null_pct = (df[column].isna().sum() / len(df)) * 100
    return QualityCheckResult(
        check_name=f"null_rate_{column}",
        table_name="",
        passed=null_pct <= max_null_pct,
        details=f"Null rate: {null_pct:.2f}% (max: {max_null_pct}%)",
        metric_value=round(null_pct, 2),
        threshold=max_null_pct,
    )


def check_value_range(
    df: pd.DataFrame, column: str, min_val: float, max_val: float
) -> QualityCheckResult:
    """Assert that all values in a column fall within [min_val, max_val]."""
    values = pd.to_numeric(df[column], errors="coerce").dropna()
    out_of_range = ((values < min_val) | (values > max_val)).sum()
    return QualityCheckResult(
        check_name=f"range_{column}",
        table_name="",
        passed=out_of_range == 0,
        details=f"{out_of_range} values out of [{min_val}, {max_val}]",
        metric_value=int(out_of_range),
        threshold=0,
    )


def check_unique(df: pd.DataFrame, column: str) -> QualityCheckResult:
    """Assert that all values in a column are unique."""
    dupes = df[column].duplicated().sum()
    return QualityCheckResult(
        check_name=f"unique_{column}",
        table_name="",
        passed=dupes == 0,
        details=f"{dupes} duplicate values found",
        metric_value=int(dupes),
        threshold=0,
    )


def check_not_empty(df: pd.DataFrame) -> QualityCheckResult:
    """Assert that the table has at least 1 row."""
    return QualityCheckResult(
        check_name="not_empty",
        table_name="",
        passed=len(df) > 0,
        details=f"Row count: {len(df)}",
        metric_value=len(df),
        threshold=1,
    )


def check_categorical_values(
    df: pd.DataFrame, column: str, allowed_values: set[str]
) -> QualityCheckResult:
    """Assert that all values in a column are from an allowed set."""
    actual = set(df[column].dropna().unique())
    invalid = actual - allowed_values
    return QualityCheckResult(
        check_name=f"categorical_{column}",
        table_name="",
        passed=len(invalid) == 0,
        details=f"Invalid values: {invalid}" if invalid else "All values valid",
        metric_value=len(invalid),
        threshold=0,
    )


def check_referential_integrity(
    child_df: pd.DataFrame,
    child_col: str,
    parent_df: pd.DataFrame,
    parent_col: str,
) -> QualityCheckResult:
    """Assert FK integrity — all child values exist in parent."""
    child_vals = set(child_df[child_col].dropna().unique())
    parent_vals = set(parent_df[parent_col].dropna().unique())
    orphans = child_vals - parent_vals
    return QualityCheckResult(
        check_name=f"fk_{child_col}_ref_{parent_col}",
        table_name="",
        passed=len(orphans) == 0,
        details=f"{len(orphans)} orphan values (sample: {list(orphans)[:3]})" if orphans else "FK integrity OK",
        metric_value=len(orphans),
        threshold=0,
    )


# ── Quality Check Suites ─────────────────────────────────────────────────

def run_quality_checks(storage_adapter) -> list[QualityCheckResult]:
    """
    Execute all quality check suites against Silver layer tables.

    Returns list of QualityCheckResult objects.
    """
    results: list[QualityCheckResult] = []

    print(f"\n{'='*60}")
    print(f"🔍 [QUALITY GATE] Running Silver Layer Data Quality Checks")
    print(f"{'='*60}")

    # ── Restaurant Quality Checks ────────────────────────────────────
    try:
        restaurants = storage_adapter.read_table("silver", "clean_restaurants")

        checks = [
            check_not_empty(restaurants),
            check_unique(restaurants, "restaurant_id"),
            check_null_rate(restaurants, "name", max_null_pct=1.0),
            check_null_rate(restaurants, "latitude", max_null_pct=2.0),
            check_null_rate(restaurants, "longitude", max_null_pct=2.0),
            check_value_range(restaurants, "rating", 1.0, 5.0),
            check_value_range(restaurants, "latitude", -90, 90),
            check_value_range(restaurants, "longitude", -180, 180),
            check_value_range(restaurants, "avg_cost_for_two", 0, 50000),
        ]
        for c in checks:
            c.table_name = "clean_restaurants"
        results.extend(checks)

    except FileNotFoundError:
        print("  ⚠️  clean_restaurants not found, skipping checks")

    # ── Order Quality Checks ─────────────────────────────────────────
    try:
        orders = storage_adapter.read_table("silver", "clean_orders")

        checks = [
            check_not_empty(orders),
            check_unique(orders, "order_id"),
            check_null_rate(orders, "order_time", max_null_pct=1.0),
            check_null_rate(orders, "total_amount", max_null_pct=0.5),
            check_value_range(orders, "total_amount", 0, 100000),
            check_value_range(orders, "items_count", 1, 50),
            check_categorical_values(
                orders, "order_status",
                {"Delivered", "Cancelled", "Returned", "In Transit", "Preparing", "Unknown"},
            ),
            check_categorical_values(
                orders, "payment_method",
                {"UPI", "Credit Card", "Debit Card", "Cash on Delivery", "Wallet"},
            ),
        ]
        for c in checks:
            c.table_name = "clean_orders"
        results.extend(checks)

        # FK: orders.restaurant_id → restaurants.restaurant_id
        try:
            restaurants = storage_adapter.read_table("silver", "clean_restaurants")
            fk_check = check_referential_integrity(orders, "restaurant_id", restaurants, "restaurant_id")
            fk_check.table_name = "clean_orders"
            results.append(fk_check)
        except FileNotFoundError:
            pass

    except FileNotFoundError:
        print("  ⚠️  clean_orders not found, skipping checks")

    # ── Delivery Quality Checks ──────────────────────────────────────
    try:
        deliveries = storage_adapter.read_table("silver", "clean_deliveries")

        checks = [
            check_not_empty(deliveries),
            check_unique(deliveries, "delivery_id"),
            check_value_range(deliveries, "distance_km", 0.1, 50.0),
            check_value_range(deliveries, "actual_eta_min", 5, 300),
            check_value_range(deliveries, "estimated_eta_min", 5, 300),
            check_value_range(deliveries, "delivery_rating", 1.0, 5.0),
            check_null_rate(deliveries, "distance_km", max_null_pct=1.0),
            check_categorical_values(
                deliveries, "weather_condition",
                {"Clear", "Cloudy", "Rain", "Heavy Rain", "Storm", "Fog"},
            ),
            check_categorical_values(
                deliveries, "traffic_level",
                {"Low", "Medium", "High", "Jam"},
            ),
        ]
        for c in checks:
            c.table_name = "clean_deliveries"
        results.extend(checks)

    except FileNotFoundError:
        print("  ⚠️  clean_deliveries not found, skipping checks")

    # ── Review Quality Checks ────────────────────────────────────────
    try:
        reviews = storage_adapter.read_table("silver", "clean_reviews")

        checks = [
            check_not_empty(reviews),
            check_unique(reviews, "review_id"),
            check_value_range(reviews, "rating", 1.0, 5.0),
            check_value_range(reviews, "helpful_votes", 0, 1000),
            check_null_rate(reviews, "review_text", max_null_pct=5.0),
        ]
        for c in checks:
            c.table_name = "clean_reviews"
        results.extend(checks)

    except FileNotFoundError:
        print("  ⚠️  clean_reviews not found, skipping checks")

    # ── Summary ──────────────────────────────────────────────────────
    passed = sum(1 for r in results if r.passed)
    failed = sum(1 for r in results if not r.passed)

    for r in results:
        status = "✅" if r.passed else "❌"
        print(f"  {status} {r.table_name}.{r.check_name}: {r.details}")

    print(f"\n  📊 Quality Gate: {passed}/{len(results)} checks passed", end="")
    if failed > 0:
        print(f" ({failed} FAILED)")
    else:
        print(" ✅ ALL PASSED")

    return results
