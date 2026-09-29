"""
Nexus-AI: Cloud Storage Adapter — Abstract Base
=================================================
Strategy Pattern for cloud-agnostic storage operations.
Each cloud provider implements this interface, so switching from
local DuckDB to GCP BigQuery requires zero code changes — only a config flag.

Design Decision: This is the same pattern used by Netflix's data platform
for multi-cloud abstraction. Business logic stays cloud-agnostic.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

import pandas as pd


class CloudStorageAdapter(ABC):
    """
    Abstract base class for cloud storage operations.

    All Medallion ETL pipeline operations go through this interface.
    Implementations:
      - LocalStorageAdapter  → DuckDB + Parquet files (zero-cost demo)
      - GCPStorageAdapter    → GCS + BigQuery
      - AWSStorageAdapter    → S3 + Athena
      - AzureStorageAdapter  → ADLS Gen2 + Synapse
    """

    @abstractmethod
    def write_dataframe(
        self,
        df: pd.DataFrame,
        layer: str,
        table_name: str,
        mode: str = "overwrite",
    ) -> str:
        """
        Write a DataFrame to the specified Medallion layer.

        Args:
            df: The DataFrame to write
            layer: Medallion layer ("bronze", "silver", "gold")
            table_name: Name of the table/file
            mode: "overwrite" or "append"

        Returns:
            The storage path/URI where data was written
        """
        ...

    @abstractmethod
    def read_table(
        self,
        layer: str,
        table_name: str,
        columns: list[str] | None = None,
        filters: dict[str, Any] | None = None,
    ) -> pd.DataFrame:
        """
        Read a table from the specified Medallion layer.

        Args:
            layer: Medallion layer ("bronze", "silver", "gold")
            table_name: Name of the table/file
            columns: Optional list of columns to select
            filters: Optional dict of column:value filters

        Returns:
            DataFrame with the requested data
        """
        ...

    @abstractmethod
    def execute_sql(self, query: str) -> pd.DataFrame:
        """
        Execute a SQL query against the storage backend.

        Args:
            query: SQL query string

        Returns:
            DataFrame with query results
        """
        ...

    @abstractmethod
    def list_tables(self, layer: str) -> list[str]:
        """
        List all tables in a Medallion layer.

        Args:
            layer: Medallion layer ("bronze", "silver", "gold")

        Returns:
            List of table names
        """
        ...

    @abstractmethod
    def table_exists(self, layer: str, table_name: str) -> bool:
        """Check if a table exists in the specified layer."""
        ...

    @abstractmethod
    def get_row_count(self, layer: str, table_name: str) -> int:
        """Get the number of rows in a table."""
        ...

    @abstractmethod
    def get_schema(self, layer: str, table_name: str) -> dict[str, str]:
        """Get the schema (column name → type mapping) of a table."""
        ...

    def get_storage_info(self) -> dict[str, str]:
        """Return metadata about the current storage backend."""
        return {
            "adapter": self.__class__.__name__,
            "provider": getattr(self, "provider_name", "unknown"),
        }
