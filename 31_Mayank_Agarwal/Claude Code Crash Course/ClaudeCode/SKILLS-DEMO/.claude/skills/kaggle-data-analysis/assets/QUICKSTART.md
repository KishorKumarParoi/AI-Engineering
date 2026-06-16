# Kaggle Data Analysis Skill - Quick Start Guide

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r .github/skills/kaggle-data-analysis/assets/requirements.txt
   ```

2. **Place Your Data**
   - Add your CSV file to the project root or specify the path

## Usage

### Option 1: Run Full Analysis Pipeline (Recommended)

```bash
python .github/skills/kaggle-data-analysis/scripts/run_full_analysis.py --input titanic.csv --output reports/
```

### Option 2: Run with Custom Parameters

```bash
# Run with specific analysis level and effort
python .github/skills/kaggle-data-analysis/scripts/run_full_analysis.py \
  --input data.csv \
  --output reports/ \
  --level advanced \
  --effort thorough \
  --model xgboost \
  --name titanic_v1
```

### Option 3: Run Individual Phases

Run any analysis phase independently:

```bash
# Phase 1: EDA
python .github/skills/kaggle-data-analysis/scripts/01_eda.py --input titanic.csv --output reports/eda_report.html

# Phase 2: Preprocessing
python .github/skills/kaggle-data-analysis/scripts/02_preprocessing.py --input titanic.csv --output reports/preprocessing_report.html

# Phase 3: Feature Engineering
python .github/skills/kaggle-data-analysis/scripts/03_feature_engineering.py --input titanic.csv --output reports/feature_engineering_report.html

# Phase 4: Statistical Analysis
python .github/skills/kaggle-data-analysis/scripts/04_statistical_analysis.py --input titanic.csv --output reports/statistical_analysis_report.html

# Phase 5: Visualization
python .github/skills/kaggle-data-analysis/scripts/05_visualization.py --input titanic.csv --output reports/visualization_report.html
```

## Command-Line Arguments

### Global Arguments (All Scripts)

| Argument | Values | Default | Description |
|----------|--------|---------|-------------|
| `--input` | file path | **Required** | CSV file to analyze |
| `--output` | file path | `reports/` | Output directory or file |
| `--level` | `basic`, `standard`, `advanced` | `standard` | Analysis depth |
| `--effort` | `quick`, `standard`, `thorough` | `standard` | Time/effort investment |
| `--model` | string | `default` | Model type (linear, tree, xgboost, etc.) |
| `--name` | string | filename | Custom dataset name |

### Argument Combinations

#### Quick Analysis (5 mins)
```bash
python .github/skills/kaggle-data-analysis/scripts/run_full_analysis.py \
  --input data.csv \
  --level basic \
  --effort quick
```

#### Standard Analysis (20-30 mins)
```bash
python .github/skills/kaggle-data-analysis/scripts/run_full_analysis.py \
  --input data.csv \
  --level standard \
  --effort standard
```

#### Deep Dive Analysis (1-2 hours)
```bash
python .github/skills/kaggle-data-analysis/scripts/run_full_analysis.py \
  --input data.csv \
  --level advanced \
  --effort thorough \
  --model xgboost
```

#### Model-Specific Analysis
```bash
# For Linear Models
python .github/skills/kaggle-data-analysis/scripts/run_full_analysis.py \
  --input data.csv --model linear --level standard

# For Tree-Based Models
python .github/skills/kaggle-data-analysis/scripts/run_full_analysis.py \
  --input data.csv --model tree --level advanced

# For Neural Networks
python .github/skills/kaggle-data-analysis/scripts/run_full_analysis.py \
  --input data.csv --model neural_net --level advanced --effort thorough
