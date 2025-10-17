# Implementation Plan: Focus on Reliable Metrics

**Status:** 📋 Planning Phase  
**Priority:** High  
**Estimated Effort:** 20-30 hours  
**Target Completion:** TBD  
**Last Updated:** October 17, 2025

---

## Executive Summary

This document outlines a comprehensive plan to restructure the BAEs experiment analysis to focus **exclusively on reliably measured metrics** in the main analysis sections, while properly documenting limitations and unmeasured/unreliable metrics in a dedicated "Future Work" section.

### Current Problem

The current analysis mixes:
- ✅ **Reliably measured metrics** (TOK_IN, TOK_OUT, T_WALL, API_CALLS, CACHED_TOKENS)
- ⚠️ **Partially measured metrics** (AUTR, AEI for BAEs - no HITL detection)
- ❌ **Unmeasured metrics** (Q\*, ESR, CRUDe, MC - applications not executed)

This creates confusion and reduces scientific credibility.

### Proposed Solution

**Strict Separation:**
1. **Main Analysis** → Only reliably measured metrics
2. **Limitations & Future Work Section** → All unreliable/unmeasured metrics
3. **Updated Visualizations** → Remove charts using unreliable data
4. **New Visualizations** → Focus on reliable metric comparisons

---

## Table of Contents

