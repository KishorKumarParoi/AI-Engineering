---
name: kaggle-data-analysis
description: 'In-depth Kaggle competition data analysis workflow. Use for exploratory data analysis (EDA), data preprocessing, feature engineering, statistical analysis, and comprehensive visualization. Generates detailed reports with insights, patterns, and recommendations.'
argument-hint: 'path/to/data.csv or dataset_name'
---

# Kaggle Data Analysis Skill

Comprehensive end-to-end data analysis framework for Kaggle competitions and datasets.

## When to Use

- Starting a new Kaggle competition project
- Exploring unfamiliar datasets before modeling
- Generating baseline data quality reports
- Feature engineering and preprocessing planning
- Statistical insights and pattern discovery
- Creating presentation-ready visualizations

## Analysis Pipeline

This skill implements a 5-phase workflow:

### Phase 1: Exploratory Data Analysis (EDA)
Understand your dataset's structure, distributions, and basic statistics.

**Script**: [01_eda.py](./scripts/01_eda.py)

Run this first to get:
- Dataset shape and data types
- Missing value analysis
- Statistical summaries
- Distribution plots for all features
- Correlation matrices and heatmaps

```bash
python scripts/01_eda.py --input titanic.csv --output reports/eda_report.html
```

### Phase 2: Data Preprocessing & Cleaning
Identify and handle data quality issues systematically.

**Script**: [02_preprocessing.py](./scripts/02_preprocessing.py)

Performs:
- Missing value detection and strategies
- Outlier identification and treatment
- Data type consistency checks
- Duplicate record detection
- Feature scaling and normalization options

```bash
python scripts/02_preprocessing.py --input titanic.csv --output reports/preprocessing_report.html
```

### Phase 3: Feature Engineering
Generate new features and analyze feature importance.

**Script**: [03_feature_engineering.py](./scripts/03_feature_engineering.py)

Creates:
- Derived features from existing columns
- Interaction terms and polynomial features
- Categorical encoding strategies
- Feature importance rankings
- Feature correlation analysis

```bash
python scripts/03_feature_engineering.py --input titanic.csv --output reports/feature_engineering_report.html
```

### Phase 4: Statistical Analysis
Deep-dive statistical insights and hypothesis testing.

**Script**: [04_statistical_analysis.py](./scripts/04_statistical_analysis.py)

Includes:
- Descriptive statistics by groups
- Correlation and causation analysis
- Distribution testing (normality, skewness, kurtosis)
- Hypothesis testing framework
- Statistical summaries and p-values

```bash
python scripts/04_statistical_analysis.py --input titanic.csv --output reports/statistical_analysis_report.html
```

### Phase 5: Visualization & Reporting
Generate comprehensive visualization suite and executive summary.

**Script**: [05_visualization.py](./scripts/05_visualization.py)

Produces:
- Multi-plot dashboards
- Distribution comparisons
- Relationship visualizations
- Time-series plots (if applicable)
- Interactive HTML reports

```bash
python scripts/05_visualization.py --input titanic.csv --output reports/visualization_report.html
```

## Quick Start

### Run Full Analysis Pipeline

Use the orchestrator script to run all phases sequentially:

```bash
python scripts/run_full_analysis.py --input titanic.csv --output reports/
```

### Customize Analysis Depth

```bash
# Quick analysis (basic level, quick effort)
python scripts/run_full_analysis.py --input data.csv --level basic --effort quick

# Standard analysis (default)
python scripts/run_full_analysis.py --input data.csv --level standard --effort standard

# Deep dive analysis (advanced level, thorough effort)
python scripts/run_full_analysis.py --input data.csv --level advanced --effort thorough --model xgboost
```

### Run Individual Phases

Each script can be run independently with:

```bash
python scripts/02_preprocessing.py --input data.csv --level advanced --effort thorough
```

## Configuration

See [config_template.yaml](./assets/config_template.yaml) for customization options:
- Column renaming rules
- Outlier detection thresholds
- Feature engineering parameters
- Statistical test selections

## Command-Line Arguments

All scripts support the following arguments to customize analysis:

### Available Arguments

```
--input CSV_FILE          # Input CSV file (required)
--output OUTPUT_PATH      # Output directory or file (default: reports/)
--level LEVEL             # Analysis depth: basic, standard, advanced (default: standard)
--effort EFFORT           # Effort level: quick, standard, thorough (default: standard)
--model MODEL_TYPE        # Model context: default, linear, tree, xgboost, neural_net
--name DATASET_NAME       # Custom dataset name for reports
```

### Examples

```bash
# Basic quick analysis
python scripts/run_full_analysis.py --input data.csv --level basic --effort quick

# Advanced thorough analysis for XGBoost
python scripts/run_full_analysis.py --input data.csv --level advanced --effort thorough --model xgboost --name my_dataset

# Linear model focused analysis
python scripts/run_full_analysis.py --input data.csv --model linear --level standard
```

### What Each Setting Controls

| Setting | Impact |
|---------|--------|
| `--level basic` | Faster computation, core analysis only |
| `--level standard` | Balanced depth and speed (default) |
| `--level advanced` | Detailed analysis, advanced tests, all features |
| `--effort quick` | Minimal processing, low DPI images |
| `--effort thorough` | Extended tests, high resolution (150 DPI) |
| `--model <type>` | Tailors feature engineering to model type |
| `--name <id>` | Custom identifier in reports |

## Project Structure

```
reports/                          # Generated analysis outputs
├── eda_report.html
├── preprocessing_report.html
├── feature_engineering_report.html
├── statistical_analysis_report.html
├── visualization_report.html
└── final_analysis_summary.md

data/                            # Input data
├── titanic.csv                  # Raw dataset
└── processed_data.csv           # Cleaned dataset (auto-generated)
```

## Requirements

Install dependencies:

```bash
pip install pandas numpy scikit-learn matplotlib seaborn scipy statsmodels plotly
```

## References

- [Kaggle Best Practices](./references/kaggle_best_practices.md)
- [Feature Engineering Guide](./references/feature_engineering_guide.md)
- [Statistical Methods Reference](./references/statistical_methods.md)
- [Python Data Analysis Toolkit](./references/data_analysis_toolkit.md)

## Next Steps After Analysis

1. Review generated reports for key insights
2. Identify target variable and create baseline model
3. Use feature engineering insights to select top features
4. Address data quality issues from preprocessing report
5. Plan model architecture based on data characteristics
