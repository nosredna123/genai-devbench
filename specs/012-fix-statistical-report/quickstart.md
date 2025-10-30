# Quickstart: Testing & Validation Guide

**Feature**: Fix Statistical Report Generation Issues  
**Date**: 2025-10-29  
**Audience**: Developers implementing and testing the 9 statistical fixes

## Overview

This guide shows how to test the statistical report fixes end-to-end, from unit tests to integration validation. All tests follow the existing pytest structure and BAEs constitution principles (reproducibility, fail-fast, educational).

## Prerequisites

```bash
# From repository root
cd /home/amg/projects/uece/baes/genai-devbench

# Ensure dependencies installed
pip install -r requirements.txt

# Verify statsmodels installed (new dependency for power analysis)
python -c "import statsmodels; print(f'statsmodels {statsmodels.__version__}')"
# Expected: statsmodels 0.14.0 or higher
```

## Quick Validation (5 minutes)

### 1. Run Unit Tests for Fixed Components

```bash
# Test bootstrap CI fix (Issue #1, #2)
pytest tests/unit/test_bootstrap_ci_fix.py -v

# Test Welch's test selection (Issue #3)
pytest tests/unit/test_welch_test_selection.py -v

# Test power analysis (Issue #4)
pytest tests/unit/test_power_analysis.py -v

# Test p-value formatting (Issue #6)
pytest tests/unit/test_pvalue_formatting.py -v

# Test multiple comparisons (Issue #7)
pytest tests/unit/test_multiple_comparisons.py -v

# Run all new statistical tests
pytest tests/unit/test_*.py -k "bootstrap_ci or welch or power or pvalue or multiple" -v
```

**Expected Output**:
```
tests/unit/test_bootstrap_ci_fix.py::test_ci_contains_point_estimate PASSED
tests/unit/test_bootstrap_ci_fix.py::test_independent_group_resampling PASSED
tests/unit/test_welch_test_selection.py::test_welch_anova_selected PASSED
tests/unit/test_power_analysis.py::test_achieved_power_calculation PASSED
...
==================== 25 passed in 3.2s ====================
```

### 2. Run Integration Test

```bash
# Full end-to-end validation (all 9 issues)
pytest tests/integration/test_phase9_statistical_fixes.py -v --tb=short

# With detailed output showing statistical calculations
pytest tests/integration/test_phase9_statistical_fixes.py -v -s
```

**Expected Output**:
```
tests/integration/test_phase9_statistical_fixes.py::test_bootstrap_cis_valid PASSED
tests/integration/test_phase9_statistical_fixes.py::test_welch_tests_used PASSED
tests/integration/test_phase9_statistical_fixes.py::test_power_analysis_section_exists PASSED
tests/integration/test_phase9_statistical_fixes.py::test_effect_size_alignment PASSED
tests/integration/test_phase9_statistical_fixes.py::test_multiple_comparison_correction PASSED
tests/integration/test_phase9_statistical_fixes.py::test_pvalue_formatting PASSED
tests/integration/test_phase9_statistical_fixes.py::test_skewness_emphasis PASSED
tests/integration/test_phase9_statistical_fixes.py::test_neutral_language PASSED
tests/integration/test_phase9_statistical_fixes.py::test_all_fixes_integrated PASSED
==================== 9 passed in 12.4s ====================
```

### 3. Generate Sample Report

```bash
# Generate statistical report with fixed implementation
python -m src.paper_generation.paper_generator \
    --run-file tests/fixtures/sample_run_data.json \
    --output-dir ./test_report \
    --sections statistical

# View generated report
cat ./test_report/statistical_report_full.md | less
```

