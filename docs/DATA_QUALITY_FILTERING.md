# Data Quality Filtering: Reconciliation-Based Run Selection

**Status:** ✅ Implemented  
**Date:** October 17, 2025  
**Priority:** Critical for Data Integrity

---

## Overview

The analysis pipeline now **filters runs based on Usage API reconciliation status**, ensuring only data-quality-verified runs are included in statistical analysis and visualizations.

## Problem Statement

### Before Filtering

Previously, the analysis included **all runs** from the manifest regardless of their data quality status:
- Runs with pending reconciliation
- Runs too recent (< 30 min, data still propagating)
- Runs without reconciliation verification

This could lead to:
- ❌ Inaccurate token counts (OpenAI Usage API data not yet stable)
- ❌ Statistical analysis on incomplete/unstable data
- ❌ Misleading comparisons between frameworks
- ❌ Reproducibility issues (results change as data stabilizes)

### After Filtering

Analysis now includes **only verified runs**:
- ✅ Data confirmed stable across multiple checks
- ✅ Token counts accurate and final
- ✅ Statistical analysis on high-quality data only
- ✅ Reproducible results (verified data doesn't change)

---

## Implementation

### Reconciliation Status Field

Each run's `metrics.json` contains:

```json
{
  "usage_api_reconciliation": {
    "verification_status": "verified",  // or "pending" or "none"
    "attempts": [
      {
        "timestamp": "2025-10-17T17:47:31.944029+00:00",
        "steps": [...]
      }
    ]
  }
}
```

### Status Values

| Status | Meaning | Include in Analysis? |
|--------|---------|---------------------|
| `"verified"` | ✅ Data stable across multiple checks (44+ min apart) | **YES** |
| `"pending"` | ⏳ Reconciliation in progress, waiting for verification | **NO** |
| `"none"` | 🕐 Too recent (< 30 min), no reconciliation attempted yet | **NO** |

### Filtering Logic

**Location:** `runners/analyze_results.sh`, lines ~165-177

```python
# ✅ FILTER: Only include runs with verified reconciliation status
reconciliation = metrics.get('usage_api_reconciliation', {})
verification_status = reconciliation.get('verification_status', 'none')

if verification_status != 'verified':
    logger.warning(
        "Skipping run %s: reconciliation status '%s' (not verified)",
        run_id, verification_status
    )
    continue
```

### Logging Output

The analysis script now shows filtering results:

```
{"level": "WARNING", "message": "Skipping run d47522e4...: reconciliation status 'pending' (not verified)"}
{"level": "WARNING", "message": "Skipping run fba14d2d...: reconciliation status 'none' (not verified)"}
{"level": "INFO", "message": "✅ Loaded 61 VERIFIED runs (reconciliation complete)"}
{"level": "INFO", "message": "Breakdown by framework:"}
{"level": "INFO", "message": "  baes: 23 verified runs"}
{"level": "INFO", "message": "  chatdev: 20 verified runs"}
{"level": "INFO", "message": "  ghspec: 18 verified runs"}
```

---

## Current Statistics (October 17, 2025, 18:53 UTC)

### Total Runs in Manifest: 65

**Breakdown by Status:**
- ✅ **Verified:** 61 runs (93.8%)
  - baes: 23 runs
  - chatdev: 20 runs
  - ghspec: 18 runs
- ⏳ **Pending:** 1 run (1.5%)
- 🕐 **None (too recent):** 3 runs (4.6%)

**Analysis Includes:** 61 verified runs (93.8% of total)

---

## Impact on Analysis

### Data Quality Improvements

1. **Token Accuracy:** ✅
   - Only includes runs with stable OpenAI Usage API data
   - Token counts verified across multiple checks (44+ min interval)
   - No discrepancies or data propagation delays

2. **Statistical Validity:** ✅
   - All statistical tests based on verified data
   - Bootstrap confidence intervals reliable
   - Pairwise comparisons accurate

3. **Reproducibility:** ✅
   - Results consistent across analysis runs
   - Verified data doesn't change over time
   - Clear documentation of which runs included

4. **Visualization Accuracy:** ✅
   - All charts based on quality-verified data
   - No misleading metrics from unstable data
   - Token efficiency comparisons valid

### Transparency

**Report Header (to be added in Phase 2):**
```markdown
## Data Quality Statement

This analysis includes **61 runs with verified reconciliation status** 
(93.8% of 65 total runs in manifest):
- baes: 23 verified runs
- chatdev: 20 verified runs  
- ghspec: 18 verified runs

**Excluded runs:**
- 1 run with pending reconciliation (verification in progress)
- 3 runs too recent (< 30 min old, data still propagating)

All token counts confirmed stable via OpenAI Usage API double-check mechanism.
```

---

## Reconciliation Process

For context, the reconciliation system:

1. **Initial Data Collection** (during run)
   - Counts tokens/calls as framework executes
   - Stores preliminary counts in metrics.json

2. **First Reconciliation** (~30 min after run)
   - Queries OpenAI Usage API
   - Compares with preliminary counts
   - Stores first verification

3. **Double-Check** (~44-300 min later)
   - Queries Usage API again
   - Compares with first verification
   - If stable → mark as "verified"
   - If different → continue checking

4. **Verified Status**
   - Data confirmed stable
   - No further changes expected
   - Safe for analysis

See `docs/reconcile_usage_quick_reference.md` for details.

---

## Benefits

### For Research Quality

1. **Eliminates "Moving Target" Problem**
   - Results don't change as data propagates
   - Statistical tests remain valid
   - Comparisons are fair and accurate

2. **Increases Confidence**
   - Every metric backed by verified data
   - No guesswork about data stability
   - Clear audit trail

3. **Publication-Ready**
   - Can claim "all data verified"
   - Methodology section clear
   - Reproducibility documented

### For Development

1. **Clear Debugging**
   - If analysis fails, know data is good
   - Issues in code, not data quality
   - Fast iteration

2. **Safe Experimentation**
   - Can re-run analysis confidently
   - Results stable and consistent
   - No surprises from data changes

---

## Future Enhancements

### Planned (Phase 2)

1. **Report Section:** Add "Data Quality Statement" to report
2. **Metadata Table:** Show run count breakdown by status
3. **Quality Metrics:** Include reconciliation statistics

### Potential

1. **Reconciliation Threshold:** Make verification criteria configurable
2. **Partial Analysis:** Option to include "pending" with warning
3. **Historical Tracking:** Track verification status over time
4. **Quality Dashboard:** Visual summary of data quality metrics

---

## Validation

### Test Results

**Before Filtering:** 65 runs loaded  
**After Filtering:** 61 runs loaded ✅

**Runs Excluded:**
- `d47522e4-7f0f-4c71-bf27-80151e18b2bb` (baes, status: pending)
- `fba14d2d-9ff6-4ec8-a9a4-4fd517e944ca` (chatdev, status: none)
- `d325f6af-05f6-48dc-97d7-42a51a2ec9a7` (ghspec, status: none)
- `5b3890c7-5504-484e-a3fe-70b20139a74d` (baes, status: none)

All visualizations generated successfully with verified data only.

---

## Conclusion

✅ **Data quality filtering is now active and working correctly.**

The analysis pipeline ensures scientific rigor by:
1. Including only verified, stable data
2. Documenting filtering criteria clearly
3. Providing transparency about excluded runs
4. Maintaining reproducibility across analysis runs

This is a **critical improvement** for publication-quality research and aligns with the honest, transparent approach established in the HITL metrics documentation.

---

## References

- `runners/analyze_results.sh` - Filtering implementation
- `docs/reconcile_usage_quick_reference.md` - Reconciliation system
- `docs/usage_reconciliation_guide.md` - Usage API reconciliation details
- `docs/RELIABLE_METRICS_IMPLEMENTATION_PLAN.md` - Overall quality improvement plan
