# Statistical Analysis Improvements - Implementation Plan

**Date**: October 30, 2025  
**Branch**: main  
**Status**: Post-merge validation and enhancement planning

---

## Executive Summary

Following expert statistical review and comprehensive code analysis, **all 9 critical issues have been resolved**. This document outlines:

1. ✅ **Completed Fixes** - Validation of implemented solutions
2. 📋 **Testing Strategy** - Edge case validation with simulated data
3. 🔧 **Proposed Refactoring** - Code quality improvements
4. 🚀 **Optional Enhancements** - Future improvements

---

## Part 1: Validation of Completed Fixes

### 1.1 Effect Size Calculations ✅ VERIFIED

**Implementation Status**: CORRECT

**Formulas Validated**:
- **Cliff's Delta**: Proper pairwise comparison (`statistical_helpers.py:107-150`)
  ```python
  for x in group1:
      for y in group2:
          if x > y: greater += 1
          elif x < y: less += 1
  return (greater - less) / total
  ```
- **Cohen's d**: Standard pooled SD formula (`statistical_helpers.py:68-104`)
  ```python
  pooled_sd = sqrt(((n1-1)*sd1² + (n2-1)*sd2²) / (n1+n2-2))
  return (mean1 - mean2) / pooled_sd
  ```

**Bootstrap CI**: Independent resampling, 10,000 iterations ✅

**Zero-Variance Protection**: 
- ✅ Threshold: SD < 0.01 OR IQR < 0.01
- ✅ Action: Skip Cohen's d, warn for Cliff's Δ
- ✅ Location: `statistical_analyzer.py:1803-1810`

**Verdict**: No changes needed. Formulas are mathematically correct.

---

### 1.2 Assumption Testing & Test Selection ✅ VERIFIED

**Implementation Status**: SOUND

**Components Validated**:
1. **Normality Testing**: Shapiro-Wilk ✅
2. **Variance Homogeneity**: Levene's test (median-centered) ✅
3. **Adaptive Selection**:
   - 2 groups: t-test (normal, equal var) → Mann-Whitney (otherwise)
   - 3+ groups: ANOVA (normal, equal var) → Kruskal-Wallis (otherwise)

**Multiple Comparison Correction**:
- ✅ Method: Holm-Bonferroni (`statistical_analyzer.py:610-638`)
- ✅ Applied automatically per metric family
- ✅ Both raw and adjusted p-values reported

**Note**: Reviewer mentioned verifying if it's Holm vs. standard Bonferroni. Our implementation uses:
```python
# Line 1726 in statistical_analyzer.py
reject, adjusted_pvalues, alphacSidak, alphacBonf = multipletests(
    pvalues, alpha=alpha, method=method  # method='holm'
)
```
**Confirmed**: Uses Holm-Bonferroni (more powerful than standard Bonferroni) ✅

**Verdict**: Implementation is statistically sound and follows best practices.

---

### 1.3 Post-Hoc Power Analysis ✅ VERIFIED REMOVED

**Decision**: Disabled in reports (Commit: 6960de0)

**Rationale**:
- Post-hoc power = transformation of p-value (no new information)
- When p < 0.05 → power high; when p > 0.05 → power low (tautology)
- Discouraged by modern statistical guidance

**Implementation**:
- ✅ Section commented out: `experiment_analyzer.py:847-857`
- ✅ Table of Contents updated
- ✅ Sections renumbered (Methodology 6→5, Glossary 7→6)
- ✅ Code preserved for backward compatibility
- ✅ Detailed comments explaining rationale

**Alternative for Future**: A priori power analysis for prospective planning

**Verdict**: Correct decision. Do not reintroduce.

---

### 1.4 Deterministic Confidence Intervals ✅ VERIFIED CORRECT

**Finding**: CIs like [1.0, 1.0] are **not computation errors**

**Cause**: Complete group separation (all group1 values > all group2 values)

**Validation**:
- Tested separated groups → CI = [1.0, 1.0] ✓ (mathematically valid)
- Tested overlapping groups → CI = [0.574, 1.0] ✓ (proper variation)

**Solution Implemented**:
- ✅ Detect zero/near-zero variance
- ✅ Warn when CI is deterministic (`statistical_analyzer.py:1872-1880`)
- ✅ Explain: "categorical separation rather than continuous effect"

