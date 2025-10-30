# Statistical Report Critique - Analysis & Action Plan

**Date**: 2025-10-29  
**Status**: Issues Identified - Action Plan Created  
**Severity**: 🚨 Major issues found requiring code fixes

---

## Executive Summary

External statistical review identified **9 major issues** in the statistical report generation:
1. **Critical**: Bootstrap confidence intervals mathematically impossible (point estimate outside CI)
2. **Critical**: Cliff's Delta = ±1.000 with zero-width CIs (statistically improbable)
3. **Major**: Inconsistent test selection (Kruskal-Wallis used even when ANOVA assumptions met)
4. **Major**: Missing power analysis section despite claiming it exists
5. **Moderate**: Cohen's d used for non-parametric data (contradicts methodology)
6. **Moderate**: P-values reported as 0.0000 instead of p < 0.001
7. **Moderate**: Mean/SD reported for highly skewed data (should use median/IQR)
8. **Moderate**: No multiple comparison corrections (Bonferroni/Holm)
9. **Moderate**: Causal language ("outperforms") for associative tests

---

## Detailed Issue Analysis

### 🚨 Issue 1: Impossible Confidence Intervals

**Example from Report**:
```
Cohen's d = -1.705 with CI [-0.492, 0.491]
Cohen's d = 4.643 with CI [-0.491, 0.492]
```

**Problem**: Point estimate MUST be contained within its confidence interval by definition.

**Root Cause**:
```python
# Current implementation (lines 1112-1133)
def cohens_d_bootstrap(combined_data, n1):
    return cohens_d(combined_data[:n1].tolist(), combined_data[n1:].tolist())

combined = np.array(vals1 + vals2)
n1 = len(vals1)
bootstrap_stats = []
for _ in range(10000):
    sample = self.rng.choice(len(combined), size=len(combined), replace=True)
    resampled = combined[sample]
    d = cohens_d_bootstrap(resampled, n1)
    bootstrap_stats.append(d)
```

**Issue**: Resampling indices (not values) causes wrong data reassignment. After resampling indices, the first n1 elements are NOT necessarily from group1 anymore.

**Fix Required**:
```python
# Correct approach: Bootstrap each group independently
bootstrap_stats = []
for _ in range(10000):
    sample1 = self.rng.choice(vals1, size=len(vals1), replace=True)
    sample2 = self.rng.choice(vals2, size=len(vals2), replace=True)
    d = cohens_d(sample1.tolist(), sample2.tolist())
    bootstrap_stats.append(d)
```

---

### 🚨 Issue 2: Cliff's Delta = ±1.000 with Zero-Width CIs

**Example from Report**:
```
Cliff's Delta = 1.000 [1.000, 1.000]
Cliff's Delta = -1.000 [-1.000, -1.000]
```

**Problem**: 
- Perfect separation (δ = ±1.000) means ALL values in group1 > ALL values in group2
- Zero-width CI [1.000, 1.000] implies 100% certainty across bootstrap samples
- Statistically improbable unless datasets are tiny (<5 samples each) or artificially separated

**Root Cause**: Same bootstrap issue as Issue #1 - sampling strategy preserves perfect separation across all 10,000 iterations.

**Additional Concern**: 
Check if BAES dataset has artificially low variance (std_dev = 0.49 for api_calls suggests near-identical values).

---

### 🚨 Issue 3: Inconsistent Test Selection Logic

**Declared Methodology** (line 949):
```python
if both_normal and equal_variance:
    # Use t-test or ANOVA
else:
    # Use Mann-Whitney or Kruskal-Wallis
```

**Report Behavior**:
```markdown
execution_time:
  - All 3 groups: ✅ Normal (Shapiro-Wilk p > 0.05)
  - Test Used: Kruskal-Wallis ❌ (should be ANOVA)
  
Rationale: "unequal variances. Non-parametric test appropriate"
```

**Problem**: 
- When normal but unequal variances → Should use **Welch's ANOVA** (not Kruskal-Wallis)
- Welch's ANOVA doesn't assume equal variances but maintains parametric power
- Kruskal-Wallis sacrifices power unnecessarily when normality holds

**Fix Required**:
Add Welch's ANOVA as intermediate option:
```python
if all_normal:
    if equal_variance:
        # Use standard ANOVA
    else:
        # Use Welch's ANOVA
else:
    # Use Kruskal-Wallis
```

