"""
Nexus-AI: Bronze Layer — Raw Ingestion with Audit Metadata
============================================================
Ingests raw CSV files into the Bronze layer with full data lineage:
- _ingested_at:  Timestamp of ingestion
- _source_file:  Original filename
- _batch_id:     Unique batch identifier for idempotent replay
- _raw_hash:     SHA-256 hash of the original row (for dedup in Silver)

Design Decision: Bronze layer preserves raw data EXACTLY as received,
with only audit columns added. No cleaning, no transformations.
This enables full reproducibility and lineage tracing.
"""

import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from etl.bronze.schemas import (
    BRONZE_SCHEMAS,
    validate_bronze_schema,
)


def _compute_row_hash(row: pd.Series) -> str:
    """Compute SHA-256 hash of a row for deduplication tracking."""
    raw_str = "|".join(str(v) for v in row.values)
    return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()[:16]


def ingest_to_bronze(
    source_dir: str | Path,
    storage_adapter,
    batch_id: str | None = None,
) -> dict[str, dict]:
    """
    Ingest all raw CSV files from source_dir into the Bronze layer.

    Each file gets:
    1. Audit columns appended (_ingested_at, _source_file, _batch_id, _raw_hash)
    2. Written as Parquet via the storage adapter
    3. Schema validation against expected column lists

    Args:
        source_dir: Directory containing raw CSV files
        storage_adapter: CloudStorageAdapter instance
        batch_id: Optional batch identifier (auto-generated if None)

    Returns:
        Dict mapping table_name -> {rows, path, columns, status}
    """
    source_path = Path(source_dir)
    if not source_path.exists():
        raise FileNotFoundError(f"Source directory not found: {source_path}")

    if batch_id is None:
        batch_id = f"batch_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

    ingested_at = datetime.now(timezone.utc).isoformat()

    # Map CSV filenames to Bronze table names
    file_table_map = {
        "restaurants.csv": "raw_restaurants",
        "orders.csv": "raw_orders",
        "deliveries.csv": "raw_deliveries",
        "reviews.csv": "raw_reviews",
    }

    results = {}
    total_rows = 0

    print(f"\n{'='*60}")
    print(f"📦 [BRONZE LAYER] Raw Ingestion (Batch: {batch_id})")
    print(f"{'='*60}")

    for csv_filename, table_name in file_table_map.items():
        csv_path = source_path / csv_filename
        if not csv_path.exists():
            print(f"  ⚠️  Skipping {csv_filename} (not found)")
            results[table_name] = {"status": "skipped", "reason": "file_not_found"}
            continue

        # Read raw CSV
        df = pd.read_csv(csv_path, dtype=str)  # Read everything as string to preserve raw data
        original_rows = len(df)

        # Add audit columns
        df["_ingested_at"] = ingested_at
        df["_source_file"] = csv_filename
        df["_batch_id"] = batch_id
        df["_raw_hash"] = df.apply(_compute_row_hash, axis=1)

        # Validate schema
        schema_name = csv_filename.replace(".csv", "")
        validation = validate_bronze_schema(df, schema_name)
        if not validation["valid"]:
            print(f"  ⚠️  Schema warning for {csv_filename}: {validation['issues']}")

        # Write to storage
        path = storage_adapter.write_dataframe(df, "bronze", table_name)

        results[table_name] = {
            "status": "ingested",
            "rows": original_rows,
            "columns": list(df.columns),
            "path": path,
            "schema_valid": validation["valid"],
        }
        total_rows += original_rows

        print(f"  ✅ {table_name:<25s} │ {original_rows:>7,} rows │ {len(df.columns)} cols │ schema: {'✓' if validation['valid'] else '⚠'}")

    print(f"\n  📊 Bronze Total: {total_rows:,} rows across {len([r for r in results.values() if r.get('status') == 'ingested'])} tables")
    return results
