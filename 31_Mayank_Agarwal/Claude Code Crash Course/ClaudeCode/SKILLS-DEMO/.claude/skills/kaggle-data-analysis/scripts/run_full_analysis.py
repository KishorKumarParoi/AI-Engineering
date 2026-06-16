#!/usr/bin/env python3
"""
Kaggle Data Analysis - Full Pipeline Orchestrator
Runs all analysis phases sequentially and generates comprehensive reports.
"""

import subprocess
import sys
from pathlib import Path
import argparse
from datetime import datetime

def run_analysis_pipeline(input_file, output_dir=None, level="standard", effort="standard", 
                          model="default", dataset_name=None):
    """Run the complete analysis pipeline with customizable parameters."""
    
    input_path = Path(input_file)
    if not input_path.exists():
        print(f"❌ Error: Input file '{input_file}' not found")
        sys.exit(1)
    
    if output_dir is None:
        output_dir = "reports"
    
    if dataset_name is None:
        dataset_name = Path(input_file).stem

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Create reports subfolder for HTML files
    reports_path = output_path / "reports"
    reports_path.mkdir(parents=True, exist_ok=True)
    
    script_dir = Path(__file__).parent
    scripts = [
        ('01_eda.py', 'Exploratory Data Analysis'),
        ('02_preprocessing.py', 'Data Preprocessing'),
        ('03_feature_engineering.py', 'Feature Engineering'),
        ('04_statistical_analysis.py', 'Statistical Analysis'),
        ('05_visualization.py', 'Visualization & Reporting'),
    ]
    
    print("=" * 70)
    print("🚀 KAGGLE DATA ANALYSIS PIPELINE")
    print("=" * 70)
    print(f"\n📂 Input File: {input_file}")
    print(f"📂 Dataset Name: {dataset_name}")
    print(f"📂 Output Directory: {output_dir}")
    print(f"⚙️  Analysis Level: {level.upper()}")
    print(f"⚙️  Effort Level: {effort.upper()}")
    print(f"⚙️  Model Type: {model.upper()}\n")
    
    results = []
    
    for script_name, description in scripts:
        print(f"\n{'='*70}")
        print(f"▶ Phase: {description}")
        print(f"{'='*70}")
        
        script_path = script_dir / script_name
        
        if not script_path.exists():
            print(f"❌ Script not found: {script_path}")
            continue
        
        output_file = reports_path / f"{Path(input_file).stem}_{script_name.replace('.py', '')}_report.html"
        
        try:
            # Run the script
            cmd = [
                sys.executable,
                str(script_path),
                '--input', str(input_file),
                '--output', str(output_file),
                '--level', level,
                '--effort', effort,
                '--model', model,
                '--name', dataset_name
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(result.stdout)
                results.append((description, True, str(output_file)))
            else:
                print(f"❌ Error running {script_name}:")
                print(result.stderr)
                results.append((description, False, None))
        
        except subprocess.TimeoutExpired:
            print(f"❌ Script timed out (>5 minutes): {script_name}")
            results.append((description, False, None))
        except Exception as e:
            print(f"❌ Exception: {e}")
            results.append((description, False, None))
    
    # Generate summary
    print(f"\n{'='*70}")
    print("📊 ANALYSIS SUMMARY")
    print(f"{'='*70}\n")
    
    for description, success, output_file in results:
        status = "✅ Completed" if success else "❌ Failed"
        print(f"{status}: {description}")
        if success and output_file:
            print(f"   📄 Report: {output_file}\n")
    
    # Generate executive summary
    summary_file = output_path / 'final_analysis_summary.md'
    generate_summary(summary_file, input_file, results)
    
    print(f"\n{'='*70}")
    print("✨ ANALYSIS COMPLETE")
    print(f"{'='*70}")
    print(f"\n📋 All HTML reports saved to: {output_dir}/reports/")
    print(f"📄 Executive Summary: {summary_file}")
    print(f"\n🎯 Next Steps:")
    print(f"   1. Review the generated HTML reports in your browser")
    print(f"   2. Read the executive summary for key insights")
    print(f"   3. Use insights from EDA and feature engineering for modeling")
    print(f"   4. Address data quality issues identified in preprocessing report")

def generate_summary(summary_file, input_file, results):
    """Generate executive summary markdown."""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    summary_content = f"""# Kaggle Data Analysis - Executive Summary

**Generated:** {timestamp}  
**Dataset:** {input_file}

## Analysis Phases Executed

| Phase | Status | Output |
|-------|--------|--------|
"""
    
    for description, success, output_file in results:
        status = "✅ Completed" if success else "❌ Failed"
        output_ref = f"[Report](./reports/{Path(output_file).name})" if output_file else "N/A"
        summary_content += f"| {description} | {status} | {output_ref} |\n"
    
    summary_content += """
## Key Reports Generated

### 1. Exploratory Data Analysis (EDA)
- Dataset shape and composition
- Feature distributions and statistics
- Correlation analysis
- Quick insights into data patterns

### 2. Data Preprocessing
- Missing value analysis
- Data quality assessment
- Outlier detection
- Data type recommendations
- Quality score

### 3. Feature Engineering
- Feature importance ranking
- Polynomial feature suggestions
- Interaction feature candidates
- Categorical encoding strategies
- Feature scaling recommendations
- Feature selection best practices

### 4. Statistical Analysis
- Descriptive statistics
- Distribution shape analysis (skewness, kurtosis)
- Normality testing results
- Correlation matrix analysis
- Group statistics
- Statistical recommendations

### 5. Visualization & Reporting
- Distribution charts
- Box plots for outlier detection
- Correlation heatmap
- Categorical features visualization
- Feature relationship scatter plots
- Summary statistics table

## Recommendations

### Immediate Actions
1. **Review EDA Report**: Understand your data structure and distributions
2. **Address Data Quality**: Handle missing values and outliers as recommended
3. **Feature Preprocessing**: Apply suggested encoding and scaling techniques
4. **Statistical Validation**: Check normality assumptions for your modeling approach

### Model Building
1. Use feature importance scores to select top features
2. Consider polynomial/interaction features for complex relationships
3. Apply appropriate transformations for non-normal distributions
4. Be aware of highly correlated features (multicollinearity)

### Validation
1. Re-run this analysis after preprocessing to confirm improvements
2. Compare model performance before/after feature engineering
3. Use statistical insights to validate modeling assumptions

## Quick Links
- [EDA Report](./reports/{{dataset}}_01_eda_report.html)
- [Preprocessing Report](./reports/{{dataset}}_02_preprocessing_report.html)
- [Feature Engineering Report](./reports/{{dataset}}_03_feature_engineering_report.html)
- [Statistical Analysis Report](./reports/{{dataset}}_04_statistical_analysis_report.html)
- [Visualization Report](./reports/{{dataset}}_05_visualization_report.html)

---
*This analysis was generated using the Kaggle Data Analysis Skill*
"""
    
    with open(summary_file, 'w') as f:
        f.write(summary_content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Run complete Kaggle data analysis pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_full_analysis.py --input titanic.csv
  python run_full_analysis.py --input data.csv --output my_reports/
  python run_full_analysis.py --input data.csv --level advanced --effort thorough --model xgboost --name titanic_v1
  python run_full_analysis.py --input data.csv --level basic --effort quick
        """
    )
    
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', default='reports', help='Output directory for reports')
    
    parser.add_argument(
        '--level', 
        choices=['basic', 'standard', 'advanced'],
        default='standard',
        help='Analysis depth level (default: standard)'
    )
    
    parser.add_argument(
        '--effort',
        choices=['quick', 'standard', 'thorough'],
        default='standard',
        help='Effort/time investment level (default: standard)'
    )
    
    parser.add_argument(
        '--model',
        default='default',
        help='Model type or complexity (e.g., default, linear, tree, xgboost, neural_net)'
    )
    
    parser.add_argument(
        '--name',
        default=None,
        help='Custom dataset name for reports (default: input filename)'
    )
    
    args = parser.parse_args()
    run_analysis_pipeline(args.input, args.output, args.level, args.effort, args.model, args.name)