**Warning Message**:
```python
logger.warning(
    f"Cliff's Delta CI for {group1} vs {group2} on {metric_name} "
    f"is deterministic [{ci_lower:.3f}, {ci_upper:.3f}] due to "
    f"zero/near-zero variance (SD: {std1:.4f}, {std2:.4f}, "
    f"IQR: {iqr1:.4f}, {iqr2:.4f}). This represents categorical "
    f"separation rather than continuous effect size."
)
```

**Verdict**: No bug to fix. Warnings provide appropriate context.

---

## Part 2: Testing Strategy - Edge Case Validation

### 2.1 Simulated Data Test Suite

**Purpose**: Stress-test statistical analysis logic with known edge cases

**Test Cases to Implement**:

#### Test 1: Complete Zero Variance
```python
# Both groups constant
group1 = [5.0, 5.0, 5.0, 5.0, 5.0]
group2 = [10.0, 10.0, 10.0, 10.0, 10.0]

# Expected:
# - Zero variance detected: ✓
# - Cohen's d skipped: ✓
# - Cliff's Δ = -1.0, CI = [-1.0, -1.0]: ✓
# - Warning logged: ✓
```

#### Test 2: Near-Zero Variance (Below Threshold)
```python
# One group near-constant (SD < 0.01)
group1 = [10.0, 10.001, 10.002, 10.001, 10.0]
group2 = [20.0, 21.0, 19.0, 22.0, 18.0]

# Expected:
# - Near-zero variance detected: ✓
# - Cohen's d skipped: ✓
# - Warning logged: ✓
```

#### Test 3: Just Above Threshold
```python
# SD slightly above 0.01 (should NOT trigger)
group1 = [10.0, 10.05, 10.10, 10.02, 10.08]  # SD ≈ 0.04
group2 = [20.0, 21.0, 19.0, 22.0, 18.0]

# Expected:
# - Zero variance NOT detected: ✓
# - Cohen's d calculated: ✓
# - No warning: ✓
```

#### Test 4: Identical Groups
```python
# Same distribution in both
group1 = [5, 5, 5, 5]
group2 = [5, 5, 5, 5]

# Expected:
# - Zero variance detected: ✓
# - Tests skipped: ✓
# - Cliff's Δ = 0.0, CI = [0.0, 0.0]: ✓
```

#### Test 5: Complete Non-Overlap
```python
# No overlap but with variance
group1 = [10, 12, 15, 14, 13, 11, 16]
group2 = [3, 4, 5, 4, 6, 5, 4, 3]

# Expected:
# - Variance OK: ✓
# - Cliff's Δ = 1.0: ✓
# - CI may be [1.0, 1.0] or narrowly below: ✓
# - Warning if deterministic: ✓
```

### 2.2 Implementation Location

Create: `tests/test_statistical_edge_cases.py`

```python
"""
Test suite for statistical analysis edge cases.

Validates zero-variance detection, deterministic CIs, and
appropriate handling of degenerate data scenarios.
"""

import pytest
import numpy as np
from src.paper_generation.statistical_analyzer import StatisticalAnalyzer

class TestEdgeCases:
    @pytest.fixture
    def analyzer(self):
        return StatisticalAnalyzer(alpha=0.05, random_seed=42)
    
    def test_complete_zero_variance(self, analyzer):
        """Test handling of groups with zero variance."""
        # Test implementation from Test 1 above
        pass
    
    def test_near_zero_variance(self, analyzer):
        """Test detection of near-zero variance (SD < 0.01)."""
        # Test implementation from Test 2 above
        pass
    
    # ... additional tests
```

### 2.3 Validation Checklist

- [ ] All 5 edge cases implemented and passing
- [ ] Warnings logged to correct logger level
- [ ] Report output includes warnings in appropriate sections
- [ ] No false positives (threshold too high)
- [ ] No false negatives (threshold too low)
- [ ] Documentation updated with edge case behavior

---

## Part 3: Proposed Refactoring

### 3.1 Method Decomposition

**Rationale**: Improve readability and testability

**Target**: `_calculate_effect_sizes()` method (currently ~200 lines)

