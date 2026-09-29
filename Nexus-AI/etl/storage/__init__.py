"""Nexus-AI ETL Storage Package — Cloud Storage Abstraction Layer."""

from etl.storage.base import CloudStorageAdapter
from etl.storage.local_adapter import LocalStorageAdapter


def get_storage_adapter(provider: str = "local", **kwargs) -> CloudStorageAdapter:
    """
    Factory function to create the appropriate storage adapter.

    Args:
        provider: Cloud provider name ("local", "gcp", "aws", "azure")
        **kwargs: Provider-specific configuration

    Returns:
        CloudStorageAdapter instance

    Example:
        adapter = get_storage_adapter("local", base_dir="data")
        adapter = get_storage_adapter("gcp", project_id="my-project", bucket="my-bucket")
    """
    if provider == "local":
        return LocalStorageAdapter(**kwargs)
    elif provider == "gcp":
        # Lazy import to avoid requiring GCP SDK when not needed
        from etl.storage.gcp_adapter import GCPStorageAdapter
        return GCPStorageAdapter(**kwargs)
    elif provider == "aws":
        from etl.storage.aws_adapter import AWSStorageAdapter
        return AWSStorageAdapter(**kwargs)
    elif provider == "azure":
        from etl.storage.azure_adapter import AzureStorageAdapter
        return AzureStorageAdapter(**kwargs)
    else:
        raise ValueError(
            f"Unknown provider: '{provider}'. "
            f"Supported: local, gcp, aws, azure"
        )


__all__ = [
    "CloudStorageAdapter",
    "LocalStorageAdapter",
    "get_storage_adapter",
]
