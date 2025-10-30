# Phase 1: Data Model & Entity Design

**Feature**: Fix Statistical Report Generation Issues  
**Date**: 2025-10-29  
**Prerequisites**: research.md complete

## Overview

This document defines the enhanced data models required to support the 9 statistical fixes. All entities are enhancements to existing classes in `src/paper_generation/statistical_analyzer.py` and `src/paper_generation/models.py`.

## Enhanced Entities

### 1. StatisticalTest (Enhanced)

**Location**: `src/paper_generation/statistical_analyzer.py` (existing dataclass)

**Purpose**: Represents a statistical comparison between groups with all necessary metadata for reporting.

**Enhancements**:
```python
@dataclass
class StatisticalTest:
    """Enhanced statistical test result with power analysis and corrections."""
    
    # EXISTING FIELDS (preserved)
    test_type: TestType
    metric_name: str
    group_names: List[str]
    statistic: float
    pvalue: float
    is_significant: bool
    
    # NEW FIELDS (additions)
    pvalue_raw: float = None                # Raw p-value before correction
    pvalue_adjusted: float = None           # Adjusted p-value (if multi-comparison)
    correction_method: str = None           # "holm" or None
    test_rationale: str = ""                # Why this test was selected
    assumptions_checked: Dict[str, bool] = field(default_factory=dict)  # {normality: True, equal_var: False}
    achieved_power: float = None            # Calculated achieved power (0.0-1.0)
    recommended_n: int = None               # Sample size for 80% power (if underpowered)
    power_adequate: bool = None             # True if power ≥ 0.80
```

**Validation Rules**:
- `pvalue_raw` must be set if `correction_method` is not None
- `pvalue_adjusted` must be set if `correction_method` is not None
- `achieved_power` must be between 0.0 and 1.0 if present
- `power_adequate` must match `achieved_power ≥ 0.80` if both present

**State Transitions**:
1. Initial: Basic test result with raw p-value
2. After correction: `pvalue_adjusted` and `correction_method` populated
3. After power analysis: `achieved_power`, `recommended_n`, `power_adequate` populated

---

### 2. EffectSize (Enhanced)

**Location**: `src/paper_generation/statistical_analyzer.py` (existing dataclass)

**Purpose**: Represents an effect size measurement with confidence intervals.

**Enhancements**:
```python
@dataclass
class EffectSize:
    """Enhanced effect size with validated confidence intervals."""
    
    # EXISTING FIELDS (preserved)
    measure: EffectSizeMeasure  # COHENS_D or CLIFFS_DELTA
    value: float                # Point estimate
    ci_lower: float            # 95% CI lower bound
    ci_upper: float            # 95% CI upper bound
    interpretation: str        # "small", "medium", "large", etc.
    
    # NEW FIELDS (additions)
    bootstrap_iterations: int = 10000      # Number of bootstrap samples used
    ci_method: str = "bootstrap"           # "bootstrap" or "analytic"
    ci_valid: bool = True                  # Whether CI contains point estimate
    test_type_alignment: TestType = None   # Which test this aligns with
    
    def __post_init__(self):
        """Validate that CI contains point estimate (FR-002)."""
        self.ci_valid = self.ci_lower <= self.value <= self.ci_upper
        
        if not self.ci_valid:
            raise StatisticalAnalysisError(
                f"Invalid confidence interval: point estimate {self.value:.3f} "
                f"is outside CI [{self.ci_lower:.3f}, {self.ci_upper:.3f}]. "
                f"This indicates a bootstrap resampling bug."
            )
```

**Validation Rules** (FR-002, FR-039):
- `ci_lower ≤ value ≤ ci_upper` must hold (enforced in `__post_init__`)
- `bootstrap_iterations ≥ 10000` for bootstrap CIs (FR-003)
- `measure` must align with `test_type_alignment` (FR-013, FR-014)

**Invariants**:
- If `measure == COHENS_D`, then `test_type_alignment` must be parametric (T_TEST, ANOVA, WELCH_T, WELCH_ANOVA)
- If `measure == CLIFFS_DELTA`, then `test_type_alignment` must be non-parametric (MANN_WHITNEY, KRUSKAL_WALLIS)

---

### 3. PowerAnalysis (New)

**Location**: `src/paper_generation/models.py` (new dataclass)

**Purpose**: Stores power analysis results for a single statistical comparison.

