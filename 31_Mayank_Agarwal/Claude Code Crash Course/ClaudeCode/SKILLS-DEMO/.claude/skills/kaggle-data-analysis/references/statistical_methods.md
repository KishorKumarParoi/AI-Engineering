# Statistical Methods Reference

## Descriptive Statistics

### Measures of Central Tendency
- **Mean**: Average value (sensitive to outliers)
- **Median**: Middle value (robust to outliers)
- **Mode**: Most frequent value

### Measures of Spread
- **Range**: Max - Min
- **Variance**: Average squared deviation from mean
- **Standard Deviation**: Square root of variance
- **Interquartile Range (IQR)**: Q3 - Q1 (middle 50% of data)

### Interpreting Distributions

**Skewness:**
- Negative (left-skewed): Tail on left, mean < median
- Zero (symmetric): Mean ≈ median
- Positive (right-skewed): Tail on right, mean > median

**Kurtosis:**
- Negative (platykurtic): Lighter tails, flatter peak
- Zero (mesokurtic): Normal distribution-like tails
- Positive (leptokurtic): Heavier tails, sharper peak

## Normality Testing

### Tests for Normality

**Shapiro-Wilk Test:**
- Works well for samples ≤ 5000
- Most powerful test
- Null hypothesis: data is normally distributed

**Kolmogorov-Smirnov Test:**
- Works for larger samples
- Compares with theoretical distribution
- Less powerful than Shapiro-Wilk

**Anderson-Darling Test:**
- More sensitive to tails
- Better for testing specific distributions

**Jarque-Bera Test:**
- Based on skewness and kurtosis
- Good for large samples
- Combines measures of distribution shape

### Interpreting Results
- p-value > 0.05: Likely normally distributed (fail to reject null)
- p-value ≤ 0.05: Likely NOT normally distributed (reject null)

## Correlation Analysis

### Correlation Coefficients

**Pearson Correlation:**
- Measures linear relationship
- Range: -1 to 1
- Assumes normality

**Spearman Correlation:**
- Measures monotonic relationship
- Rank-based (non-parametric)
- Robust to outliers

**Kendall Correlation:**
- Similar to Spearman
- More robust to ties
- Slower to compute

### Interpretation
- 0.7 to 1.0: Strong positive
- 0.3 to 0.7: Moderate positive
- -0.3 to 0.3: Weak or no correlation
- -0.7 to -0.3: Moderate negative
- -1.0 to -0.7: Strong negative

## Hypothesis Testing

### ANOVA (Analysis of Variance)

**Purpose:** Test if means differ across groups
**Null Hypothesis:** All group means are equal
**Assumptions:** 
- Normality
- Homogeneity of variance
- Independence

**When significant:** At least one group mean differs

### Kruskal-Wallis Test

**Purpose:** Non-parametric alternative to ANOVA
**Use when:** Normality or homogeneity assumptions violated
**Better for:** Ordinal data, outliers present

### T-Tests

**Independent Samples T-Test:**
- Compare means of two independent groups
- Assumes normal distributions and equal variance

**Paired Samples T-Test:**
- Compare means of same group at different times
- Assumes differences are normally distributed

**Welch's T-Test:**
- More robust variant
- Doesn't assume equal variance

## Outlier Detection

### Statistical Methods

**Z-Score Method:**
- Points > 3 standard deviations from mean
- Assumes normal distribution
- `|z| = (x - mean) / std > 3`

**Interquartile Range (IQR) Method:**
- More robust to non-normal data
- Lower bound: Q1 - 1.5*IQR
- Upper bound: Q3 + 1.5*IQR
- Outliers: outside bounds

**Modified Z-Score:**
- Uses median absolute deviation
- Better for non-normal distributions
- |Mi| = 0.6745*(xi - median) / MAD > 3.5

### Handling Outliers
1. Keep: If business-relevant
2. Remove: If measurement error
3. Cap: Replace with cap value
4. Transform: Log/sqrt transformation
5. Separate Model: Model outliers separately

## Multicollinearity

### Detection

**Correlation Matrix:**
- Check for high correlations (> 0.8)
- Pairwise relationships

**Variance Inflation Factor (VIF):**
- VIF = 1 / (1 - R²)
- VIF > 5-10: Problematic multicollinearity
- Check each feature

### Solutions
1. Remove one feature from correlated pair
2. Combine features (e.g., average)
3. Use dimensionality reduction (PCA)
4. Use regularization (Ridge, Lasso)
5. Use tree-based models (robust to collinearity)

## Effect Size

### Understanding Practical Significance

**Cohen's d (standardized difference):**
- Small: 0.2
- Medium: 0.5
- Large: 0.8

**Eta-squared (proportion of variance explained):**
- Small: 0.01
- Medium: 0.06
- Large: 0.14

**Common Language Effect Size:**
- Probability that one group scores higher

## Statistical Power

### Concepts
- **Power**: Probability of detecting true effect (1 - β)
- **Alpha (α)**: Significance level (typically 0.05)
- **Beta (β)**: Type II error rate (typically 0.20 for power = 0.80)
- **Effect Size**: Magnitude of difference to detect

### Trade-offs
- Higher power requires larger sample size
- More stringent alpha reduces power
- Smaller effect sizes require more samples

## Choosing Statistical Tests

| Scenario | Test |
|----------|------|
| 2 groups, normal, equal variance | Independent t-test |
| 2 groups, non-normal or unequal variance | Mann-Whitney U |
| 2 groups, paired/repeated | Paired t-test |
| 3+ groups, normal | ANOVA |
| 3+ groups, non-normal | Kruskal-Wallis |
| Association between continuous variables | Pearson or Spearman correlation |
| Association between categorical variables | Chi-square test |
| Predict continuous with continuous | Linear regression |
| Predict continuous with categorical | ANOVA (or regression) |
| Predict categorical with continuous | Logistic regression |
| Predict categorical with categorical | Chi-square or loglinear |

## Python Implementation

```python
from scipy import stats
import pandas as pd

# Normality test
stat, pvalue = stats.shapiro(df['column'])

# Correlation
corr, pval = stats.pearsonr(x, y)
corr_spear, pval_spear = stats.spearmanr(x, y)

# T-test
t_stat, pval = stats.ttest_ind(group1, group2)

# ANOVA
f_stat, pval = stats.f_oneway(group1, group2, group3)

# Kruskal-Wallis
h_stat, pval = stats.kruskal(group1, group2, group3)

# VIF
from statsmodels.stats.outliers_influence import variance_inflation_factor
vif = [variance_inflation_factor(X.values, i) for i in range(X.shape[1])]
```
