# Visualization and Report Restructuring Plan

## Current Issues

### Unreliable/Unmeasured Metrics in Visualizations
1. **Radar Chart** - Currently includes:
   - ❌ AUTR (partially measured - BAEs unreliable)
   - ❌ CRUDe (not measured - always 0)
   - ❌ ESR (not measured - always 0)
   - ❌ MC (not measured - always 0)

2. **Pareto Plot** - Uses Q* (not measured - always 0)

3. **Timeline Chart** - Uses CRUDe (not measured - always 0)

## Proposed Changes

### A. Visualizations - Focus on Reliable Metrics Only

#### 1. Updated Radar Chart
**Reliable Metrics to Include:**
- ✅ TOK_IN (Input Tokens)
- ✅ TOK_OUT (Output Tokens)  
- ✅ T_WALL_seconds (Execution Time)
- ✅ API_CALLS (API Call Count)
- ✅ CACHED_TOKENS (Cache Usage)
- ✅ ZDI (Downtime Intervals)

**Note:** 6 metrics - good for radar chart symmetry

#### 2. Remove Pareto Plot
- Depends on Q* (unmeasured)
- Not meaningful with current data

#### 3. Remove Timeline Chart  
- Depends on CRUDe (unmeasured)
- Not meaningful with current data

#### 4. Add New Plots

**Token Efficiency Chart:**
- Scatter: TOK_IN vs TOK_OUT
- Shows input/output relationship
- Color by framework

**API Efficiency Chart:**
- Bar chart: API_CALLS by framework
- Shows call patterns
- Annotate with average tokens per call

**Cache Efficiency Chart:**
- Stacked bar: CACHED_TOKENS vs TOK_IN
- Shows cache hit rates
- Compare frameworks

**Time Efficiency Chart:**
- Box plot: T_WALL distribution by framework
- Shows variability and outliers

### B. Report Structure Changes

#### Current Structure:
1. Foundational Concepts
2. Experimental Methodology
3. Metric Definitions
4. Statistical Methods
5. Executive Summary
6. Aggregate Statistics
7. Relative Performance
8. Kruskal-Wallis Tests
9. Pairwise Comparisons
10. Outlier Detection
11. Composite Scores (Q*, AEI)
12. Visual Summary
13. Recommendations

#### Proposed New Structure:
1. Foundational Concepts
2. Experimental Methodology  
3. Metric Definitions (with clear reliability markers)
4. Statistical Methods
5. Executive Summary
6. **RELIABLE METRICS ANALYSIS** ← New clear section
   - Aggregate Statistics (TOK_IN, TOK_OUT, T_WALL, API_CALLS, etc.)
   - Relative Performance (reliable metrics only)
   - Statistical Tests (reliable metrics only)
   - Visualizations (reliable metrics only)
7. **LIMITATIONS AND FUTURE WORK** ← New consolidated section
   - Unreliable Metrics (AUTR, AEI for BAEs)
   - Unmeasured Metrics (Q*, ESR, CRUDe, MC)
   - Implementation Roadmap
   - Resource Requirements
8. Recommendations (based on reliable metrics only)

### C. New "Limitations and Future Work" Section Content

#### Structure:

```markdown
## ⚠️ Limitations and Future Work

### Metrics Not Included in Current Analysis

This section documents metrics that are **not reliably measured** or **not measured at all** 
in the current experiment. These are candidates for future implementation.

#### 🔴 Category 1: Unmeasured Quality Metrics

**Metrics:** Q*, ESR, CRUDe, MC

**Status:** Always zero (applications not executed)

**Why Not Measured:**
- Requires running generated applications as servers
- Needs HTTP endpoint testing
- Validation logic not implemented

**Implementation Requirements:**
- Effort: 20-40 hours
- Dependencies: Server management, HTTP testing framework
- Steps:
  1. Implement server startup logic
  2. Create endpoint validation suite
  3. Measure CRUD operation success rates
  4. Calculate emerging state transitions
  5. Track model call efficiency

#### 🟡 Category 2: Partially Measured Autonomy Metrics

**Metrics:** AUTR, AEI (for BAEs), HIT, HEU

**Status:** Measured for ChatDev & GHSpec; hardcoded for BAEs

**Why Not Reliable for BAEs:**
- No HITL detection mechanism implemented
- Values are assumptions, not measurements
- Cannot verify if interventions occur

**Implementation Requirements:**
- Effort: 15-20 hours
- Dependencies: Log parsing, pattern matching
- Steps:
  1. Implement BAEs-specific HITL detection
  2. Add pattern matching for clarification requests
  3. Update adapter to use detected values
  4. Validate against intentionally ambiguous tasks
  5. Document false positive/negative rates

#### 🔵 Category 3: Composite Metrics

**Metrics:** Q*, AEI

**Status:** Q* depends on unmeasured metrics; AEI unreliable for BAEs

**Dependencies:**
- Q* requires: ESR, CRUDe, MC (all unmeasured)
- AEI requires: AUTR (unreliable for BAEs)

**Implementation:** Blocked until dependencies resolved

### Recommended Priority Order

1. **High Priority:** BAEs HITL detection (enables AUTR/AEI comparison)
2. **Medium Priority:** Quality metrics (enables Q* calculation)
3. **Low Priority:** Composite score validation (after above complete)

### Expected Benefits

Once implemented, will enable:
- ✅ Full autonomy comparison across all frameworks
- ✅ Quality vs efficiency trade-off analysis
- ✅ Comprehensive Pareto frontier identification
- ✅ Complete framework ranking methodology
```

### D. Code Changes Required

#### File: `src/analysis/visualizations.py`
- Update `radar_chart()` default metrics
- Remove or deprecate `pareto_plot()`
- Remove or deprecate `timeline_chart()`
- Add `token_efficiency_chart()`
- Add `api_efficiency_chart()`
- Add `cache_efficiency_chart()`
- Add `time_distribution_chart()`

#### File: `src/analysis/statistics.py`
- Update Visual Summary section
- Add "Limitations and Future Work" section
- Move unreliable metric discussion out of main analysis
- Update recommendations to focus on reliable metrics

#### File: `runners/analyze_results.sh`
- Update to skip deprecated visualizations
- Add new visualization calls

## Benefits of This Approach

### Scientific Rigor
✅ Clear separation of reliable vs unreliable data
✅ No misleading visualizations
✅ Transparent about limitations

### Reader Experience
✅ Focus on actionable insights first
✅ Clear roadmap for future improvements
✅ No confusion about metric reliability

### Reproducibility
✅ Other researchers know exactly what's measured
✅ Clear requirements for replication
✅ Honest about current capabilities

## Next Steps

1. Implement new visualization functions
2. Update report generation logic
3. Reorganize report sections
4. Test with current data
5. Regenerate all outputs
6. Verify no misleading content remains
