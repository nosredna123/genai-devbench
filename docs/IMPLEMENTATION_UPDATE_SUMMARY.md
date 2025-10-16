# Implementation Plan Update Summary

**Date**: October 16, 2025  
**Action**: Extended scope from single metric to dual metrics

## What Changed

### Original Plan (api_calls only)
- Add single metric: `api_calls`
- Extract `num_model_requests` from OpenAI Usage API
- Return 3-tuple: `(tokens_in, tokens_out, api_calls)`
- Estimated effort: 1 hour

### Updated Plan (api_calls + cached_tokens)
- Add **TWO** metrics: `api_calls` AND `cached_tokens`
- Extract both `num_model_requests` AND `input_cached_tokens` from OpenAI Usage API
- Return **4-tuple**: `(tokens_in, tokens_out, api_calls, cached_tokens)`
- Estimated effort: 1.5 hours

## Why the Extension?

### Discovery Process
1. User requested `api_calls` metric ("utterances" preliminary name)
2. Agent confirmed feasibility and created implementation plan
3. User asked: "Is there other unused data coming from the Open AI Usage API response beyond num_model_requests?"
4. Agent queried live OpenAI Usage API with `bucket_width=1m`
5. **Discovered**: 21 total fields, 13 currently used, **8 unused**
6. **Identified 3 high-value unused fields**:
   - `num_model_requests` (PRIORITY 1) - original request
   - `input_cached_tokens` (PRIORITY 2) - **10% cache hit rate observed**
   - `model` (PRIORITY 3) - validation field

### Decision Rationale

**Why add `cached_tokens`?**
1. **Significant cache usage**: 10% cache hit rate in recent data (42,624 cached / 426,712 input tokens)
2. **Cost impact**: 90% discount on cached tokens ($0.25 vs. $2.50 per 1M)
3. **Minimal extra effort**: +30 minutes (~20% more code)
4. **Scientific value**: Framework efficiency comparison (which benefits most from caching?)
5. **No additional API calls**: Same response object as `api_calls`

**Why not add `model` field yet?**
- Returns `null` in current data (needs investigation)
- Lower scientific priority (config already specifies model)
- Can be added later if needed

## Updated Files

### Documentation
1. **`docs/api_calls_metric_implementation.md`** (1,259 lines)
   - Title: "API Calls + Cache Metrics Implementation Plan"
   - Added Quick Summary (TL;DR) section
   - Extended Motivation section with Cache Metrics
   - Updated all code examples to 4-tuple
   - Added Cache Efficiency analysis functions
   - Updated Expected Results with cache baselines
   - Added cache-specific success criteria
   - Updated Future Enhancements with cost analysis

2. **`docs/unused_openai_fields_analysis.md`** (NEW - 358 lines)
   - Complete analysis of all 21 API response fields
   - 3 high-value unused fields identified
   - 5 low-value fields documented
   - Recommendations and implementation priorities
   - Real-world data samples

3. **`docs/IMPLEMENTATION_UPDATE_SUMMARY.md`** (THIS FILE)
   - Captures the scope extension decision
   - Documents discovery process
   - Quick reference for future context

### Tests
4. **`tests/unit/test_base_adapter.py`** (363 lines, was 269)
   - Renamed: `test_extract_num_model_requests_from_response` → `test_extract_all_fields_from_response`
   - Updated all extraction logic to 4-tuple
   - Added `cached_tokens` assertions to all tests
   - Added cache hit rate calculations
   - NEW: `TestCacheEfficiencyMetrics` class
     - `test_calculate_cache_hit_rate`
     - `test_calculate_cost_savings`
     - `test_cache_handles_zero_input_tokens`
   - Total: 12 test functions (was 8)

## Implementation Changes

### Return Signature Evolution

**Before (current)**:
```python
def fetch_usage_from_openai(...) -> Tuple[int, int]:
    return tokens_in, tokens_out
```

**After Phase 1 (original plan)**:
```python
def fetch_usage_from_openai(...) -> Tuple[int, int, int]:
    return tokens_in, tokens_out, api_calls
```

