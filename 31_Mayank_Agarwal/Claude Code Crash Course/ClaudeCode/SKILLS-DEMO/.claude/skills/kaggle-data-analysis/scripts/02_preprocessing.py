#!/usr/bin/env python3
"""
Phase 2: Data Preprocessing & Cleaning
Identifies and handles data quality issues systematically.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import argparse
import warnings
warnings.filterwarnings('ignore')

def detect_outliers_iqr(data, column):
    """Detect outliers using Interquartile Range method."""
    Q1 = data[column].quantile(0.25)
    Q3 = data[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    
    outliers = data[(data[column] < lower_bound) | (data[column] > upper_bound)]
    return len(outliers), lower_bound, upper_bound

def generate_preprocessing_report(input_file, output_file=None, level="standard", effort="standard", 
                                  model="default", dataset_name=None):
    """Generate comprehensive preprocessing report with customizable depth."""
    
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    if output_file is None:
        output_file = Path(input_file).stem + "_preprocessing_report.html"
    
    if dataset_name is None:
        dataset_name = Path(input_file).stem
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Adjust thresholds based on analysis level
    detailed_outlier_analysis = level in ['standard', 'advanced']
    check_multicollinearity = level == 'advanced'
    
    html_content = """
    <html>
    <head>
        <title>Preprocessing Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .section { background-color: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #e74c3c; padding-bottom: 10px; }
            h2 { color: #34495e; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #e74c3c; color: white; }
            tr:nth-child(even) { background-color: #ecf0f1; }
            .warning { background-color: #ffe6e6; border-left: 4px solid #e74c3c; padding: 10px; margin: 10px 0; }
            .success { background-color: #e6ffe6; border-left: 4px solid #27ae60; padding: 10px; margin: 10px 0; }
            .stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
            .stat-box { background-color: #ecf0f1; padding: 15px; border-radius: 5px; border-left: 4px solid #e74c3c; }
            .metadata { font-size: 12px; color: #7f8c8d; background-color: #ecf0f1; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>🔧 Data Preprocessing & Cleaning Report</h1>
        <div class="metadata">
            <strong>Dataset:</strong> """ + dataset_name + """<br>
            <strong>Analysis Level:</strong> """ + level.upper() + """<br>
            <strong>Effort Level:</strong> """ + effort.upper() + """<br>
            <strong>Model Context:</strong> """ + model.upper() + """
        </div>
    """
    
    # 1. Missing Values Analysis
    html_content += """
    <div class="section">
        <h2>1. Missing Values Analysis</h2>
        <table>
            <tr>
                <th>Column</th>
                <th>Missing Count</th>
                <th>Missing %</th>
                <th>Recommendation</th>
            </tr>
    """
    
    missing_data = df.isnull().sum()
    for col in df.columns:
        missing_count = missing_data[col]
        missing_pct = (missing_count / len(df)) * 100
        
        if missing_pct == 0:
            recommendation = "✅ No missing values"
        elif missing_pct < 5:
            recommendation = "Remove rows or use forward fill"
        elif missing_pct < 30:
            recommendation = "Impute with mean/median or create 'missing' category"
        else:
            recommendation = "⚠️ Consider dropping column (too many missing values)"
        
        html_content += f"""
            <tr>
                <td><strong>{col}</strong></td>
                <td>{missing_count}</td>
                <td>{missing_pct:.2f}%</td>
                <td>{recommendation}</td>
            </tr>
        """
    
    html_content += "</table>"
    
    total_missing = missing_data.sum()
    html_content += f'<div class="success">Total missing cells: {total_missing} out of {df.size} ({(total_missing/df.size)*100:.2f}%)</div>'
    html_content += "</div>"
    
    # 2. Duplicate Records
    html_content += f"""
    <div class="section">
        <h2>2. Duplicate Records</h2>
        <div class="stat-grid">
            <div class="stat-box"><strong>Total Duplicates:</strong> {df.duplicated().sum()}</div>
            <div class="stat-box"><strong>Duplicate %:</strong> {(df.duplicated().sum()/len(df)*100):.2f}%</div>
        </div>
    """
    
    if df.duplicated().sum() > 0:
        html_content += '<div class="warning">Action: Review and remove duplicates if not intentional</div>'
    else:
        html_content += '<div class="success">✅ No duplicate records found</div>'
    
    html_content += "</div>"
    
    # 3. Data Type Analysis
    html_content += """
    <div class="section">
        <h2>3. Data Type Consistency</h2>
        <table>
            <tr>
                <th>Column</th>
                <th>Current Type</th>
                <th>Suggested Type</th>
                <th>Notes</th>
            </tr>
    """
    
    for col in df.columns:
        current_type = str(df[col].dtype)
        
        # Infer best type
        if pd.api.types.is_numeric_dtype(df[col]):
            suggested_type = 'numeric (int/float)'
            notes = 'Consider int if no decimals'
        elif pd.api.types.is_bool_dtype(df[col]):
            suggested_type = 'boolean'
            notes = 'Already correct'
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            suggested_type = 'datetime'
            notes = 'Already correct'
        else:
            suggested_type = 'category or string'
            unique_ratio = df[col].nunique() / len(df)
            if unique_ratio < 0.05:
                notes = 'Convert to category for memory efficiency'
            else:
                notes = 'Keep as string'
        
        html_content += f"""
            <tr>
                <td><strong>{col}</strong></td>
                <td>{current_type}</td>
                <td>{suggested_type}</td>
                <td>{notes}</td>
            </tr>
        """
    
    html_content += "</table></div>"
    
    # 4. Outlier Detection
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    html_content += """
    <div class="section">
        <h2>4. Outlier Detection (IQR Method)</h2>
        <table>
            <tr>
                <th>Column</th>
                <th>Outlier Count</th>
                <th>Outlier %</th>
                <th>Lower Bound</th>
                <th>Upper Bound</th>
                <th>Action</th>
            </tr>
    """
    
    for col in numeric_cols:
        outlier_count, lower_bound, upper_bound = detect_outliers_iqr(df, col)
        outlier_pct = (outlier_count / len(df)) * 100
        
        if outlier_count == 0:
            action = "✅ None"
        elif outlier_pct < 5:
            action = "Review and consider removing"
        else:
            action = "⚠️ Investigate (high outlier rate)"
        
        html_content += f"""
            <tr>
                <td><strong>{col}</strong></td>
                <td>{outlier_count}</td>
                <td>{outlier_pct:.2f}%</td>
                <td>{lower_bound:.4f}</td>
                <td>{upper_bound:.4f}</td>
                <td>{action}</td>
            </tr>
        """
    
    html_content += "</table></div>"
    
    # 5. Data Quality Score
    html_content += """
    <div class="section">
        <h2>5. Data Quality Assessment</h2>
    """
    
    quality_score = 100
    issues = []
    
    # Deduct for missing values
    if total_missing > 0:
        quality_score -= min(20, (total_missing / df.size) * 100)
        issues.append(f"Missing values: {total_missing} cells")
    
    # Deduct for duplicates
    if df.duplicated().sum() > 0:
        quality_score -= min(15, (df.duplicated().sum() / len(df)) * 100)
        issues.append(f"Duplicate records: {df.duplicated().sum()}")
    
    # Deduct for outliers
    total_outliers = sum(detect_outliers_iqr(df, col)[0] for col in numeric_cols)
    if total_outliers > 0:
        quality_score -= min(10, (total_outliers / len(df)) * 100)
        issues.append(f"Outliers detected: {total_outliers} records")
    
    quality_score = max(0, quality_score)
    
    # Color based on score
    if quality_score >= 90:
        color = '#27ae60'
        assessment = "Excellent"
    elif quality_score >= 75:
        color = '#f39c12'
        assessment = "Good"
    else:
        color = '#e74c3c'
        assessment = "Needs Improvement"
    
    html_content += f"""
        <div style="background-color: {color}; color: white; padding: 20px; border-radius: 5px; margin: 15px 0;">
            <h3>Quality Score: {quality_score:.1f}/100 ({assessment})</h3>
        </div>
    """
    
    if issues:
        html_content += "<h3>Identified Issues:</h3><ul>"
        for issue in issues:
            html_content += f"<li>{issue}</li>"
        html_content += "</ul>"
    else:
        html_content += '<div class="success">✅ No significant data quality issues detected</div>'
    
    html_content += "</div>"
    
    # 6. Recommendations
    html_content += """
    <div class="section">
        <h2>6. Action Items & Recommendations</h2>
        <ul>
            <li><strong>Handle Missing Values:</strong> Review the recommendations above and apply appropriate imputation strategies</li>
            <li><strong>Remove Duplicates:</strong> Use <code>df.drop_duplicates()</code> if duplicates are unintentional</li>
            <li><strong>Fix Data Types:</strong> Convert columns to suggested types for better memory usage and processing speed</li>
            <li><strong>Address Outliers:</strong> Consider domain expertise before removing outliers - they may be valuable insights</li>
            <li><strong>Validate Changes:</strong> Re-run this report after preprocessing to confirm improvements</li>
        </ul>
    </div>
    """
    
    html_content += """
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Preprocessing report saved to {output_file}")
    print(f"\n📋 Data Quality Summary:")
    print(f"   - Quality Score: {quality_score:.1f}/100")
    print(f"   - Missing Values: {total_missing} cells")
    print(f"   - Duplicate Rows: {df.duplicated().sum()}")
    print(f"   - Outliers Detected: {total_outliers}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate preprocessing report')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', default=None, help='Output HTML file')
    parser.add_argument('--level', choices=['basic', 'standard', 'advanced'], default='standard', help='Analysis depth level')
    parser.add_argument('--effort', choices=['quick', 'standard', 'thorough'], default='standard', help='Effort level')
    parser.add_argument('--model', default='default', help='Model context')
    parser.add_argument('--name', default=None, help='Dataset name')
    
    args = parser.parse_args()
    generate_preprocessing_report(args.input, args.output, args.level, args.effort, args.model, args.name)
