# API Contract: Statistical Analyzer Methods

**Feature**: Fix Statistical Report Generation Issues  
**Date**: 2025-10-29  
**Module**: `src.paper_generation.statistical_analyzer.StatisticalAnalyzer`

## Overview

This document specifies the contracts (inputs, outputs, behaviors) for modified methods in the StatisticalAnalyzer class. All contracts preserve backward compatibility while adding new optional parameters and return fields.

---

## Method Contracts

### 1. `_bootstrap_confidence_interval()`

**Purpose**: Compute bootstrap confidence interval for effect sizes using independent group resampling.

**Signature**:
```python
def _bootstrap_confidence_interval(
    self,
    group1_values: List[float],
    group2_values: List[float],
    effect_size_func: Callable[[List[float], List[float]], float],
    n_iterations: int = 10000,
    confidence_level: float = 0.95,
    random_seed: Optional[int] = None
) -> Tuple[float, float, bool]
```

**Parameters**:
- `group1_values`: First group's data (length n1)
- `group2_values`: Second group's data (length n2)
- `effect_size_func`: Function that computes effect size (cohens_d or cliffs_delta)
- `n_iterations`: Number of bootstrap samples (must be ≥ 10,000)
- `confidence_level`: CI level (default 0.95 for 95% CI)
- `random_seed`: Optional seed for reproducibility

**Returns**: `(ci_lower, ci_upper, ci_valid)`
- `ci_lower` (float): Lower bound of CI
- `ci_upper` (float): Upper bound of CI
- `ci_valid` (bool): True if CI contains point estimate

**Behavior** (FR-001, FR-002, FR-003):
1. Compute point estimate on original data
2. For each iteration:
   - Resample group1_values → group1_sample (length n1, with replacement)
   - Resample group2_values → group2_sample (length n2, with replacement)
   - Compute effect_size_func(group1_sample, group2_sample)
3. Compute percentiles: [α/2, 1-α/2] where α = 1 - confidence_level
4. Validate that ci_lower ≤ point_estimate ≤ ci_upper
5. Return (ci_lower, ci_upper, ci_valid)

**Preconditions**:
- len(group1_values) ≥ 2
- len(group2_values) ≥ 2
- n_iterations ≥ 10000
- 0.0 < confidence_level < 1.0

**Postconditions**:
- ci_lower ≤ ci_upper
- If ci_valid is False, raise StatisticalAnalysisError

**Error Handling** (FR-004):
- If bootstrap fails (e.g., all samples identical), fall back to analytic CI or raise clear error
- Never silently return invalid CIs

---

### 2. `_select_statistical_test()`

**Purpose**: Select appropriate statistical test based on normality and variance equality.

**Signature**:
```python
def _select_statistical_test(
    self,
    distributions: List[MetricDistribution],
    alpha: float = 0.05
) -> Tuple[TestType, Dict[str, bool], str]
```

**Parameters**:
- `distributions`: List of MetricDistribution objects (one per group)
- `alpha`: Significance level for assumption tests (default 0.05)

**Returns**: `(test_type, assumptions, rationale)`
- `test_type` (TestType): Selected test (T_TEST, WELCH_T, MANN_WHITNEY, ANOVA, WELCH_ANOVA, KRUSKAL_WALLIS)
- `assumptions` (dict): {normality: bool, equal_variance: bool}
- `rationale` (str): Explanation of test selection

**Behavior** (FR-005 to FR-012):

**For pairwise (k=2)**:
```python
if all_normal(distributions):
    if equal_variance(distributions):
        return TestType.T_TEST, {normality: True, equal_var: True}, "Both groups normal with equal variances; Student's t-test selected"
    else:
        return TestType.WELCH_T, {normality: True, equal_var: False}, "Both groups normal with unequal variances; Welch's t-test selected"  # FR-010
else:
    return TestType.MANN_WHITNEY, {normality: False, equal_var: N/A}, "At least one group non-normal; Mann-Whitney U test selected"
```

**For multi-group (k≥3)**:
```python
if all_normal(distributions):
    if equal_variance(distributions):
        return TestType.ANOVA, {normality: True, equal_var: True}, "All groups normal with equal variances; standard ANOVA selected"  # FR-006
    else:
        return TestType.WELCH_ANOVA, {normality: True, equal_var: False}, "All groups normal with unequal variances; Welch's ANOVA selected"  # FR-007
else:
    return TestType.KRUSKAL_WALLIS, {normality: False, equal_var: N/A}, "At least one group non-normal; Kruskal-Wallis test selected"  # FR-008
```

