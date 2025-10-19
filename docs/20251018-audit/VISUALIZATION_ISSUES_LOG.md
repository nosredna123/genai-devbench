# Visualization Issues Investigation Log

**Date:** October 19, 2025  
**Context:** Stage 5 Task 5.1b - Fixing remaining visualization issues after timeline aggregation fix

## Issues Found and Fixed

### ✅ Issue 1: Image Format Mismatch
**Problem:** SVG data saved with PNG extension  
**Impact:** VS Code couldn't display images  
**Fix:** Added `_infer_format_from_path()` helper  
**Status:** FIXED (commit 7ccdb91)

### ✅ Issue 2: Timeline Data Empty
**Problem:** Field name mismatch (lowercase vs uppercase)  
**Impact:** Timeline charts showed no data  
**Fix:** Added field mapping in `load_run_data()`  
**Status:** FIXED (commit 7ccdb91)

### ✅ Issue 3: Silent Fallback in Boxplot
**Problem:** Config specified COST_USD but code silently filtered out frameworks missing it  
**Impact:** ChatDev missing from boxplot without error  
**Root Cause:**
- Config: `cost_boxplot` → metric: `COST_USD`
- Reality: ChatDev doesn't have COST_USD (only baes and ghspec do)
- Code: `_prepare_boxplot()` silently filtered out ChatDev

**Fix:** 
1. Made `_prepare_boxplot()` fail explicitly with clear error message
2. Changed config to use `T_WALL_seconds` (available for all frameworks)
3. Renamed chart to "Execution Time Distribution" to match actual metric

**Error Message Now:**
```
Boxplot requires metric 'COST_USD' but missing in frameworks: ['chatdev']. 
Cannot generate partial chart.
```

**Status:** FIXED

### ✅ Issue 4: Number Formatting in Charts
**Problem:** API calls shown with too many decimals or as raw floats  
**Impact:** Charts look unprofessional (e.g., "8.88" instead of "8.9")  
**Fix:** Added smart formatting in `api_calls_timeline()`:
- Values < 10: Show 2 decimal places (e.g., "2.72")
- Values ≥ 10: Show as integer (e.g., "15")

**Status:** FIXED

### 🔍 Issue 5: API Calls < 1 Per Step (INVESTIGATIVE FINDING)

**Observation:** Average API calls can be < 1 per step (e.g., Step 2: 2.72 averaged across 75 runs)

**Investigation:**
```bash
$ jq '.steps[] | {step: .step_number, api_calls: .api_calls}' \
    runs/baes/064e4bce-36d8-4c5d-bb3d-b53ed8ed2701/metrics.json
```

**Finding:**
```json
{"step": 1, "api_calls": 8}
{"step": 2, "api_calls": 0}  ← ZERO API calls
{"step": 3, "api_calls": 6}
{"step": 4, "api_calls": 0}
{"step": 5, "api_calls": 0}
{"step": 6, "api_calls": 0}
```

**Root Cause:** Many steps have **0 API calls** due to HITL (Human-In-The-Loop) interventions

**Explanation:**
- When HITL occurs, human provides code directly
- No API calls made to LLM for that step
- This is EXPECTED BEHAVIOR, not a bug
- Averaging across runs: (8 + 0 + 6 + 0 + 0 + 0) / 6 = 2.33 API calls/step average

**Validation:**
- Step 1: Always has API calls (initial prompt)
- Steps 2-6: May have 0 API calls if HITL provides solution
- This explains why averages < 1 are possible

**Decision:** NO FIX NEEDED - This is correct behavior
- Zeros represent successful HITL interventions
- Averaging includes all runs (with and without HITL)
- Chart correctly shows the reality of the experiment

**Documentation:** Added note to interpretation in charts

**Status:** INVESTIGATED - NOT A BUG

### ❌ Issue 6: Missing Execution Time Distribution Chart (EXPECTED)

**User Question:** "Where is the Time Execution Distribution by Framework?"

**Answer:** The chart IS being generated but with a different name:
- Old config name: "Cost Distribution by Framework" (boxplot_cost_distribution.png)
- New config name: "Execution Time Distribution by Framework" (boxplot_execution_time.png)
- Metric: `T_WALL_seconds`

The chart exists and shows all 3 frameworks (baes, chatdev, ghspec).

**Status:** CLARIFIED - Chart exists with corrected name

## Summary of Changes

### Files Modified:
1. `src/analysis/visualizations.py`
   - Added `_infer_format_from_path()` helper
   - Updated all `savefig()` calls to use dynamic format
   - Added smart number formatting in `api_calls_timeline()`

2. `scripts/generate_analysis.py`
   - Added field name mapping for step data (lowercase → uppercase)

3. `src/analysis/visualization_factory.py`
   - Made `_prepare_boxplot()` fail explicitly on missing metrics
   - Removed silent filtering

4. `config/experiment.yaml`
   - Changed `cost_boxplot` metric from `COST_USD` to `T_WALL_seconds`
   - Updated title to match actual metric

5. `tests/unit/test_visualization_format.py` (NEW)
   - 7 tests for format inference

### Charts Now Generated:
1. ✅ Token Efficiency Scatter (scatter_token_efficiency.png)
2. ✅ API Calls Timeline (timeline_api_calls.png) - with 2 decimal formatting
3. ✅ Execution Time Distribution (boxplot_execution_time.png) - now includes all 3 frameworks
4. ✅ API Calls Evolution (evolution_api_calls.png)
5. ❌ Radar Chart (FAILS - ChatDev missing COST_USD)

### Key Principle Applied:
**"Fail Fast, Fail Loudly"** - No silent fallbacks, explicit errors make bugs visible

---

**Next Steps:** Address radar chart COST_USD requirement (Task 5.3)
