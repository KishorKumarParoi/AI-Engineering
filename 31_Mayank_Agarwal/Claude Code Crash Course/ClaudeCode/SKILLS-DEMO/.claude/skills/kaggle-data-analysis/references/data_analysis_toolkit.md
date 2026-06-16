# Python Data Analysis Toolkit

## Essential Libraries

### Pandas - Data Manipulation
```python
import pandas as pd

# Load data
df = pd.read_csv('data.csv')

# Basic exploration
df.head()              # First 5 rows
df.info()              # Data types and missing values
df.describe()          # Statistical summary
df.shape               # Dimensions

# Selection
df['column']           # Single column
df[['col1', 'col2']]   # Multiple columns
df.iloc[0:5]           # Position-based
df.loc[df['age'] > 30] # Label-based

# Missing values
df.isnull().sum()              # Count missing
df.fillna(value)               # Fill with value
df.dropna()                    # Remove missing
df.interpolate()               # Interpolate

# Grouping and aggregation
df.groupby('category').mean()
df.groupby('category').agg({'col1': 'sum', 'col2': 'mean'})

# Merging
pd.merge(df1, df2, on='key')
pd.concat([df1, df2])
```

### NumPy - Numerical Computing
```python
import numpy as np

# Arrays
arr = np.array([1, 2, 3])
zeros = np.zeros((3, 3))
ones = np.ones((3, 3))
random = np.random.rand(3, 3)

# Operations
arr.mean(), arr.std(), arr.min(), arr.max()
np.where(arr > 2, 1, 0)     # Conditional
np.corrcoef(x, y)           # Correlation
np.polyfit(x, y, 2)         # Polynomial fit

# Reshaping
arr.reshape(3, 1)
arr.flatten()
np.transpose(arr)
```

### Scikit-learn - Machine Learning
```python
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score

# Scaling
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

# Model training
model = RandomForestClassifier(n_estimators=100)
model.fit(X_train, y_train)

# Predictions
y_pred = model.predict(X_test)

# Evaluation
accuracy = accuracy_score(y_test, y_pred)
cv_scores = cross_val_score(model, X, y, cv=5)
```

### Matplotlib & Seaborn - Visualization
```python
import matplotlib.pyplot as plt
import seaborn as sns

# Basic plots
plt.plot(x, y)              # Line plot
plt.scatter(x, y)           # Scatter plot
plt.hist(data, bins=20)     # Histogram
plt.bar(categories, values) # Bar plot

# Seaborn
sns.heatmap(df.corr(), annot=True)  # Heatmap
sns.boxplot(data=df, x='cat', y='num')  # Box plot
sns.violinplot(data=df, x='cat', y='num')  # Violin plot

# Customization
plt.title('Title')
plt.xlabel('X Label')
plt.ylabel('Y Label')
plt.legend()
plt.show()

# Multiple subplots
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes[0, 0].plot(x, y)
```

## Common Data Analysis Tasks

### 1. Handling Missing Values
```python
# Check missing values
print(df.isnull().sum())

# Drop rows with any missing
df.dropna()

# Drop specific column if too many missing
if df['col'].isnull().sum() / len(df) > 0.3:
    df = df.drop('col', axis=1)

# Fill numeric with mean
df['numeric_col'].fillna(df['numeric_col'].mean(), inplace=True)

# Fill categorical with mode
df['category_col'].fillna(df['category_col'].mode()[0], inplace=True)

# Forward fill (for time series)
df['col'].fillna(method='ffill', inplace=True)
```

### 2. Handling Outliers
```python
# IQR method
Q1 = df['col'].quantile(0.25)
Q3 = df['col'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR
df_clean = df[(df['col'] >= lower_bound) & (df['col'] <= upper_bound)]

# Z-score method
from scipy import stats
z_scores = np.abs(stats.zscore(df['col']))
df_clean = df[z_scores < 3]

# Capping
df['col'] = df['col'].clip(lower=lower_bound, upper=upper_bound)
```

### 3. Feature Engineering
```python
# Polynomial features
from sklearn.preprocessing import PolynomialFeatures
poly = PolynomialFeatures(degree=2)
X_poly = poly.fit_transform(X)

# Binning
df['age_group'] = pd.cut(df['age'], bins=[0, 18, 35, 50, 65, 100])

# One-hot encoding
df = pd.get_dummies(df, columns=['category'])

# Label encoding
from sklearn.preprocessing import LabelEncoder
le = LabelEncoder()
df['encoded'] = le.fit_transform(df['category'])

# Interaction features
df['interaction'] = df['col1'] * df['col2']
```

### 4. Exploratory Data Analysis
```python
# Correlation analysis
corr_matrix = df.corr()
print(corr_matrix['target'].sort_values(ascending=False))

# Distribution analysis
df['col'].value_counts()
df['col'].hist(bins=20)

# Grouping analysis
df.groupby('category').agg({
    'value': ['mean', 'std', 'min', 'max']
})
```

## Performance Tips

### Memory Optimization
```python
# Use efficient data types
df['int_col'] = df['int_col'].astype('int32')
df['cat_col'] = df['cat_col'].astype('category')

# Read only needed columns
df = pd.read_csv('large_file.csv', usecols=['col1', 'col2'])

# Read in chunks for very large files
chunks = pd.read_csv('huge_file.csv', chunksize=10000)
for chunk in chunks:
    process(chunk)
```

### Computation Optimization
```python
# Vectorized operations (faster)
df['new_col'] = df['col1'] + df['col2']

# Avoid loops
# Instead of:
# result = []
# for i in range(len(df)):
#     result.append(df.iloc[i]['col'] * 2)

# Use:
result = df['col'] * 2

# Use apply efficiently
df['new_col'] = df['col'].apply(function)

# Parallel processing
from joblib import Parallel, delayed
results = Parallel(n_jobs=-1)(delayed(func)(row) for row in df.iterrows())
```

## Useful Snippets

### Find columns by data type
```python
numeric_cols = df.select_dtypes(include=[np.number]).columns
categorical_cols = df.select_dtypes(include=['object']).columns
```

### Duplicate detection
```python
df[df.duplicated(subset=['col1', 'col2'], keep=False)]
df.drop_duplicates(inplace=True)
```

### Data type conversion
```python
df['date'] = pd.to_datetime(df['date'])
df['number'] = pd.to_numeric(df['number'], errors='coerce')
```

### Renaming columns
```python
df.rename(columns={'old_name': 'new_name'}, inplace=True)
```

### Reset index
```python
df.reset_index(drop=True, inplace=True)
```

### Sorting
```python
df.sort_values('column', ascending=False)
df.sort_values(['col1', 'col2'], ascending=[True, False])
```

### Statistical summary
```python
from scipy.stats import describe
describe(df['column'])
```
