# Phase 0: Research & Technical Decisions

**Feature**: Fix Statistical Report Generation Issues  
**Date**: 2025-10-29  
**Status**: Complete

## Overview

This document consolidates research findings for fixing 9 statistical issues in the report generation system. All technical decisions are based on established statistical best practices, peer-reviewed methodologies, and existing codebase patterns.

## Research Tasks

### 1. Bootstrap Confidence Interval Methodology

**Question**: How should bootstrap resampling be performed for effect sizes comparing two independent groups?

**Decision**: **Independent group resampling** (resample each group separately, then compute effect size on resampled groups)

**Rationale**:
- Preserves group structure and sample sizes
- Accurately reflects sampling variability within each group
- Standard approach in statistical literature (Efron & Tibshirani, 1993)
- Ensures CI mathematically contains point estimate (computed on original data)

**Alternatives Considered**:
1. ❌ **Combined array resampling** (current broken implementation)
   - Resamples from pooled array, destroying group boundaries
   - Results in scrambled group assignments
   - Produces CIs that don't contain point estimates
   
2. ❌ **Stratified resampling**
   - Overly complex for two-group comparisons
   - No additional benefit over independent resampling
   
**Implementation Pattern**:
```python
def bootstrap_effect_size(group1_values, group2_values, n_iterations=10000):
    """
    Bootstrap CI for effect sizes using independent group resampling.
    
    Correct approach:
    1. Resample group1 → group1_resampled (preserves n1)
    2. Resample group2 → group2_resampled (preserves n2)
    3. Compute effect_size(group1_resampled, group2_resampled)
    4. Repeat 10,000 times
    5. CI = [2.5th percentile, 97.5th percentile]
    """
    bootstrapped_effects = []
    for _ in range(n_iterations):
        g1_sample = np.random.choice(group1_values, size=len(group1_values), replace=True)
        g2_sample = np.random.choice(group2_values, size=len(group2_values), replace=True)
        effect = compute_effect_size(g1_sample, g2_sample)
        bootstrapped_effects.append(effect)
    
    return np.percentile(bootstrapped_effects, [2.5, 97.5])
```

**References**:
- Efron, B., & Tibshirani, R. (1993). *An Introduction to the Bootstrap*. Chapman & Hall.
- DiCiccio, T. J., & Efron, B. (1996). Bootstrap confidence intervals. *Statistical Science*, 11(3), 189-228.

---

### 2. Statistical Test Selection Logic

**Question**: How should the system decide between parametric (ANOVA/t-test), Welch's variants, and non-parametric tests?

**Decision**: **Three-way decision tree based on normality AND variance equality**

**Rationale**:
- Current implementation only uses binary logic (parametric vs non-parametric)
- Welch's tests are robust when assumptions partially hold (normal but unequal variance)
- Following standard statistical decision flowcharts (Field, 2013)

**Decision Tree**:
```
For multi-group (k ≥ 3):
├─ All groups normal? (Shapiro-Wilk p > 0.05 for each group)
│  ├─ YES: Equal variances? (Levene's test p > 0.05)
│  │  ├─ YES: Standard ANOVA (F-test)
│  │  └─ NO:  Welch's ANOVA (unequal variance robust)
│  └─ NO: Kruskal-Wallis (non-parametric)

For pairwise (k = 2):
├─ Both groups normal?
│  ├─ YES: Equal variances?
│  │  ├─ YES: Student's t-test
│  │  └─ NO:  Welch's t-test
│  └─ NO: Mann-Whitney U test
```

**Alternatives Considered**:
1. ❌ **Always use Welch's tests**
   - Loses statistical power when variances truly equal
   - Doesn't handle non-normal data
   
2. ❌ **Always use non-parametric**
   - Loses statistical power when parametric assumptions hold
   - Not best practice in field
   
3. ✅ **Three-way logic** (CHOSEN)
   - Maximum statistical power
   - Appropriate for data characteristics
   - Follows published guidelines

**Implementation**:
- Welch's ANOVA: Use `scipy.stats.f_oneway` with custom Welch correction or implement using statsmodels
- Welch's t-test: `scipy.stats.ttest_ind(equal_var=False)` (already exists)

**References**:
- Field, A. (2013). *Discovering Statistics Using IBM SPSS Statistics* (4th ed.). SAGE Publications.
- Welch, B. L. (1951). On the comparison of several mean values: an alternative approach. *Biometrika*, 38(3/4), 330-336.
- Zimmerman, D. W. (2004). A note on preliminary tests of equality of variances. *British Journal of Mathematical and Statistical Psychology*, 57(1), 173-181.