**After Phase 1 (updated plan)**:
```python
def fetch_usage_from_openai(...) -> Tuple[int, int, int, int]:
    return tokens_in, tokens_out, api_calls, cached_tokens
```

### metrics.json Schema Extension

**Before (current)**:
```json
{
  "step_number": 1,
  "tokens_in": 2883,
  "tokens_out": 1795,
  "duration_seconds": 42.5
}
```

**After (updated plan)**:
```json
{
  "step_number": 1,
  "tokens_in": 2883,
  "tokens_out": 1795,
  "api_calls": 4,           // ← NEW
  "cached_tokens": 0,       // ← NEW
  "duration_seconds": 42.5
}
```

### Derived Metrics Added

**From api_calls**:
1. API Efficiency Ratio: `api_calls / (tokens_total / 1000)`
2. Calls Per Step: Aggregated by step number
3. Avg Tokens Per Call: `tokens_total / api_calls`

**From cached_tokens (NEW)**:
1. Cache Hit Rate: `(cached_tokens / tokens_in) * 100`
2. Cost Savings: `cached_tokens * (base_price - cache_price)`
3. Effective Cost Per Token: Account for cache discount

## Expected Baselines (from 7-day data)

| Metric | Value | Source |
|--------|-------|--------|
| Total API requests | 314 | OpenAI Usage API |
| Total input tokens | 426,712 | OpenAI Usage API |
| Total output tokens | 129,619 | OpenAI Usage API |
| **Total cached tokens** | **42,624** | OpenAI Usage API |
| | | |
| **API efficiency** | **0.56 calls/1K tokens** | Calculated |
| **Cache hit rate** | **10.0%** | Calculated |
| **Avg tokens per call** | **1,772 tokens/call** | Calculated |
| **Cost savings from cache** | **~$0.096** | Calculated |

## Implementation Effort Adjustment

| Phase | Original (api_calls only) | Updated (both metrics) | Δ Time |
|-------|---------------------------|------------------------|--------|
| Phase 1: Data Collection | 15 min | 20 min | +5 min |
| Phase 2: Adapter Updates | 15 min | 20 min | +5 min |
| Phase 3: Storage & Reconciliation | 10 min | 15 min | +5 min |
| Phase 4: Analysis & Reporting | 15 min | 20 min | +5 min |
| Phase 5: Visualization | 10 min | 15 min | +5 min |
| | | | |
| **TOTAL** | **1 hour** | **1.5 hours** | **+30 min** |

**Effort increase**: 50% more time, but 100% more metrics (efficient!)

## Benefits of Extended Scope

1. **Cost Transparency**: Actual API costs considering cache discounts
2. **Framework Comparison**: Which framework benefits most from caching?
3. **Optimization Insights**: Identify opportunities to improve cache hit rate
4. **Complete Picture**: Communication intensity (api_calls) + efficiency (cache rate)
5. **Future-Proof**: Captures data now, can analyze later without re-running experiments

## Backward Compatibility

### Test Suite
- Integration tests updated to support **both** 2-tuple (old) and 4-tuple (new)
- No breaking changes to existing tests
- Graceful degradation if fields missing

### Error Handling
- All error paths return `(0, 0, 0, 0)` instead of `(0, 0)`
- Missing fields default to `0`
- Null values handled gracefully: `int(result.get("field", 0) or 0)`

## Next Steps

1. **Review and approve** this extended scope
2. **Implement** according to updated plan (`docs/api_calls_metric_implementation.md`)
3. **Run tests** to validate extraction logic
4. **Execute** first experimental run with new metrics
5. **Analyze** cache efficiency differences between frameworks

## References

- **Updated Implementation Plan**: `docs/api_calls_metric_implementation.md`
- **Field Analysis**: `docs/unused_openai_fields_analysis.md`
- **Updated Tests**: `tests/unit/test_base_adapter.py`
- **Quick Start Guide**: `docs/api_calls_quickstart.md` (needs update for cached_tokens)

---

**Status**: ✅ Documentation and tests updated, ready for implementation  
**Decision Point**: User approved extending scope to include `cached_tokens` metric