1. [Metric Classification](#1-metric-classification)
2. [Visualization Changes](#2-visualization-changes)
3. [Report Structure Reorganization](#3-report-structure-reorganization)
4. [Code Changes Required](#4-code-changes-required)
5. [Testing Strategy](#5-testing-strategy)
6. [Implementation Timeline](#6-implementation-timeline)
7. [Success Criteria](#7-success-criteria)
8. [Future Work Roadmap](#8-future-work-roadmap)

---

## 1. Metric Classification

### 1.1 Reliably Measured Metrics ✅

**Category: Token Consumption**
- `TOK_IN` - Input tokens (OpenAI Usage API)
- `TOK_OUT` - Output tokens (OpenAI Usage API)
- `CACHED_TOKENS` - Cached input tokens (OpenAI Usage API)

**Category: Time & Performance**
- `T_WALL_seconds` - Wall-clock execution time
- `ZDI` - Zero-downtime intervals between steps

**Category: API Efficiency**
- `API_CALLS` - Number of LLM API requests

**Category: Fixed Values**
- `UTT` - User task total (always 6)

**Why Reliable:**
- Measured via authoritative source (OpenAI Usage API for tokens)
- Direct timing measurements (Python `time.time()`)
- Count-based metrics with clear definition
- No framework-specific interpretation needed

### 1.2 Partially Measured Metrics ⚠️

**Metrics:** `AUTR`, `AEI`, `HIT`, `HEU`

**Status by Framework:**
| Framework | HITL Detection | Measurement Reliability |
|-----------|----------------|------------------------|
| ChatDev   | ✅ Implemented (5 regex patterns) | ✅ Reliable |
| GHSpec    | ✅ Implemented (explicit markers) | ✅ Reliable |
| BAEs      | ❌ Not Implemented (hardcoded 0) | ❌ Unreliable |

**Why Partially Measured:**
- AUTR depends on HIT (human interventions)
- HIT detection missing for BAEs
- Cannot verify if BAEs truly autonomous or just undetected
- AEI depends on AUTR (inherits reliability issues)

**Current Values (May Be Inaccurate for BAEs):**
- BAEs: AUTR=1.0, HIT=0 (hardcoded assumptions)
- ChatDev: AUTR=1.0, HIT=0 (verified via detection)
- GHSpec: AUTR=1.0, HIT=0 (verified via detection)

### 1.3 Unmeasured Metrics ❌

**Metrics:** `Q*`, `ESR`, `CRUDe`, `MC`

**Status:** Always zero across all frameworks

**Why Not Measured:**
- Generated applications are never executed
- No server startup implemented
- No HTTP endpoint testing
- No CRUD operation validation

**Configuration Setting:** `auto_restart_servers: false`

---

## 2. Visualization Changes

### 2.1 Current Visualizations (To Be Modified/Removed)

#### ❌ **Remove: Pareto Plot** (`pareto_plot.svg`)

**Current:** Plots Q\* vs TOK_IN

**Problem:**
- Q\* always zero (unmeasured)
- Creates misleading scatter plot at origin
- No meaningful information conveyed

**Action:** Remove from report generation

#### ❌ **Remove: Timeline Chart** (`timeline_chart.svg`)

**Current:** Shows CRUDe evolution over steps

**Problem:**
- CRUDe always zero (unmeasured)
- Flat line at zero
- Misleading - suggests no evolution

**Action:** Remove from report generation

#### ⚠️ **Update: Radar Chart** (`radar_chart.svg`)

**Current Metrics:**
- AUTR (partially measured)
- API_CALLS (reliable)
- TOK_IN (reliable)
- T_WALL_seconds (reliable)
- CRUDe (unmeasured - always 0)
- ESR (unmeasured - always 0)
- MC (unmeasured - always 0)

**Problems:**
- 3/7 metrics unmeasured (42% unreliable)
- AUTR unreliable for BAEs
- Misleading framework comparison

**Proposed New Metrics (6 reliable metrics):**
```python
metrics = [
    "TOK_IN",           # Input tokens
    "TOK_OUT",          # Output tokens
    "T_WALL_seconds",   # Execution time
    "API_CALLS",        # API call count
    "CACHED_TOKENS",    # Cache usage
    "ZDI"               # Downtime intervals
]
```

**Benefits:**
- 100% reliable metrics
- Symmetric 6-point radar
- Clear performance comparison
- No caveats needed

### 2.2 New Visualizations to Add

#### ✅ **NEW: Token Efficiency Scatter** (`token_efficiency.svg`)

**Purpose:** Compare input vs output token relationship

**Axes:**
- X-axis: TOK_IN (input tokens)
- Y-axis: TOK_OUT (output tokens)
- Color: Framework
- Size: T_WALL_seconds (execution time)

**Insights:**
- Shows verbosity (output per input)
- Identifies token-efficient frameworks
- Correlates with execution time

**Implementation:**
```python
def token_efficiency_chart(frameworks_data, output_path):
    """Scatter plot: TOK_IN vs TOK_OUT by framework."""
    # Plot TOK_IN (x) vs TOK_OUT (y)
    # Color by framework
    # Marker size proportional to T_WALL_seconds
    # Add trend lines per framework
```

#### ✅ **NEW: API Efficiency Bar Chart** (`api_efficiency.svg`)

**Purpose:** Compare API call efficiency across frameworks

**Components:**
- Bar chart: API_CALLS by framework
- Annotation: Tokens per API call (TOK_IN / API_CALLS)
- Color: By framework
- Error bars: 95% confidence intervals

**Insights:**
- Shows batching efficiency
- Identifies retry patterns
- Highlights framework strategies

**Implementation:**
```python
def api_efficiency_chart(frameworks_data, output_path):
    """Bar chart: API_CALLS with tokens-per-call annotations."""
    # Bar height: API_CALLS
    # Annotation: (TOK_IN / API_CALLS)
    # Error bars from bootstrap CI
```

#### ✅ **NEW: Cache Hit Rate Comparison** (`cache_efficiency.svg`)

**Purpose:** Compare prompt caching effectiveness

**Components:**
- Stacked bar chart per framework
- Bottom segment: Uncached tokens (TOK_IN - CACHED_TOKENS)
- Top segment: CACHED_TOKENS
- Percentage label: Cache hit rate

**Insights:**
- Shows prompt reuse strategies
- Identifies cost-saving opportunities
- Compares framework caching architectures

**Implementation:**
```python
def cache_efficiency_chart(frameworks_data, output_path):
    """Stacked bar: cached vs uncached tokens."""
    # Bottom: TOK_IN - CACHED_TOKENS
    # Top: CACHED_TOKENS
    # Label: (CACHED_TOKENS / TOK_IN) * 100%
```

#### ✅ **NEW: Execution Time Distribution** (`time_distribution.svg`)

**Purpose:** Show execution time variability

**Components:**
- Box plot per framework
- Whiskers: Min/max
- Box: Q1, median, Q3
- Outliers marked separately

**Insights:**
- Shows consistency vs variability
- Identifies outlier runs
- Compares median vs mean

**Implementation:**
```python
def time_distribution_chart(frameworks_data, output_path):
    """Box plot: T_WALL_seconds distribution by framework."""
    # One box per framework
    # Overlay: individual run points
    # Highlight: statistical outliers
```

### 2.3 Visualization Summary Table

| Visualization | Status | Metrics Used | Reliability |
|---------------|--------|--------------|-------------|
| ❌ Pareto Plot | **REMOVE** | Q\*, TOK_IN | Q\* unmeasured |
| ❌ Timeline Chart | **REMOVE** | CRUDe, ZDI | CRUDe unmeasured |
| ⚠️ Radar Chart | **UPDATE** | 6 reliable metrics | 100% reliable |
| ✅ Token Efficiency | **ADD** | TOK_IN, TOK_OUT, T_WALL | 100% reliable |
| ✅ API Efficiency | **ADD** | API_CALLS, TOK_IN | 100% reliable |
| ✅ Cache Efficiency | **ADD** | CACHED_TOKENS, TOK_IN | 100% reliable |
| ✅ Time Distribution | **ADD** | T_WALL_seconds | 100% reliable |

---

## 3. Report Structure Reorganization

### 3.1 Current Structure (Problems Highlighted)

```markdown
1. Foundational Concepts
2. Experimental Methodology
3. Metric Definitions
   ⚠️ Problem: Mixes reliable and unreliable status
4. Statistical Methods Guide
5. Executive Summary
   ⚠️ Problem: Mentions unreliable metrics
6. Aggregate Statistics
   ⚠️ Problem: Includes all metrics (reliable + unreliable)
7. Relative Performance
   ⚠️ Problem: Compares AUTR, AEI (unreliable for BAEs)
8. Kruskal-Wallis H-Tests
   ⚠️ Problem: Tests unreliable metrics
9. Pairwise Comparisons
   ⚠️ Problem: Compares unreliable metrics
10. Outlier Detection
11. Composite Scores
    ⚠️ Problem: Q* always zero, AEI unreliable
12. Visual Summary
    ⚠️ Problem: Shows charts with unreliable metrics
13. Recommendations
    ⚠️ Problem: Based on unreliable metrics
```

### 3.2 Proposed New Structure

```markdown
1. Foundational Concepts
   - No changes needed

2. Experimental Methodology
   - No changes needed

3. Metric Definitions
   ✅ Update: Clear reliability markers (✅/⚠️/❌)
   ✅ Add: Separate tables by reliability category

4. Statistical Methods Guide
   - No changes needed

5. Executive Summary
   ✅ Update: Focus on reliable metrics only
   ✅ Remove: References to AUTR, AEI, Q*

6. ✅ NEW SECTION: Reliable Metrics Analysis
   6.1. Aggregate Statistics (Reliable Metrics Only)
   6.2. Relative Performance (Reliable Metrics Only)
   6.3. Statistical Significance Tests (Reliable Metrics Only)
   6.4. Pairwise Comparisons (Reliable Metrics Only)
   6.5. Outlier Detection (Reliable Metrics Only)
   6.6. Visualizations (Reliable Metrics Only)

7. ✅ NEW SECTION: Limitations and Future Work
   7.1. Overview of Limitations
   7.2. Unmeasured Quality Metrics
       - Q*, ESR, CRUDe, MC
       - Why not measured
       - Implementation requirements
   7.3. Partially Measured Autonomy Metrics
       - AUTR, AEI (for BAEs)
       - Why unreliable for BAEs
       - Implementation requirements
   7.4. Future Work Roadmap
       - Priority ordering
       - Resource estimates
       - Expected benefits
   7.5. Implications for Current Results
       - What we can conclude
       - What we cannot conclude

8. Recommendations
   ✅ Update: Based on reliable metrics only
   ✅ Focus: Token efficiency, speed, API usage
```

### 3.3 Section-Level Changes

#### **Section 3: Metric Definitions** (Enhanced)

**Current:** Single table with all metrics

**Proposed:** Three separate tables

**Table 1: Reliably Measured Metrics ✅**
```markdown
| Metric | Full Name | Description | Range | Ideal | Method |
|--------|-----------|-------------|-------|-------|--------|
| TOK_IN | Input Tokens | Tokens sent to LLM | 0-∞ | Lower ↓ | OpenAI Usage API |
| TOK_OUT | Output Tokens | Tokens from LLM | 0-∞ | Lower ↓ | OpenAI Usage API |
| API_CALLS | API Call Count | LLM requests | 0-∞ | Lower ↓ | Count-based |
| CACHED_TOKENS | Cached Tokens | Tokens from cache | 0-∞ | Higher ↑ | OpenAI Usage API |
| T_WALL | Wall Time | Execution time | 0-∞ | Lower ↓ | time.time() |
| ZDI | Downtime | Idle intervals | 0-∞ | Lower ↓ | Calculated |
| UTT | Task Total | Step count | Fixed | 6 | Configuration |
```

**Table 2: Partially Measured Metrics ⚠️**
```markdown
| Metric | Reliability by Framework | Issue |
|--------|--------------------------|-------|
| AUTR | ChatDev: ✅, GHSpec: ✅, BAEs: ❌ | BAEs: No HITL detection |
| AEI | ChatDev: ✅, GHSpec: ✅, BAEs: ❌ | Depends on AUTR |
| HIT | ChatDev: ✅, GHSpec: ✅, BAEs: ❌ | BAEs: Hardcoded to 0 |
| HEU | ChatDev: ✅, GHSpec: ✅, BAEs: ❌ | Depends on HIT |
```

**Table 3: Unmeasured Metrics ❌**
```markdown
| Metric | Status | Reason |
|--------|--------|--------|
| Q* | Always 0 | Depends on unmeasured metrics |
| ESR | Always 0 | Applications not executed |
| CRUDe | Always 0 | No endpoint validation |
| MC | Always 0 | No runtime efficiency measured |
```

#### **Section 5: Executive Summary** (Focused)

**Remove:**
```markdown
❌ "Most Efficient (AEI): baes (0.095)"
❌ "All frameworks achieved perfect autonomy (AUTR = 1.0)"
❌ References to Q*, ESR, CRUDe, MC
```

**Add:**
```markdown
✅ "Most Token-Efficient: baes (23,910 input tokens)"
✅ "Fastest Execution: baes (178.9 seconds)"
✅ "Best Cache Efficiency: chatdev (13.7% hit rate)"
✅ "Lowest API Calls: baes (14 calls average)"

Key Insight:
"Analysis focuses on reliably measured metrics. See 'Limitations 
and Future Work' section for discussion of unmeasured/unreliable 
metrics (AUTR, Q*, ESR, CRUDe, MC)."
```

#### **Section 6: Reliable Metrics Analysis** (NEW)

**Structure:**
```markdown
## 6. Reliable Metrics Analysis

This section presents statistical analysis of **reliably measured metrics only**.
All metrics in this section have:
- ✅ Consistent measurement across all frameworks
- ✅ Authoritative data sources (OpenAI Usage API, Python timing)
- ✅ No framework-specific interpretation required

### 6.1 Aggregate Statistics

[Table with only: TOK_IN, TOK_OUT, T_WALL, API_CALLS, CACHED_TOKENS, ZDI]

### 6.2 Relative Performance

[Comparison table with reliable metrics only]

### 6.3 Statistical Significance Tests

**Kruskal-Wallis H-Tests (Reliable Metrics)**

[Tests for: TOK_IN, TOK_OUT, T_WALL, API_CALLS, CACHED_TOKENS, ZDI]

### 6.4 Pairwise Comparisons

[Comparisons for reliable metrics only]

### 6.5 Outlier Detection

[Outliers in reliable metrics]

### 6.6 Visualizations

- Updated Radar Chart (6 reliable metrics)
- Token Efficiency Scatter
- API Efficiency Bar Chart
- Cache Hit Rate Comparison
- Execution Time Distribution
```

#### **Section 7: Limitations and Future Work** (NEW)

**Full section content:**

```markdown
## 7. ⚠️ Limitations and Future Work

### 7.1 Overview

This experiment successfully measures **code generation efficiency** (tokens, 
time, API usage) but does NOT measure **code quality** or **autonomy** for all 
frameworks consistently. This section documents what is NOT included in the 
main analysis and provides a roadmap for future implementation.

### 7.2 Unmeasured Quality Metrics

#### Metrics Not Measured

- **Q\*** (Quality Star): Composite quality score
- **ESR** (Emerging State Rate): Evolution success rate
- **CRUDe** (CRUD Coverage): CRUD operations implemented
- **MC** (Model Call Efficiency): Runtime model efficiency

#### Why Not Measured

**Root Cause:** Generated applications are never executed.

**Technical Details:**
- Configuration: `auto_restart_servers: false`
- No server startup logic implemented
- No HTTP endpoint testing framework
- No CRUD operation validation

**Current Behavior:**
- All quality metrics show zero
- Cannot distinguish "no features" from "features not tested"
- Q* calculation meaningless (0.4·0 + 0.3·0 + 0.3·0 = 0)

#### Implementation Requirements

**Effort Estimate:** 20-40 hours

**Components Needed:**
1. **Server Management Module** (8-12 hours)
   - Auto-detect server startup commands
   - Port management (8000-8002)
   - Health check endpoints
   - Graceful shutdown

2. **Endpoint Validation Suite** (6-10 hours)
   - HTTP request framework integration
   - CRUD operation test cases
   - Response validation
   - Error handling

3. **Metric Calculation Logic** (4-8 hours)
   - ESR: Track successful state transitions
   - CRUDe: Count implemented operations (0-12 scale)
   - MC: Measure model call efficiency during runtime
   - Q*: Composite score calculation

4. **Integration & Testing** (2-10 hours)
   - Update adapters
   - Add timeout handling
   - Test with all three frameworks
   - Documentation

**Dependencies:**
- `requests` or `httpx` for HTTP testing
- Port availability checking
- Process management (subprocess, psutil)

**Risk Factors:**
- Framework-specific server startup patterns
- Port conflicts
- Long-running server processes
- Inconsistent API patterns

### 7.3 Partially Measured Autonomy Metrics

#### Metrics Partially Measured

- **AUTR** (Automated User Testing Rate): Autonomy measure
- **AEI** (Automation Efficiency Index): Quality per token
- **HIT** (Human-in-the-Loop): Intervention count
- **HEU** (Human Effort Units): Manual effort

#### Reliability Status

| Framework | HITL Detection | AUTR | AEI | Status |
|-----------|----------------|------|-----|--------|
| ChatDev   | ✅ Implemented | ✅ Reliable | ✅ Reliable | Properly measured |
| GHSpec    | ✅ Implemented | ✅ Reliable | ✅ Reliable | Properly measured |
| BAEs      | ❌ Not Impl.   | ❌ Unreliable | ❌ Unreliable | Hardcoded values |

#### Why Unreliable for BAEs

**Root Cause:** No HITL detection mechanism in BAEs adapter.

**Technical Details:**
- Lines 330 & 348 in `src/adapters/baes_adapter.py`: `hitl_count = 0`
- Hardcoded assumption, not measurement
- Cannot detect if clarification requests occur
- Prevents valid autonomy comparison

**Current Behavior:**
- BAEs always shows AUTR=1.0 (perfect autonomy)
- May be accurate OR may miss interventions
- No way to verify scientifically

**Manual Investigation (October 2025):**
- Reviewed 23 BAEs runs
- Found no clarification patterns in logs
- Suggests autonomy is likely real
- But this is NOT a substitute for proper instrumentation

#### Implementation Requirements

**Effort Estimate:** 15-20 hours

**Components Needed:**
1. **Pattern Detection Module** (6-8 hours)
   - Regex patterns for clarification requests
   - Keywords: "clarification", "ambiguous", "cannot determine"
   - Similar to ChatDev implementation (5 patterns)
   - BAEs-specific patterns for kernel communication

2. **Log Parsing Integration** (4-6 hours)
   - Search kernel output logs
   - Track entity communication failures
   - Count request-response validation errors
   - Timestamp matching for step attribution

3. **Adapter Updates** (3-4 hours)
   - Replace hardcoded `hitl_count = 0`
   - Call detection function
   - Update lines 330 & 348
   - Maintain backward compatibility

4. **Validation & Testing** (2-2 hours)
   - Test with intentionally ambiguous prompts
   - Measure false positive/negative rates
   - Compare with ChatDev/GHSpec detection
   - Document accuracy metrics

**Dependencies:**
- Access to kernel execution logs
- Understanding of BAEs communication patterns
- Test scenarios with known HITL events

**Risk Factors:**
- False positives (design discussions vs. actual clarification needs)
- False negatives (implicit vs. explicit clarification requests)
- BAEs-specific communication patterns differ from ChatDev/GHSpec

### 7.4 Future Work Roadmap

#### Priority 1: BAEs HITL Detection (HIGH)

**Why First:**
- Enables complete autonomy comparison
- Relatively straightforward (pattern matching)
- Unblocks AEI comparison

**Timeline:** 15-20 hours

**Deliverables:**
- HITL detection function in BAEs adapter
- Updated metrics collection
- Validation test suite
- Documentation

**Success Criteria:**
- BAEs HITL detection implemented
- Accuracy validated (>95% detection rate)
- All 3 frameworks use consistent methodology
- AUTR/AEI comparisons become valid

#### Priority 2: Quality Metrics Infrastructure (MEDIUM)

**Why Second:**
- Enables Q* calculation
- Provides code quality insights
- More complex than HITL detection

**Timeline:** 20-40 hours

**Deliverables:**
- Server management module
- Endpoint validation suite
- ESR, CRUDe, MC measurement
- Integration with all frameworks

**Success Criteria:**
- Applications successfully executed
- CRUD operations validated
- Q* values > 0 for functional code
- Quality vs efficiency trade-offs visible

#### Priority 3: Composite Metric Validation (LOW)

**Why Last:**
- Depends on above implementations
- Primarily validation, not new measurement

**Timeline:** 4-8 hours

**Deliverables:**
- Q* calculation verification
- AEI comparison across all frameworks
- Pareto frontier analysis
- Updated visualizations

**Success Criteria:**
- Q* accurately reflects code quality
- AEI enables valid efficiency comparison
- Pareto plot shows meaningful trade-offs

### 7.5 Expected Benefits After Implementation

#### Once BAEs HITL Detection Complete:

**Enabled Analyses:**
- ✅ Complete autonomy comparison (all 3 frameworks)
- ✅ Valid AEI comparison across frameworks
- ✅ Identification of scenarios requiring human intervention
- ✅ Framework autonomy ranking

**New Research Questions:**
- Does architectural difference affect autonomy?
- Are multi-agent frameworks more/less autonomous?
- What task characteristics predict HITL events?

#### Once Quality Metrics Complete:

**Enabled Analyses:**
- ✅ Quality vs efficiency trade-off analysis
- ✅ Pareto frontier identification
- ✅ Complete framework ranking (speed + quality)
- ✅ Cost-benefit analysis (tokens vs quality)

**New Research Questions:**
- Does faster generation sacrifice quality?
- Do more API calls improve code quality?
- What's the optimal efficiency-quality balance?

#### Complete Implementation:

**Full Comparison Matrix:**
```
Metric Type        | Measured | Comparable | Validated |
-------------------|----------|------------|-----------|
Efficiency         |    ✅    |     ✅     |     ✅    |
Autonomy           |    ✅    |     ✅     |     ✅    |
Quality            |    ✅    |     ✅     |     ✅    |
Composite Scores   |    ✅    |     ✅     |     ✅    |
```

**Publication Impact:**
- Comprehensive framework evaluation
- No methodological caveats
- Valid cross-framework comparisons
- Strong scientific contribution

### 7.6 Implications for Current Results

#### What We CAN Conclude ✅

**From Reliable Metrics:**
- BAEs uses 9.6× fewer input tokens than ChatDev
- BAEs executes 9.1× faster than ChatDev
- ChatDev achieves 13.7% cache hit rate vs ~2% others
- API call efficiency varies significantly
- Token consumption highly variable across frameworks

**Scientific Validity:**
- High confidence (authoritative measurement)
- Direct comparisons valid
- Statistical significance confirmed
- Reproducible results

#### What We CANNOT Conclude ❌

**Autonomy Claims:**
- ❌ "BAEs achieves perfect autonomy"
- ❌ "All frameworks equally autonomous"
- ❌ "BAEs most efficient (AEI)" - AEI unreliable

**Quality Claims:**
- ❌ "Generated code is functional"
- ❌ "Frameworks produce equivalent quality"
- ❌ "Q* comparison shows X is better"

**Composite Comparisons:**
- ❌ Cross-framework ranking including quality
- ❌ Pareto frontier analysis
- ❌ Efficiency-quality trade-offs

#### Current Research Contribution

**What This Study Successfully Demonstrates:**

1. **Code Generation Efficiency Varies Dramatically**
   - Order-of-magnitude differences in tokens
   - Substantial speed variations
   - Different API usage strategies

2. **Architectural Differences Have Measurable Impact**
   - Kernel mediation (BAEs) → fewer tokens, faster
   - Multi-agent (ChatDev) → more tokens, better caching
   - Sequential specification (GHSpec) → intermediate performance

3. **Measurement Methodology Matters**
   - Need for consistent instrumentation
   - Importance of authoritative data sources
   - Value of transparent limitation disclosure

**This is valuable research** - focus on reliable findings, honest about limitations.
```

#### **Section 8: Recommendations** (Revised)

**Remove:**
```markdown
❌ "Choose BAEs for efficiency (AEI)"
❌ "All frameworks autonomous (AUTR=1.0)"
❌ References to quality metrics
```

**Replace with:**
```markdown
### Recommendations Based on Reliably Measured Metrics

#### For Cost-Sensitive Projects
**Recommendation:** BAEs
- 9.6× fewer input tokens than ChatDev
- 89% reduction in token costs
- Fastest execution (9.1× faster)

#### For Speed-Critical Applications
**Recommendation:** BAEs
- 178.9s average (vs 1724s ChatDev)
- 90% reduction in wait time
- Consistent performance

#### For Prompt Reuse Scenarios
**Recommendation:** ChatDev
- 13.7% cache hit rate
- Best prompt caching efficiency
- Cost savings on repeated patterns

#### For Balanced Performance
**Recommendation:** GHSpec
- Middle ground on tokens
- Moderate execution time
- Reasonable caching

#### What We Cannot Recommend (Yet)

**Due to Unmeasured Metrics:**
- Cannot recommend based on code quality
- Cannot assess autonomy for BAEs
- Cannot evaluate quality-efficiency trade-offs

**See "Limitations and Future Work" for implementation roadmap.**
```

---

## 4. Code Changes Required

### 4.1 File: `src/analysis/visualizations.py`

#### Changes Summary
- ✅ Update `radar_chart()` - Change default metrics
- ❌ Deprecate `pareto_plot()` - Add warning, skip in main flow
- ❌ Deprecate `timeline_chart()` - Add warning, skip in main flow
- ✅ Add `token_efficiency_chart()` - NEW
- ✅ Add `api_efficiency_chart()` - NEW
- ✅ Add `cache_efficiency_chart()` - NEW
- ✅ Add `time_distribution_chart()` - NEW

#### Detailed Changes

**Function: `radar_chart()`**

```python
# BEFORE (lines 69-70):
if metrics is None:
    metrics = ["AUTR", "API_CALLS", "TOK_IN", "T_WALL_seconds", "CRUDe", "ESR", "MC"]

# AFTER:
if metrics is None:
    # Only reliable metrics (all properly measured across frameworks)
    metrics = ["TOK_IN", "TOK_OUT", "T_WALL_seconds", "API_CALLS", "CACHED_TOKENS", "ZDI"]
```

**Function: `pareto_plot()` - Deprecation**

```python
# Add at beginning of function:
def pareto_plot(...):
    """
    Generate a Pareto plot showing quality (Q*) vs cost (TOK_IN).
    
    ⚠️ DEPRECATED: This visualization uses Q* which is not measured
    in current experiments (always 0). Will be re-enabled once quality
    metrics are implemented. See docs/RELIABLE_METRICS_IMPLEMENTATION_PLAN.md
    
    ...
    """
    import warnings
    warnings.warn(
        "pareto_plot() deprecated: uses unmeasured metric Q*. "
        "Skipping visualization generation.",
        DeprecationWarning
    )
    return  # Early exit
```

**Function: `timeline_chart()` - Deprecation**

```python
# Add at beginning:
def timeline_chart(...):
    """
    Generate a timeline chart showing CRUD coverage and downtime over steps.
    
    ⚠️ DEPRECATED: This visualization uses CRUDe which is not measured
    in current experiments (always 0). Will be re-enabled once quality
    metrics are implemented. See docs/RELIABLE_METRICS_IMPLEMENTATION_PLAN.md
    
    ...
    """
    import warnings
    warnings.warn(
        "timeline_chart() deprecated: uses unmeasured metric CRUDe. "
        "Skipping visualization generation.",
        DeprecationWarning
    )
    return  # Early exit
```

**NEW Function: `token_efficiency_chart()`**

```python
def token_efficiency_chart(
    frameworks_data: Dict[str, List[Dict[str, float]]],
    output_path: str,
    title: str = "Token Efficiency: Input vs Output"
) -> None:
    """
    Generate scatter plot showing input vs output token relationship.
    
    Shows how frameworks trade off input context vs output generation.
    Marker size represents execution time.
    
    Args:
        frameworks_data: Dict mapping framework names to lists of run metrics
        output_path: Path to save SVG
        title: Chart title
    """
    # Implementation:
    # 1. Extract TOK_IN, TOK_OUT, T_WALL for each framework
    # 2. Create scatter plot (x=TOK_IN, y=TOK_OUT)
    # 3. Color by framework
    # 4. Marker size proportional to T_WALL_seconds
    # 5. Add framework labels and legend
    # 6. Annotate with verbosity ratio (TOK_OUT/TOK_IN)
```

**NEW Function: `api_efficiency_chart()`**

```python
def api_efficiency_chart(
    frameworks_data: Dict[str, Dict[str, float]],
    output_path: str,
    title: str = "API Call Efficiency by Framework"
) -> None:
    """
    Generate bar chart comparing API call efficiency.
    
    Shows API_CALLS count with annotations for tokens-per-call ratio.
    
    Args:
        frameworks_data: Dict mapping framework names to aggregated metrics
        output_path: Path to save SVG
        title: Chart title
    """
    # Implementation:
    # 1. Bar chart: API_CALLS by framework
    # 2. Calculate tokens-per-call: TOK_IN / API_CALLS
    # 3. Annotate bars with ratio
    # 4. Color by framework
    # 5. Add error bars (confidence intervals)
```

**NEW Function: `cache_efficiency_chart()`**

```python
def cache_efficiency_chart(
    frameworks_data: Dict[str, Dict[str, float]],
    output_path: str,
    title: str = "Cache Hit Rate Comparison"
) -> None:
    """
    Generate stacked bar chart showing cache efficiency.
    
    Shows proportion of cached vs uncached tokens.
    
    Args:
        frameworks_data: Dict mapping framework names to aggregated metrics
        output_path: Path to save SVG
        title: Chart title
    """
    # Implementation:
    # 1. Stacked bar per framework
    # 2. Bottom segment: TOK_IN - CACHED_TOKENS (uncached)
    # 3. Top segment: CACHED_TOKENS
    # 4. Calculate hit rate: (CACHED_TOKENS / TOK_IN) × 100%
    # 5. Annotate with percentage
```

**NEW Function: `time_distribution_chart()`**

```python
def time_distribution_chart(
    frameworks_data: Dict[str, List[Dict[str, float]]],
    output_path: str,
    title: str = "Execution Time Distribution"
) -> None:
    """
    Generate box plot showing execution time variability.
    
    Shows distribution of T_WALL_seconds across runs for each framework.
    
    Args:
        frameworks_data: Dict mapping framework names to lists of run metrics
        output_path: Path to save SVG
        title: Chart title
    """
    # Implementation:
    # 1. Extract T_WALL_seconds for each framework
    # 2. Create box plot (one box per framework)
    # 3. Show median, Q1, Q3, min, max
    # 4. Mark outliers
    # 5. Optionally overlay individual run points
```

### 4.2 File: `src/analysis/statistics.py`

#### Changes Summary
- ✅ Update metric definitions table (separate by reliability)
- ✅ Update executive summary (reliable metrics only)
- ✅ Create new "Reliable Metrics Analysis" section
- ✅ Create new "Limitations and Future Work" section
- ✅ Update aggregate statistics (separate tables)
- ✅ Update statistical tests (exclude unreliable metrics)
- ✅ Update visual summary section
- ✅ Update recommendations

#### Detailed Changes

**Location: Line ~1437 (Metric Definitions)**

Add three separate tables as specified in Section 3.3 above.

**Location: Line ~593 (Executive Summary)**

Replace AEI/AUTR mentions with token/time/API efficiency findings.

**Location: After current Section 5 (around line 1933)**

Insert NEW "Section 6: Reliable Metrics Analysis" with subsections.

**Location: Before Recommendations (around line 1930)**

Insert NEW "Section 7: Limitations and Future Work" with full content from Section 3.3 above.

**Location: Line ~1910 (Visual Summary)**

Update to reference only new reliable-metric visualizations.

**Location: Line ~1933 (Recommendations)**

Replace with revised recommendations from Section 3.3 above.

### 4.3 File: `runners/analyze_results.sh` or Analysis Script

#### Changes Needed

```bash
# BEFORE: Generate all visualizations
python -c "
from src.analysis.visualizations import radar_chart, pareto_plot, timeline_chart
# ... generate all three ...
"

# AFTER: Skip deprecated, add new
python -c "
from src.analysis.visualizations import (
    radar_chart,                  # Updated metrics
    # pareto_plot,                # DEPRECATED - skip
    # timeline_chart,             # DEPRECATED - skip
    token_efficiency_chart,       # NEW
    api_efficiency_chart,         # NEW
    cache_efficiency_chart,       # NEW
    time_distribution_chart       # NEW
)
# ... generate reliable charts only ...
"
```

### 4.4 File: `.gitignore` or Cleanup

Consider deprecating old visualization files:
```
analysis_output/pareto_plot.svg      # Mark as deprecated
analysis_output/timeline_chart.svg   # Mark as deprecated
```

---

## 5. Testing Strategy

### 5.1 Unit Tests

**New Test File:** `tests/unit/test_reliable_visualizations.py`

```python
def test_token_efficiency_chart_generation():
    """Verify token efficiency chart creates valid output."""
    # Test with mock data
    # Verify SVG file created
    # Check plot contains expected elements
    
def test_api_efficiency_chart_with_ci():
    """Verify API efficiency chart includes confidence intervals."""
    # Test with bootstrap CI data
    # Verify error bars present
    
def test_cache_efficiency_stacked_bars():
    """Verify cache chart shows correct stacking."""
    # Test calculation: cached + uncached = total
    # Verify percentages sum to 100%
    
def test_time_distribution_outliers():
    """Verify time distribution marks outliers correctly."""
    # Test with known outlier data
    # Verify outlier detection
```

**Updated Test File:** `tests/unit/test_visualizations.py`

```python
def test_radar_chart_reliable_metrics_only():
    """Verify radar chart uses only reliable metrics."""
    # Generate with default metrics
    # Assert no AUTR, CRUDe, ESR, MC in chart
    # Assert TOK_IN, TOK_OUT, etc. present
    
def test_pareto_plot_deprecated_warning():
    """Verify pareto_plot issues deprecation warning."""
    with warnings.catch_warnings(record=True) as w:
        pareto_plot(test_data, "/tmp/test.svg")
        assert len(w) == 1
        assert "deprecated" in str(w[0].message).lower()
        assert "Q*" in str(w[0].message)
```

### 5.2 Integration Tests

**Test File:** `tests/integration/test_report_generation.py`

```python
def test_report_excludes_unreliable_metrics_from_main():
    """Verify main analysis sections use reliable metrics only."""
    report_path = "analysis_output/report.md"
    with open(report_path) as f:
        content = f.read()
    
    # Find "Reliable Metrics Analysis" section
    reliable_section = extract_section(content, "Reliable Metrics Analysis")
    
    # Assert no mentions of AUTR, Q*, CRUDe, ESR, MC in this section
    assert "AUTR" not in reliable_section
    assert "Q*" not in reliable_section
    assert "CRUDe" not in reliable_section
    
def test_limitations_section_present():
    """Verify Limitations and Future Work section exists."""
    report_path = "analysis_output/report.md"
    with open(report_path) as f:
        content = f.read()
    
    assert "Limitations and Future Work" in content
    assert "Unmeasured Quality Metrics" in content
    assert "Partially Measured Autonomy Metrics" in content
    
def test_visualizations_use_reliable_metrics():
    """Verify generated visualizations use reliable metrics only."""
    # Check radar_chart.svg references
    # Verify no pareto_plot.svg or timeline_chart.svg generated
    # Verify new charts present
```

### 5.3 Visual Inspection Checklist

After regenerating report, manually verify:

- [ ] Executive summary mentions only reliable metrics
- [ ] No AUTR/AEI comparisons in main analysis
- [ ] No Q*/CRUDe/ESR/MC values in aggregate tables
- [ ] Radar chart shows 6 reliable metrics
- [ ] No Pareto plot in report
- [ ] No Timeline chart in report
- [ ] 4 new charts present (token, API, cache, time)
- [ ] "Limitations and Future Work" section complete
- [ ] Recommendations based on reliable metrics only
- [ ] Statistical tests exclude unreliable metrics

---

## 6. Implementation Timeline

### Phase 1: Visualization Updates (Week 1)
**Duration:** 8-12 hours

**Tasks:**
- [ ] Update `radar_chart()` default metrics
- [ ] Deprecate `pareto_plot()` and `timeline_chart()`
- [ ] Implement `token_efficiency_chart()`
- [ ] Implement `api_efficiency_chart()`
- [ ] Implement `cache_efficiency_chart()`
- [ ] Implement `time_distribution_chart()`
- [ ] Write unit tests for new visualizations
- [ ] Test with current data

**Deliverable:** Updated `src/analysis/visualizations.py` with reliable-metric charts only

### Phase 2: Report Structure Changes (Week 1-2)
**Duration:** 8-12 hours

**Tasks:**
- [ ] Refactor metric definitions (3 tables)
- [ ] Update executive summary
- [ ] Create "Reliable Metrics Analysis" section
- [ ] Create "Limitations and Future Work" section
- [ ] Update statistical tests to filter metrics
- [ ] Update visual summary section
- [ ] Update recommendations section
- [ ] Write integration tests

**Deliverable:** Updated `src/analysis/statistics.py` with new structure

### Phase 3: Testing & Validation (Week 2)
**Duration:** 4-6 hours

**Tasks:**
- [ ] Run full analysis pipeline
- [ ] Generate test report
- [ ] Verify all visualizations correct
- [ ] Check metric filtering in tables
- [ ] Validate section organization
- [ ] Manual visual inspection
- [ ] Fix any issues found

**Deliverable:** Validated report generation

### Phase 4: Documentation (Week 2)
**Duration:** 2-4 hours

**Tasks:**
- [ ] Update README.md
- [ ] Update docs/metrics.md
- [ ] Update docs/quickstart.md
- [ ] Add migration notes
- [ ] Document new visualizations
- [ ] Update troubleshooting guide

**Deliverable:** Complete documentation

### Phase 5: Final Review & Deployment (Week 2-3)
**Duration:** 2-4 hours

**Tasks:**
- [ ] Peer review
- [ ] Generate production report
- [ ] Archive old visualizations
- [ ] Tag release version
- [ ] Update CHANGELOG
- [ ] Announce changes

**Deliverable:** Production-ready analysis pipeline

**Total Estimated Time:** 24-38 hours across 2-3 weeks

---

## 7. Success Criteria

### 7.1 Technical Success Criteria

- [ ] All visualizations use reliable metrics only (100% coverage)
- [ ] No unreliable metrics in main analysis sections
- [ ] "Limitations and Future Work" section complete and comprehensive
- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Report generation completes without warnings
- [ ] New visualizations render correctly

### 7.2 Scientific Success Criteria

- [ ] No misleading claims about unmeasured metrics
- [ ] Clear distinction between reliable and unreliable data
- [ ] Honest disclosure of limitations
- [ ] Actionable recommendations based on reliable metrics
- [ ] Clear roadmap for future implementation
- [ ] Reviewers can easily understand what's measured vs not measured

### 7.3 User Experience Success Criteria

- [ ] Report easy to navigate
- [ ] Visualizations intuitive and informative
- [ ] Limitations section doesn't undermine main findings
- [ ] Future work section provides clear path forward
- [ ] No confusion about metric reliability

### 7.4 Code Quality Success Criteria

- [ ] Code follows existing patterns
- [ ] Functions properly documented
- [ ] No code duplication
- [ ] Deprecation warnings clear and actionable
- [ ] Backward compatibility maintained where possible

---

## 8. Future Work Roadmap

This section documents the implementation path for unreliable/unmeasured metrics.

### 8.1 Priority 1: BAEs HITL Detection

**Timeline:** 2-3 weeks  
**Effort:** 15-20 hours  
**Assignee:** TBD

**Deliverables:**
- [ ] HITL detection function in BAEs adapter
- [ ] Pattern matching implementation
- [ ] Integration with metrics collection
- [ ] Validation test suite
- [ ] Documentation update

**Success Criteria:**
- BAEs HITL detection matches ChatDev/GHSpec approach
- >95% detection accuracy
- AUTR/AEI values reliable for BAEs
- All frameworks use consistent methodology

### 8.2 Priority 2: Quality Metrics Infrastructure

**Timeline:** 4-6 weeks  
**Effort:** 20-40 hours  
**Assignee:** TBD

**Deliverables:**
- [ ] Server management module
- [ ] Endpoint validation suite
- [ ] ESR measurement implementation
- [ ] CRUDe measurement implementation
- [ ] MC measurement implementation
- [ ] Q* calculation verification
- [ ] Integration tests
- [ ] Documentation

**Success Criteria:**
- Applications successfully execute
- CRUD endpoints validated
- Quality metrics > 0 for functional code
- Q* meaningfully differentiates frameworks

### 8.3 Priority 3: Visualization Re-enablement

**Timeline:** 1 week  
**Effort:** 4-8 hours  
**Assignee:** TBD

**Deliverables:**
- [ ] Re-enable Pareto plot with real Q* values
- [ ] Re-enable Timeline chart with real CRUDe values
- [ ] Update radar chart to include quality metrics
- [ ] Add quality-efficiency scatter plots
- [ ] Update documentation

**Success Criteria:**
- All visualizations use measured data
- No deprecated warnings
- Quality dimensions visible in charts

---

## 9. References

### Related Documentation
- `docs/metrics.md` - Metric definitions
- `docs/QUALITY_METRICS_INVESTIGATION.md` - Why quality metrics are zero
- `AUTR_ADAPTER_ANALYSIS.md` - HITL detection analysis
- `BAES_HITL_INVESTIGATION.md` - BAEs autonomy investigation
- `HITL_SCIENTIFIC_HONESTY.md` - Decision to treat HITL as partially measured

### Code References
- `src/analysis/visualizations.py` - Visualization functions
- `src/analysis/statistics.py` - Report generation
- `src/adapters/baes_adapter.py` - BAEs adapter (lines 330, 348)
- `src/adapters/chatdev_adapter.py` - ChatDev HITL detection (lines 821-832)
- `src/adapters/ghspec_adapter.py` - GHSpec HITL detection (line 544)

### Configuration
- `config/experiment.yaml` - `auto_restart_servers: false`

---

## Appendix A: Metric Classification Matrix

| Metric | Reliable? | Reason | Frameworks |
|--------|-----------|--------|------------|
| TOK_IN | ✅ Yes | OpenAI Usage API | All |
| TOK_OUT | ✅ Yes | OpenAI Usage API | All |
| API_CALLS | ✅ Yes | Count-based | All |
| CACHED_TOKENS | ✅ Yes | OpenAI Usage API | All |
| T_WALL_seconds | ✅ Yes | Python timing | All |
| ZDI | ✅ Yes | Calculated from timing | All |
| UTT | ✅ Yes | Configuration fixed | All |
| AUTR | ⚠️ Partial | No BAEs detection | ChatDev, GHSpec only |
| AEI | ⚠️ Partial | Depends on AUTR | ChatDev, GHSpec only |
| HIT | ⚠️ Partial | No BAEs detection | ChatDev, GHSpec only |
| HEU | ⚠️ Partial | Depends on HIT | ChatDev, GHSpec only |
| Q* | ❌ No | Apps not executed | None |
| ESR | ❌ No | Apps not executed | None |
| CRUDe | ❌ No | Apps not executed | None |
| MC | ❌ No | Apps not executed | None |

---

## Appendix B: Visualization Comparison

### Current Visualizations
| Name | Metrics Used | Reliable Metrics | Unreliable Metrics | Status |
|------|--------------|------------------|-------------------|--------|
| Radar Chart | 7 | 3 (43%) | 4 (57%) | ⚠️ UPDATE |
| Pareto Plot | 2 | 1 (50%) | 1 (50%) | ❌ REMOVE |
| Timeline Chart | 2 | 1 (50%) | 1 (50%) | ❌ REMOVE |

### Proposed Visualizations
| Name | Metrics Used | Reliable Metrics | Unreliable Metrics | Status |
|------|--------------|------------------|-------------------|--------|
| Radar Chart | 6 | 6 (100%) | 0 (0%) | ✅ UPDATED |
| Token Efficiency | 3 | 3 (100%) | 0 (0%) | ✅ NEW |
| API Efficiency | 2 | 2 (100%) | 0 (0%) | ✅ NEW |
| Cache Efficiency | 2 | 2 (100%) | 0 (0%) | ✅ NEW |
| Time Distribution | 1 | 1 (100%) | 0 (0%) | ✅ NEW |

**Improvement:** 100% reliable metrics in all visualizations (vs 43-50% currently)

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-17 | System | Initial comprehensive plan created |

---

**End of Implementation Plan**
