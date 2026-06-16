#!/usr/bin/env python3
"""
Phase 5: Visualization & Reporting
Generate comprehensive visualization suite and executive summary.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import argparse
import warnings
warnings.filterwarnings('ignore')

def generate_visualization_report(input_file, output_file=None, level="standard", effort="standard", 
                                 model="default", dataset_name=None):
    """Generate comprehensive visualization report with customizable depth."""
    
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    if output_file is None:
        output_file = Path(input_file).stem + "_visualization_report.html"
    
    if dataset_name is None:
        dataset_name = Path(input_file).stem
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Adjust visualization depth based on level and effort
    figure_width = 14 if level == 'advanced' else 12
    figure_dpi = 150 if effort == 'thorough' else 100
    max_scatter_plots = 8 if level == 'advanced' else 4
    
    html_content = """
    <html>
    <head>
        <title>Visualization Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .section { background-color: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #e67e22; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            .chart-container { margin: 20px 0; }
            img { max-width: 100%; height: auto; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
            .stat-box { background-color: #ecf0f1; padding: 15px; border-radius: 5px; border-left: 4px solid #e67e22; }
            .metadata { font-size: 12px; color: #7f8c8d; background-color: #ecf0f1; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>📈 Visualization & Reporting</h1>
        <div class="metadata">
            <strong>Dataset:</strong> """ + dataset_name + """<br>
            <strong>Analysis Level:</strong> """ + level.upper() + """<br>
            <strong>Effort Level:</strong> """ + effort.upper() + """<br>
            <strong>Model Context:</strong> """ + model.upper() + """
        </div>
    """
    
    # Set style
    sns.set_style("whitegrid")
    plt.rcParams['figure.figsize'] = (figure_width, 6)
    
    # 1. Overview
    html_content += f"""
    <div class="section">
        <h2>1. Dataset Overview</h2>
        <div class="stat-grid">
            <div class="stat-box"><strong>Total Records:</strong> {len(df):,}</div>
            <div class="stat-box"><strong>Total Features:</strong> {len(df.columns)}</div>
            <div class="stat-box"><strong>Numeric Features:</strong> {len(numeric_cols)}</div>
            <div class="stat-box"><strong>Categorical Features:</strong> {len(categorical_cols)}</div>
        </div>
    </div>
    """
    
    # 2. Numeric Feature Distributions
    if numeric_cols:
        html_content += """
        <div class="section">
            <h2>2. Numeric Feature Distributions</h2>
        """
        
        # Create grid of histograms
        n_cols = min(3, len(numeric_cols))
        n_rows = (len(numeric_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 4*n_rows))
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        for idx, col in enumerate(numeric_cols):
            ax = axes[idx]
            ax.hist(df[col].dropna(), bins=30, edgecolor='black', alpha=0.7, color='#e67e22')
            ax.set_title(f'{col}', fontsize=12, fontweight='bold')
            ax.set_xlabel(col)
            ax.set_ylabel('Frequency')
            ax.grid(axis='y', alpha=0.3)
        
        # Hide empty subplots
        for idx in range(len(numeric_cols), len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        plt.savefig('temp_distributions.png', dpi=figure_dpi, bbox_inches='tight')
        plt.close()
        
        with open('temp_distributions.png', 'rb') as img_file:
            import base64
            img_base64 = base64.b64encode(img_file.read()).decode()
            html_content += f"""
            <div class="chart-container">
                <h3>Distribution Charts</h3>
                <img src="data:image/png;base64,{img_base64}" />
            </div>
            """
        
        Path('temp_distributions.png').unlink()
        html_content += "</div>"
    
    # 3. Box Plots (Outlier Detection)
    if numeric_cols and len(numeric_cols) > 1:
        html_content += """
        <div class="section">
            <h2>3. Box Plots (Outlier Detection)</h2>
        """
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Normalize data for comparison
        normalized_data = df[numeric_cols].copy()
        for col in numeric_cols:
            normalized_data[col] = (df[col] - df[col].mean()) / df[col].std()
        
        normalized_data.boxplot(ax=ax, patch_artist=True)
        ax.set_title('Box Plot Comparison (Normalized Values)', fontsize=14, fontweight='bold')
        ax.set_ylabel('Normalized Value')
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('temp_boxplots.png', dpi=figure_dpi, bbox_inches='tight')
        plt.close()
        
        with open('temp_boxplots.png', 'rb') as img_file:
            import base64
            img_base64 = base64.b64encode(img_file.read()).decode()
            html_content += f"""
            <div class="chart-container">
                <img src="data:image/png;base64,{img_base64}" />
            </div>
            """
        
        Path('temp_boxplots.png').unlink()
        html_content += "</div>"
    
    # 4. Correlation Heatmap
    if numeric_cols and len(numeric_cols) > 1:
        html_content += """
        <div class="section">
            <h2>4. Correlation Heatmap</h2>
        """
        
        fig, ax = plt.subplots(figsize=(10, 8))
        corr_matrix = df[numeric_cols].corr()
        
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='coolwarm', center=0,
                   square=True, ax=ax, cbar_kws={'label': 'Correlation Coefficient'},
                   linewidths=0.5)
        ax.set_title('Feature Correlation Matrix', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        plt.savefig('temp_heatmap.png', dpi=figure_dpi, bbox_inches='tight')
        plt.close()
        
        with open('temp_heatmap.png', 'rb') as img_file:
            import base64
            img_base64 = base64.b64encode(img_file.read()).decode()
            html_content += f"""
            <div class="chart-container">
                <img src="data:image/png;base64,{img_base64}" />
            </div>
            """
        
        Path('temp_heatmap.png').unlink()
        html_content += "</div>"
    
    # 5. Categorical Feature Value Counts
    if categorical_cols:
        html_content += """
        <div class="section">
            <h2>5. Categorical Features Distribution</h2>
        """
        
        n_cols = min(2, len(categorical_cols))
        n_rows = (len(categorical_cols) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(14, 4*n_rows))
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        for idx, col in enumerate(categorical_cols[:len(axes)]):
            ax = axes[idx]
            value_counts = df[col].value_counts().head(10)
            value_counts.plot(kind='bar', ax=ax, color='#e67e22', edgecolor='black')
            ax.set_title(f'{col} (Top 10)', fontsize=12, fontweight='bold')
            ax.set_xlabel(col)
            ax.set_ylabel('Count')
            ax.tick_params(axis='x', rotation=45)
            ax.grid(axis='y', alpha=0.3)
        
        # Hide empty subplots
        for idx in range(len(categorical_cols), len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        plt.savefig('temp_categorical.png', dpi=figure_dpi, bbox_inches='tight')
        plt.close()
        
        with open('temp_categorical.png', 'rb') as img_file:
            import base64
            img_base64 = base64.b64encode(img_file.read()).decode()
            html_content += f"""
            <div class="chart-container">
                <img src="data:image/png;base64,{img_base64}" />
            </div>
            """
        
        Path('temp_categorical.png').unlink()
        html_content += "</div>"
    
    # 6. Scatter Plots (Pairwise Relationships)
    if len(numeric_cols) >= 2:
        html_content += """
        <div class="section">
            <h2>6. Feature Relationships (Scatter Plots)</h2>
        """
        
        n_plots = min(max_scatter_plots, len(numeric_cols) * (len(numeric_cols) - 1) // 2)
        n_cols = 2
        n_rows = (n_plots + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, 4*n_rows))
        if n_rows == 1 and n_cols == 1:
            axes = [axes]
        elif n_rows == 1:
            axes = axes.flatten()
        else:
            axes = axes.flatten()
        
        plot_idx = 0
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i+1:]:
                if plot_idx < n_plots:
                    ax = axes[plot_idx]
                    ax.scatter(df[col1], df[col2], alpha=0.5, s=20, color='#e67e22')
                    ax.set_xlabel(col1)
                    ax.set_ylabel(col2)
                    ax.set_title(f'{col1} vs {col2}', fontsize=11, fontweight='bold')
                    ax.grid(alpha=0.3)
                    plot_idx += 1
        
        # Hide empty subplots
        for idx in range(plot_idx, len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        plt.savefig('temp_scatter.png', dpi=figure_dpi, bbox_inches='tight')
        plt.close()
        
        with open('temp_scatter.png', 'rb') as img_file:
            import base64
            img_base64 = base64.b64encode(img_file.read()).decode()
            html_content += f"""
            <div class="chart-container">
                <img src="data:image/png;base64,{img_base64}" />
            </div>
            """
        
        Path('temp_scatter.png').unlink()
        html_content += "</div>"
    
    # 7. Summary Statistics Table
    html_content += """
    <div class="section">
        <h2>7. Complete Statistical Summary</h2>
        <table style="border-collapse: collapse; width: 100%; margin: 15px 0; font-size: 12px;">
            <tr>
                <th style="background-color: #e67e22; color: white; padding: 10px; text-align: left;">Feature</th>
                <th style="background-color: #e67e22; color: white; padding: 10px; text-align: center;">Type</th>
                <th style="background-color: #e67e22; color: white; padding: 10px; text-align: center;">Missing</th>
                <th style="background-color: #e67e22; color: white; padding: 10px; text-align: center;">Unique</th>
            </tr>
    """
    
    for col in df.columns:
        col_type = 'Numeric' if pd.api.types.is_numeric_dtype(df[col]) else 'Categorical'
        missing = df[col].isnull().sum()
        unique = df[col].nunique()
        
        html_content += f"""
            <tr style="border: 1px solid #ddd;">
                <td style="padding: 10px;"><strong>{col}</strong></td>
                <td style="padding: 10px; text-align: center;">{col_type}</td>
                <td style="padding: 10px; text-align: center;">{missing}</td>
                <td style="padding: 10px; text-align: center;">{unique}</td>
            </tr>
        """
    
    html_content += """
        </table>
    </div>
    """
    
    html_content += """
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Visualization report saved to {output_file}")
    print(f"\n📊 Visualization Summary:")
    print(f"   - Charts Generated: {5 if numeric_cols else 0}")
    print(f"   - Distribution plots: {min(3, len(numeric_cols))}")
    print(f"   - Correlation heatmap: {'Yes' if len(numeric_cols) > 1 else 'No'}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate visualization report')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', default=None, help='Output HTML file')
    parser.add_argument('--level', choices=['basic', 'standard', 'advanced'], default='standard', help='Analysis depth level')
    parser.add_argument('--effort', choices=['quick', 'standard', 'thorough'], default='standard', help='Effort level')
    parser.add_argument('--model', default='default', help='Model context')
    parser.add_argument('--name', default=None, help='Dataset name')
    
    args = parser.parse_args()
    generate_visualization_report(args.input, args.output, args.level, args.effort, args.model, args.name)