---

### 🚨 Issue 4: Missing Power Analysis Section

**Claimed** (reproducibility table):
```
target_power: 0.8
```

**Reality**: No Section 5 "Power Analysis" exists in report. Only power warnings mentioned:
```
"Parsed statistical data: 21 comparisons, 2 visualizations, 0 power warnings"
```

**Problem**: Users expect:
- Achieved power per comparison
- Recommended sample sizes for underpowered tests
- Interpretation of non-significant results in power context

**Fix Required**: Implement actual power analysis using statsmodels:
```python
from statsmodels.stats.power import TTestIndPower, FTestAnovaPower

power_analyzer = TTestIndPower()
achieved_power = power_analyzer.solve_power(
    effect_size=effect_value,
    nobs1=len(group1),
    ratio=len(group2)/len(group1),
    alpha=self.alpha
)
```

---

### ⚠️ Issue 5: Cohen's d for Non-Parametric Data

**Example from Report**:
```
api_calls (ghspec vs chatdev):
  - ghspec: ✅ Normal
  - chatdev: ✅ Normal
  - Test: Kruskal-Wallis (non-parametric)
  - Effect Size: Cohen's d = -1.705
```

**Problem**: Mixing non-parametric test with parametric effect size.

**Current Logic** (lines 1106-1145):
```python
if both_normal:
    effect_value = cohens_d(vals1, vals2)  # Uses Cohen's d
else:
    effect_value = cliffs_delta(vals1, vals2)  # Uses Cliff's Delta
```

**Issue**: `both_normal` checks pairwise normality, but test selection also considers variance homogeneity. Creates mismatch.

**Fix Required**: Align effect size choice with actual test used:
```python
if test_type in [TestType.T_TEST, TestType.ANOVA]:
    use_cohens_d = True
else:
    use_cohens_d = False
```

---

### ⚠️ Issue 6: P-value Reporting Format

**Current**:
```
p-value: 0.0000
```

**Problem**: 
- Implies exactly zero (mathematically impossible)
- Standard: p < 0.001 for very small values

**Fix Required**:
```python
p_str = f"p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"
```

---

### ⚠️ Issue 7: Mean/SD for Skewed Data

**Example**:
```
cached_tokens (baes):
  Mean: 145.78
  Median: 0.00
  Std Dev: 609.78
  Skewness: 3.88
```

**Problem**: When median = 0 but mean = 145, distribution is extremely right-skewed. Mean is misleading.

**Fix Required**: Emphasize median/IQR in summary tables for skewed metrics:
```python
if abs(skewness) > 1.0:
    # Flag as skewed, emphasize median in narrative
    summary = f"Median = {median:.2f} (IQR: {q1:.2f}-{q3:.2f})"
else:
    summary = f"Mean = {mean:.2f} ± {std:.2f}"
```

---

### ⚠️ Issue 8: No Multiple Comparison Corrections

**Current Behavior**: 21 pairwise comparisons with α=0.05 → Expected ~1 false positive

**Problem**: No Bonferroni, Holm, or FDR correction applied.

**Fix Required**: Implement Holm-Bonferroni correction:
```python
from statsmodels.stats.multitest import multipletests

p_values = [test.p_value for test in all_tests]
reject, p_adjusted, _, _ = multipletests(p_values, alpha=0.05, method='holm')

for test, p_adj, is_sig in zip(all_tests, p_adjusted, reject):
    test.p_value_adjusted = p_adj
    test.is_significant = is_sig
```

---

### ⚠️ Issue 9: Causal Language for Associative Tests

**Current**:
```
"ghspec outperforms baes"
"Probability that ghspec exceeds baes is 100.0%"
```

**Problem**: 
- Kruskal-Wallis/Mann-Whitney only test distributional differences
- "Outperforms" implies causality (requires controlled experiment)
- "100% probability" overstates certainty

**Fix Required**:
```python
# Replace causal language
"ghspec shows higher values than baes"
"ghspec distributions differ from baes"

# Replace certainty claims
"Probability..." → "Based on observed data, ghspec values tend to exceed baes"
```

---

## Priority Action Items

