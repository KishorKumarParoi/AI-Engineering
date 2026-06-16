#!/usr/bin/env python3
"""
Phase 1: Exploratory Data Analysis (EDA)
Generates comprehensive dataset overview, distributions, and correlations.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse
import warnings
warnings.filterwarnings('ignore')

def generate_eda_report(input_file, output_file=None, level="standard", effort="standard", 
                        model="default", dataset_name=None):
    """Generate comprehensive EDA report with customizable depth."""
    
    # Load data
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    if output_file is None:
        output_file = Path(input_file).stem + "_eda_report.html"
    
    if dataset_name is None:
        dataset_name = Path(input_file).stem
    
    # Create output directory
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Determine analysis depth based on level and effort
    include_advanced_corr = level in ['standard', 'advanced']
    include_detailed_dist = level in ['standard', 'advanced'] or effort == 'thorough'
    num_distribution_bins = 50 if level == 'advanced' else 30
    max_categorical_unique = 20 if level == 'advanced' else 10
    
    # Start HTML report
    html_content = """
    <html>
    <head>
        <title>EDA Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .section { background-color: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #3498db; color: white; }
            tr:nth-child(even) { background-color: #ecf0f1; }
            .stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
            .stat-box { background-color: #ecf0f1; padding: 15px; border-radius: 5px; border-left: 4px solid #3498db; }
            img { max-width: 100%; height: auto; margin: 15px 0; }
            .metadata { font-size: 12px; color: #7f8c8d; background-color: #ecf0f1; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>📊 Exploratory Data Analysis Report</h1>
        <div class="metadata">
            <strong>Dataset:</strong> """ + dataset_name + """<br>
            <strong>Analysis Level:</strong> """ + level.upper() + """<br>
            <strong>Effort Level:</strong> """ + effort.upper() + """<br>
            <strong>Model Context:</strong> """ + model.upper() + """
        </div>
    """
    
    # 1. Dataset Overview
    html_content += f"""
    <div class="section">
        <h2>1. Dataset Overview</h2>
        <div class="stat-grid">
            <div class="stat-box"><strong>Shape:</strong> {df.shape[0]} rows × {df.shape[1]} columns</div>
            <div class="stat-box"><strong>Memory Usage:</strong> {df.memory_usage(deep=True).sum() / 1024**2:.2f} MB</div>
            <div class="stat-box"><strong>Missing Values:</strong> {df.isnull().sum().sum()} total</div>
            <div class="stat-box"><strong>Duplicate Rows:</strong> {df.duplicated().sum()}</div>
        </div>
    </div>
    """
    
    # 2. Data Types and Missing Values
    html_content += """
    <div class="section">
        <h2>2. Data Types & Missing Values</h2>
        <table>
            <tr>
                <th>Column</th>
                <th>Data Type</th>
                <th>Missing Count</th>
                <th>Missing %</th>
                <th>Unique Values</th>
            </tr>
    """
    
    for col in df.columns:
        missing_count = df[col].isnull().sum()
        missing_pct = (missing_count / len(df)) * 100
        unique_count = df[col].nunique()
        html_content += f"""
            <tr>
                <td><strong>{col}</strong></td>
                <td>{df[col].dtype}</td>
                <td>{missing_count}</td>
                <td>{missing_pct:.2f}%</td>
                <td>{unique_count}</td>
            </tr>
        """
    
    html_content += "</table></div>"
    
    # 3. Numerical Features Summary
    html_content += """
    <div class="section">
        <h2>3. Numerical Features Summary</h2>
        <table>
            <tr>
                <th>Column</th>
                <th>Count</th>
                <th>Mean</th>
                <th>Std Dev</th>
                <th>Min</th>
                <th>25%</th>
                <th>50% (Median)</th>
                <th>75%</th>
                <th>Max</th>
            </tr>
    """
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    desc = df[numeric_cols].describe().T
    
    for col in numeric_cols:
        row = desc.loc[col]
        html_content += f"""
            <tr>
                <td><strong>{col}</strong></td>
                <td>{int(row['count'])}</td>
                <td>{row['mean']:.4f}</td>
                <td>{row['std']:.4f}</td>
                <td>{row['min']:.4f}</td>
                <td>{row['25%']:.4f}</td>
                <td>{row['50%']:.4f}</td>
                <td>{row['75%']:.4f}</td>
                <td>{row['max']:.4f}</td>
            </tr>
        """
    
    html_content += "</table></div>"
    
    # 4. Distribution Analysis
    html_content += """
    <div class="section">
        <h2>4. Distribution Analysis</h2>
    """
    
    # Histograms
    if len(numeric_cols) > 0:
        fig, axes = plt.subplots(len(numeric_cols), 1, figsize=(10, 3*len(numeric_cols)))
        if len(numeric_cols) == 1:
            axes = [axes]
        
        for idx, col in enumerate(numeric_cols):
            axes[idx].hist(df[col].dropna(), bins=num_distribution_bins, edgecolor='black', alpha=0.7, color='#3498db')
            axes[idx].set_title(f'Distribution: {col}', fontsize=12, fontweight='bold')
            axes[idx].set_xlabel(col)
            axes[idx].set_ylabel('Frequency')
            axes[idx].grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('temp_distributions.png', dpi=100, bbox_inches='tight')
        plt.close()
        
        with open('temp_distributions.png', 'rb') as img_file:
            import base64
            img_base64 = base64.b64encode(img_file.read()).decode()
            html_content += f'<img src="data:image/png;base64,{img_base64}" />'
        
        Path('temp_distributions.png').unlink()
    
    html_content += "</div>"
    
    # 5. Correlation Analysis
    html_content += """
    <div class="section">
        <h2>5. Correlation Analysis</h2>
    """
    
    if len(numeric_cols) > 1:
        corr_matrix = df[numeric_cols].corr()
        
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0, 
                   square=True, ax=ax, cbar_kws={'label': 'Correlation'})
        plt.title('Correlation Matrix', fontsize=14, fontweight='bold')
        plt.tight_layout()
        plt.savefig('temp_correlation.png', dpi=100, bbox_inches='tight')
        plt.close()
        
        with open('temp_correlation.png', 'rb') as img_file:
            import base64
            img_base64 = base64.b64encode(img_file.read()).decode()
            html_content += f'<img src="data:image/png;base64,{img_base64}" />'
        
        Path('temp_correlation.png').unlink()
    
    html_content += "</div>"
    
    # 6. Categorical Features Summary
    categorical_cols = df.select_dtypes(include=['object']).columns
    
    if len(categorical_cols) > 0:
        html_content += """
        <div class="section">
            <h2>6. Categorical Features</h2>
        """
        
        for col in categorical_cols:
            value_counts = df[col].value_counts()
            html_content += f"""
            <h3>{col}</h3>
            <table>
                <tr><th>Value</th><th>Count</th><th>Percentage</th></tr>
            """
            for val, count in value_counts.head(max_categorical_unique).items():
                pct = (count / len(df)) * 100
                html_content += f"<tr><td>{val}</td><td>{count}</td><td>{pct:.2f}%</td></tr>"
            
            html_content += "</table>"
        
        html_content += "</div>"
    
    html_content += """
    </body>
    </html>
    """
    
    # Write report
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ EDA report saved to {output_file}")
    print(f"\n📈 Dataset Summary:")
    print(f"   - Shape: {df.shape}")
    print(f"   - Numeric columns: {len(numeric_cols)}")
    print(f"   - Categorical columns: {len(categorical_cols)}")
    print(f"   - Missing values: {df.isnull().sum().sum()}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate EDA report')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', default=None, help='Output HTML file')
    parser.add_argument('--level', choices=['basic', 'standard', 'advanced'], default='standard', help='Analysis depth level')
    parser.add_argument('--effort', choices=['quick', 'standard', 'thorough'], default='standard', help='Effort level')
    parser.add_argument('--model', default='default', help='Model context')
    parser.add_argument('--name', default=None, help='Dataset name')
    
    args = parser.parse_args()
    generate_eda_report(args.input, args.output, args.level, args.effort, args.model, args.name)