**Assumption Tests**:
- Normality: Shapiro-Wilk test (p > 0.05 → normal)
- Variance equality: Levene's test (p > 0.05 → equal)

**Preconditions**:
- len(distributions) ≥ 2
- All distributions have n ≥ 3

**Postconditions**:
- test_type is one of the 6 supported types
- assumptions dict contains relevant keys
- rationale is non-empty human-readable string

---

### 3. `_calculate_power_analysis()`

**Purpose**: Compute achieved power and sample size recommendations (NEW METHOD).

**Signature**:
```python
def _calculate_power_analysis(
    self,
    test_type: TestType,
    effect_size: float,
    n1: int,
    n2: Optional[int] = None,
    n_groups: Optional[int] = None,
    alpha: float = 0.05,
    target_power: float = 0.80
) -> PowerAnalysis
```

**Parameters**:
- `test_type`: Type of statistical test performed
- `effect_size`: Cohen's d (for t-tests) or Cohen's f (for ANOVA)
- `n1`: Sample size of group 1 (or per-group for ANOVA)
- `n2`: Sample size of group 2 (for pairwise tests only)
- `n_groups`: Number of groups (for ANOVA only)
- `alpha`: Significance level (default 0.05)
- `target_power`: Desired power threshold (default 0.80)

**Returns**: PowerAnalysis object (see data-model.md)

**Behavior** (FR-016 to FR-021):

**For t-tests (T_TEST, WELCH_T, MANN_WHITNEY)**:
```python
from statsmodels.stats.power import TTestIndPower

analysis = TTestIndPower()
achieved_power = analysis.solve_power(
    effect_size=effect_size,
    nobs1=n1,
    ratio=n2/n1,
    alpha=alpha,
    power=None  # Solve for power
)

if achieved_power < target_power:
    recommended_n = analysis.solve_power(
        effect_size=effect_size,
        nobs1=None,  # Solve for n
        ratio=1.0,   # Assume equal n for recommendation
        alpha=alpha,
        power=target_power
    )
else:
    recommended_n = None
```

**For ANOVA (ANOVA, WELCH_ANOVA, KRUSKAL_WALLIS)**:
```python
from statsmodels.stats.power import FTestAnovaPower

# Convert Cohen's d to Cohen's f if needed
cohens_f = effect_size if is_f else effect_size / 2  # Approximation

analysis = FTestAnovaPower()
achieved_power = analysis.solve_power(
    effect_size=cohens_f,
    nobs=n1 * n_groups,  # Total sample size
    alpha=alpha,
    k_groups=n_groups,
    power=None
)

# Similar solve for recommended_n
```

**Preconditions**:
- effect_size > 0
- n1 ≥ 3
- If pairwise, n2 ≥ 3
- If ANOVA, n_groups ≥ 3

**Postconditions**:
- achieved_power in [0.0, 1.0] (or None if indeterminate)
- power_adequate set based on threshold
- If power < 0.50, warning_message populated

**Error Handling**:
- If sample size too small for power calculation (n < 5), set adequacy_flag = "indeterminate"
- If effect size extreme (d > 5), power may be 1.0 or calculation may fail → handle gracefully

---

### 4. `_apply_multiple_comparison_correction()`

**Purpose**: Apply Holm-Bonferroni correction to family of p-values (NEW METHOD).

**Signature**:
```python
def _apply_multiple_comparison_correction(
    self,
    pvalues: List[float],
    comparison_labels: List[str],
    alpha: float = 0.05,
    method: str = "holm"
) -> MultipleComparisonCorrection
```

**Parameters**:
- `pvalues`: List of raw p-values from statistical tests
- `comparison_labels`: Identifiers for each comparison (e.g., "baes_vs_chatdev")
- `alpha`: Family-wise error rate threshold (default 0.05)
- `method`: Correction method ("holm", "bonferroni", "fdr_bh", or "none")

**Returns**: MultipleComparisonCorrection object (see data-model.md)

