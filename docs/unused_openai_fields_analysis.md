# OpenAI Usage API - Unused Fields Analysis

**Date**: October 16, 2025  
**API Endpoint**: `/v1/organization/usage/completions`  
**Query**: Last 7 days, 1-minute buckets

## Executive Summary

The OpenAI Usage API returns **21 fields per result**, but we currently use **only 13** (token-related fields). This analysis identifies **3 high-value fields** that should be captured immediately and **5 additional fields** available for future use.

---

## Complete Field Inventory

### ✅ Currently Used (13 fields) - Token Counting

| Field | Description | Current Use |
|-------|-------------|-------------|
| `input_tokens` | Total input tokens | ✅ Extracted & stored |
| `output_tokens` | Total output tokens | ✅ Extracted & stored |
| `input_text_tokens` | Text-based input tokens | ✅ Available (fallback) |
| `output_text_tokens` | Text-based output tokens | ✅ Available (fallback) |
| `input_uncached_tokens` | Non-cached input tokens | ✅ Available (fallback) |
| `input_cached_tokens` | Cached input tokens | ✅ Available (fallback) |
| `input_cached_text_tokens` | Cached text tokens | ✅ Available (fallback) |
| `input_audio_tokens` | Audio input tokens | ✅ Available (fallback) |
| `input_cached_audio_tokens` | Cached audio tokens | ✅ Available (fallback) |
| `output_audio_tokens` | Audio output tokens | ✅ Available (fallback) |
| `input_image_tokens` | Image input tokens | ✅ Available (fallback) |
| `input_cached_image_tokens` | Cached image tokens | ✅ Available (fallback) |
| `output_image_tokens` | Image output tokens | ✅ Available (fallback) |

**Note**: Only `input_tokens` and `output_tokens` are actively extracted. Other token fields exist in the extraction logic as fallbacks but aren't separately stored.

---

## ❌ High-Value Unused Fields (3 fields)

### 1. `num_model_requests` 🎯 **PRIORITY 1**

**Value**: `4` (sample from 2025-10-09 11:39:00)

**Description**: Number of OpenAI API calls made during the time bucket.

**Scientific Value**: **HIGH**
- **Primary use**: Communication intensity metric
- **Analysis**: Measure framework efficiency (calls per token)
- **Pattern detection**: Identify chatty vs. efficient frameworks
- **Step-wise analysis**: Which development phases trigger most API calls

**Example Aggregate (7 days)**:
- Total API calls: **314**
- Total tokens: **556,331**
- Efficiency: **0.56 calls per 1K tokens** (very efficient batching)
- Avg tokens per call: **1,772 tokens/call**

**Implementation Effort**: **EASY**
- Extract from `result.get("num_model_requests", 0)`
- Return as 3rd value in tuple: `(tokens_in, tokens_out, api_calls)`
- Store in `metrics.json` as `"api_calls": 4`

**Status**: 📋 **Implementation plan created** (see `docs/api_calls_metric_implementation.md`)

---

### 2. `input_cached_tokens` 🎯 **PRIORITY 2**

**Value**: `0` (sample), **42,624 total** (7 days)

**Description**: Number of input tokens served from cache (prompt caching feature).

**Scientific Value**: **MEDIUM-HIGH**
- **Primary use**: Cost optimization metric
- **Analysis**: Measure cache effectiveness
- **Cost savings**: Cached tokens are ~90% cheaper than uncached
- **Framework comparison**: Which frameworks benefit most from caching

**Example Aggregate (7 days)**:
- Total cached: **42,624 tokens**
- Total input: **426,712 tokens**
- **Cache hit rate: 10.0%**
- **Cost savings**: ~$0.0064 (estimated)

**Derived Metrics**:
1. **Cache Hit Rate**: `(input_cached_tokens / input_tokens) * 100`
2. **Cache Efficiency**: High cache rate = good prompt reuse
3. **Cost Savings**: `cached_tokens * (uncached_price - cached_price)`

**Implementation Effort**: **EASY**
- Extract from `result.get("input_cached_tokens", 0)`
- Store in `metrics.json` as `"cached_tokens": 42624`
- Add to aggregate metrics

**Status**: ⚠️ **Not planned yet** (could be added alongside `api_calls`)

---

### 3. `model` 🎯 **PRIORITY 3**

**Value**: `null` (sample) - often null when aggregated across models

**Description**: Specific model identifier (e.g., `"gpt-4o-mini-2024-07-18"`).

**Scientific Value**: **MEDIUM**
- **Primary use**: Validation & reproducibility
- **Analysis**: Ensure experiments used intended model
- **Tracking**: Detect unintended model changes
- **Reporting**: Document exact model version for reproducibility

**Caveats**:
- May be `null` if multiple models used in same bucket
- More useful with smaller bucket widths (1m vs. 1d)
- Already specified in config, but this confirms actual usage

**Implementation Effort**: **EASY**
- Extract from `result.get("model")`
- Store as validation field (not aggregated)
- Log warning if `model != config['model']`

**Status**: ⚠️ **Not planned yet** (low priority - config already specifies model)

---

## 📝 Other Available Fields (5 fields)

These fields are available but have **lower scientific value** for this experiment:

| Field | Description | Value | Potential Use |
|-------|-------------|-------|---------------|
| `project_id` | OpenAI project ID | `null` | Multi-project tracking (not applicable) |
| `user_id` | End-user identifier | `null` | Per-user attribution (not applicable) |
| `api_key_id` | API key identifier | `null` | Key-based filtering (not needed with time windows) |
| `batch` | Batch API flag | `null` | Batch vs. real-time detection (not using batch API) |
| `service_tier` | Service tier | `null` | Performance tier tracking (not applicable) |