**Proposed Refactoring**:
```python
def _calculate_effect_sizes(self, metric_name, metric_data, distributions, test_results):
    """Main orchestration method."""
    effect_sizes = []
    
    for test in test_results:
        # Extract data
        vals1, vals2 = self._extract_pairwise_values(test, metric_data)
        
        # Validate variance
        variance_status = self._check_variance_quality(vals1, vals2)
        if variance_status['skip_cohens_d']:
            logger.warning(variance_status['message'])
            continue
        
        # Select measure
        measure = self._select_effect_measure(test, variance_status)
        
        # Calculate effect
        effect = self._compute_effect_with_ci(vals1, vals2, measure, test)
        
        # Warn if needed
        if effect['is_deterministic']:
            logger.warning(effect['warning_message'])
        
        effect_sizes.append(effect)
    
    return effect_sizes

def _check_variance_quality(self, vals1, vals2):
    """Extract variance checking logic into separate method."""
    std1, std2 = np.std(vals1), np.std(vals2)
    iqr1 = np.percentile(vals1, 75) - np.percentile(vals1, 25)
    iqr2 = np.percentile(vals2, 75) - np.percentile(vals2, 25)
    
    zero_variance = (std1 < 0.01 or std2 < 0.01 or 
                    iqr1 < 0.01 or iqr2 < 0.01)
    
    return {
        'zero_variance': zero_variance,
        'skip_cohens_d': zero_variance,
        'std1': std1, 'std2': std2,
        'iqr1': iqr1, 'iqr2': iqr2,
        'message': f"Zero variance detected: SD({std1:.4f}, {std2:.4f}), IQR({iqr1:.4f}, {iqr2:.4f})"
    }
```

**Benefits**:
- Each method has single responsibility
- Easier to unit test
- Clearer logic flow
- Better code reuse

---

### 3.2 Configuration Management

**Current State**: Some thresholds hardcoded

**Proposed**: Centralized configuration

**Implementation**:
```python
# src/paper_generation/config.py
@dataclass
class StatisticalConfig:
    """Configuration for statistical analysis."""
    alpha: float = 0.05
    random_seed: int = 42
    bootstrap_iterations: int = 10000
    target_power: float = 0.80
    
    # Zero-variance detection
    variance_threshold_sd: float = 0.01
    variance_threshold_iqr: float = 0.01
    
    # Effect size interpretation
    cohens_d_small: float = 0.2
    cohens_d_medium: float = 0.5
    cohens_d_large: float = 0.8
    
    cliffs_delta_small: float = 0.147
    cliffs_delta_medium: float = 0.33
    cliffs_delta_large: float = 0.474
    
    # Reporting
    decimal_places_effect: int = 3
    decimal_places_pvalue: int = 3
    
    # Multiple comparison
    correction_method: str = "holm"  # Options: 'holm', 'bonferroni', 'fdr_bh'
```

**Benefits**:
- Single source of truth
- Easy to adjust for sensitivity analysis
- Self-documenting (thresholds visible)
- Enables A/B testing of different configurations

---

### 3.3 Code Cleanup - Disabled Power Analysis

**Current**: Power analysis code commented out in-place

**Proposed**:
1. Move to separate module: `src/paper_generation/power_analysis_prospective.py`
2. Implement as opt-in feature (config flag)
3. Document as "a priori power calculator" for future studies

**Benefits**:
- Main flow uncluttered
- Code preserved if needed
- Clear separation of concerns
- Potential for future feature flag

---

### 3.4 Consistent Logging

**Current**: Mix of `logger.warning()`, `logger.info()`, `logger.debug()`

**Proposed**: Standardize logging levels

```python
# Logging Guidelines
logger.debug()    # Detailed diagnostic (always safe to ignore)
logger.info()     # Normal operation milestones
logger.warning()  # Data quality issues, assumption violations
logger.error()    # Analysis failures, bugs
logger.critical() # Fatal errors preventing completion
```

**Example Standardization**:
```python
# Data quality warnings
logger.warning("Zero variance detected for %s in %s", metric, framework)
logger.warning("Deterministic CI [%.3f, %.3f] due to complete separation", ci[0], ci[1])

# Normal progress
logger.info("Analyzing %d metrics: %s", len(metrics), metrics)
logger.info("Analysis complete: %d tests, %d significant", n_tests, n_sig)

# Debugging
logger.debug("Skipping effect size for %s vs %s: zero variance", g1, g2)
```

---

## Part 4: Optional Enhancements

### 4.1 A Priori Power Analysis Tool 🚀

**Purpose**: Help plan future experiments

