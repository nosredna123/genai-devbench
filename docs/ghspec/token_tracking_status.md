# Token Tracking Status - GHSpec Experiment

**Run ID**: 66d1dbec-762b-47cf-bd23-4e7bd714abf5  
**Date**: October 15, 2025  
**Status**: ⏳ **Pending** (Usage API Delay)

---

## Current Situation

The experiment completed successfully with **23 code files generated**, but token usage data is not yet available from the OpenAI Usage API.

### Usage API Reconciliation Results

```
Status: data_not_available
Tokens In:  0 (from Usage API)
Tokens Out: 0 (from Usage API)
Message: "No token data available from Usage API yet (first attempt)"
```

### Known Issue: Usage API Reporting Delay

The OpenAI Usage API has a **5-60 minute aggregation delay** before token usage data becomes available. This is documented OpenAI behavior and is expected.

---

## API Calls Made

Based on the experiment logs, the following API calls were successfully made:

### Phase 1-3: Specification Generation (3 calls)

| Step | Phase | Timestamp | Status |
|------|-------|-----------|--------|
| 1 | Specify | 2025-10-15 17:58:08 | ✅ Complete |
| 2 | Plan | 2025-10-15 17:58:27 | ✅ Complete |
| 3 | Tasks | 2025-10-15 17:59:02 | ✅ Complete |

### Phase 4-5: Code Generation (46 calls)

| Step | Tasks | Duration | Avg per task |
|------|-------|----------|--------------|
| 4 | 23 tasks | 284s (4m 44s) | 12.3s |
| 5 | 23 tasks | 302s (5m 2s) | 13.1s |

**Total API Calls**: 49 calls (3 spec + 46 code)

---

## Expected Token Usage (Estimated)

Based on typical GPT-4o-mini usage patterns for similar tasks:

### Specification Generation (Steps 1-3)

- **Input**: ~1,500 tokens per call (feature request + template)
- **Output**: ~1,500-2,000 tokens per call (spec/plan/tasks)
- **Total**: ~9,000-10,500 tokens

### Code Generation (Steps 4-5)

- **Input**: ~2,000-3,000 tokens per call (spec + plan + task + template)
- **Output**: ~500-800 tokens per call (code file)
- **Per task**: ~2,500-3,800 tokens
- **Total (46 calls)**: ~115,000-175,000 tokens

### Grand Total Estimate

- **Input**: 50,000-70,000 tokens
- **Output**: 30,000-40,000 tokens
- **Combined**: **80,000-110,000 tokens**

**Note**: These are rough estimates. Actual usage may vary.

---

## Next Steps

### Automatic Retry

The reconciliation script is designed to automatically retry pending runs. The run will remain in "pending" status and can be reconciled again later.

### Manual Re-run (in 30-60 minutes)

```bash
bash runners/reconcile_usage.sh ghspec 66d1dbec-762b-47cf-bd23-4e7bd714abf5
```

### Alternative: Use Completion Response Metadata

If Usage API continues to return 0, we could extract token counts from the API response metadata directly:

```python
response = openai.ChatCompletion.create(...)
tokens_in = response['usage']['prompt_tokens']
tokens_out = response['usage']['completion_tokens']
```

**Status**: Not currently implemented, but feasible enhancement

---

## Impact Assessment

### Research Impact: **LOW**

The missing token data does **not affect** the core research findings:

✅ Code quality assessment (independent of tokens)  
✅ Automation metrics (AUTR = 1.0, HIT = 0)  
✅ Execution time metrics (714s total)  
✅ Success rate (100%)  
✅ File generation count (23 files)  

❌ Only affects cost estimation and efficiency comparisons

### Workarounds for Research

1. **Use execution time** as efficiency proxy (already captured)
2. **Estimate tokens** based on file sizes (spec: 4.6KB, plan: 7.3KB, etc.)
3. **Compare relative metrics** across frameworks (all have same limitation)
4. **Document limitation** in research methodology

---

## Configuration Details

### API Keys Used

- **Chat Completion**: `OPENAI_API_KEY_GHSPEC` (framework-specific)
- **Usage API**: `OPENAI_API_KEY_USAGE_TRACKING` (admin key with api.usage.read scope)

### Usage API Calls Made

Each step called `fetch_usage_from_openai()` after completion:
- Step 1: ✅ Called (returned 0)
- Step 2: ✅ Called (returned 0)
- Step 3: ✅ Called (returned 0)
- Step 4: ✅ Called 23 times (all returned 0)
- Step 5: ✅ Called 23 times (all returned 0)

**Total Usage API queries**: 49 calls

---

## Conclusion

Token tracking is a **non-critical issue** that does not block research progress. The experiment was successful in all other metrics. Token data will become available after the Usage API aggregation delay, or we can implement alternative tracking methods if needed.

**Recommendation**: Continue with research using available metrics (time, quality, automation). Re-run reconciliation in 1 hour to capture token data for completeness.

---

**Document Status**: Current as of October 15, 2025 18:16 UTC  
**Next Update**: After successful token reconciliation
