# Stage 5: Metrics & Visualization Validation

**Date:** October 19, 2025  
**Status:** 🔄 IN PROGRESS  
**Current Task:** 5.2 - Investigate ZDI metric capture

## Overview

Stage 5 focuses on investigating and fixing identified issues in metrics calculation and chart generation. This is **not** about implementing unmeasured quality metrics (Q*, CRUDe, ESR, MC) - those are intentionally zero because servers aren't started during experiments (expected behavior).

## Tasks

### ✅ Task 5.1: Audit API Calls Timeline aggregation (COMPLETE)

**Status:** ✅ COMPLETE  
**Investigation Date:** 2025-10-19  
**Implementation Date:** 2025-10-19  
**Testing Date:** 2025-10-19  

**Bug Identified:**
- Timeline data was being **overwritten** instead of **aggregated** across multiple runs
- Code in `scripts/generate_analysis.py` lines 116-119:
  ```python
  # BUGGY CODE:
  timeline_data[framework_name][step_num][metric] = step[metric]  # ❌ OVERWRITES!
  ```
- Impact: Timeline charts showed only the LAST run's data, no averaging

**Fix Implemented:**

1. **Changed data structure** (line 40):
   ```python
   # FROM: {fw: {step: {metric: value}}}
   # TO:   {fw: {step: {metric: [val1, val2, ...]}}}
   timeline_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
   ```

2. **Updated data collection** (lines 116-119):
   ```python
   # FROM: timeline_data[fw][step][metric] = value
   # TO:   timeline_data[fw][step][metric].append(value)
   ```

3. **Added aggregation function** (`aggregate_timeline_data()`, lines 142-181):
   - Supports three aggregation methods: mean, median, last
   - Config-driven: uses `aggregation` field from `experiment.yaml`
   - Default: mean

4. **Applied aggregation** in `main()` (lines 260-269):
   ```python
   aggregation_method = config.get('aggregation', 'mean')
   aggregated_timeline_data = aggregate_timeline_data(timeline_data, aggregation_method)
   factory.generate_all(..., timeline_data=aggregated_timeline_data)
   ```

**Testing:**
- ✅ 12 comprehensive unit tests in `tests/unit/test_timeline_aggregation.py`
- ✅ All tests passing
- ✅ Integration test with real data (192 verified runs)
- ✅ Timeline charts generated successfully

**Files Modified:**
- `scripts/generate_analysis.py` (~45 lines of changes)
- `tests/unit/test_timeline_aggregation.py` (new file, ~200 lines)
- `docs/20251018-audit/STAGE_5_PROGRESS.md` (this file)

**Result:** Timeline data now properly aggregates across all runs using configured method (mean by default).

---

### ⏳ Task 5.2: Investigate ZDI metric capture (NOT STARTED)

Trace ZDI calculation from adapters through metrics collector.

### ⏳ Task 5.3: Debug Radar Chart - BAEs zero values (NOT STARTED)

Check why BAEs shows zeros on radar chart.

### ⏳ Task 5.4: Improve Radar Chart scaling (NOT STARTED)

Add config option for scale type (normalized vs percentage).

### ⏳ Task 5.5: Analyze Token Efficiency Scatter anomalies (NOT STARTED)

Understand scatter plot anomalies (all points above diagonal, zero values).

### ⏳ Task 5.6: Fix API Calls Evolution - ghspec step 6 zeros (NOT STARTED)

Check if ghspec step 6 data is missing.

### ⏳ Task 5.7: Document all findings and resolutions (NOT STARTED)

Create comprehensive validation log.

## Progress Tracking

- [x] Stage 5 started
- [x] Task 5.1: Investigation complete, bug identified
- [x] Task 5.1: Implement fix
- [x] Task 5.1: Add tests
- [x] Task 5.1: Documentation
- [x] **Task 5.1 COMPLETE** ✅
- [ ] Task 5.2-5.6: Remaining investigations
- [ ] Task 5.7: Final documentation
- [ ] Stage 5 complete

## Files to Modify

### Task 5.1 ✅
- ✅ `scripts/generate_analysis.py` - Fixed timeline data collection
- ✅ `tests/unit/test_timeline_aggregation.py` - Added aggregation tests
- ✅ `docs/20251018-audit/STAGE_5_PROGRESS.md` - Updated documentation

---

**Last Updated:** October 19, 2025  
**Next Action:** Task 5.2 - Investigate ZDI metric capture