**Note**: All these fields returned `null` in our dataset, suggesting they're either:
1. Not applicable to our use case
2. Require specific API features we're not using
3. Privacy-protected when aggregated

---

## 📊 Real-World Data Sample

**Time Bucket**: 2025-10-09 11:39:00 → 11:40:00 (1 minute)

```json
{
  "object": "organization.usage.completions.result",
  
  "num_model_requests": 4,           // ← NOT USED (HIGH VALUE)
  "input_cached_tokens": 0,          // ← NOT USED (MEDIUM VALUE)
  "model": null,                     // ← NOT USED (MEDIUM VALUE)
  
  "input_tokens": 2883,              // ✅ USED
  "output_tokens": 1795,             // ✅ USED
  
  "input_uncached_tokens": 2883,     // Available but not stored
  "input_text_tokens": 2883,         // Available but not stored
  "output_text_tokens": 1795,        // Available but not stored
  
  "project_id": null,                // Low value (null)
  "user_id": null,                   // Low value (null)
  "api_key_id": null,                // Low value (null)
  "batch": null,                     // Low value (null)
  "service_tier": null,              // Low value (null)
  
  "input_cached_text_tokens": 0,
  "input_audio_tokens": 0,
  "input_cached_audio_tokens": 0,
  "output_audio_tokens": 0,
  "input_image_tokens": 0,
  "input_cached_image_tokens": 0,
  "output_image_tokens": 0
}
```

---

## 💡 Recommendations

### Immediate Action (HIGH PRIORITY)

1. ✅ **Implement `num_model_requests` extraction**
   - **Implementation plan exists**: `docs/api_calls_metric_implementation.md`
   - **Effort**: ~1 hour (50 lines of code)
   - **Scientific value**: HIGH
   - **Tests ready**: 9 test functions created

2. ⚠️ **Consider `input_cached_tokens` extraction**
   - **Effort**: ~30 minutes (can piggyback on api_calls implementation)
   - **Scientific value**: MEDIUM-HIGH (cost optimization)
   - **Add to Phase 1** of api_calls implementation

### Future Consideration (MEDIUM PRIORITY)

3. **`model` field validation**
   - Extract and log warnings if `model != config['model']`
   - Useful for reproducibility documentation
   - Low effort: ~15 minutes

### Low Priority

4. **Other fields** (`project_id`, `user_id`, etc.)
   - All returned `null` in our dataset
   - Not applicable to current experiment design
   - Can be ignored

---

## 🎯 Recommended Implementation Order

### Phase 1: `num_model_requests` + `input_cached_tokens` (1.5 hours)

**Modify**: `src/adapters/base_adapter.py`

```python
def _extract_tokens(result: Dict[str, Any]) -> tuple[int, int, int, int]:
    # ... existing token extraction ...
    num_requests = int(result.get("num_model_requests", 0) or 0)
    cached_tokens = int(result.get("input_cached_tokens", 0) or 0)
    return tokens_in, tokens_out, num_requests, cached_tokens
```

**Store in metrics.json**:
```json
{
  "tokens_in": 2883,
  "tokens_out": 1795,
  "api_calls": 4,          // ← NEW
  "cached_tokens": 0       // ← NEW
}
```

**Derived Metrics**:
1. API Efficiency: `api_calls / (tokens_total / 1000)`
2. Cache Hit Rate: `(cached_tokens / tokens_in) * 100`
3. Cost Savings: `cached_tokens * (base_price - cached_price)`

### Phase 2: `model` validation (optional, 15 min)

Log warning if actual model differs from config.

---

## 📈 Expected Impact

### With `num_model_requests`:
- **New analysis dimension**: Communication intensity
- **Efficiency metric**: Calls per 1K tokens
- **Framework comparison**: ChatDev (high) vs. GHSpec (medium) vs. BAEs (low)
- **Step-wise patterns**: Identify API-intensive development phases

### With `input_cached_tokens`:
- **Cost optimization**: Measure cache effectiveness
- **Cache hit rate**: Track prompt reuse
- **Framework comparison**: Which benefits most from caching
- **Cost reporting**: Actual savings from caching

---

## 🔗 References

- **OpenAI Usage API Docs**: https://platform.openai.com/docs/api-reference/usage
- **Implementation Plan**: `docs/api_calls_metric_implementation.md`
- **Quick Start Guide**: `docs/api_calls_quickstart.md`
- **Token Counting Implementation**: `docs/token_counting_implementation.md`

---

## Appendix: Aggregate Statistics (7 days)

**Data Source**: 52 buckets with usage data (out of 200 total buckets)

| Metric | Value |
|--------|-------|
| Total input tokens | 426,712 |
| Total output tokens | 129,619 |
| **Total tokens** | **556,331** |
| **Total API requests** | **314** |
| **Total cached tokens** | **42,624** |
| | |
| **API Efficiency** | **0.56 calls/1K tokens** |
| **Cache hit rate** | **10.0%** |
| **Avg tokens per call** | **1,772 tokens/call** |

**Interpretation**:
- Very efficient API usage (< 1 call per 1K tokens)
- Moderate cache utilization (10% hit rate)
- Large average call size (1.7K tokens/call) suggests good batching

---

**Last Updated**: October 16, 2025  
**Generated by**: OpenAI Usage API field discovery script
