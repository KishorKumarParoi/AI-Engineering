#!/usr/bin/env python3
"""
Data Preprocessing & Feature Engineering Script
Applies all analysis recommendations: handles missing values, outliers,
and creates engineered features for Titanic dataset.
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, LabelEncoder
from pathlib import Path
import argparse


def load_data(input_file):
  """Load CSV file and return DataFrame."""
  print(f"📂 Loading data from {input_file}...")
  df = pd.read_csv(input_file)
  print(f"✅ Loaded {len(df)} rows × {len(df.columns)} columns\n")
  return df


def analyze_missing_values(df):
  """Analyze and report missing values in dataset."""
  missing = df.isnull().sum()
  missing_pct = (missing / len(df)) * 100

  print("📊 Missing Values Analysis:")
  for col in missing[missing > 0].index:
    print(f"   {col}: {missing[col]} ({missing_pct[col]:.1f}%)")
  print()

  return missing


def handle_missing_values(df):
  """Handle missing values based on column type and analysis findings."""
  df = df.copy()

  print("🔧 Handling Missing Values:")

  # Age: fill with median (numeric, skewed distribution)
  if 'Age' in df.columns and df['Age'].isnull().sum() > 0:
    age_median = df['Age'].median()
    df['Age'] = df['Age'].fillna(age_median)
    print(f"   Age: filled with median ({age_median:.1f})")

  # Embarked: fill with mode (categorical)
  if 'Embarked' in df.columns and df['Embarked'].isnull().sum() > 0:
    embarked_mode = df['Embarked'].mode()[0]
    df['Embarked'] = df['Embarked'].fillna(embarked_mode)
    print(f"   Embarked: filled with mode ({embarked_mode})")

  # Cabin: fill with 'Unknown' (categorical, too sparse)
  if 'Cabin' in df.columns and df['Cabin'].isnull().sum() > 0:
    df['Cabin'] = df['Cabin'].fillna('Unknown')
    print(f"   Cabin: filled with 'Unknown'")

  print()
  return df


def handle_outliers(df):
  """Detect and handle outliers using IQR method."""
  df = df.copy()
  numeric_cols = df.select_dtypes(include=[np.number]).columns

  print("🎯 Outlier Detection & Treatment (IQR method):")
  outliers_removed = 0

  for col in numeric_cols:
    if col == 'PassengerId':  # Skip ID column
      continue

    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    outlier_count = ((df[col] < lower_bound) | (df[col] > upper_bound)).sum()
    if outlier_count > 0:
      # Cap outliers instead of removing rows
      df[col] = df[col].clip(lower_bound, upper_bound)
      outliers_removed += outlier_count
      print(f"   {col}: capped {outlier_count} outliers")

  print(f"   Total outliers treated: {outliers_removed}\n")
  return df


def encode_categorical(df):
  """Encode categorical variables."""
  df = df.copy()

  print("🔤 Categorical Encoding:")
  categorical_cols = df.select_dtypes(include=['object']).columns

  for col in categorical_cols:
    if col not in ['PassengerId', 'Name', 'Ticket']:
      le = LabelEncoder()
      df[col + '_encoded'] = le.fit_transform(df[col])
      print(f"   {col}: {len(le.classes_)} categories encoded")

  print()
  return df


def create_engineered_features(df):
  """Create polynomial and interaction features."""
  df = df.copy()

  print("⚙️  Feature Engineering:")

  # Polynomial features for numeric columns
  numeric_cols = ['Age', 'Fare', 'Parch', 'SibSp']
  for col in numeric_cols:
    if col in df.columns:
      df[f'{col}_squared'] = df[col] ** 2
      print(f"   Created: {col}_squared")

  # Interaction features
  interactions = [
    ('Age', 'Pclass'),
    ('Age', 'Fare'),
    ('Pclass', 'Fare'),
    ('SibSp', 'Parch'),
  ]

  for col1, col2 in interactions:
    if col1 in df.columns and col2 in df.columns:
      df[f'{col1}_x_{col2}'] = df[col1] * df[col2]
      print(f"   Created: {col1}_x_{col2}")

  # Family size feature
  if 'SibSp' in df.columns and 'Parch' in df.columns:
    df['FamilySize'] = df['SibSp'] + df['Parch'] + 1
    print(f"   Created: FamilySize (SibSp + Parch + 1)")

  # Cabin feature - extract deck info
  if 'Cabin' in df.columns:
    df['CabinDeck'] = df['Cabin'].str[0]
    df['CabinDeck'] = df['CabinDeck'].fillna('Unknown')
    print(f"   Created: CabinDeck")

  # Title extraction from Name
  if 'Name' in df.columns:
    df['Title'] = df['Name'].str.extract(r'([A-Za-z]+)\.', expand=False)
    print(f"   Created: Title")

  print()
  return df


def scale_features(df):
  """Standardize numeric features."""
  df = df.copy()

  print("📈 Feature Scaling (StandardScaler):")
  numeric_cols = df.select_dtypes(include=[np.number]).columns
  numeric_cols = [col for col in numeric_cols if col != 'PassengerId']

  scaler = StandardScaler()
  df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
  print(f"   Scaled {len(numeric_cols)} numeric features\n")

  return df


def save_processed_data(df, output_file):
  """Save processed dataset to CSV."""
  output_path = Path(output_file)
  output_path.parent.mkdir(parents=True, exist_ok=True)

  df.to_csv(output_file, index=False)
  print(f"✅ Processed data saved to: {output_file}")
  print(f"   Shape: {df.shape[0]} rows × {df.shape[1]} columns\n")

  return output_file


def generate_report(df_original, df_processed):
  """Generate processing summary report."""
  print("=" * 70)
  print("📋 PREPROCESSING & FEATURE ENGINEERING REPORT")
  print("=" * 70)
  print(f"\n📊 Dataset Transformation:")
  print(f"   Original:  {df_original.shape[0]} rows × {df_original.shape[1]} columns")
  print(f"   Processed: {df_processed.shape[0]} rows × {df_processed.shape[1]} columns")
  print(f"   New features created: {df_processed.shape[1] - df_original.shape[1]}")
  print(f"\n✨ Original Features: {list(df_original.columns)}")
  new_features = set(df_processed.columns) - set(df_original.columns)
  print(f"\n🆕 New Features ({len(new_features)}):")
  for feat in sorted(new_features):
    print(f"   - {feat}")
  print("\n" + "=" * 70)


def main():
  """Main processing pipeline."""
  parser = argparse.ArgumentParser(
    description='Preprocess and engineer features for Titanic dataset'
  )
  parser.add_argument('--input', default='titanic.csv',
                      help='Input CSV file (default: titanic.csv)')
  parser.add_argument('--output', default='titanic_processed.csv',
                      help='Output CSV file (default: titanic_processed.csv)')

  args = parser.parse_args()

  print("\n" + "=" * 70)
  print("🚀 DATA PREPROCESSING & FEATURE ENGINEERING")
  print("=" * 70 + "\n")

  # Load data
  df = load_data(args.input)
  df_original = df.copy()

  # Processing steps
  analyze_missing_values(df)
  df = handle_missing_values(df)
  df = handle_outliers(df)
  df = encode_categorical(df)
  df = create_engineered_features(df)
  df = scale_features(df)

  # Save processed data
  save_processed_data(df, args.output)

  # Generate report
  generate_report(df_original, df)

  print("\n✅ Processing complete!")
  print(f"🎯 Next steps: Use {args.output} for model training\n")


if __name__ == '__main__':
  main()
