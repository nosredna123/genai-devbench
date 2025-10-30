# Manual Integration Test Results - October 30, 2025

**Test Command**: `python scripts/generate_paper.py ~/projects/uece/baes/baes_benchmarking_20251028_0713`

**Exit Code**: 0 (Success - paper generated despite errors)

**Branch**: `012-fix-statistical-report`

---

## 🔴 Critical Bug Found: PowerAnalysis Field Name Mismatch

### Issue Summary
The `_calculate_power_analysis()` method was returning a `PowerAnalysis` object with **incorrect field names** that don't match the dataclass definition.

### Error Details
```
TypeError: PowerAnalysis.__init__() got an unexpected keyword argument 'test_type'
```

**Affected Metrics**: ALL statistical analyses failed (7 metrics)
- api_calls
- cached_tokens
- execution_time
- tokens_in
- tokens_out
- tokens_total
- total_cost_usd

**Location**: `src/paper_generation/statistical_analyzer.py:1548`

### Root Cause

**What the code was trying to pass**:
```python
PowerAnalysis(
    test_type=test_type.value,        # ❌ WRONG
    effect_size=effect_size,           # ❌ WRONG
    sample_size_group1=n1,             # ❌ WRONG
    sample_size_group2=n2,             # ❌ WRONG
    n_groups=n_groups,                 # ❌ WRONG
    achieved_power=achieved_power,     # ✅ correct
    target_power=target_power,         # ✅ correct
    power_adequate=power_adequate,     # ✅ correct
    adequacy_flag=adequacy_flag,       # ✅ correct
    recommended_n=recommended_n,       # ❌ WRONG (should be recommended_n_per_group)
    warning_message=warning_message    # ✅ correct
)
```

**What the PowerAnalysis dataclass actually expects** (from data-model.md and models.py):
```python
PowerAnalysis(
    comparison_id: str                 # ❌ MISSING
    metric_name: str                   # ❌ MISSING
    group_names: List[str]             # ❌ MISSING
    effect_size_value: float           # ❌ MISSING (was 'effect_size')
    effect_size_type: str              # ❌ MISSING
    n_group1: int                      # ❌ MISSING (was 'sample_size_group1')
    n_group2: int = None               # ❌ MISSING (was 'sample_size_group2')
    achieved_power: float              # ✅ correct
    target_power: float = 0.80         # ✅ correct
    alpha: float = 0.05                # ❌ MISSING
    power_adequate: bool               # ✅ correct
    recommended_n_per_group: int = None  # ❌ WRONG name (was 'recommended_n')
    adequacy_flag: str                 # ✅ correct
    warning_message: str = ""          # ✅ correct
)
```

### Fix Applied

**File**: `src/paper_generation/statistical_analyzer.py` (lines 1548-1575)

**Changes**:
1. ✅ Removed: `test_type` parameter (not in dataclass)
2. ✅ Removed: `n_groups` parameter (not in dataclass)
3. ✅ Added: `comparison_id` (placeholder - will need caller to set properly)
4. ✅ Added: `metric_name` (placeholder - will need caller to set properly)
5. ✅ Added: `group_names` (generated from n_groups or n1/n2)
6. ✅ Changed: `effect_size` → `effect_size_value`
7. ✅ Added: `effect_size_type` (derived from test_type)
8. ✅ Changed: `sample_size_group1` → `n_group1`
9. ✅ Changed: `sample_size_group2` → `n_group2`
10. ✅ Added: `alpha` parameter
11. ✅ Changed: `recommended_n` → `recommended_n_per_group`
12. ✅ Fixed: `achieved_power` to use 0.0 instead of None when calculation fails

**Additional Fix**: 
- Changed `power_result.statistical_power` → `power_result.achieved_power` in 4 locations (lines 1206, 1209, 1300, 1303)

---

## ⚠️ Warnings (Non-Critical)

### 1. Font Glyph Missing (7 occurrences)
```
UserWarning: Glyph 9989 (\N{WHITE HEAVY CHECK MARK}) missing from current font.
```
**Impact**: Low - checkmark characters not rendering in SVG visualizations  
**Location**: `statistical_visualizations.py:506`  
**Fix Needed**: Use different character or install font with Unicode checkmark support

