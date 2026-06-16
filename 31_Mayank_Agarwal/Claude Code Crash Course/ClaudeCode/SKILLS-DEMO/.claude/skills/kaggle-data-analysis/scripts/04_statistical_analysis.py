#!/usr/bin/env python3
"""
Phase 4: Statistical Analysis
Deep-dive statistical insights and hypothesis testing.
"""

import pandas as pd
import numpy as np
from scipy import stats
from pathlib import Path
import argparse
import warnings
warnings.filterwarnings('ignore')

def calculate_skewness_kurtosis(df, numeric_cols):
    """Calculate skewness and kurtosis for each numeric column."""
    results = {}
    for col in numeric_cols:
        data = df[col].dropna()
        results[col] = {
            'skewness': stats.skew(data),
            'kurtosis': stats.kurtosis(data),
            'jarque_bera_stat': stats.jarque_bera(data)[0],
            'jarque_bera_pvalue': stats.jarque_bera(data)[1]
        }
    return results

def test_normality(df, numeric_cols):
    """Test if features are normally distributed using Shapiro-Wilk test."""
    results = {}
    for col in numeric_cols:
        data = df[col].dropna()
        if len(data) <= 5000:  # Shapiro-Wilk works best with smaller samples
            stat, p_value = stats.shapiro(data)
        else:
            # Use Kolmogorov-Smirnov test for large samples
            stat, p_value = stats.kstest(data, 'norm', args=(data.mean(), data.std()))
        
        results[col] = {
            'test_statistic': stat,
            'p_value': p_value,
            'is_normal': p_value > 0.05
        }
    return results

def calculate_group_statistics(df, numeric_cols, categorical_col):
    """Calculate statistics grouped by categorical variable."""
    if categorical_col not in df.columns:
        return None
    
    group_stats = {}
    for col in numeric_cols:
        group_stats[col] = df.groupby(categorical_col)[col].agg(['count', 'mean', 'std', 'min', 'max'])
    
    return group_stats