**What to Look For**:
- ✅ All CIs contain their point estimates (Issue #1, #2)
- ✅ Welch's ANOVA used when appropriate (Issue #3)
- ✅ Section 5 "Power Analysis" exists with all comparisons (Issue #4)
- ✅ Effect sizes match test types (Issue #5)
- ✅ Both raw and adjusted p-values shown (Issue #7)
- ✅ P-values formatted as "p < 0.001" not "p = 0.0000" (Issue #6)
- ✅ Skewed metrics emphasize median/IQR (Issue #8)
- ✅ Neutral language ("shows higher values") used (Issue #9)

## Detailed Testing Workflows

### Workflow 1: Validate Bootstrap CI Fix (Issue #1, #2)

**Problem**: Old implementation produced CIs that don't contain point estimates

**Test Steps**:
```python
# tests/unit/test_bootstrap_ci_fix.py
def test_ci_contains_point_estimate():
    """Verify all bootstrap CIs mathematically contain point estimates."""
    group1 = np.random.normal(10, 2, 50)  # Mean=10, SD=2
    group2 = np.random.normal(12, 2, 50)  # Mean=12, SD=2
    
    analyzer = StatisticalAnalyzer(random_seed=42)
    
    # Compute Cohen's d with CI
    d_point = cohens_d(group1, group2)
    ci_lower, ci_upper, ci_valid = analyzer._bootstrap_confidence_interval(
        group1, group2, cohens_d, n_iterations=10000
    )
    
    # FR-002: CI must contain point estimate
    assert ci_lower <= d_point <= ci_upper, \
        f"CI [{ci_lower:.3f}, {ci_upper:.3f}] does not contain point estimate {d_point:.3f}"
    assert ci_valid is True
```

**Manual Verification**:
```bash
# Run with verbose output to see CI values
pytest tests/unit/test_bootstrap_ci_fix.py::test_ci_contains_point_estimate -v -s

# Expected output includes:
# Point estimate: d = -1.023
# Bootstrap CI: [-1.487, -0.562]
# CI valid: True ✓
```

### Workflow 2: Validate Test Selection (Issue #3)

**Problem**: System didn't use Welch's ANOVA for normal data with unequal variances

**Test Steps**:
```python
# tests/unit/test_welch_test_selection.py
def test_welch_anova_selected_for_normal_unequal_variance():
    """Verify Welch's ANOVA selected when groups are normal but variances differ."""
    # Create 3 groups: all normal, different variances
    group1 = np.random.normal(10, 1, 30)   # SD=1
    group2 = np.random.normal(11, 3, 30)   # SD=3 (3x larger)
    group3 = np.random.normal(12, 5, 30)   # SD=5 (5x larger)
    
    distributions = [
        create_distribution(group1, "Group1"),
        create_distribution(group2, "Group2"),
        create_distribution(group3, "Group3")
    ]
    
    analyzer = StatisticalAnalyzer()
    test_type, assumptions, rationale = analyzer._select_statistical_test(distributions)
    
    # FR-007: Welch's ANOVA for normal + unequal variance
    assert test_type == TestType.WELCH_ANOVA
    assert assumptions['normality'] is True
    assert assumptions['equal_variance'] is False
    assert "Welch's ANOVA" in rationale
```

**Manual Verification**:
```bash
# Generate report with known data characteristics
python tests/fixtures/generate_synthetic_data.py --case "normal_unequal_var"

# Run report generation
python -m src.paper_generation.paper_generator \
    --run-file tests/fixtures/normal_unequal_var.json \
    --output-dir ./test_welch

# Check methodology section
grep "Welch's ANOVA" ./test_welch/statistical_report_full.md
# Expected: "Welch's ANOVA was used for execution_time (3 groups, all normal, unequal variances)"
```

### Workflow 3: Validate Power Analysis (Issue #4)

**Problem**: Power Analysis section missing despite being claimed

**Test Steps**:
```python
# tests/unit/test_power_analysis.py
def test_power_analysis_calculation():
    """Verify power analysis calculates achieved power correctly."""
    analyzer = StatisticalAnalyzer()
    
    # Small effect (d=0.3), small n (20 per group) → low power expected
    power_result = analyzer._calculate_power_analysis(
        test_type=TestType.T_TEST,
        effect_size=0.3,  # Cohen's d
        n1=20,
        n2=20,
        alpha=0.05,
        target_power=0.80
    )
    
    # Should have low power (<0.80) and recommend larger n
    assert power_result.achieved_power < 0.80
    assert power_result.power_adequate is False
    assert power_result.recommended_n_per_group > 20
    
    # Large effect (d=1.0), large n (100 per group) → high power expected
    power_result_high = analyzer._calculate_power_analysis(
        test_type=TestType.T_TEST,
        effect_size=1.0,
        n1=100,
        n2=100,
        alpha=0.05,
        target_power=0.80
    )
    
    assert power_result_high.achieved_power > 0.95
    assert power_result_high.power_adequate is True
```

**Manual Verification**:
```bash
# Generate report and check Section 5
python -m src.paper_generation.paper_generator \
    --run-file tests/fixtures/sample_run_data.json \
    --output-dir ./test_power \
    --sections statistical

# Check for Section 5
grep -A 20 "## 5. Power Analysis" ./test_power/statistical_report_full.md

# Expected to see table:
# | Comparison | Effect Size | Achieved Power | Recommended n |
# |------------|-------------|----------------|---------------|
# | baes vs chatdev | d=0.42 | 0.73 | n=52 per group |
```

### Workflow 4: End-to-End Validation (All 9 Issues)

**Complete Validation Script**:
```bash
#!/bin/bash
# tests/integration/validate_all_fixes.sh

set -e  # Fail-fast

echo "=== Validating All Statistical Fixes ==="

# 1. Run all unit tests
echo "Step 1: Unit tests..."
pytest tests/unit/test_bootstrap_ci_fix.py \
       tests/unit/test_welch_test_selection.py \
       tests/unit/test_power_analysis.py \
       tests/unit/test_pvalue_formatting.py \
       tests/unit/test_multiple_comparisons.py \
       -v --tb=short

# 2. Generate synthetic test data with known properties
echo "Step 2: Generate synthetic test data..."
python tests/fixtures/generate_synthetic_data.py --all-cases

# 3. Run report generation on each case
echo "Step 3: Generate reports..."
for case in normal_equal_var normal_unequal_var non_normal skewed; do
    python -m src.paper_generation.paper_generator \
        --run-file tests/fixtures/${case}.json \
        --output-dir ./test_reports/${case} \
        --sections statistical
done

# 4. Validate each report against checklist
echo "Step 4: Validate reports..."
python tests/integration/validate_reports.py ./test_reports/

# 5. Run integration test suite
echo "Step 5: Integration tests..."
pytest tests/integration/test_phase9_statistical_fixes.py -v

echo "✅ All validations passed!"
```

**Run Complete Validation**:
```bash
chmod +x tests/integration/validate_all_fixes.sh
./tests/integration/validate_all_fixes.sh
```

## Common Issues & Troubleshooting

### Issue: "Module 'statsmodels' not found"

**Solution**:
```bash
pip install statsmodels>=0.14.0
```

### Issue: "Bootstrap CI does not contain point estimate"

**Diagnosis**: Old implementation still in use

**Solution**:
```bash
# Verify you're on the correct branch
git branch --show-current
# Should show: 012-fix-statistical-report

# Check bootstrap implementation
grep -A 10 "_bootstrap_confidence_interval" src/paper_generation/statistical_analyzer.py
# Should see: "# Resample each group independently"
```

### Issue: "Power Analysis section not found in report"

**Diagnosis**: Section generation not updated

**Solution**:
```bash
# Check section_generator.py has Power Analysis section
grep "def _generate_power_analysis_section" src/paper_generation/section_generator.py

# Verify it's being called
grep "power_analysis_section" src/paper_generation/section_generator.py
```

### Issue: "Tests fail with 'CI is invalid'"

**Expected**: This is correct behavior now! The fix enforces that CIs must contain point estimates.

**Action**: Check if test data or implementation has a bug. All valid bootstrap CIs should contain their point estimates.

## Success Criteria Checklist

Run this checklist after implementation:

```
Statistical Accuracy:
- [ ] 100% of bootstrap CIs contain their point estimates (run 1000+ times, seed varied)
- [ ] Welch's ANOVA selected for (normal + unequal var) cases
- [ ] Power Analysis section present in all full reports
- [ ] Effect sizes match test types (parametric→d, non-parametric→δ)

Completeness:
- [ ] Section 5 "Power Analysis" exists with table of all comparisons
- [ ] Both raw and adjusted p-values reported when corrections applied
- [ ] Holm-Bonferroni documented in methodology section

Professional Quality:
- [ ] Zero instances of "p = 0.0000" in any generated report
- [ ] Skewed metrics (|skew|>1) emphasize median/IQR in text
- [ ] No causal language ("outperforms") in generated reports

Reproducibility:
- [ ] Same input data produces identical results on re-run (check with seed)
- [ ] All statistical formulas documented with inline comments
- [ ] Test selection rationale included in reports
```

## Performance Benchmarks

Expected performance (measured on standard laptop):

```
Bootstrap CI calculation:  < 5 seconds per comparison (n≤100, 10k iterations)
Full statistical report:   < 3 minutes (10 metrics × 3 groups = 21 comparisons)
Power analysis overhead:   < 20% increase to total time
Unit test suite:           < 10 seconds (all new tests)
Integration test suite:    < 15 seconds (all 9 validation tests)
```

**Benchmark Script**:
```python
# tests/performance/benchmark_statistical_fixes.py
import time
from src.paper_generation.statistical_analyzer import StatisticalAnalyzer

def benchmark_bootstrap_ci():
    analyzer = StatisticalAnalyzer(random_seed=42)
    group1 = np.random.normal(10, 2, 100)
    group2 = np.random.normal(12, 2, 100)
    
    start = time.time()
    ci_lower, ci_upper, ci_valid = analyzer._bootstrap_confidence_interval(
        group1, group2, cohens_d, n_iterations=10000
    )
    elapsed = time.time() - start
    
    assert elapsed < 5.0, f"Bootstrap took {elapsed:.2f}s, should be <5s"
    print(f"✓ Bootstrap CI: {elapsed:.2f}s (target: <5s)")

# Run benchmark
pytest tests/performance/benchmark_statistical_fixes.py -v
```

## Next Steps

After successful validation:

1. **Merge to main**: All tests passing, checklist complete
2. **Update documentation**: Add statistical fixes to changelog
3. **Notify stakeholders**: Share improved report example with team
4. **Monitor production**: Watch for any edge cases in real experiment data

## Reference

- **Specification**: `/specs/012-fix-statistical-report/spec.md`
- **Implementation Plan**: `/specs/012-fix-statistical-report/plan.md`
- **Data Models**: `/specs/012-fix-statistical-report/data-model.md`
- **API Contracts**: `/specs/012-fix-statistical-report/contracts/`
- **Statistical Analysis Document**: `/docs/STATISTICAL_REPORT_CRITIQUE_RESPONSE.md`