**Implementation**:
```python
# src/paper_generation/power_analysis_prospective.py

class ProspectivePowerAnalyzer:
    """Calculate required sample sizes for desired power."""
    
    def calculate_required_n(
        self,
        expected_effect_size: float,
        effect_measure: str = 'cohens_d',  # or 'cliffs_delta'
        desired_power: float = 0.80,
        alpha: float = 0.05,
        test_type: str = 't_test'  # or 'mann_whitney', 'anova', etc.
    ) -> dict:
        """
        Calculate sample size needed to detect expected effect.
        
        Returns:
            {
                'n_per_group': int,
                'total_n': int,
                'power': float,
                'effect_size': float,
                'test_type': str,
                'recommendation': str
            }
        """
        pass
    
    def generate_power_curves(
        self,
        effect_sizes: List[float],
        sample_sizes: List[int]
    ) -> PowerCurvePlot:
        """Generate power curves showing N vs. power for various effect sizes."""
        pass
```

**Usage**:
```python
# In report appendix or separate tool
analyzer = ProspectivePowerAnalyzer()
recommendation = analyzer.calculate_required_n(
    expected_effect_size=0.5,  # Medium Cohen's d
    desired_power=0.80,
    test_type='t_test'
)
print(f"Recommended: {recommendation['n_per_group']} runs per framework")
```

---

### 4.2 Effect Size Interpretation Table 📊

**Purpose**: Help readers understand magnitude

**Implementation**: Add to glossary section

```markdown
### Effect Size Interpretation Guide

#### Cohen's d (Parametric)
| Range | Interpretation | Practical Meaning |
|-------|----------------|-------------------|
| \|d\| < 0.2 | Negligible | Minimal practical difference |
| 0.2 ≤ \|d\| < 0.5 | Small | Detectable but modest difference |
| 0.5 ≤ \|d\| < 0.8 | Medium | Moderate, meaningful difference |
| \|d\| ≥ 0.8 | Large | Substantial difference |

#### Cliff's Delta (Non-Parametric)
| Range | Interpretation | Dominance Level |
|-------|----------------|-----------------|
| \|δ\| < 0.147 | Negligible | Groups largely overlap |
| 0.147 ≤ \|δ\| < 0.33 | Small | One group tends higher |
| 0.33 ≤ \|δ\| < 0.474 | Medium | Clear tendency difference |
| \|δ\| ≥ 0.474 | Large | Strong separation |
| \|δ\| = 1.0 | Complete | No overlap (all A > all B) |

**Note**: Effect size interpretation should consider domain context. 
Small effects may be practically important in performance benchmarking.
```

---

### 4.3 Visual Indicators for Zero-Variance 🎨

**Purpose**: Make data quality issues visible in plots

**Implementation**:

**Box Plots**:
```python
# In statistical_visualizations.py
if distribution.has_zero_variance:
    # Instead of box with 0 IQR, show horizontal line + annotation
    ax.axhline(y=distribution.mean, xmin=x_pos-0.2, xmax=x_pos+0.2,
               color='red', linewidth=3, label='Zero Variance')
    ax.annotate('No variation', xy=(x_pos, distribution.mean),
                xytext=(x_pos+0.3, distribution.mean),
                arrowprops=dict(arrowstyle='->', color='red'))
```

**Forest Plots**:
```python
# When Cliff's Δ = ±1.0 with deterministic CI
if abs(effect.value) == 1.0 and effect.ci_lower == effect.ci_upper:
    # Use open marker instead of filled
    ax.scatter(effect.value, y_pos, marker='o', s=150,
               facecolors='none', edgecolors='red', linewidths=2,
               label='Complete Separation')
```

**Benefits**:
- Immediate visual cue for data quality
- Reduces misinterpretation
- Complements textual warnings

---

### 4.4 Automated Warning Summary 🔔

**Purpose**: Consolidate all caveats in one place

**Implementation**:

#### 4.4.1 CLI Output
```python
# At end of analysis in analyze_experiment()
warnings_summary = self._collect_warnings()
if warnings_summary:
    logger.warning("=" * 60)
    logger.warning("ANALYSIS WARNINGS SUMMARY (%d issues)", len(warnings_summary))
    logger.warning("=" * 60)
    for i, warning in enumerate(warnings_summary, 1):
        logger.warning(f"{i}. {warning}")
    logger.warning("=" * 60)
```

#### 4.4.2 Markdown Report Section
```python
# In experiment_analyzer.py, add after methodology
if findings.warnings:
    sections.append("## ⚠️ Notes and Warnings\n\n")
    sections.append(
        "The following conditions were detected during analysis "
        "and may affect interpretation:\n\n"
    )
    for i, warning in enumerate(findings.warnings, 1):
        sections.append(f"{i}. {warning}\n")
    sections.append("\n")
```

