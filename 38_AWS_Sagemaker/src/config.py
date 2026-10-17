import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent


class AWSConfig(BaseModel):
    region: str = "us-east-1"
    s3_bucket: str = "sagemaker-mobile-price-classification-mlops"
    s3_prefix: str = "sagemaker/mobile_price_classification"
    role_arn: Optional[str] = None


class PipelineConfig(BaseModel):
    name: str = "MobilePriceClassificationPipeline"
    base_job_prefix: str = "mobile-price-pipe"
    model_package_group_name: str = "MobilePriceClassificationModelPackageGroup"
    model_approval_status: str = "PendingManualApproval"


class ComputeConfig(BaseModel):
    processing_instance_type: str = "ml.m5.large"
    processing_instance_count: int = 1
    training_instance_type: str = "ml.m5.large"
    training_instance_count: int = 1
    inference_instance_type: str = "ml.m5.large"
    inference_instance_count: int = 1
    use_spot_instances: bool = True
    max_run_seconds: int = 3600
    max_wait_seconds: int = 7200


class ServerlessInferenceConfig(BaseModel):
    enabled: bool = False
    memory_size_in_mb: int = 2048
    max_concurrency: int = 5


class DataCaptureConfig(BaseModel):
    enabled: bool = True
    sampling_percentage: int = 100
    destination_s3_prefix: str = "datacapture"


class AppConfig(BaseModel):
    aws: AWSConfig
    pipeline: PipelineConfig
    compute: ComputeConfig
    serverless_inference: ServerlessInferenceConfig
    data_capture: DataCaptureConfig


class DatasetConfig(BaseModel):
    target_column: str = "price_range"
    id_column: Optional[str] = None
    features: List[str]
    target_classes: Dict[int, str]


class SplitConfig(BaseModel):
    train_ratio: float = 0.70
    validation_ratio: float = 0.15
    test_ratio: float = 0.15
    random_state: int = 42


class HyperparametersConfig(BaseModel):
    n_estimators: int = 150
    max_depth: int = 15
    min_samples_split: int = 4
    min_samples_leaf: int = 2
    random_state: int = 42
    criterion: str = "gini"


class QualityGateConfig(BaseModel):
    min_accuracy_threshold: float = 0.85
    min_f1_macro_threshold: float = 0.83


class ModelConfig(BaseModel):
    dataset: DatasetConfig
    split: SplitConfig
    hyperparameters: HyperparametersConfig
    quality_gate: QualityGateConfig


def load_app_config(config_path: Optional[Path] = None) -> AppConfig:
    """Load application configuration from YAML with environment overrides."""
    if config_path is None:
        config_path = PROJECT_ROOT / "configs" / "config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    cfg = AppConfig(**data)

    # Environment variable overrides
    if env_role := os.environ.get("SAGEMAKER_ROLE_ARN"):
        cfg.aws.role_arn = env_role
    if env_region := os.environ.get("AWS_DEFAULT_REGION"):
        cfg.aws.region = env_region
    if env_bucket := os.environ.get("S3_BUCKET_NAME"):
        cfg.aws.s3_bucket = env_bucket

    return cfg


def load_model_config(config_path: Optional[Path] = None) -> ModelConfig:
    """Load model and dataset configuration from YAML."""
    if config_path is None:
        config_path = PROJECT_ROOT / "configs" / "model_config.yaml"

    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    return ModelConfig(**data)
