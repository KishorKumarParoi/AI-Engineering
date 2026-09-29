"""
Nexus-AI: Unified Medallion ETL Pipeline Orchestrator
=======================================================
Single entry point that executes the complete ETL flow:

    Bronze (Raw Ingestion) → Silver (Clean/Validate) → Gold (Aggregate/Features)

Usage:
    python -m etl.pipeline --provider=local --input-dir=data/raw
    python -m etl.pipeline --provider=gcp --input-dir=data/raw --bucket=my-bucket
"""

import argparse
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Add project root for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from etl.bronze.ingest import ingest_to_bronze
from etl.gold.aggregate import run_gold_aggregations
from etl.gold.feature_store import build_features_delivery_eta
from etl.silver.quality_checks import run_quality_checks
from etl.silver.transform import run_silver_transforms
from etl.storage import get_storage_adapter


def run_pipeline(
    input_dir: str = "data/raw",
    provider: str = "local",
    data_dir: str = "data",
    batch_id: str | None = None,
    skip_quality: bool = False,
    **provider_kwargs,
) -> dict:
    """
    Execute the complete Medallion ETL pipeline.

    Args:
        input_dir: Directory containing raw CSV files
        provider: Cloud provider ("local", "gcp", "aws", "azure")
        data_dir: Base directory for Parquet storage (local mode)
        batch_id: Optional batch ID for idempotent replay
        skip_quality: Skip Silver quality checks
        **provider_kwargs: Provider-specific config (bucket, project_id, etc.)

    Returns:
        Complete pipeline execution report
    """
    start_time = time.time()

    if batch_id is None:
        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    print("\n" + "▓" * 60)
    print(f"  🚀 NEXUS-AI MEDALLION ETL PIPELINE")
    print(f"  Provider: {provider.upper()} │ Batch: {batch_id}")
    print("▓" * 60)

    # ── Initialize Storage Adapter ───────────────────────────────────
    adapter = get_storage_adapter(provider, base_dir=data_dir, **provider_kwargs)
    storage_info = adapter.get_storage_info()
    print(f"\n  🗄️  Storage: {storage_info.get('engine', storage_info.get('adapter'))}")

    # ── PHASE 1: BRONZE — Raw Ingestion ──────────────────────────────
    bronze_results = ingest_to_bronze(
        source_dir=input_dir,
        storage_adapter=adapter,
        batch_id=batch_id,
    )

    # ── PHASE 2: SILVER — Clean & Transform ──────────────────────────
    silver_results = run_silver_transforms(adapter)

    # ── PHASE 2.5: QUALITY GATE ──────────────────────────────────────
    quality_results = []
    if not skip_quality:
        quality_results = run_quality_checks(adapter)
        failed_checks = [r for r in quality_results if not r.passed]
        if failed_checks:
            print(f"\n  ⚠️  {len(failed_checks)} quality checks failed (non-blocking)")

    # ── PHASE 3: GOLD — Aggregate & Feature Store ────────────────────
    gold_results = run_gold_aggregations(adapter)

    # ── PHASE 3.5: ML Feature Store ──────────────────────────────────
    feature_df = build_features_delivery_eta(adapter)

    # ── Pipeline Summary ─────────────────────────────────────────────
    elapsed = time.time() - start_time

    # Count totals
    bronze_total = sum(r.get("rows", 0) for r in bronze_results.values())
    silver_total = sum(r.get("silver_rows", 0) for r in silver_results.values())
    gold_total = sum(r.get("rows", 0) for r in gold_results.values())
    quality_passed = sum(1 for r in quality_results if r.passed) if quality_results else 0
    quality_total = len(quality_results)

    print("\n" + "▓" * 60)
    print(f"  ✅ MEDALLION ETL PIPELINE COMPLETE")
    print("▓" * 60)
    print(f"  ┌─────────────────────────────────────────────┐")
    print(f"  │ Bronze (Raw):     {bronze_total:>8,} rows ingested      │")
    print(f"  │ Silver (Clean):   {silver_total:>8,} rows validated     │")
    print(f"  │ Gold (Business):  {gold_total:>8,} rows aggregated    │")
    print(f"  │ Feature Store:    {len(feature_df):>8,} ML samples       │")
    print(f"  │ Quality Checks:   {quality_passed}/{quality_total} passed              │")
    print(f"  │ Duration:         {elapsed:>8.1f}s                    │")
    print(f"  │ Provider:         {provider.upper():<26s}     │")
    print(f"  └─────────────────────────────────────────────┘")

    # List all Gold tables for Agent queries
    gold_tables = adapter.list_tables("gold")
    if gold_tables:
        print(f"\n  📋 Gold Tables Available for Agent Queries:")
        for table in sorted(gold_tables):
            rows = adapter.get_row_count("gold", table)
            print(f"     • gold_{table} ({rows:,} rows)")

    report = {
        "status": "SUCCESS",
        "batch_id": batch_id,
        "provider": provider,
        "duration_seconds": round(elapsed, 2),
        "bronze": bronze_results,
        "silver": silver_results,
        "gold": gold_results,
        "feature_store": {
            "table": "features_delivery_eta_v1",
            "rows": len(feature_df),
            "columns": list(feature_df.columns),
        },
        "quality": {
            "total_checks": quality_total,
            "passed": quality_passed,
            "failed": quality_total - quality_passed,
        },
    }

    return report


def main():
    parser = argparse.ArgumentParser(
        description="Nexus-AI: Run Medallion ETL Pipeline (Bronze → Silver → Gold)"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="local",
        choices=["local", "gcp", "aws", "azure"],
        help="Cloud storage provider (default: local)",
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default="data/raw",
        help="Directory containing raw CSV files (default: data/raw)",
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data",
        help="Base directory for Parquet storage (default: data)",
    )
    parser.add_argument(
        "--batch-id",
        type=str,
        default=None,
        help="Custom batch ID for this run",
    )
    parser.add_argument(
        "--skip-quality",
        action="store_true",
        help="Skip Silver quality checks",
    )
    parser.add_argument(
        "--bucket",
        type=str,
        default=None,
        help="Cloud storage bucket name (for gcp/aws/azure)",
    )
    args = parser.parse_args()

    kwargs = {}
    if args.bucket:
        kwargs["bucket"] = args.bucket

    report = run_pipeline(
        input_dir=args.input_dir,
        provider=args.provider,
        data_dir=args.data_dir,
        batch_id=args.batch_id,
        skip_quality=args.skip_quality,
        **kwargs,
    )

    return report


if __name__ == "__main__":
    main()