---

### 3. Power Analysis Implementation

**Question**: What power analysis methods should be used for each test type?

**Decision**: **Use statsmodels.stats.power classes with test-specific formulas**

**Rationale**:
- statsmodels provides validated, peer-reviewed implementations
- Handles both t-tests and ANOVA power calculations
- Already a project dependency (for multiple comparison corrections)
- Provides sample size estimation (solve_power)

**Test-to-Power Method Mapping**:
```
Student's t-test    → TTestIndPower (equal variance assumption)
Welch's t-test      → TTestIndPower (conservative, slight underestimate)
ANOVA              → FTestAnovaPower (k groups, equal variance)
Welch's ANOVA      → FTestAnovaPower (approximate, conservative)
Mann-Whitney U     → TTestIndPower with rank-based effect size (approximation)
Kruskal-Wallis     → FTestAnovaPower with epsilon-squared (approximation)
```

**Implementation Pattern**:
```python
from statsmodels.stats.power import TTestIndPower, FTestAnovaPower

def calculate_achieved_power(effect_size, n1, n2, alpha=0.05, test_type='t_test'):
    """
    Calculate achieved power for a given test configuration.
    
    Returns:
        power (float): Achieved power (0.0 to 1.0)
        recommended_n (int): Sample size needed for 80% power (if underpowered)
    """
    if test_type in ['t_test', 'welch_t', 'mann_whitney']:
        analysis = TTestIndPower()
        power = analysis.solve_power(
            effect_size=effect_size,
            nobs1=n1,
            ratio=n2/n1,
            alpha=alpha,
            power=None  # Solve for power
        )
        
        if power < 0.80:
            recommended_n = analysis.solve_power(
                effect_size=effect_size,
                nobs1=None,  # Solve for n
                ratio=n2/n1,
                alpha=alpha,
                power=0.80
            )
        else:
            recommended_n = None
            
    elif test_type in ['anova', 'welch_anova', 'kruskal_wallis']:
        # k = number of groups, effect_size = f (Cohen's f for ANOVA)
        analysis = FTestAnovaPower()
        # ... similar pattern
    
    return power, recommended_n
```

**Alternatives Considered**:
1. ❌ **Monte Carlo simulation**
   - Too computationally expensive (would need 10,000+ simulations per test)
   - Not necessary when analytic solutions exist
   
2. ❌ **G*Power integration**
   - External dependency, not Python-native
   - Overkill for simple power calculations
   
3. ✅ **statsmodels** (CHOSEN)
   - Already in dependency tree
   - Well-tested, widely used
   - Analytic formulas (fast)

**References**:
- Cohen, J. (1988). *Statistical Power Analysis for the Behavioral Sciences* (2nd ed.). Lawrence Erlbaum Associates.
- Faul, F., Erdfelder, E., Lang, A. G., & Buchner, A. (2007). G*Power 3. *Behavior Research Methods*, 39(2), 175-191.
- statsmodels documentation: https://www.statsmodels.org/stable/stats.html#power-and-sample-size-calculations

---

### 4. Multiple Comparison Correction Methods

**Question**: Which multiple testing correction method balances Type I error control with statistical power?

**Decision**: **Holm-Bonferroni method**

**Rationale**:
- More powerful than Bonferroni (fewer Type II errors)
- Controls family-wise error rate (FWER) as well as Bonferroni
- Widely accepted in statistical community
- Available in statsmodels.stats.multitest.multipletests

**Comparison of Methods**:
```
Method             | FWER Control | Power | Simplicity | Recommendation
-------------------|--------------|-------|------------|----------------
Bonferroni         | Yes (strict) | Low   | High       | Too conservative
Holm-Bonferroni    | Yes          | Med   | High       | ✅ CHOSEN
Benjamini-Hochberg | No (FDR)     | High  | Medium     | For exploratory work
Šidák             | Yes          | Low   | Medium     | Similar to Bonferroni
```

**Implementation**:
```python
from statsmodels.stats.multitest import multipletests

def apply_multiple_comparison_correction(pvalues, alpha=0.05, method='holm'):
    """
    Apply Holm-Bonferroni correction to raw p-values.
    
    Returns:
        reject (array): Boolean array of significance decisions
        pvals_corrected (array): Adjusted p-values
        alphacSidak (float): Not used for Holm
        alphacBonf (float): Corrected alpha threshold
    """
    reject, pvals_corrected, alphacSidak, alphacBonf = multipletests(
        pvalues, alpha=alpha, method=method
    )
    return reject, pvals_corrected
```

