#!/usr/bin/env python3
"""
SageMaker Pipeline DAG Definition.

Constructs an end-to-end SageMaker Pipeline:
1. ProcessingStep: Preprocessing raw dataset into stratified splits and monitor baseline.
2. TrainingStep: Training RandomForest model using SKLearn Estimator with CloudWatch metrics.
3. ProcessingStep: Model evaluation on holdout test set outputting evaluation.json.
4. ConditionStep: Evaluating model against accuracy threshold.
5. ModelStep (RegisterModel): Registering approved model package into SageMaker Model Registry.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import sagemaker
from sagemaker.inputs import TrainingInput
from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.sklearn.estimator import SKLearn
from sagemaker.sklearn.model import SKLearnModel
from sagemaker.sklearn.processing import SKLearnProcessor
from sagemaker.workflow.condition_step import ConditionStep
from sagemaker.workflow.conditions import ConditionGreaterThanOrEqualTo
from sagemaker.workflow.functions import JsonGet
from sagemaker.workflow.model_step import ModelStep
from sagemaker.workflow.parameters import (
    ParameterFloat,
    ParameterInteger,
    ParameterString,
)
from sagemaker.workflow.pipeline import Pipeline
from sagemaker.workflow.pipeline_context import PipelineSession
from sagemaker.workflow.properties import PropertyFile
from sagemaker.workflow.steps import ProcessingStep, TrainingStep
from sagemaker.model_metrics import MetricsSource, ModelMetrics

from src.config import PROJECT_ROOT, AppConfig, ModelConfig, load_app_config, load_model_config

SKLEARN_FRAMEWORK_VERSION = "1.2-1"


def get_pipeline(
    app_config: Optional[AppConfig] = None,
    model_config: Optional[ModelConfig] = None,
    sagemaker_session: Optional[PipelineSession] = None,
    role_arn: Optional[str] = None,
) -> Pipeline:
    """
    Constructs and returns a SageMaker Pipeline instance.
    """
    if app_config is None:
        app_config = load_app_config()
    if model_config is None:
        model_config = load_model_config()

    role = role_arn or app_config.aws.role_arn or "arn:aws:iam::123456789012:role/AmazonSageMaker-ExecutionRole"

    if sagemaker_session is None:
        sagemaker_session = PipelineSession(default_bucket=app_config.aws.s3_bucket)

    bucket = app_config.aws.s3_bucket
    prefix = app_config.aws.s3_prefix

    # -------------------------------------------------------------------------
    # 1. Pipeline Execution Parameters
    # -------------------------------------------------------------------------
    processing_instance_type = ParameterString(
        name="ProcessingInstanceType",
        default_value=app_config.compute.processing_instance_type,
    )
    training_instance_type = ParameterString(
        name="TrainingInstanceType",
        default_value=app_config.compute.training_instance_type,
    )
    model_approval_status = ParameterString(
        name="ModelApprovalStatus",
        default_value=app_config.pipeline.model_approval_status,
    )
    input_data_uri = ParameterString(
        name="InputDataUri",
        default_value=f"s3://{bucket}/{prefix}/data/raw/mob_price_classification_train.csv",
    )
    accuracy_threshold = ParameterFloat(
        name="AccuracyThreshold",
        default_value=model_config.quality_gate.min_accuracy_threshold,
    )

    # -------------------------------------------------------------------------
    # 2. Processing Step (Data Validation & Preprocessing)
    # -------------------------------------------------------------------------
    sklearn_processor = SKLearnProcessor(
        framework_version=SKLEARN_FRAMEWORK_VERSION,
        role=role,
        instance_type=processing_instance_type,
        instance_count=app_config.compute.processing_instance_count,
        base_job_name=f"{app_config.pipeline.base_job_prefix}-preprocess",
        sagemaker_session=sagemaker_session,
    )

    preprocess_script_path = str(PROJECT_ROOT / "src" / "processing" / "preprocess.py")

    step_process = ProcessingStep(
        name="PreprocessMobileData",
        processor=sklearn_processor,
        inputs=[
            ProcessingInput(
                source=input_data_uri,
                destination="/opt/ml/processing/input",
                input_name="raw-data",
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="train",
                source="/opt/ml/processing/train",
                destination=f"s3://{bucket}/{prefix}/processed/train",
            ),
            ProcessingOutput(
                output_name="validation",
                source="/opt/ml/processing/validation",
                destination=f"s3://{bucket}/{prefix}/processed/validation",
            ),
            ProcessingOutput(
                output_name="test",
                source="/opt/ml/processing/test",
                destination=f"s3://{bucket}/{prefix}/processed/test",
            ),
            ProcessingOutput(
                output_name="baseline",
                source="/opt/ml/processing/baseline",
                destination=f"s3://{bucket}/{prefix}/processed/baseline",
            ),
        ],
        code=preprocess_script_path,
        job_arguments=[
            "--train-ratio", str(model_config.split.train_ratio),
            "--val-ratio", str(model_config.split.validation_ratio),
            "--test-ratio", str(model_config.split.test_ratio),
            "--random-state", str(model_config.split.random_state),
        ],
    )

    # -------------------------------------------------------------------------
    # 3. Training Step (RandomForest Estimator)
    # -------------------------------------------------------------------------
    metric_definitions = [
        {"Name": "train:accuracy", "Regex": r"train:accuracy = ([0-9\\.]+)"},
        {"Name": "validation:accuracy", "Regex": r"validation:accuracy = ([0-9\\.]+)"},
        {"Name": "validation:f1", "Regex": r"validation:f1 = ([0-9\\.]+)"},
        {"Name": "validation:precision", "Regex": r"validation:precision = ([0-9\\.]+)"},
        {"Name": "validation:recall", "Regex": r"validation:recall = ([0-9\\.]+)"},
    ]

    train_script_path = str(PROJECT_ROOT / "src" / "training" / "train.py")

    sklearn_estimator = SKLearn(
        entry_point=train_script_path,
        role=role,
        instance_type=training_instance_type,
        instance_count=app_config.compute.training_instance_count,
        framework_version=SKLEARN_FRAMEWORK_VERSION,
        base_job_name=f"{app_config.pipeline.base_job_prefix}-train",
        metric_definitions=metric_definitions,
        use_spot_instances=app_config.compute.use_spot_instances,
        max_run=app_config.compute.max_run_seconds,
        max_wait=app_config.compute.max_wait_seconds if app_config.compute.use_spot_instances else None,
        hyperparameters={
            "n_estimators": model_config.hyperparameters.n_estimators,
            "max_depth": model_config.hyperparameters.max_depth,
            "min_samples_split": model_config.hyperparameters.min_samples_split,
            "min_samples_leaf": model_config.hyperparameters.min_samples_leaf,
            "random_state": model_config.hyperparameters.random_state,
        },
        sagemaker_session=sagemaker_session,
    )

    step_train = TrainingStep(
        name="TrainRandomForestModel",
        estimator=sklearn_estimator,
        inputs={
            "train": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs["train"].S3Output.S3Uri,
                content_type="text/csv",
            ),
            "validation": TrainingInput(
                s3_data=step_process.properties.ProcessingOutputConfig.Outputs["validation"].S3Output.S3Uri,
                content_type="text/csv",
            ),
        },
    )

    # -------------------------------------------------------------------------
    # 4. Evaluation Step (Processing on Holdout Test Split)
    # -------------------------------------------------------------------------
    eval_processor = SKLearnProcessor(
        framework_version=SKLEARN_FRAMEWORK_VERSION,
        role=role,
        instance_type=processing_instance_type,
        instance_count=1,
        base_job_name=f"{app_config.pipeline.base_job_prefix}-eval",
        sagemaker_session=sagemaker_session,
    )

    evaluate_script_path = str(PROJECT_ROOT / "src" / "evaluation" / "evaluate.py")

    evaluation_report = PropertyFile(
        name="EvaluationReport",
        output_name="evaluation",
        path="evaluation.json",
    )

    step_eval = ProcessingStep(
        name="EvaluateModelQuality",
        processor=eval_processor,
        inputs=[
            ProcessingInput(
                source=step_train.properties.ModelArtifacts.S3ModelArtifacts,
                destination="/opt/ml/processing/model",
                input_name="model-artifacts",
            ),
            ProcessingInput(
                source=step_process.properties.ProcessingOutputConfig.Outputs["test"].S3Output.S3Uri,
                destination="/opt/ml/processing/test",
                input_name="test-data",
            ),
        ],
        outputs=[
            ProcessingOutput(
                output_name="evaluation",
                source="/opt/ml/processing/evaluation",
                destination=f"s3://{bucket}/{prefix}/evaluation",
            ),
        ],
        code=evaluate_script_path,
        property_files=[evaluation_report],
    )

    # -------------------------------------------------------------------------
    # 5. Model Registration Step (SageMaker Model Registry)
    # -------------------------------------------------------------------------
    inference_script_path = str(PROJECT_ROOT / "src" / "inference" / "inference.py")

    model_metrics = ModelMetrics(
        model_statistics=MetricsSource(
            content_type="application/json",
            s3_uri=step_eval.properties.ProcessingOutputConfig.Outputs["evaluation"].S3Output.S3Uri,
        )
    )

    sklearn_model = SKLearnModel(
        model_data=step_train.properties.ModelArtifacts.S3ModelArtifacts,
        role=role,
        entry_point=inference_script_path,
        framework_version=SKLEARN_FRAMEWORK_VERSION,
        sagemaker_session=sagemaker_session,
    )

    step_register = ModelStep(
        name="RegisterApprovedModelPackage",
        step_args=sklearn_model.register(
            content_types=["application/json", "text/csv"],
            response_types=["application/json", "text/csv"],
            inference_instances=[app_config.compute.inference_instance_type],
            transform_instances=[app_config.compute.inference_instance_type],
            model_package_group_name=app_config.pipeline.model_package_group_name,
            approval_status=model_approval_status,
            model_metrics=model_metrics,
        ),
    )

    # -------------------------------------------------------------------------
    # 6. Condition Step (Quality Gate Decision)
    # -------------------------------------------------------------------------
    cond_gte = ConditionGreaterThanOrEqualTo(
        left=JsonGet(
            step_name=step_eval.name,
            property_file=evaluation_report,
            json_path="multiclass_classification_metrics.accuracy.value",
        ),
        right=accuracy_threshold,
    )

    step_cond = ConditionStep(
        name="CheckEvaluationAccuracyGate",
        conditions=[cond_gte],
        if_steps=[step_register],
        else_steps=[],
    )

    # -------------------------------------------------------------------------
    # 7. Construct Pipeline DAG
    # -------------------------------------------------------------------------
    pipeline = Pipeline(
        name=app_config.pipeline.name,
        parameters=[
            processing_instance_type,
            training_instance_type,
            model_approval_status,
            input_data_uri,
            accuracy_threshold,
        ],
        steps=[step_process, step_train, step_eval, step_cond],
        sagemaker_session=sagemaker_session,
    )

    return pipeline
