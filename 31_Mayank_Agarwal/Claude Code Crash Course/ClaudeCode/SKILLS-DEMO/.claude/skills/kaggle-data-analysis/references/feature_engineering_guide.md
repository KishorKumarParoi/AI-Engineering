# Feature Engineering Guide

## Types of Features to Create

### 1. Polynomial Features
Create higher-order interactions of numeric features.

**When to use:**
- Non-linear relationships suspected
- Decision trees (can capture implicitly)
- Linear/logistic regression (need explicit polynomials)

**Example:**
```python
from sklearn.preprocessing import PolynomialFeatures
poly = PolynomialFeatures(degree=2, include_bias=False)
X_poly = poly.fit_transform(X)
```

### 2. Interaction Features
Multiply or divide related features.

**Common combinations:**
- Ratio features: A / B
- Product features: A * B
- Sum features: A + B
- Difference features: A - B

**Business logic:**
- Price * Quantity → Total Revenue
- Area * Price per Area → Total Price
- Score1 * Weight1 + Score2 * Weight2 → Weighted Score

### 3. Domain-Specific Features
Create features based on domain knowledge.

**Examples by domain:**

**E-commerce:**
- Customer lifetime value
- Purchase frequency
- Average order value
- Time since last purchase

**Finance:**
- Debt-to-income ratio
- Return on investment
- Volatility measures
- Trend indicators

**Healthcare:**
- BMI (weight / height²)
- Age groups
- Risk scores
- Comorbidity index

### 4. Temporal Features
Extract time-based information.

**From datetime columns:**
- Year, month, day, day of week
- Quarter, week number
- Days since a reference date
- Is holiday, is weekend
- Seasonal indicators

**Example:**
```python
df['day_of_week'] = df['date'].dt.dayofweek
df['month'] = df['date'].dt.month
df['days_since_start'] = (df['date'] - df['date'].min()).dt.days
```

### 5. Aggregation Features
Create features by grouping data.

**Examples:**
- Mean, median, std of groups
- Count of items per group
- Min/max values in group
- Rank within group

**Example:**
```python
user_mean = df.groupby('user_id')['amount'].transform('mean')
user_count = df.groupby('user_id').size()
```

### 6. Binning and Bucketing
Convert continuous to categorical.

**Strategies:**
- Equal width binning
- Equal frequency (quantile) binning
- Custom business logic

**Example:**
```python
df['age_group'] = pd.cut(df['age'], bins=[0, 18, 35, 50, 65, 100])
df['income_bucket'] = pd.qcut(df['income'], q=4)
```

### 7. Text Features
Extract information from text.

**Common approaches:**
- Word count
- Character count
- Average word length
- Presence of specific keywords
- TF-IDF scores

### 8. Encoding Categorical Variables

**Binary Variables:**
```python
# Label encoding
df['encoded'] = (df['category'] == 'A').astype(int)
```

**Multiple Categories (Few):**
```python
# One-hot encoding
df = pd.get_dummies(df, columns=['category'], drop_first=True)
```

**Multiple Categories (Many):**
```python
# Target encoding
target_mean = df.groupby('category')['target'].mean()
df['encoded'] = df['category'].map(target_mean)

# Frequency encoding
freq = df['category'].value_counts()
df['encoded'] = df['category'].map(freq)
```

## Feature Selection Strategies

### 1. Correlation-Based
Remove features highly correlated with others.

```python
corr_matrix = df.corr()
# Find highly correlated pairs
high_corr_pairs = np.argwhere(np.abs(corr_matrix) > 0.9)
```

### 2. Variance Threshold
Remove low-variance features.

```python
from sklearn.feature_selection import VarianceThreshold
selector = VarianceThreshold(threshold=0.01)
X_selected = selector.fit_transform(X)
```

### 3. Univariate Statistical Tests
Select features with strong individual relationships to target.

```python
from sklearn.feature_selection import SelectKBest, f_classif
selector = SelectKBest(f_classif, k=10)
X_selected = selector.fit_transform(X, y)
```

### 4. Model-Based Importance
Use model feature importance scores.

```python
# Tree-based models
from sklearn.ensemble import RandomForestClassifier
rf = RandomForestClassifier()
rf.fit(X, y)
importances = rf.feature_importances_
```

### 5. Permutation Importance
Measure how much model performance drops when feature is shuffled.

```python
from sklearn.inspection import permutation_importance
perm_importance = permutation_importance(model, X, y)
```

## Feature Scaling

### When to Scale
- Linear/logistic regression
- Distance-based algorithms (KNN, K-Means)
- Neural networks
- Algorithms with regularization (Ridge, Lasso)

### When NOT to Scale
- Tree-based models (independent of scale)
- Models using only binary splits

### Scaling Methods

**StandardScaler:**
- Center to mean 0, scale to std 1
- Good for normally distributed data
- Default for most algorithms

**MinMaxScaler:**
- Scale to [0, 1] range
- Good for neural networks
- Sensitive to outliers

**RobustScaler:**
- Uses median and IQR
- Better with outliers
- Good when outliers should be retained

**Log Transformation:**
- For skewed distributions
- Reduces effect of outliers
- Good for right-skewed data

```python
df['log_feature'] = np.log1p(df['feature'])  # log1p handles 0s
```

## Feature Engineering Checklist

- [ ] Understand the target variable and problem
- [ ] Create domain-relevant features based on business logic
- [ ] Identify and handle missing values appropriately
- [ ] Create polynomial/interaction features where meaningful
- [ ] Add temporal features if time is relevant
- [ ] Engineer aggregation features from grouping
- [ ] Apply appropriate encoding for categorical variables
- [ ] Create binned/bucketed versions of continuous features
- [ ] Scale/normalize features as needed
- [ ] Remove low-variance or highly correlated features
- [ ] Perform statistical tests on new features
- [ ] Validate that new features improve model performance
- [ ] Document feature engineering logic for reproducibility

## Common Pitfalls

1. **Overfitting**: Creating too many features without regularization
2. **Data Leakage**: Using future information to create features
3. **Ignoring Domain Knowledge**: Using only statistical approaches
4. **Feature Explosion**: Creating too many interaction features
5. **Encoding Errors**: Inconsistent encoding between train/test
6. **Forgetting Features**: Not applying same transformations to test data