**When to Apply**:
- Number of comparisons > 1
- All pairwise comparisons for the same metric
- NOT across different metrics (each metric family separate)

**References**:
- Holm, S. (1979). A simple sequentially rejective multiple test procedure. *Scandinavian Journal of Statistics*, 6(2), 65-70.
- Benjamini, Y., & Hochberg, Y. (1995). Controlling the false discovery rate. *Journal of the Royal Statistical Society: Series B*, 57(1), 289-300.
- Noble, W. S. (2009). How does multiple testing correction work?. *Nature Biotechnology*, 27(12), 1135-1137.

---

### 5. P-value Formatting Conventions

**Question**: What are the standard p-value reporting conventions in scientific publications?

**Decision**: **APA 7th edition format**

**Rationale**:
- Most widely used style in psychological and social sciences
- Adopted by many journals across disciplines
- Prevents false precision ("p = 0.0000")
- Maintains 3 decimal places for interpretability

**Formatting Rules**:
```python
def format_pvalue(p, alpha=0.05):
    """
    Format p-value according to APA 7th edition guidelines.
    
    Rules:
    - p < 0.001: Report as "p < 0.001"
    - p ≥ 0.001: Report as "p = 0.XXX" (3 decimals, include leading zero)
    - p = 0.050: Report as "p = 0.050" (not "p = 0.05")
    - Always use equals sign or less-than, never "p = 0.000" or "p = 0.0000"
    
    Examples:
        format_pvalue(0.0000023) → "p < 0.001"
        format_pvalue(0.0234)    → "p = 0.023"
        format_pvalue(0.05)      → "p = 0.050"
        format_pvalue(0.234)     → "p = 0.234"
    """
    if p < 0.001:
        return "p < 0.001"
    else:
        return f"p = {p:.3f}"
```

**Alternatives Considered**:
1. ❌ **Scientific notation for small p**
   - Less readable (p = 2.3 × 10⁻⁶)
   - Not standard in most journals
   
2. ❌ **Exact p-values always**
   - False precision (p = 0.00000234 implies 9-digit accuracy)
   - Not aligned with statistical philosophy
   
3. ✅ **APA format** (CHOSEN)
   - Standard across disciplines
   - Balances precision and readability

**References**:
- American Psychological Association. (2020). *Publication Manual of the American Psychological Association* (7th ed.).
- Wasserstein, R. L., & Lazar, N. A. (2016). The ASA statement on p-values. *The American Statistician*, 70(2), 129-133.

---

### 6. Skewness Thresholds for Summary Statistics

**Question**: What threshold should trigger median/IQR emphasis over mean/SD?

**Decision**: **|skewness| > 1.0 for "moderate" flag, |skewness| > 2.0 for "severe" warning**

**Rationale**:
- Bulmer (1979) classification: |skew| < 0.5 symmetric, 0.5-1.0 moderate, >1.0 highly skewed
- Mean becomes less representative when |skew| > 1.0
- Aligns with common practice in robust statistics

**Skewness Interpretation**:
```
|skewness| < 0.5:  Nearly symmetric → Use mean ± SD
|skewness| 0.5-1.0: Moderately skewed → Flag both, prefer median
|skewness| > 1.0:   Highly skewed → Emphasize median/IQR, note mean is biased
|skewness| > 2.0:   Severely skewed → Add warning, median strongly preferred
```

**Implementation**:
```python
def recommend_summary_statistic(skewness):
    """
    Recommend which summary statistic to emphasize based on skewness.
    
    Returns:
        primary: 'mean' or 'median'
        emphasis: 'normal', 'flag', 'warning'
        message: Explanation for users
    """
    abs_skew = abs(skewness)
    
    if abs_skew < 0.5:
        return 'mean', 'normal', "Distribution is nearly symmetric; mean ± SD appropriate."
    elif abs_skew <= 1.0:
        return 'median', 'flag', "Moderate skewness detected; median and IQR are more robust."
    elif abs_skew <= 2.0:
        return 'median', 'warning', "High skewness detected; median strongly preferred over mean."
    else:
        return 'median', 'warning', "Severe skewness detected; mean is substantially biased by extreme values."
```