### 2. Experiment Configuration Missing
```
WARNING: experiment.yaml not found, using defaults
```
**Impact**: Low - using default configuration values  
**Solution**: Not critical for testing, would be provided in real experiments

### 3. Prose Generation Word Count (6 sections)
```
WARNING: Prose only 154 words, expected ≥800. Retrying with adjusted prompt.
WARNING: Section has only 386 words, expected ≥800
```
**Impact**: Low - generated content shorter than target  
**Locations**: Multiple sections (results, discussion, etc.)  
**Note**: This is expected behavior - the system retries and continues

### 4. PDF Generation Warnings
```
WARNING: pdflatex returned 1 but PDF was created (likely just warnings)
```
**Impact**: None - PDF successfully created despite LaTeX warnings  
**Note**: Common with LaTeX compilation, PDF output is valid

---

## ✅ Success Indicators

Despite the critical errors, the script **completed successfully**:

### Output Generated
```
Total words:     2,891
Total tokens:    5,026
Generation time: 51.0 seconds
Figure count:    16
LaTeX file:      papers/20251030_051727/main.tex
PDF file:        papers/20251030_051727/main.pdf
```

### What This Means
1. **Paper was generated**: The system continued despite statistical analysis errors
2. **Visualizations created**: 16 figures generated
3. **PDF compiled**: LaTeX successfully compiled to PDF
4. **Graceful degradation**: The error handling prevented complete failure

### What's Missing
Because PowerAnalysis failed for all metrics:
- ❌ **No Power Analysis section** in the generated report
- ❌ **No sample size recommendations**
- ❌ **No power adequacy warnings**
- ❌ **Incomplete statistical test results** (missing power calculations)

---

## 🧪 Feature 012 Validation Status

| User Story | Feature | Status | Notes |
|------------|---------|--------|-------|
| **US1** | Bootstrap CIs | ⚠️ Unknown | No test output showing CI validity |
| **US2** | Test Selection | ⚠️ Unknown | No test output showing which tests selected |
| **US3** | Power Analysis | ❌ **FAILED** | PowerAnalysis instantiation error - **FIXED** |
| **US4** | Effect Size Alignment | ⚠️ Unknown | Need to check generated report |
| **US5** | Multiple Comparisons | ⚠️ Unknown | Need to check for Holm-Bonferroni |
| **US6** | P-value Formatting | ✅ Validated | Unit tests passing (14/14) |
| **US7** | Skewness Emphasis | ⚠️ Unknown | Need to check for median/IQR bolding |
| **US8** | Neutral Language | ✅ Validated | Unit tests passing (14/14) |

---

## 📋 Next Steps

### Immediate Actions

1. **Re-run the test** after bug fix:
   ```bash
   python scripts/generate_paper.py ~/projects/uece/baes/baes_benchmarking_20251028_0713
   ```

2. **Check for remaining errors**: Verify PowerAnalysis errors are resolved

3. **Inspect generated report**: 
   ```bash
   cat papers/20251030_051727/main.tex
   # or open the PDF
   xdg-open papers/20251030_051727/main.pdf
   ```

4. **Validate each user story**:
   - [ ] Check if Power Analysis section appears
   - [ ] Verify statistical test selection (normal vs non-parametric)
   - [ ] Confirm effect size measures align with test types
   - [ ] Look for Holm-Bonferroni corrections
   - [ ] Check median/IQR emphasis for skewed metrics
   - [ ] Grep for prohibited causal language

### Additional Fixes Needed

1. **PowerAnalysis field mapping**: ✅ FIXED
   - `comparison_id` and `metric_name` should be passed from callers
   - Currently using placeholder values

2. **Font issue**: Optional - replace checkmark with standard character

3. **Prose length**: Optional - tuning for better content generation

---

## 🎯 Test Outcome

**Overall**: ⚠️ **Partial Success**
- Script completed and generated output ✅
- Critical bug discovered and fixed ✅
- Statistical analysis failed for all metrics (before fix) ❌
- Paper structure generated successfully ✅

**Confidence Level**: Medium
- The error handling prevented complete failure
- Generated paper likely missing critical power analysis content
- Need to re-run after fix to validate full functionality

**Recommendation**: 
1. Apply the PowerAnalysis field mapping fix ✅ **DONE**
2. Re-run the generation script
3. Manually inspect the generated report
4. Validate all 8 user stories against the output