**Definition**:
```python
@dataclass
class PowerAnalysis:
    """
    Power analysis result for a statistical test.
    
    Enables researchers to assess sample size adequacy and plan future studies.
    """
    comparison_id: str              # E.g., "execution_time_baes_vs_chatdev"
    metric_name: str                # Metric being compared
    group_names: List[str]          # Groups involved in comparison
    
    # Effect size used for power calculation
    effect_size_value: float        # Cohen's d or f (ANOVA)
    effect_size_type: str           # "cohens_d" or "cohens_f"
    
    # Sample sizes
    n_group1: int
    n_group2: int = None            # None for multi-group ANOVA
    
    # Power analysis results
    achieved_power: float           # Calculated power (0.0-1.0)
    target_power: float = 0.80      # Desired power threshold
    alpha: float = 0.05             # Significance level
    
    # Recommendations
    power_adequate: bool            # True if achieved_power ≥ target_power
    recommended_n_per_group: int = None  # Sample size needed for target_power (if underpowered)
    
    # Interpretation
    adequacy_flag: str              # "sufficient", "insufficient", "indeterminate"
    warning_message: str = ""       # Warning for underpowered tests
    
    def __post_init__(self):
        """Set adequacy flag based on achieved power."""
        if self.achieved_power is None or np.isnan(self.achieved_power):
            self.adequacy_flag = "indeterminate"
            self.warning_message = "Power could not be calculated (insufficient sample size or extreme effect size)"
        elif self.achieved_power >= self.target_power:
            self.adequacy_flag = "sufficient"
            self.power_adequate = True
        else:
            self.adequacy_flag = "insufficient"
            self.power_adequate = False
            if self.achieved_power < 0.50:
                self.warning_message = (
                    f"Low power ({self.achieved_power:.2f}) indicates insufficient "
                    f"sample size to detect effects. Non-significant results may reflect "
                    f"inadequate power rather than true absence of effects."
                )
```

**Validation Rules** (FR-016, FR-018, FR-021):
- `achieved_power` must be between 0.0 and 1.0 (or None/NaN)
- `target_power` typically 0.80 (configurable)
- `recommended_n_per_group` only set if `power_adequate == False`
- Warning message required if `achieved_power < 0.50`

---

### 4. MultipleComparisonCorrection (New)

**Location**: `src/paper_generation/models.py` (new dataclass)

**Purpose**: Tracks multiple comparison correction metadata for a family of tests.

**Definition**:
```python
@dataclass
class MultipleComparisonCorrection:
    """
    Multiple testing correction metadata for a family of comparisons.
    
    Ensures researchers understand when and how p-values were adjusted.
    """
    metric_name: str                    # Metric family being corrected
    correction_method: str = "holm"     # "holm", "bonferroni", "fdr_bh", or "none"
    n_comparisons: int = 0              # Number of tests in family
    alpha: float = 0.05                 # Original significance level
    
    # P-value mapping (before → after correction)
    raw_pvalues: List[float] = field(default_factory=list)
    adjusted_pvalues: List[float] = field(default_factory=list)
    comparison_labels: List[str] = field(default_factory=list)  # e.g., "baes_vs_chatdev"
    
    # Results
    reject_decisions: List[bool] = field(default_factory=list)  # Significance after correction
    corrected_alpha: float = None       # Effective alpha after correction
    
    # Documentation
    citation: str = ""                  # Reference for method used
    explanation: str = ""               # Why correction was applied
    
    def __post_init__(self):
        """Set citation and explanation based on method."""
        if self.correction_method == "holm":
            self.citation = "Holm, S. (1979). Scandinavian Journal of Statistics, 6(2), 65-70"
            self.explanation = (
                f"Holm-Bonferroni correction applied to control family-wise error rate "
                f"across {self.n_comparisons} pairwise comparisons. This method is less "
                f"conservative than Bonferroni while maintaining FWER ≤ {self.alpha}."
            )
        elif self.correction_method == "none":
            self.explanation = "No correction applied (single comparison only)"
```

**Validation Rules** (FR-022, FR-023, FR-026):
- `len(raw_pvalues) == len(adjusted_pvalues) == len(comparison_labels) == n_comparisons`
- `correction_method` must be "none" if `n_comparisons == 1`
- `correction_method` must NOT be "none" if `n_comparisons > 1` (FR-022)
- All `adjusted_pvalues` must be ≥ corresponding `raw_pvalues`