**References**:
- Bulmer, M. G. (1979). *Principles of Statistics*. Dover Publications.
- Wilcox, R. R. (2012). *Introduction to Robust Estimation and Hypothesis Testing* (3rd ed.). Academic Press.

---

### 7. Effect Size and Test Type Alignment

**Question**: Should effect size measure always match test type (parametric vs non-parametric)?

**Decision**: **Yes - strict alignment for methodological consistency**

**Rationale**:
- Mixing assumptions creates interpretation confusion
- Cohen's d assumes normality (parametric)
- Cliff's Delta is distribution-free (non-parametric)
- Following recommendations from Grissom & Kim (2012)

**Mapping**:
```
Test Used           | Effect Size | Rationale
--------------------|-------------|------------------------------------------
Student's t-test    | Cohen's d   | Both assume normality
Welch's t-test      | Cohen's d   | Parametric test, d is robust to unequal variance
ANOVA              | Cohen's d   | Parametric family
Welch's ANOVA      | Cohen's d   | Still parametric despite variance adjustment
Mann-Whitney U     | Cliff's Delta | Non-parametric test needs non-parametric effect size
Kruskal-Wallis     | Cliff's Delta | Non-parametric test family
```

**Interpretation Alignment**:
- Cohen's d educational content: References normal distributions, mean differences
- Cliff's Delta educational content: References ordinal dominance, median differences

**Alternatives Considered**:
1. ❌ **Always use Cohen's d**
   - Inappropriate for non-normal data
   - Makes assumptions not verified by test
   
2. ❌ **Report both measures**
   - Adds confusion
   - Implies equivalence when they measure different things
   
3. ✅ **Match effect size to test** (CHOSEN)
   - Methodologically consistent
   - Clear interpretation

**References**:
- Grissom, R. J., & Kim, J. J. (2012). *Effect Sizes for Research: Univariate and Multivariate Applications* (2nd ed.). Routledge.
- Lakens, D. (2013). Calculating and reporting effect sizes. *Frontiers in Psychology*, 4, 863.

---

### 8. Neutral Statistical Language Guidelines

**Question**: How should results be described to avoid causal inference from associative tests?

**Decision**: **Descriptive comparative language only**

**Rationale**:
- Kruskal-Wallis and Mann-Whitney test distributional differences, not causality
- Even with experiments, observational confounders possible
- Following APA guidelines for statistical reporting

**Language Transformations**:
```
❌ AVOID (Causal/Superiority)        | ✅ USE (Descriptive/Comparative)
-------------------------------------|---------------------------------------
"Framework X outperforms Y"          | "Framework X shows higher values than Y"
"X is better than Y"                 | "X differs from Y" or "X exceeds Y"
"X improves upon Y"                  | "X demonstrates higher performance on metric Z"
"100% certain X beats Y"             | "All observed values in X exceed those in Y"
"X causes higher performance"        | "X is associated with higher performance"
"No effect exists"                   | "Insufficient evidence to detect a difference"
```

**Implementation**:
- Create phrase dictionary in educational_content.py
- Template system for interpretations
- Automated substitution in prose generation

**Exceptions**:
- If config explicitly marks study as "experimental" with controls → Can use stronger language
- Default assumption: observational comparison

**References**:
- American Psychological Association. (2020). *Publication Manual* (7th ed.), Section 6.36 on Causal Language.
- Pearl, J. (2009). *Causality: Models, Reasoning, and Inference* (2nd ed.). Cambridge University Press.

---

## Summary of Technical Decisions

| Issue # | Decision | Primary Technology/Method |
|---------|----------|--------------------------|
| 1 | Bootstrap CIs | Independent group resampling (NumPy) |
| 2 | Test selection | Three-way logic tree (SciPy) |
| 3 | Power analysis | statsmodels.stats.power (TTestIndPower, FTestAnovaPower) |
| 4 | Effect size alignment | Strict parametric/non-parametric matching |
| 5 | Multiple comparisons | Holm-Bonferroni (statsmodels.stats.multitest) |
| 6 | P-value formatting | APA 7th edition conventions |
| 7 | Skewness thresholds | |skew| > 1.0 triggers median/IQR emphasis |
| 8 | Neutral language | Descriptive comparative phrases only |

## No Remaining Clarifications

All technical questions have been resolved through literature review and best practices research. Implementation can proceed to Phase 1 (data model and contracts).