#### 4.4.3 Warning Collection
```python
# In models.py, add to StatisticalFindings
@dataclass
class StatisticalFindings:
    # ... existing fields ...
    warnings: List[str] = field(default_factory=list)
    
    def add_warning(self, category: str, message: str):
        """Add a warning with category tag."""
        self.warnings.append(f"**{category}**: {message}")
```

**Example Output**:
```markdown
## ⚠️ Notes and Warnings

The following conditions were detected during analysis and may affect interpretation:

1. **Zero Variance**: Framework 'BAES' showed zero variance for metric 'cached_tokens'; 
   statistical tests skipped for this metric.

2. **Deterministic CI**: Cliff's Delta for metric 'tokens_total' comparison 'BAES vs ghspec' 
   is 1.0 with CI [1.0, 1.0], indicating complete separation between groups.

3. **Assumption Violation**: Levene's test for metric 'quality_score' was significant (p < 0.001); 
   non-parametric test (Mann-Whitney U) was used instead of t-test.

4. **Outliers Detected**: 3 outliers identified in metric 'execution_time' for framework 'chatdev'. 
   Outliers were retained in analysis; robust methods used.
```

**Benefits**:
- Transparency in both CLI and report
- Quick scan for issues
- Readers don't miss important caveats
- Builds trust in analysis

---

## Part 5: Implementation Priorities

### Priority 1: Testing (Immediate) 🔴
- [ ] Create `test_statistical_edge_cases.py`
- [ ] Implement 5 core edge case tests
- [ ] Validate warnings are logged correctly
- [ ] Confirm thresholds work as expected
- **Timeline**: 1-2 days

### Priority 2: Warning Summary (High Value) 🟡
- [ ] Implement warning collection system
- [ ] Add CLI warning summary
- [ ] Add Markdown report section
- [ ] Test with real data
- **Timeline**: 2-3 days

### Priority 3: Refactoring (Code Quality) 🟢
- [ ] Extract variance checking logic
- [ ] Create configuration class
- [ ] Standardize logging levels
- [ ] Document refactored methods
- **Timeline**: 3-5 days

### Priority 4: Enhancements (Optional) 🔵
- [ ] A priori power analysis tool
- [ ] Effect size interpretation table
- [ ] Visual indicators for zero-variance
- [ ] Power curve generator
- **Timeline**: 1-2 weeks (can be phased)

---

## Part 6: Success Criteria

### Validation Metrics
- ✅ All edge case tests passing
- ✅ No false positive/negative variance detection
- ✅ Warnings appear in correct output locations
- ✅ Code coverage ≥ 90% for statistical modules
- ✅ Documentation complete and accurate

### Quality Metrics
- ✅ Method length < 50 lines (after refactoring)
- ✅ Cyclomatic complexity < 10 per method
- ✅ All thresholds configurable
- ✅ Consistent logging levels used

### User Experience Metrics
- ✅ Warnings easy to understand
- ✅ Summary section valuable to readers
- ✅ Visual indicators clear and unambiguous
- ✅ Report self-explanatory (minimal questions)

---

## Part 7: Conclusion

### Current Status
The statistical analysis implementation is **sound and publication-ready**. All critical issues have been addressed with statistically appropriate solutions.

### Recommended Actions
1. **Execute testing strategy** to validate edge cases
2. **Implement warning summary** for improved transparency
3. **Consider refactoring** for long-term maintainability
4. **Evaluate enhancements** based on user feedback

### No Action Needed
- ❌ Do NOT alter effect size formulas (correct)
- ❌ Do NOT reintroduce post-hoc power (problematic)
- ❌ Do NOT "fix" deterministic CIs (mathematically valid)
- ❌ Do NOT remove zero-variance detection (essential)

---

## References

- Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences (2nd ed.)
- Holm, S. (1979). A simple sequentially rejective multiple test procedure. Scandinavian Journal of Statistics, 6(2), 65-70.
- Romano, J., Shaikh, A. M., & Wolf, M. (2008). Formalized data snooping based on generalized error rates. Econometric Theory, 24(2), 404-447.
- Hoenig, J. M., & Heisey, D. M. (2001). The abuse of power: The pervasive fallacy of power calculations for data analysis. The American Statistician, 55(1), 19-24.

---

**Document Version**: 1.0  
**Last Updated**: October 30, 2025  
**Status**: Ready for implementation