def generate_statistical_analysis_report(input_file, output_file=None, level="standard", effort="standard", 
                                        model="default", dataset_name=None):
    """Generate comprehensive statistical analysis report with customizable depth."""
    
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    if output_file is None:
        output_file = Path(input_file).stem + "_statistical_analysis_report.html"
    
    if dataset_name is None:
        dataset_name = Path(input_file).stem
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Adjust statistical tests based on effort level
    perform_advanced_tests = level == 'advanced' or effort == 'thorough'
    
    html_content = """
    <html>
    <head>
        <title>Statistical Analysis Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .section { background-color: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #16a085; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; font-size: 13px; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background-color: #16a085; color: white; }
            tr:nth-child(even) { background-color: #ecf0f1; }
            .stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
            .stat-box { background-color: #ecf0f1; padding: 15px; border-radius: 5px; border-left: 4px solid #16a085; }
            .normal { background-color: #d5f4e6; }
            .not-normal { background-color: #fadbd8; }
            .metadata { font-size: 12px; color: #7f8c8d; background-color: #ecf0f1; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>📊 Statistical Analysis Report</h1>
        <div class="metadata">
            <strong>Dataset:</strong> """ + dataset_name + """<br>
            <strong>Analysis Level:</strong> """ + level.upper() + """<br>
            <strong>Effort Level:</strong> """ + effort.upper() + """<br>
            <strong>Model Context:</strong> """ + model.upper() + """
        </div>
    """
    
    # 1. Descriptive Statistics
    html_content += """
    <div class="section">
        <h2>1. Descriptive Statistics</h2>
        <table>
            <tr>
                <th>Column</th>
                <th>Count</th>
                <th>Mean</th>
                <th>Std Dev</th>
                <th>Min</th>
                <th>Q1 (25%)</th>
                <th>Median</th>
                <th>Q3 (75%)</th>
                <th>Max</th>
                <th>Range</th>
            </tr>
    """
    
    desc_stats = df[numeric_cols].describe()
    
    for col in numeric_cols:
        col_data = df[col].dropna()
        col_range = col_data.max() - col_data.min()
        
        html_content += f"""
            <tr>
                <td><strong>{col}</strong></td>
                <td>{int(desc_stats.loc['count', col])}</td>
                <td>{desc_stats.loc['mean', col]:.4f}</td>
                <td>{desc_stats.loc['std', col]:.4f}</td>
                <td>{desc_stats.loc['min', col]:.4f}</td>
                <td>{desc_stats.loc['25%', col]:.4f}</td>
                <td>{desc_stats.loc['50%', col]:.4f}</td>
                <td>{desc_stats.loc['75%', col]:.4f}</td>
                <td>{desc_stats.loc['max', col]:.4f}</td>
                <td>{col_range:.4f}</td>
            </tr>
        """
    
    html_content += "</table></div>"
    
    # 2. Distribution Shape Analysis
    html_content += """
    <div class="section">
        <h2>2. Distribution Shape Analysis (Skewness & Kurtosis)</h2>
        <table>
            <tr>
                <th>Column</th>
                <th>Skewness</th>
                <th>Skew Interpretation</th>
                <th>Kurtosis</th>
                <th>Kurt Interpretation</th>
                <th>Jarque-Bera p-value</th>
            </tr>
    """
    
    shape_analysis = calculate_skewness_kurtosis(df, numeric_cols)
    
    for col, stats_dict in shape_analysis.items():
        skew = stats_dict['skewness']
        kurt = stats_dict['kurtosis']
        jb_pvalue = stats_dict['jarque_bera_pvalue']
        
        # Interpret skewness
        if abs(skew) < 0.5:
            skew_interp = "Fairly Symmetrical"
        elif skew > 0:
            skew_interp = f"Right-skewed (positive)"
        else:
            skew_interp = f"Left-skewed (negative)"
        
        # Interpret kurtosis
        if abs(kurt) < 0.5:
            kurt_interp = "Normal (mesokurtic)"
        elif kurt > 0:
            kurt_interp = "Heavy-tailed (leptokurtic)"
        else:
            kurt_interp = "Light-tailed (platykurtic)"
        
        html_content += f"""
            <tr>
                <td><strong>{col}</strong></td>
                <td>{skew:.4f}</td>
                <td>{skew_interp}</td>
                <td>{kurt:.4f}</td>
                <td>{kurt_interp}</td>
                <td>{jb_pvalue:.6f}</td>
            </tr>
        """
    
    html_content += "</table></div>"
    
    # 3. Normality Testing
    html_content += """
    <div class="section">
        <h2>3. Normality Testing</h2>
        <table>
            <tr>
                <th>Column</th>
                <th>Test Statistic</th>
                <th>p-value</th>
                <th>Is Normal?</th>
                <th>Interpretation</th>
            </tr>
    """
    
    normality_tests = test_normality(df, numeric_cols)
    
    for col, test_dict in normality_tests.items():
        is_normal = test_dict['is_normal']
        row_class = 'normal' if is_normal else 'not-normal'
        
        html_content += f"""
            <tr class="{row_class}">
                <td><strong>{col}</strong></td>
                <td>{test_dict['test_statistic']:.4f}</td>
                <td>{test_dict['p_value']:.6f}</td>
                <td>{"✅ Yes" if is_normal else "❌ No"}</td>
                <td>{"Normally distributed (α=0.05)" if is_normal else "Non-normal distribution"}</td>
            </tr>
        """
    
    html_content += "</table></div>"
    
    # 4. Correlation Analysis
    html_content += """
    <div class="section">
        <h2>4. Correlation Matrix</h2>
        <table>
    """
    
    if len(numeric_cols) > 1:
        corr_matrix = df[numeric_cols].corr()
        
        # Header
        html_content += "<tr><th>Feature</th>"
        for col in numeric_cols:
            html_content += f"<th>{col}</th>"
        html_content += "</tr>"
        
        # Rows
        for col1 in numeric_cols:
            html_content += f"<tr><th>{col1}</th>"
            for col2 in numeric_cols:
                corr_val = corr_matrix.loc[col1, col2]
                
                # Color based on correlation strength
                if abs(corr_val) > 0.7:
                    color = '#ff6b6b'  # Strong
                elif abs(corr_val) > 0.4:
                    color = '#ffd93d'  # Moderate
                else:
                    color = '#6bcf7f'  # Weak
                
                html_content += f'<td style="background-color: {color}; opacity: {abs(corr_val)};">{corr_val:.3f}</td>'
            html_content += "</tr>"
    
    html_content += "</table></div>"
    
    # 5. Group Statistics (if categorical variables exist)
    if categorical_cols and numeric_cols:
        html_content += """
        <div class="section">
            <h2>5. Group Statistics</h2>
        """
        
        for cat_col in categorical_cols[:3]:  # Limit to first 3 categorical columns
            html_content += f"<h3>Groups by {cat_col}</h3>"
            
            group_stats = calculate_group_statistics(df, numeric_cols, cat_col)
            
            for num_col, group_data in group_stats.items():
                html_content += f"""
                <h4>{num_col}</h4>
                <table>
                    <tr>
                        <th>Group</th>
                        <th>Count</th>
                        <th>Mean</th>
                        <th>Std Dev</th>
                        <th>Min</th>
                        <th>Max</th>
                    </tr>
                """
                
                for group_name, row in group_data.iterrows():
                    html_content += f"""
                    <tr>
                        <td><strong>{group_name}</strong></td>
                        <td>{int(row['count'])}</td>
                        <td>{row['mean']:.4f}</td>
                        <td>{row['std']:.4f}</td>
                        <td>{row['min']:.4f}</td>
                        <td>{row['max']:.4f}</td>
                    </tr>
                    """
                
                html_content += "</table>"
        
        html_content += "</div>"
    
    # 6. Statistical Insights
    html_content += """
    <div class="section">
        <h2>6. Key Statistical Insights</h2>
        <ul>
    """
    
    # Count non-normal distributions
    non_normal_count = sum(1 for test in normality_tests.values() if not test['is_normal'])
    html_content += f"<li><strong>Non-normal Distributions:</strong> {non_normal_count} out of {len(numeric_cols)} features are non-normally distributed. Consider transformations for linear models.</li>"
    
    # High correlations
    if len(numeric_cols) > 1:
        high_corr_pairs = []
        corr_matrix = df[numeric_cols].corr()
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i+1:]:
                if abs(corr_matrix.loc[col1, col2]) > 0.8:
                    high_corr_pairs.append((col1, col2, corr_matrix.loc[col1, col2]))
        
        if high_corr_pairs:
            html_content += f"<li><strong>Highly Correlated Features:</strong> Found {len(high_corr_pairs)} pairs with |correlation| > 0.8. Consider multicollinearity in modeling.</li>"
            for col1, col2, corr in high_corr_pairs[:5]:
                html_content += f"<ul><li>{col1} & {col2}: {corr:.3f}</li></ul>"
    
    html_content += """
        </ul>
    </div>
    """
    
    # 7. Recommendations
    html_content += """
    <div class="section">
        <h2>7. Recommendations</h2>
        <ul>
            <li><strong>For Non-Normal Distributions:</strong> Apply log, square root, or Box-Cox transformations before using linear models</li>
            <li><strong>For High Correlations:</strong> Remove redundant features or use dimensionality reduction (PCA)</li>
            <li><strong>For Skewed Data:</strong> Use robust scaling or quantile normalization</li>
            <li><strong>For Outliers:</strong> Use robust statistical methods or cap extreme values</li>
            <li><strong>For Group Differences:</strong> Use ANOVA or Kruskal-Wallis test to test significance</li>
        </ul>
    </div>
    """
    
    html_content += """
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Statistical analysis report saved to {output_file}")
    print(f"\n📈 Statistical Summary:")
    print(f"   - Numeric Features: {len(numeric_cols)}")
    print(f"   - Normal Distributions: {len(numeric_cols) - non_normal_count}/{len(numeric_cols)}")
    print(f"   - Average Skewness: {np.mean([abs(s['skewness']) for s in shape_analysis.values()]):.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate statistical analysis report')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', default=None, help='Output HTML file')
    parser.add_argument('--level', choices=['basic', 'standard', 'advanced'], default='standard', help='Analysis depth level')
    parser.add_argument('--effort', choices=['quick', 'standard', 'thorough'], default='standard', help='Effort level')
    parser.add_argument('--model', default='default', help='Model context')
    parser.add_argument('--name', default=None, help='Dataset name')
    
    args = parser.parse_args()
    generate_statistical_analysis_report(args.input, args.output, args.level, args.effort, args.model, args.name)
