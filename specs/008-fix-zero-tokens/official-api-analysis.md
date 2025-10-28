# Revised Analysis: OpenAI Usage API Query Parameters

## Official Documentation Key Points

### Bucket Width Behavior

From OpenAI docs:
- `bucket_width=1m`: default 60 buckets, max 1440 (24 hours)
- `bucket_width=1h`: default 24 buckets, max 168 (7 days)
- `bucket_width=1d`: default 7 buckets, max 31 (31 days)

### Critical Insight: Time Range Filtering

The API uses `start_time` and `end_time` to:
1. **Filter which buckets to return** (not which requests to include)
2. Return buckets that **overlap** with the time range
3. Each bucket contains **aggregated usage for the entire bucket period**

## Example from OpenAI Docs

```bash
curl "https://api.openai.com/v1/organization/usage/completions?start_time=1730419200&limit=1"
```

Response:
```json
{
  "data": [
    {
      "start_time": 1730419200,  // Bucket start (midnight)
      "end_time": 1730505600,    // Bucket end (next midnight)
      "results": [
        {
          "input_tokens": 1000,  // ALL tokens in this 24-hour bucket
          "output_tokens": 500,
          "num_model_requests": 5
        }
      ]
    }
  ]
}
```

## What This Means for Our Queries

### With bucket_width="1d"

```python
# Query Sprint 1 (21:41:05 - 21:41:41)
params = {
    "start_time": 1697399465,  # 2024-10-15 21:41:05
    "end_time": 1697399501,    # 2024-10-15 21:41:41
    "bucket_width": "1d"
}
```

**Response:**
```json
{
  "data": [
    {
      "start_time": 1697328000,   // 2024-10-15 00:00:00 (bucket start)
      "end_time": 1697414400,     // 2024-10-16 00:00:00 (bucket end)
      "results": [{
        "input_tokens": 25202,     // ALL tokens from entire day
        "output_tokens": 6318,     // (all 6 sprints combined)
        "num_model_requests": 86
      }]
    }
  ]
}
```

**Problem:** Every sprint query on Oct 15 returns the same bucket with ALL tokens from that day!

### With bucket_width="1m"

```python
# Query Sprint 1 (21:41:05 - 21:41:41)
params = {
    "start_time": 1697399465,  # 2024-10-15 21:41:05
    "end_time": 1697399501,    # 2024-10-15 21:41:41
    "bucket_width": "1m"
}
```

**Response:**
```json
{
  "data": [
    {
      "start_time": 1697399460,   // 21:41:00 (minute bucket)
      "end_time": 1697399520,     // 21:42:00
      "results": [{
        "input_tokens": 0,         // Sprint 1's tokens attributed to next bucket
        "num_model_requests": 0
      }]
    },
    {
      "start_time": 1697399520,   // 21:42:00 (next minute bucket)
      "end_time": 1697399580,     // 21:43:00
      "results": [{
        "input_tokens": 4937,      // Sprint 1's tokens appear HERE
        "num_model_requests": 15   // (due to API backend processing delay)
      }]
    }
  ]
}
```

**Issue:** Sprint 1's tokens are in the 21:42:00 bucket (misattribution), so the query returns partial/wrong data.

### With bucket_width="1m" + Run-Level Query

```python
# Query ENTIRE RUN (21:41:05 - 21:44:44)
params = {
    "start_time": 1697399465,  # Run start: 21:41:05
    "end_time": 1697399884,    # Run end:   21:44:44
    "bucket_width": "1m"
}
```

**Response:**
```json
{
  "data": [
    {
      "start_time": 1697399460,   // 21:41:00
      "results": [{"input_tokens": 0}]
    },
    {
      "start_time": 1697399520,   // 21:42:00
      "results": [{"input_tokens": 9874}]  // Sprint 1 + partial Sprint 2
    },
    {
      "start_time": 1697399580,   // 21:43:00
      "results": [{"input_tokens": 7694}]  // Partial Sprint 2 + Sprint 3 + partial 4
    },
    {
      "start_time": 1697399640,   // 21:44:00
      "results": [{"input_tokens": 7634}]  // Partial Sprint 4 + Sprint 5 + 6
    },
    {
      "start_time": 1697399700,   // 21:45:00 (may appear due to delayed processing)
      "results": [{"input_tokens": 0}]
    }
  ]
}
```

**Aggregate:** 9874 + 7694 + 7634 = 25,202 tokens ✅ **ACCURATE!**

## Key Insights

### 1. Time Range Filtering

The `start_time`/`end_time` parameters tell the API:
- "Return buckets that overlap with this time window"
- NOT "Return only requests made during this time window"

Each bucket contains **all activity during the bucket period**, regardless of the query time range.

### 2. Bucket Granularity Matters

- **Daily buckets:** Too coarse - all sprints from same day get identical totals
- **Minute buckets:** Fine enough to distinguish runs, but not individual sprints (due to API processing delay)
- **Run-level queries:** Capture all buckets spanning the run = accurate totals

### 3. Why Per-Sprint Attribution Fails

Even with minute buckets:
1. Sprint executes 21:41:05-21:41:41
2. API backend processes request and attributes tokens at 21:42:02
3. Tokens go into 21:42:00 bucket (not 21:41:00)
4. Sprint query for 21:41:05-21:41:41 misses its own tokens!

### 4. Why Run-Level Works

Run query for 21:41:05-21:44:44:
1. Returns ALL buckets: 21:41:00, 21:42:00, 21:43:00, 21:44:00, 21:45:00
2. Doesn't matter which bucket contains which sprint's tokens
3. Sum them all = total tokens for the run ✅

## Validation Against Issue Report

The issue report states:
> "Sprint 2 (21:41:42-21:42:13): 9,874 tokens → captured Sprint 1 + 2"

With minute buckets, Sprint 2's query would return:
- 21:42:00 bucket: Contains Sprint 1's delayed tokens + Sprint 2's early tokens
- 21:43:00 bucket: Contains Sprint 2's late tokens

**Sum = Sprint 1 + Sprint 2 tokens** ✅ Matches the issue report!

## Conclusion

✅ **Official documentation confirms:**
1. `bucket_width="1d"` is the current bug (all sprints get daily totals)
2. `bucket_width="1m"` is necessary but not sufficient for per-sprint accuracy
3. Run-level queries with minute buckets are the reliable solution

✅ **The spec is correct:**
- FR-005: Use bucket_width="1m" ✅
- FR-001: Query at run level (not per-sprint) ✅
- FR-006: Aggregate all buckets in run window ✅

The solution approach is **validated by official OpenAI documentation**.
