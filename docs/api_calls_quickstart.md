# API Calls Metric - Quick Reference

## Overview

New metric: **`api_calls`** - tracks the number of OpenAI API requests per experimental step.

**Status**: 📋 **Planned** (implementation ready, tests written)  
**Effort**: ~1 hour (50 lines of code changes)  
**Tests**: 9 test functions (all passing/ready)

## Quick Start

### 1. Read the Plan
```bash
cat docs/api_calls_metric_implementation.md
```

### 2. Run Pre-Implementation Tests (should show warnings)
```bash
# Unit test (should pass - tests extraction logic)
pytest tests/unit/test_base_adapter.py -v

# Integration test (will show "OLD 2-tuple format" warning)
python tests/integration/test_usage_api.py

# E2E test (will show "WARNING: No api_calls field" if run hasn't implemented it)
python tests/integration/test_api_calls_e2e.py
```

### 3. Implement Following the Plan
Follow **docs/api_calls_metric_implementation.md** phases 1-5:
- Phase 1: Update `BaseAdapter.fetch_usage_from_openai()` (~15 lines)
- Phase 2: Update 3 adapters (~12 lines total)
- Phase 3: Update reconciler (~10 lines)
- Phase 4: Update statistics analyzer (~15 lines)
- Phase 5: Add visualization (~10 lines)

### 4. Run Post-Implementation Tests (should all pass)
```bash
# All tests
pytest tests/unit/test_base_adapter.py tests/integration/test_api_calls_e2e.py -v

# Integration test should show "NEW 3-tuple format"
python tests/integration/test_usage_api.py

# Full suite
./run_tests.sh
```

### 5. Validate with Real Experiment
```bash
# Run single experiment
./runners/run_experiment.sh --framework chatdev --runs 1

# Check metrics.json contains api_calls
cat runs/chatdev/*/metrics.json | jq '.steps[0].api_calls'

# Generate report
./runners/analyze_results.sh

# Verify API Calls section in report
grep -A 20 "API Calls" analysis_output/report.md
```

## What Gets Changed

### Files Modified (5 files)
1. `src/adapters/base_adapter.py` - Return 3-tuple instead of 2-tuple
2. `src/adapters/chatdev_adapter.py` - Capture api_calls
3. `src/adapters/ghspec_adapter.py` - Capture api_calls
4. `src/adapters/baes_adapter.py` - Capture api_calls
5. `src/orchestrator/usage_reconciler.py` - Extract api_calls
6. `src/analysis/statistics.py` - Analyze & report api_calls

### Metrics.json Structure (NEW field)
```json
{
  "steps": [
    {
      "step_number": 1,
      "tokens_in": 1000,
      "tokens_out": 500,
      "api_calls": 15,  // ← NEW FIELD
      "duration_seconds": 120.5
    }
  ]
}
```

### Analysis Report (NEW section)
```markdown
### API Calls (Communication Intensity)

**Results**:
- ChatDev: 200 ± 30 calls (5.2 calls/1K tokens)
- GHSpec: 80 ± 15 calls (2.8 calls/1K tokens)
- BAEs: 50 ± 10 calls (1.5 calls/1K tokens)
```

## Expected Results

### Typical Values (6-step experiment)

| Framework | API Calls | Efficiency (calls/1K tokens) | Interpretation |
|-----------|-----------|------------------------------|----------------|
| ChatDev   | 150-300   | 5-10                         | High (multi-agent dialogue) |
| GHSpec    | 50-100    | 2-5                          | Moderate (4-phase workflow) |
| BAEs      | 30-80     | 1-4                          | Low (direct API) |

### Interpretation Guide

**API Efficiency Ratio**: `api_calls / (tokens_total / 1000)`

- **< 1**: Very efficient batching ✅
- **1-5**: Balanced ✅
- **5-10**: Chatty communication ⚠️
- **> 10**: Very chatty (potential inefficiency) ⚠️

## Scientific Value

1. **Efficiency Analysis**: Measure request batching effectiveness
2. **Communication Patterns**: Understand framework interaction styles
3. **Cost-Effectiveness**: Correlate API volume with quality outcomes
4. **Step-wise Insights**: Identify API-intensive development phases

## Test Coverage

### Unit Tests (8 test cases)
- ✅ Extract from normal response
- ✅ Handle missing field
- ✅ Handle null values
- ✅ Handle zero values
- ✅ Multiple buckets aggregation
- ✅ Efficiency calculations
- ✅ Zero token edge case
- ✅ Zero calls edge case

### Integration Tests (2 test scripts)
- ✅ Live OpenAI Usage API query
- ✅ 3-tuple return validation
- ✅ Efficiency metrics calculation
- ✅ Anomaly detection

### End-to-End Test (1 comprehensive test)
- ✅ Metrics.json structure validation
- ✅ Step-by-step analysis
- ✅ Data integrity checks
- ✅ Summary statistics
- ✅ Efficiency calculations

## Troubleshooting

### Test shows "OLD 2-tuple format"
→ Implementation not yet complete. Follow plan phases 1-2.

### Test shows "No api_calls field found"
→ Run a new experiment after implementing. Old runs won't have the field.

### Efficiency ratio > 100
→ Data integrity issue. Check if num_model_requests is being extracted correctly.

### Efficiency ratio < 0.01
→ Missing data. Verify OpenAI Usage API returns num_model_requests field.

## Documentation

- **Implementation Plan**: `docs/api_calls_metric_implementation.md` (1036 lines)
- **Unit Tests**: `tests/unit/test_base_adapter.py` (268 lines)
- **E2E Test**: `tests/integration/test_api_calls_e2e.py` (164 lines)
- **This Guide**: `docs/api_calls_quickstart.md`

## Commit Strategy

```bash
# After Phase 1-3 (data collection)
git commit -m "feat: Add api_calls metric - data collection"

# After Phase 4-5 (analysis & visualization)
git commit -m "feat: Add api_calls metric - analysis & visualization"

# After documentation updates
git commit -m "docs: Document api_calls metric"
```

## References

- OpenAI Usage API: https://platform.openai.com/docs/api-reference/usage
- Token Counting Implementation: `docs/token_counting_implementation.md`
- Metrics Documentation: `docs/metrics.md`

---

**Ready to implement?** Start with Phase 1 in `docs/api_calls_metric_implementation.md`
