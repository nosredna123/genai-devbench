# Variance Check Audit - Feature 013

## Summary
Complete audit of all variance detection logic in the paper generation pipeline after fixing the precision loss and variance check issues.

## Problem Discovery
1. **Precision loss**: 2-decimal formatting hid 20% variance in cost metrics
2. **False warnings**: Absolute thresholds (< 0.01) flagged legitimate 5% variance as "zero"
3. **Box plot inconsistency**: Box plots still used old absolute thresholds

## Solution: Relative Variance Detection
All variance checks now use **coefficient of variation (CV)** instead of absolute thresholds:
- CV = std_dev / mean < 1%
- Relative IQR = IQR / median < 1%
- Only flag as zero-variance if BOTH < 1%

## Complete Variance Check Inventory

### ✅ CORRECT - Using Relative Variance

**1. statistical_analyzer.py: `_check_variance_quality()` (Lines 563-612)**
- **Status**: ✅ Fixed in commit b8d1187
- **Logic**: Relative CV and relative IQR checks
- **Used by**: 
  - MetricDistribution.has_zero_variance (line 873)
  - Effect size calculations (line 1919)

**2. statistical_visualizations.py: Box plot generation (Lines 192-205)**
- **Status**: ✅ Fixed in commit 67f1b3c
- **Logic**: Same relative CV and relative IQR checks
- **Purpose**: Decide whether to render box plot or red line indicator

### ✅ CORRECT - Using Exact Zero Checks

**3. statistical_analyzer.py: Levene's test (Line 1035)**
```python
has_zero_variance = any(len(set(vals)) == 1 for vals in values_list)
```
- **Status**: ✅ Correct (exact zero needed)
- **Reason**: Levene's test mathematically cannot run with identical values

**4. statistical_visualizations.py: Forest plot (Lines 437-439)**
```python
if abs(es.value) == 1.0 and es.ci_lower == es.ci_upper:
```
- **Status**: ✅ Correct (exact equality check)
- **Reason**: Detects complete separation (Cliff's Delta = ±1.0 with no uncertainty)

### ✅ CORRECT - Using Absolute Thresholds (Appropriate Context)

**5. statistical_analyzer.py: Deterministic CI warning (Line 1990)**
```python
if zero_variance_detected and abs(ci_upper - ci_lower) < 0.01:
```
- **Status**: ✅ Correct (absolute check appropriate)
- **Reason**: CI widths are already normalized effect sizes (scale-independent)
- **Note**: Only triggers if zero_variance already detected by relative check

### ✅ CORRECT - Documentation Only

**6. statistical_analyzer.py: Methodology text (Line 2437)**
- **Status**: ✅ Updated in commit 67f1b3c
- **Change**: Documentation now describes relative variance approach
- **Old**: "standard deviation < 0.01 or interquartile range < 0.01"
- **New**: "coefficient of variation < 1% AND relative IQR < 1%"

### ✅ DEPRECATED (Not Used)

**7. config.py: StatisticalConfig.variance_threshold**
- **Status**: ✅ Deprecated (kept for API compatibility)
- **Current value**: 0.01 (not used anywhere)
- **Replaced by**: Relative variance logic in `_check_variance_quality()`

## Precision Formatting (Related Fix)

**experiment_analyzer.py: `_format_metric_value()` (Lines 73-98)**
- **Status**: ✅ Fixed in commit b8d1187
- **Logic**: Adaptive precision based on metric type
  - Cost metrics: 5 decimals
  - Values < 0.01: 5 decimals
  - Normal metrics: 2 decimals
- **Purpose**: Prevent precision loss from hiding variance

## Validation

### Test Case: total_cost_usd (BAES)
- **Raw data**: 0.01049 to 0.01260 (range: 0.00211, ~20% variance)
- **IQR**: 0.00097
- **Std Dev**: 0.00050
- **CV**: 0.00050 / 0.01102 = 4.5%

**Old behavior (absolute thresholds)**:
- ❌ IQR (0.00097) < 0.01 → flagged as zero variance
- ❌ Formatted as 0.01 (all values) → variance hidden
- ❌ Box plot showed red line instead of box

**New behavior (relative thresholds)**:
- ✅ CV (4.5%) > 1% → has variance
- ✅ Formatted with 5 decimals → variance visible (0.01049 to 0.01260)
- ✅ Box plot shows proper distribution

## Pipeline Consistency

All variance checks now use the same logic:
1. Exact zero check: `std == 0 or len(set(values)) == 1`
2. If not exact zero, check relative variance: `CV < 1% AND relative_IQR < 1%`
3. Only flag as deterministic if BOTH relative measures < 1%

This works correctly across all metric scales:
- **tokens_total**: mean ~45,000, std ~1,555 (3.5% CV) ✅ variance detected
- **total_cost_usd**: mean ~0.01, std ~0.0005 (4.5% CV) ✅ variance detected
- **execution_time**: mean ~180s, std ~15s (8% CV) ✅ variance detected

## Commits

1. **b8d1187**: Adaptive precision + relative variance in statistical_analyzer.py
2. **67f1b3c**: Relative variance in box plots + documentation update

## Conclusion

✅ **All variance checks audited and verified correct**
✅ **Consistent relative variance logic throughout pipeline**
✅ **No remaining absolute threshold issues**
✅ **Documentation updated to reflect new approach**
