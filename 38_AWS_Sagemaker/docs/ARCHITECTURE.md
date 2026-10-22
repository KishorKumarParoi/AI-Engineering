# End-to-End AWS SageMaker MLOps Architecture

This document details the enterprise architecture, container lifecycle, network topologies, and security posture implemented in this project.

---

## 1. High-Level Architecture Overview

```mermaid
flowchart TD
    subgraph Data Layer ["Storage & Ingestion (Amazon S3)"]
        S3_RAW[("s3://bucket/data/raw/")]
        S3_PROC[("s3://bucket/processed/")]
        S3_MODEL[("s3://bucket/models/")]
        S3_EVAL[("s3://bucket/evaluation/")]
        S3_CAPTURE[("s3://bucket/datacapture/")]
    end

    subgraph Pipeline Layer ["SageMaker Pipelines DAG Orchestration"]
        STEP_PROC["Step 1: ProcessingStep\n(SKLearnProcessor)"]
        STEP_TRAIN["Step 2: TrainingStep\n(SKLearn Estimator)"]
        STEP_EVAL["Step 3: ProcessingStep\n(Model Evaluation)"]
        STEP_COND{"Step 4: ConditionStep\n(Accuracy >= 0.85)"}
        STEP_REG["Step 5: ModelStep\n(Register in Model Registry)"]
    end

    subgraph Registry Layer ["Governance & Lineage"]
        MODEL_REG[("SageMaker Model Registry\nMobilePricePackageGroup")]
        APPROVAL{"Manual Approval / CI Webhook"}
    end

    subgraph Serving Layer ["Inference & Production Serving"]
        ENDPOINT["SageMaker Endpoint\n(Real-time / Serverless)"]
        CLIENT["Client / Consumer Applications"]
        LOCAL_API["FastAPI Local Microservice\n(:8000/predict)"]
    end

    subgraph Monitoring Layer ["Observability & Governance"]
        CW["CloudWatch Metrics & Logs"]
        MM["SageMaker Model Monitor\n(Data Drift Detection)"]
    end

    %% Flow connections
    S3_RAW --> STEP_PROC
    STEP_PROC -->|Train / Val Splits| S3_PROC
    STEP_PROC -->|Baseline Data| S3_PROC

    S3_PROC --> STEP_TRAIN
    STEP_TRAIN -->|model.tar.gz| S3_MODEL
    STEP_TRAIN -->|Metrics| CW

    S3_MODEL --> STEP_EVAL
    S3_PROC -->|Test Split| STEP_EVAL
    STEP_EVAL -->|evaluation.json| S3_EVAL

    S3_EVAL --> STEP_COND
    STEP_COND -->|Passed| STEP_REG
    STEP_COND -->|Failed| REJECT["Stop: Do Not Register"]

    STEP_REG --> MODEL_REG
    MODEL_REG --> APPROVAL
    APPROVAL -->|Approved| ENDPOINT

    CLIENT -->|REST / JSON| ENDPOINT
    ENDPOINT -->|Live Payload Capture| S3_CAPTURE
    S3_CAPTURE --> MM
    MM -->|Drift Alert| CW

    CLIENT -.->|Offline / Local Testing| LOCAL_API
```

---

## 2. Pipeline Execution Stages

### Step 1: Processing Step (`PreprocessMobileData`)
- **Container**: AWS Prebuilt Scikit-Learn Processor (`image_uris.retrieve('sklearn')`).
- **Input**: Raw mobile dataset from S3 or local storage.
- **Actions**:
  - Schema validation (verifies all 20 features and target `price_range`).
  - Missing value imputation using median strategy.
  - Stratified 3-way split: **Train (70%)**, **Validation (15%)**, **Test (15%)**.
  - Baseline dataset generation (headerless 20 features) for SageMaker Model Monitor.
- **Output**: S3 channels mounted to subsequent pipeline stages.

### Step 2: Training Step (`TrainRandomForestModel`)
- **Container**: `sagemaker.sklearn.estimator.SKLearn`.
- **Infrastructure**: Managed Spot Instances (`use_spot_instances=True`) to reduce training compute costs by up to 70%.
- **Metrics Emission**: Custom regex filters parse training and validation metrics (`accuracy`, `f1`, `precision`, `recall`) directly into Amazon CloudWatch Metrics.
- **Artifact**: `model.joblib` and `metadata.json` packaged into `model.tar.gz`.

### Step 3: Evaluation Step (`EvaluateModelQuality`)
- **Input**: Model artifacts from Step 2 and holdout Test dataset from Step 1.
- **Actions**: Unpacks `model.tar.gz`, performs inference across the unseen test split, and computes multi-class classification metrics (accuracy, macro/weighted F1, precision, recall, and full confusion matrix).
- **Output**: Generates `evaluation.json` strictly formatted to SageMaker Model Quality Specification.

### Step 4: Quality Gate Decision (`CheckEvaluationAccuracyGate`)
- **Type**: `sagemaker.workflow.condition_step.ConditionStep`.
- **Condition**: Holdout test accuracy must satisfy:
  $$\text{Accuracy} \ge 0.85$$
- **Behavior**:
  - If **True**: Proceeds to Step 5 (Register Model).
  - If **False**: Halts pipeline execution without registering the model, preventing degraded models from reaching staging or production.

### Step 5: Model Registry Registration (`RegisterApprovedModelPackage`)
- **Catalog**: Registers the model version into `MobilePriceClassificationModelPackageGroup`.
- **Metadata**: Associates evaluation metrics (`ModelMetrics`), container inference code (`src/inference/inference.py`), and sets approval status to `PendingManualApproval`.

---

## 3. SageMaker Container Filesystem Contract

AWS SageMaker manages container execution through strict POSIX directory conventions:

```
/opt/ml/
├── input/
│   ├── config/
│   │   ├── hyperparameters.json      # Hyperparameters passed to Estimator
│   │   ├── inputdataconfig.json      # Channel configuration
│   │   └── resourceconfig.json       # Hostnames and cluster topology
│   └── data/
│       ├── train/                    # Channel SM_CHANNEL_TRAIN
│       └── validation/               # Channel SM_CHANNEL_VALIDATION
├── processing/
│   ├── input/                        # Processing input mounts
│   ├── train/                        # Processing output
│   ├── validation/                   # Processing output
│   ├── test/                         # Processing output
│   └── evaluation/                   # Output for evaluation.json
├── model/                            # SM_MODEL_DIR: Compressed into model.tar.gz
└── output/
    └── data/                         # SM_OUTPUT_DATA_DIR: Failure logs and reports
```

---

## 4. Security & Governance

1. **IAM Least Privilege**:
   - Training & Processing roles only access the designated S3 bucket prefix and Amazon CloudWatch Logs.
2. **Encryption**:
   - Data at rest in S3 encrypted with AWS KMS (`aws:kms`).
   - Inter-container training communication encrypted via TLS when distributed.
3. **VPC Integration**:
   - Subnets and security groups can be attached to Estimators and Processors to keep network traffic inside private corporate subnets without public internet exposure.