**Behavior** (FR-022 to FR-026):
```python
from statsmodels.stats.multitest import multipletests

n_comparisons = len(pvalues)

if n_comparisons == 1:  # FR-026
    method = "none"
    adjusted_pvalues = pvalues
    reject_decisions = [p < alpha for p in pvalues]
else:  # FR-022
    if method == "none":
        raise ValueError("Must apply correction when n_comparisons > 1")
    
    reject, adjusted_pvalues, alphacSidak, alphacBonf = multipletests(
        pvalues, alpha=alpha, method=method
    )
    reject_decisions = list(reject)

return MultipleComparisonCorrection(
    metric_name=metric_name,
    correction_method=method,
    n_comparisons=n_comparisons,
    alpha=alpha,
    raw_pvalues=pvalues,
    adjusted_pvalues=list(adjusted_pvalues),
    comparison_labels=comparison_labels,
    reject_decisions=reject_decisions,
    corrected_alpha=alphacBonf if method != "none" else alpha
)
```

**Preconditions**:
- len(pvalues) == len(comparison_labels)
- All pvalues in [0.0, 1.0]
- method in ["holm", "bonferroni", "fdr_bh", "none"]

**Postconditions** (FR-023, FR-024):
- len(adjusted_pvalues) == len(pvalues)
- All adjusted_pvalues ≥ corresponding raw_pvalues
- reject_decisions based on adjusted_pvalues vs alpha

---

### 5. `format_pvalue()` (Utility Function)

**Purpose**: Format p-value according to APA 7th edition guidelines (NEW UTILITY).

**Location**: `src/utils/statistical_helpers.py`

**Signature**:
```python
def format_pvalue(p: float, precision: int = 3) -> str
```

**Parameters**:
- `p`: P-value to format (0.0 to 1.0)
- `precision`: Number of decimal places (default 3)

**Returns**: Formatted string

**Behavior** (FR-027 to FR-029):
```python
if p < 0.001:
    return "p < 0.001"  # FR-027
elif p >= 1.0:
    return "p = 1.000"
else:
    return f"p = {p:.{precision}f}"  # FR-028, FR-029
```

**Examples**:
- `format_pvalue(0.0000023)` → `"p < 0.001"`
- `format_pvalue(0.0234)` → `"p = 0.023"`
- `format_pvalue(0.05)` → `"p = 0.050"`
- `format_pvalue(0.234)` → `"p = 0.234"`

**Preconditions**:
- 0.0 ≤ p ≤ 1.0

**Postconditions**:
- Result always starts with "p "
- Never returns "p = 0.000" or "p = 0.0000"

---

### 6. `_get_interpretation_language()`

**Purpose**: Get neutral statistical language for interpretations (ENHANCED).

**Signature**:
```python
def _get_interpretation_language(
    self,
    comparison_type: str,
    effect_magnitude: str,
    power_adequate: bool = True
) -> Dict[str, str]
```

**Parameters**:
- `comparison_type`: "higher", "lower", or "no_difference"
- `effect_magnitude`: "small", "medium", "large", "very_large"
- `power_adequate`: Whether power ≥ 0.80 (for non-significant results)

**Returns**: Dictionary of phrase templates

**Behavior** (FR-035 to FR-038):
```python
phrases = {
    "higher": {
        "neutral": "shows higher values than",  # FR-035
        "avoid": "outperforms",  # Do not use
    },
    "lower": {
        "neutral": "shows lower values than",
        "avoid": "underperforms",
    },
    "no_difference": {
        "neutral_powered": "shows no detectable difference from",
        "neutral_underpowered": "shows insufficient evidence to detect difference from",  # FR-038
        "avoid": "is the same as",
    },
    "effect_size": {
        "neutral": "differs from {} by {} amount",
        "avoid": "is better than",  # FR-036
    },
    "cliff_delta_1.0": {
        "neutral": "all observed values in group X exceed those in group Y",  # FR-037
        "avoid": "100% certain X beats Y",
    }
}

return phrases
```

**Preconditions**:
- comparison_type in ["higher", "lower", "no_difference"]
- effect_magnitude in ["small", "medium", "large", "very_large"]

**Postconditions**:
- Returned phrases avoid causal language ("outperforms", "is better")
- Use descriptive comparative language ("shows higher values", "differs from")

---

## Backward Compatibility

All changes are **backward compatible**:
- New optional parameters have defaults
- New return fields are additions (not replacements)
- Existing method signatures preserved
- Old code calling these methods will continue to work
- New fields in dataclasses have defaults (None or empty)

## Breaking Changes

**None** - this is a bug-fix and enhancement release maintaining full backward compatibility.

## Testing Requirements

Each contract must have:
1. **Unit test**: Validates contract behavior in isolation
2. **Integration test**: Validates end-to-end flow through StatisticalAnalyzer
3. **Edge case tests**: Empty data, single comparison, extreme values

See `quickstart.md` for test execution guide.
