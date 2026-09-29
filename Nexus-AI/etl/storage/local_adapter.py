"""
Nexus-AI: Local Storage Adapter (DuckDB + Parquet)
====================================================
Zero-cost local implementation of CloudStorageAdapter.
Uses DuckDB for analytical queries and Parquet for persistence.

This is the DEFAULT adapter for local demo mode (./run_all.sh --mode=local).
Identical SQL semantics as BigQuery/Athena, enabling seamless cloud migration.
"""

from pathlib import Path
from typing import Any

import duckdb
import pandas as pd

from etl.storage.base import CloudStorageAdapter


class LocalStorageAdapter(CloudStorageAdapter):
    """
    Local storage using DuckDB (in-memory or file-backed) + Parquet files.

    Why DuckDB?
    - OLAP-optimized: Same columnar semantics as BigQuery/Athena
    - Zero infrastructure: No server needed, embedded in-process
    - SQL compatibility: Standard SQL works identically across DuckDB/BQ/Athena
    - Parquet-native: Direct read/write without serialization overhead
    """

    provider_name = "local"

    def __init__(self, base_dir: str = "data", db_path: str | None = None):
        """
        Initialize local storage adapter.

        Args:
            base_dir: Base directory for Parquet file storage
            db_path: Path to DuckDB database file (None = in-memory)
        """
        self.base_dir = Path(base_dir)
        self.db_path = db_path or str(self.base_dir / "nexus_ai.duckdb")

        # Create layer directories
        for layer in ("bronze", "silver", "gold"):
            (self.base_dir / layer).mkdir(parents=True, exist_ok=True)

        # Initialize DuckDB connection
        self.conn = duckdb.connect(self.db_path)
        self.conn.execute("SET threads TO 4")
        self.conn.execute("SET memory_limit = '2GB'")

    def _layer_path(self, layer: str, table_name: str) -> Path:
        """Get the Parquet file path for a table in a layer."""
        return self.base_dir / layer / f"{table_name}.parquet"

    def _register_if_exists(self, layer: str, table_name: str) -> str:
        """Register a Parquet file as a DuckDB view if it exists."""
        view_name = f"{layer}_{table_name}"
        parquet_path = self._layer_path(layer, table_name)
        if parquet_path.exists():
            self.conn.execute(
                f"CREATE OR REPLACE VIEW {view_name} AS "
                f"SELECT * FROM read_parquet('{parquet_path}')"
            )
        return view_name

    def write_dataframe(
        self,
        df: pd.DataFrame,
        layer: str,
        table_name: str,
        mode: str = "overwrite",
    ) -> str:
        """Write DataFrame as Parquet and register as DuckDB view."""
        parquet_path = self._layer_path(layer, table_name)

        if mode == "append" and parquet_path.exists():
            existing = pd.read_parquet(parquet_path)
            df = pd.concat([existing, df], ignore_index=True)

        df.to_parquet(parquet_path, index=False, engine="pyarrow")

        # Register as view for SQL access
        view_name = f"{layer}_{table_name}"
        self.conn.execute(
            f"CREATE OR REPLACE VIEW {view_name} AS "
            f"SELECT * FROM read_parquet('{parquet_path}')"
        )

        print(f"  📝 [{layer.upper()}] {table_name}: {len(df):,} rows → {parquet_path}")
        return str(parquet_path)

    def read_table(
        self,
        layer: str,
        table_name: str,
        columns: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """Read a table from Parquet, optionally with column/filter selection."""
        parquet_path = self._layer_path(layer, table_name)
        if not parquet_path.exists():
            raise FileNotFoundError(
                f"Table '{table_name}' not found in {layer} layer at {parquet_path}"
            )

        # Build SQL query for efficient reads
        col_clause = ", ".join(columns) if columns else "*"
        query = f"SELECT {col_clause} FROM read_parquet('{parquet_path}')"

        if filters:
            conditions = []
            for col, val in filters.items():
                if isinstance(val, str):
                    conditions.append(f"{col} = '{val}'")
                elif isinstance(val, (list, tuple)):
                    vals = ", ".join(f"'{v}'" if isinstance(v, str) else str(v) for v in val)
                    conditions.append(f"{col} IN ({vals})")
                else:
                    conditions.append(f"{col} = {val}")
            query += " WHERE " + " AND ".join(conditions)

        return self.conn.execute(query).fetchdf()

    def execute_sql(self, query: str) -> pd.DataFrame:
        """Execute arbitrary SQL against registered views."""
        # Auto-register all existing Parquet files as views
        for layer in ("bronze", "silver", "gold"):
            layer_dir = self.base_dir / layer
            if layer_dir.exists():
                for parquet_file in layer_dir.glob("*.parquet"):
                    table_name = parquet_file.stem
                    self._register_if_exists(layer, table_name)

        return self.conn.execute(query).fetchdf()

    def list_tables(self, layer: str) -> list[str]:
        """List all Parquet tables in a layer."""
        layer_dir = self.base_dir / layer
        if not layer_dir.exists():
            return []
        return [f.stem for f in layer_dir.glob("*.parquet")]

    def table_exists(self, layer: str, table_name: str) -> bool:
        """Check if a Parquet file exists for the table."""
        return self._layer_path(layer, table_name).exists()

    def get_row_count(self, layer: str, table_name: str) -> int:
        """Count rows in a table using DuckDB."""
        parquet_path = self._layer_path(layer, table_name)
        if not parquet_path.exists():
            return 0
        result = self.conn.execute(
            f"SELECT COUNT(*) FROM read_parquet('{parquet_path}')"
        ).fetchone()
        return result[0] if result else 0

    def get_schema(self, layer: str, table_name: str) -> dict[str, str]:
        """Get column names and types from Parquet metadata."""
        parquet_path = self._layer_path(layer, table_name)
        if not parquet_path.exists():
            return {}
        result = self.conn.execute(
            f"DESCRIBE SELECT * FROM read_parquet('{parquet_path}')"
        ).fetchdf()
        return dict(zip(result["column_name"], result["column_type"]))

    def get_storage_info(self) -> dict[str, str]:
        """Return metadata about the local storage backend."""
        return {
            "adapter": "LocalStorageAdapter",
            "provider": "local",
            "engine": "DuckDB + Parquet",
            "base_dir": str(self.base_dir.resolve()),
            "db_path": self.db_path,
        }

    def close(self):
        """Close the DuckDB connection."""
        self.conn.close()

    def __del__(self):
        """Ensure connection is closed on garbage collection."""
        try:
            self.close()
        except Exception:
            pass