---

### 5. DescriptiveStatistics (Enhanced)

**Location**: `src/paper_generation/statistical_analyzer.py` (existing dataclass in MetricDistribution)

**Purpose**: Summary statistics for a metric within a group.

**Enhancements to MetricDistribution**:
```python
@dataclass
class MetricDistribution:
    """Enhanced distribution characteristics with skewness analysis."""
    
    # EXISTING FIELDS (preserved - shown in earlier file read)
    metric_name: str
    group_name: str
    values: List[float]
    mean: float
    median: float
    std_dev: float
    q1: float
    q3: float
    skewness: float  # Already exists from T028
    
    # NEW FIELDS (additions for FR-030 to FR-034)
    skewness_flag: str = "normal"       # "normal", "moderate", "high", "severe"
    primary_summary: str = "mean"       # "mean" or "median" - which to emphasize
    summary_explanation: str = ""       # Why this summary was chosen
    
    def __post_init__(self):
        """Classify skewness and determine appropriate summary statistic."""
        abs_skew = abs(self.skewness)
        
        # FR-031: Flag metrics with |skewness| > 1.0
        if abs_skew < 0.5:
            self.skewness_flag = "normal"
            self.primary_summary = "mean"
            self.summary_explanation = "Distribution is nearly symmetric; mean ± SD appropriate."
        elif abs_skew <= 1.0:
            self.skewness_flag = "moderate"
            self.primary_summary = "median"  # FR-032
            self.summary_explanation = "Moderate skewness detected; median and IQR are more robust."
        elif abs_skew <= 2.0:
            self.skewness_flag = "high"
            self.primary_summary = "median"
            self.summary_explanation = "High skewness detected; median strongly preferred over mean."
        else:
            self.skewness_flag = "severe"  # FR-034
            self.primary_summary = "median"
            self.summary_explanation = (
                f"Severe skewness ({self.skewness:.2f}) detected; mean is substantially "
                f"biased by extreme values. Median provides more accurate central tendency."
            )
```

**Display Rules** (FR-032, FR-033):
- If `primary_summary == "median"`: Bold median and IQR in tables, mention median first in text
- If `primary_summary == "mean"`: Bold mean and SD in tables, mention mean first in text
- Always report both statistics, but emphasize the appropriate one

---

## Entity Relationships

```
StatisticalTest
├── has_one → EffectSize (via test_type_alignment)
├── has_one → PowerAnalysis (via comparison_id)
└── belongs_to → MultipleComparisonCorrection (via metric_name family)

EffectSize
├── validates → ci_contains_point_estimate (invariant)
└── aligns_with → TestType (parametric/non-parametric)

PowerAnalysis
├── derived_from → EffectSize (uses effect_size_value)
└── references → StatisticalTest (same comparison)

MultipleComparisonCorrection
├── has_many → StatisticalTest (all tests in metric family)
└── transforms → pvalue_raw to pvalue_adjusted

MetricDistribution
├── determines → EffectSize calculation method (parametric vs non-parametric)
└── sets → primary_summary based on skewness_flag
```

## Database Schema

**Note**: This project uses file-based storage (YAML config, JSON results). No SQL database schema required. All entities are Python dataclasses serialized to JSON in run artifacts.

## Migration Strategy

**No migrations needed** - these are backward-compatible enhancements:
- New fields have defaults (e.g., `pvalue_adjusted: float = None`)
- Existing code will continue to work with old data (missing fields use defaults)
- New validation only applied to newly-generated results

## Validation Summary

| Entity | Validation Rule | Enforced By |
|--------|----------------|-------------|
| EffectSize | CI contains point estimate | `__post_init__` (FR-002) |
| EffectSize | Bootstrap iterations ≥ 10,000 | `_bootstrap_effect_size()` (FR-003) |
| EffectSize | Measure aligns with test type | `_select_effect_size_measure()` (FR-013, FR-014) |
| StatisticalTest | Adjusted p-value ≥ raw p-value | `_apply_multiple_comparison_correction()` |
| PowerAnalysis | Achieved power in [0.0, 1.0] | `__post_init__` |
| MultipleComparisonCorrection | Correction only if n > 1 | `_should_apply_correction()` (FR-026) |
| MetricDistribution | Skewness flag matches |skew| | `__post_init__` (FR-031) |
