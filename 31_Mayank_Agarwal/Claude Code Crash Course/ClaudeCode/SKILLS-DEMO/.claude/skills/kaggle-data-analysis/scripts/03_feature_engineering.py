#!/usr/bin/env python3
"""
Phase 3: Feature Engineering
Generates new features and analyzes feature importance.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import StandardScaler
from pathlib import Path
import argparse
import warnings
warnings.filterwarnings('ignore')

def generate_polynomial_features(df, numeric_cols, degree=2):
    """Generate polynomial features."""
    new_features = {}
    for col in numeric_cols:
        for d in range(2, degree + 1):
            new_col_name = f"{col}_pow{d}"
            new_features[new_col_name] = df[col] ** d
    return pd.DataFrame(new_features)

def generate_interaction_features(df, numeric_cols, limit=10):
    """Generate interaction features between numeric columns."""
    new_features = {}
    cols_to_use = numeric_cols[:limit]  # Limit to prevent explosion
    
    for i, col1 in enumerate(cols_to_use):
        for col2 in cols_to_use[i+1:]:
            new_col_name = f"{col1}_x_{col2}"
            new_features[new_col_name] = df[col1] * df[col2]
    
    return pd.DataFrame(new_features)

def calculate_feature_importance(df, numeric_cols):
    """Calculate feature importance based on correlation and variance."""
    importance_scores = {}
    
    for col in numeric_cols:
        # Variance-based importance
        variance = df[col].var()
        
        # Correlation-based importance (average absolute correlation with others)
        corr_with_others = df[numeric_cols].corr()[col].abs().sum() - 1  # -1 to exclude self
        avg_corr = corr_with_others / (len(numeric_cols) - 1) if len(numeric_cols) > 1 else 0
        
        # Combined score (normalized)
        variance_norm = variance / df[numeric_cols].var().max()
        
        importance_scores[col] = {
            'variance': variance_norm,
            'avg_correlation': avg_corr,
            'combined_score': (variance_norm + avg_corr) / 2
        }
    
    return importance_scores

def generate_feature_engineering_report(input_file, output_file=None, level="standard", effort="standard", 
                                       model="default", dataset_name=None):
    """Generate comprehensive feature engineering report with customizable depth."""
    
    print(f"Loading data from {input_file}...")
    df = pd.read_csv(input_file)
    
    if output_file is None:
        output_file = Path(input_file).stem + "_feature_engineering_report.html"
    
    if dataset_name is None:
        dataset_name = Path(input_file).stem
    
    Path(output_file).parent.mkdir(parents=True, exist_ok=True)
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    
    # Adjust feature engineering based on model and level
    max_features_to_generate = 20 if level == 'basic' else (50 if level == 'advanced' else 35)
    include_advanced_encoding = level in ['standard', 'advanced']
    
    html_content = """
    <html>
    <head>
        <title>Feature Engineering Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .section { background-color: white; padding: 20px; margin: 20px 0; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #9b59b6; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #9b59b6; color: white; }
            tr:nth-child(even) { background-color: #ecf0f1; }
            .stat-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; }
            .stat-box { background-color: #ecf0f1; padding: 15px; border-radius: 5px; border-left: 4px solid #9b59b6; }
            img { max-width: 100%; height: auto; margin: 15px 0; }
            .code { background-color: #2c3e50; color: #ecf0f1; padding: 10px; border-radius: 5px; overflow-x: auto; margin: 10px 0; }
            pre { margin: 0; }
            .metadata { font-size: 12px; color: #7f8c8d; background-color: #ecf0f1; padding: 10px; border-radius: 5px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <h1>🔨 Feature Engineering Report</h1>
        <div class="metadata">
            <strong>Dataset:</strong> """ + dataset_name + """<br>
            <strong>Analysis Level:</strong> """ + level.upper() + """<br>
            <strong>Effort Level:</strong> """ + effort.upper() + """<br>
            <strong>Model Context:</strong> """ + model.upper() + """
        </div>
    """
    
    # 1. Feature Overview
    html_content += f"""
    <div class="section">
        <h2>1. Feature Overview</h2>
        <div class="stat-grid">
            <div class="stat-box"><strong>Total Features:</strong> {len(df.columns)}</div>
            <div class="stat-box"><strong>Numeric Features:</strong> {len(numeric_cols)}</div>
            <div class="stat-box"><strong>Categorical Features:</strong> {len(categorical_cols)}</div>
            <div class="stat-box"><strong>Feature Count:</strong> {df.shape[1]}</div>
        </div>
    </div>
    """
    
    # 2. Feature Importance
    html_content += """
    <div class="section">
        <h2>2. Feature Importance Analysis</h2>
        <p>Based on variance and inter-feature correlation patterns:</p>
        <table>
            <tr>
                <th>Feature</th>
                <th>Variance Score</th>
                <th>Avg Correlation</th>
                <th>Combined Score</th>
                <th>Importance Rank</th>
            </tr>
    """
    
    importance_scores = calculate_feature_importance(df, numeric_cols)
    sorted_features = sorted(importance_scores.items(), 
                            key=lambda x: x[1]['combined_score'], 
                            reverse=True)
    
    for rank, (feature, scores) in enumerate(sorted_features, 1):
        html_content += f"""
            <tr>
                <td><strong>{feature}</strong></td>
                <td>{scores['variance']:.4f}</td>
                <td>{scores['avg_correlation']:.4f}</td>
                <td>{scores['combined_score']:.4f}</td>
                <td>#{rank}</td>
            </tr>
        """
    
    html_content += "</table></div>"
    
    # 3. Polynomial Features Suggestions
    html_content += f"""
    <div class="section">
        <h2>3. Polynomial Features (Degree 2)</h2>
        <p>Suggested polynomial features that can capture non-linear relationships:</p>
    """
    
    poly_features = generate_polynomial_features(df, numeric_cols[:5], degree=2)
    html_content += f"""
        <p><strong>Generated Features:</strong> {len(poly_features.columns)}</p>
        <h4>Examples:</h4>
        <ul>
    """
    
    for col in poly_features.columns[:10]:
        html_content += f"<li><code>{col}</code></li>"
    
    html_content += """
        </ul>
        <h4>Implementation Code:</h4>
        <div class="code"><pre>
from sklearn.preprocessing import PolynomialFeatures

poly = PolynomialFeatures(degree=2, include_bias=False)
poly_features = poly.fit_transform(df[numeric_features])
        </pre></div>
    </div>
    """
    
    # 4. Interaction Features
    html_content += f"""
    <div class="section">
        <h2>4. Interaction Features</h2>
        <p>Features created by multiplying pairs of numeric features:</p>
    """
    
    interaction_features = generate_interaction_features(df, numeric_cols[:5])
    html_content += f"""
        <p><strong>Generated Interaction Features:</strong> {len(interaction_features.columns)}</p>
        <h4>Examples:</h4>
        <ul>
    """
    
    for col in interaction_features.columns[:15]:
        html_content += f"<li><code>{col}</code></li>"
    
    html_content += """
        </ul>
    </div>
    """
    
    # 5. Categorical Feature Encoding
    html_content += f"""
    <div class="section">
        <h2>5. Categorical Feature Encoding Strategies</h2>
        <table>
            <tr>
                <th>Feature</th>
                <th>Unique Values</th>
                <th>Recommended Encoding</th>
                <th>Why</th>
            </tr>
    """
    
    for col in categorical_cols:
        unique_count = df[col].nunique()
        
        if unique_count == 2:
            recommended = "Binary/Label Encoding (0,1)"
            reason = "Only 2 categories"
        elif unique_count < 10:
            recommended = "One-Hot Encoding"
            reason = f"Few categories ({unique_count})"
        else:
            recommended = "Target Encoding or Ordinal"
            reason = f"Many categories ({unique_count}) - one-hot would expand features"
        
        html_content += f"""
            <tr>
                <td><strong>{col}</strong></td>
                <td>{unique_count}</td>
                <td>{recommended}</td>
                <td>{reason}</td>
            </tr>
        """
    
    html_content += """
        </table>
        <h4>Implementation Examples:</h4>
        <div class="code"><pre>
# One-Hot Encoding
df_encoded = pd.get_dummies(df, columns=['categorical_col'], drop_first=True)

# Label Encoding
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
df['encoded_col'] = le.fit_transform(df['categorical_col'])

# Target Encoding (requires target variable)
target_means = df.groupby('categorical_col')['target'].mean()
df['encoded_col'] = df['categorical_col'].map(target_means)
        </pre></div>
    </div>
    """
    
    # 6. Feature Scaling Recommendations
    html_content += """
    <div class="section">
        <h2>6. Feature Scaling Recommendations</h2>
        <table>
            <tr>
                <th>Scaling Method</th>
                <th>When to Use</th>
                <th>Code Example</th>
            </tr>
            <tr>
                <td><strong>StandardScaler</strong></td>
                <td>Linear models, distance-based algorithms</td>
                <td><code>StandardScaler()</code></td>
            </tr>
            <tr>
                <td><strong>MinMaxScaler</strong></td>
                <td>Neural networks, when features need 0-1 range</td>
                <td><code>MinMaxScaler()</code></td>
            </tr>
            <tr>
                <td><strong>RobustScaler</strong></td>
                <td>Data with outliers</td>
                <td><code>RobustScaler()</code></td>
            </tr>
            <tr>
                <td><strong>PowerTransformer</strong></td>
                <td>Non-normal distributions</td>
                <td><code>PowerTransformer()</code></td>
            </tr>
        </table>
    </div>
    """
    
    # 7. Feature Selection Tips
    html_content += """
    <div class="section">
        <h2>7. Feature Selection Best Practices</h2>
        <ul>
            <li><strong>Remove Low Variance Features:</strong> Features with very low variance add noise without signal</li>
            <li><strong>Remove Highly Correlated Features:</strong> Choose one from each highly correlated pair</li>
            <li><strong>Domain Knowledge:</strong> Remove features that don't make business sense</li>
            <li><strong>Multicollinearity Check:</strong> Use VIF (Variance Inflation Factor) to detect multicollinearity</li>
            <li><strong>Statistical Tests:</strong> Use chi-square for categorical, correlation for numeric</li>
        </ul>
        <h4>Code for Removing Low Variance Features:</h4>
        <div class="code"><pre>
from sklearn.feature_selection import VarianceThreshold

selector = VarianceThreshold(threshold=0.01)
X_selected = selector.fit_transform(X)
selected_features = X.columns[selector.get_support()]
        </pre></div>
    </div>
    """
    
    # 8. Action Items
    html_content += """
    <div class="section">
        <h2>8. Next Steps</h2>
        <ol>
            <li>Review top features by importance rank</li>
            <li>Encode categorical variables using recommended methods</li>
            <li>Generate polynomial and interaction features</li>
            <li>Apply feature scaling where appropriate</li>
            <li>Perform feature selection to reduce dimensionality</li>
            <li>Validate new features improve model performance</li>
        </ol>
    </div>
    """
    
    html_content += """
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html_content)
    
    print(f"✅ Feature engineering report saved to {output_file}")
    print(f"\n🔨 Feature Engineering Summary:")
    print(f"   - Numeric Features: {len(numeric_cols)}")
    print(f"   - Categorical Features: {len(categorical_cols)}")
    print(f"   - Suggested Polynomial Features: {len(poly_features.columns)}")
    print(f"   - Suggested Interaction Features: {len(interaction_features.columns)}")
    print(f"   - Top Feature: {sorted_features[0][0]}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate feature engineering report')
    parser.add_argument('--input', required=True, help='Input CSV file')
    parser.add_argument('--output', default=None, help='Output HTML file')
    parser.add_argument('--level', choices=['basic', 'standard', 'advanced'], default='standard', help='Analysis depth level')
    parser.add_argument('--effort', choices=['quick', 'standard', 'thorough'], default='standard', help='Effort level')
    parser.add_argument('--model', default='default', help='Model context')
    parser.add_argument('--name', default=None, help='Dataset name')
    
    args = parser.parse_args()
    generate_feature_engineering_report(args.input, args.output, args.level, args.effort, args.model, args.name)