```

## What Each Level Adjusts

### Analysis Level (`--level`)

**Basic:**
- Fewer distribution bins (30)
- Limited categorical values shown (10)
- Core analysis only

**Standard:** *(Default)*
- Standard distribution bins (30)
- More categorical values (10)
- Balanced depth

**Advanced:**
- More detailed bins (50)
- All categorical values shown (20)
- Advanced statistical tests
- More feature engineering suggestions
- Higher resolution visualizations

### Effort Level (`--effort`)

**Quick:**
- Faster computation
- Essential analysis only
- Lower DPI images (100)

**Standard:** *(Default)*
- Balanced speed/depth
- Comprehensive analysis
- Good resolution (100 DPI)

**Thorough:**
- Extensive computation
- Advanced tests and metrics
- High resolution images (150 DPI)
- Extended feature exploration

### Model Context (`--model`)

Models influence feature recommendations:
- `default` - General purpose features
- `linear` - Focus on linear relationships
- `tree` - Polynomial features emphasized
- `xgboost` - Interaction features
- `neural_net` - All feature types

## Report Descriptions

### 1. EDA Report (01_eda.py)
- Dataset overview (shape, memory usage)
- Data types and missing values
- Numerical features summary
- Distribution analysis with histograms
- Correlation matrix and heatmap
- Categorical features summary

**Use for:** Understanding your data structure and basic patterns

### 2. Preprocessing Report (02_preprocessing.py)
- Missing values analysis with recommendations
- Duplicate records detection
- Data type consistency checks
- Outlier detection (IQR method)
- Data quality score
- Action items and recommendations

**Use for:** Identifying data quality issues to address

### 3. Feature Engineering Report (03_feature_engineering.py)
- Feature importance ranking
- Polynomial features suggestions
- Interaction features recommendations
- Categorical encoding strategies
- Feature scaling recommendations
- Feature selection best practices

**Use for:** Planning feature transformations and engineering

### 4. Statistical Analysis Report (04_statistical_analysis.py)
- Descriptive statistics for all features
- Distribution shape analysis (skewness, kurtosis)
- Normality testing results
- Correlation matrix with interpretations
- Group statistics (if applicable)
- Statistical recommendations

**Use for:** Understanding data distributions and relationships

### 5. Visualization Report (05_visualization.py)
- Distribution charts for numeric features
- Box plots for outlier detection
- Correlation heatmap
- Categorical features bar charts
- Feature relationship scatter plots
- Summary statistics table

**Use for:** Visual exploration and presentations

## Project Structure

```
SKILLS-DEMO/
├── titanic.csv                                 # Your dataset
├── reports/                                    # Generated reports
│   ├── eda_report.html
│   ├── preprocessing_report.html
│   ├── feature_engineering_report.html
│   ├── statistical_analysis_report.html
│   ├── visualization_report.html
│   └── final_analysis_summary.md
└── .github/skills/kaggle-data-analysis/
    ├── SKILL.md                               # Skill documentation
    ├── scripts/
    │   ├── 01_eda.py
    │   ├── 02_preprocessing.py
    │   ├── 03_feature_engineering.py
    │   ├── 04_statistical_analysis.py
    │   ├── 05_visualization.py
    │   └── run_full_analysis.py
    ├── references/
    │   ├── kaggle_best_practices.md
    │   ├── feature_engineering_guide.md
    │   ├── statistical_methods.md
    │   └── data_analysis_toolkit.md
    └── assets/
        ├── config_template.yaml
        ├── requirements.txt
        └── QUICKSTART.md
```

## Typical Workflow

1. **Load Your Data**
   - Place CSV file in project root
   - Run full analysis pipeline

2. **Review EDA Report**
   - Understand data structure
   - Identify obvious issues
   - Note data patterns

3. **Address Preprocessing Issues**
   - Handle missing values
   - Remove duplicates
   - Address outliers

4. **Apply Feature Engineering**
   - Use suggested features
   - Apply appropriate encoding
   - Scale as needed

5. **Prepare for Modeling**
   - Use statistical insights
   - Select top features
   - Create preprocessed dataset

6. **Build Models**
   - Use insights from analysis
   - Apply learned transformations
   - Validate with test data

## Tips & Tricks

### For Large Datasets
- Use `--output` parameter to save to disk
- Reports are in HTML format for easy viewing
- All scripts include progress indicators

### For Custom Analysis
- Modify scripts directly for specific needs
- Reference documentation for guidance
- Each script is standalone and can be modified

### For Multiple Datasets
- Run full pipeline for each dataset
- Compare reports to identify differences
- Store reports in separate directories

## Troubleshooting

### Script Fails with Missing Module
```bash
pip install -r .github/skills/kaggle-data-analysis/assets/requirements.txt
```

### File Not Found Error
- Check that CSV file path is correct
- Use absolute paths if relative paths don't work
- Verify file exists: `ls -la your_file.csv`

### Memory Issues with Large Files
- Reduce dataset size for testing
- Use data sampling in scripts
- Process in chunks (see references)

### Reports Not Generated
- Check that output directory is writable
- Ensure disk space is available
- Look for error messages in terminal output

## Next Steps

After analysis:
1. Review insights from statistical analysis
2. Implement preprocessing recommendations
3. Apply feature engineering suggestions
4. Create cleaned dataset for modeling
5. Compare model performance before/after analysis

## Resources

- **Feature Engineering Guide**: [./references/feature_engineering_guide.md](./references/feature_engineering_guide.md)
- **Statistical Methods**: [./references/statistical_methods.md](./references/statistical_methods.md)
- **Python Toolkit**: [./references/data_analysis_toolkit.md](./references/data_analysis_toolkit.md)
- **Kaggle Best Practices**: [./references/kaggle_best_practices.md](./references/kaggle_best_practices.md)

## Support

For issues or questions:
1. Check the relevant reference document
2. Review the generated reports for detailed explanations
3. Modify scripts for custom analysis
4. Refer to pandas/scikit-learn documentation

---

**Happy Analyzing! 🚀📊**