### P0 - Critical (Fix Immediately)
1. ✅ Fix bootstrap CI calculation (Issue #1, #2)
2. ✅ Add Welch's ANOVA option (Issue #3)
3. ✅ Implement actual power analysis (Issue #4)

### P1 - Major (Fix in Next Release)
4. ✅ Align effect size with test type (Issue #5)
5. ✅ Fix p-value formatting (Issue #6)
6. ✅ Add multiple comparison corrections (Issue #8)

### P2 - Moderate (Improve UX)
7. ✅ Emphasize median for skewed data (Issue #7)
8. ✅ Remove causal language (Issue #9)

---

## Implementation Plan

### Phase 1: Bootstrap Fix (2 hours)
**Files**: `src/paper_generation/statistical_analyzer.py`
- Lines 1112-1133: Fix Cohen's d bootstrap
- Lines 1147-1165: Fix Cliff's Delta bootstrap  
- Add unit tests to verify CI contains point estimate

### Phase 2: Test Selection Logic (2 hours)
**Files**: `src/paper_generation/statistical_analyzer.py`
- Lines 949-1000: Add Welch's t-test/ANOVA
- Update test selection flowchart
- Align effect size with test type

### Phase 3: Power Analysis (3 hours)
**Files**: 
- `src/paper_generation/statistical_analyzer.py`: Compute power
- `src/paper_generation/educational_content.py`: Power explanations
- Add power analysis section to reports

### Phase 4: Reporting Improvements (2 hours)
**Files**: 
- `src/paper_generation/statistical_analyzer.py`: p-value formatting, multiple comparisons
- `src/paper_generation/educational_content.py`: Language fixes
- Update interpretation templates

### Phase 5: Validation (2 hours)
- Re-run on baes_benchmarking experiment
- Verify all CIs contain point estimates
- Check test selection matches assumptions
- Confirm power analysis appears

**Total Estimated Effort**: 11 hours

---

## Testing Strategy

### Unit Tests
```python
def test_bootstrap_ci_contains_point_estimate():
    """CI must contain the point estimate."""
    analyzer = StatisticalAnalyzer()
    effect = analyzer._calculate_effect_size(data1, data2)
    assert effect.ci_lower <= effect.value <= effect.ci_upper

def test_welch_anova_selected_when_normal_unequal_var():
    """Should use Welch's ANOVA not Kruskal-Wallis."""
    # Create normal data with unequal variances
    group1 = np.random.normal(10, 1, 30)  # σ=1
    group2 = np.random.normal(12, 5, 30)  # σ=5
    group3 = np.random.normal(8, 2, 30)   # σ=2
    
    test = analyzer._perform_multi_group_test(...)
    assert test.test_type == TestType.WELCH_ANOVA
```

### Integration Tests
```python
def test_statistical_report_completeness():
    """All sections must be present."""
    report = generate_full_report(experiment_data)
    
    assert "1. Descriptive Statistics" in report
    assert "2. Normality Assessment" in report
    assert "3. Assumption Validation" in report
    assert "4. Statistical Comparisons" in report
    assert "5. Power Analysis" in report  # Currently missing!
    assert "6. Statistical Methodology" in report
    assert "7. Glossary" in report
```

---

## Success Criteria

✅ **All CIs contain their point estimates**  
✅ **No Cliff's Delta = ±1.000 [1.000, 1.000] (unless truly perfect separation)**  
✅ **Welch's ANOVA used when appropriate**  
✅ **Power analysis section with achieved power per test**  
✅ **Effect size matches test type (parametric ↔ Cohen's d, non-parametric ↔ Cliff's Delta)**  
✅ **P-values formatted as p < 0.001 when appropriate**  
✅ **Multiple comparison corrections applied and reported**  
✅ **No causal language for associative tests**  

---

## References

- **Bootstrap CI Theory**: Efron & Tibshirani (1993). *An Introduction to the Bootstrap*
- **Effect Sizes**: Cohen (1988). *Statistical Power Analysis for the Behavioral Sciences*
- **Multiple Comparisons**: Holm (1979). "A simple sequentially rejective multiple test procedure"
- **Welch's ANOVA**: Welch (1951). "On the comparison of several mean values"
- **Cliff's Delta**: Cliff (1993). "Dominance statistics: Ordinal analyses to answer ordinal questions"

---

**Next Steps**: Review and approve this action plan before implementation.
