# Real OpenAI Usage API Data Analysis

## CSV File Structure

**File:** `completions_usage_2025-10-27_2025-10-27.csv`

### Key Observations

#### 1. Time Buckets Are EXACTLY 1 Minute (60 seconds)

```csv
start_time,end_time,start_time_iso,end_time_iso,...
1761523200,1761523260,2025-10-27T00:00:00+00:00,2025-10-27T00:01:00+00:00,...
1761523260,1761523320,2025-10-27T00:01:00+00:00,2025-10-27T00:02:00+00:00,...
1761523320,1761523380,2025-10-27T00:02:00+00:00,2025-10-27T00:03:00+00:00,...
```

**Calculation:** 1761523260 - 1761523200 = 60 seconds ✅

Each row represents a **1-minute bucket** with aggregated usage for that minute.

#### 2. Multiple Rows Can Exist for Same Time Bucket

**Example - 00:10:00 to 00:11:00:**

```csv
1761523800,1761523860,2025-10-27T00:10:00+00:00,2025-10-27T00:11:00+00:00,proj_...,3.0,...,key_3QRCYbJRFQ0G4ycm,...,4212,1673,...
1761523800,1761523860,2025-10-27T00:10:00+00:00,2025-10-27T00:11:00+00:00,proj_...,3.0,...,key_Y0r9whvwK8Gilt6s,...,5904,1419,...
```

**Why:** Different `api_key_id` values! The API returns separate rows when grouped by API key.

**Total for 00:10-00:11:**
- key_3QRCYbJRFQ0G4ycm: 4,212 input + 1,673 output
- key_Y0r9whvwK8Gilt6s: 5,904 input + 1,419 output
- **Bucket total:** 10,116 input + 3,092 output

#### 3. Another Example - 00:14:00 to 00:15:00

```csv
1761524040,1761524100,2025-10-27T00:14:00+00:00,2025-10-27T00:15:00+00:00,...,25.0,...,key_TrCdJcJYEpJnxEzh,...,15738,1482,...
1761524040,1761524100,2025-10-27T00:14:00+00:00,2025-10-27T00:15:00+00:00,...,1.0,...,key_Y0r9whvwK8Gilt6s,...,1816,1168,...
```

**Bucket total:** 15,738 + 1,816 = 17,554 input tokens

#### 4. Token Fields in CSV

```
input_tokens: Total input tokens (includes cached)
output_tokens: Total output tokens
input_cached_tokens: Subset of input_tokens that were cached
input_uncached_tokens: input_tokens - input_cached_tokens
num_model_requests: Number of API calls in this bucket
```

#### 5. Cached Tokens Example

**00:04:00 to 00:05:00:**
```csv
input_tokens: 7162
input_cached_tokens: 1280
input_uncached_tokens: 5882
```

**Validation:** 5,882 + 1,280 = 7,162 ✅

## Critical Insights for Our Implementation

### 1. We MUST Aggregate Multiple Rows per Bucket

If querying with `group_by=api_key_id` (or any grouping), each bucket can have multiple rows:

```python
# WRONG - takes first row only
tokens = bucket['results'][0]['input_tokens']

# CORRECT - sum all rows in bucket
tokens = sum(r['input_tokens'] for r in bucket['results'])
```

Our current code at line 110-143 does this correctly:

```python
for bucket in usage_data.get("data", []):
    for result in bucket.get("results", []):
        tokens_in, tokens_out, api_calls, cached_tokens = _extract_tokens(result)
        total_input_tokens += tokens_in
        total_output_tokens += tokens_out
```

✅ **This is correct!**

### 2. Bucket Boundaries Are HARD (Minute Aligned)

Every bucket starts at :00 seconds and ends at :59 seconds:
- 00:00:00 - 00:01:00
- 00:01:00 - 00:02:00
- etc.

**Our sprint timestamps:**
```
Sprint 1: 21:41:05 - 21:41:41 (spans parts of TWO buckets)
  ├─ 21:41:00-21:42:00 bucket (6 seconds of sprint start + 41 seconds)
  └─ 21:42:00-21:43:00 bucket (0 seconds - but API response processing!)
```

### 3. No Way to Get Sub-Minute Granularity

The CSV confirms: minimum granularity is **1 minute**. There's no `bucket_width="1s"` option.

**For a 30-second sprint:**
- Can't query just those 30 seconds
- Must query the full minute bucket(s) that overlap
- Will capture other API calls in same bucket(s)

### 4. API Key Grouping Impact

The data shows different API keys in same time buckets. If we query without specifying `api_key_id` filter:

**Query for 00:10:00-00:11:00 returns:**
```
key_3QRCYbJRFQ0G4ycm: 4,212 tokens
key_Y0r9whvwK8Gilt6s: 5,904 tokens
Total: 10,116 tokens
```

**For our use case:** We use a single admin key (`OPEN_AI_KEY_ADM`) to query, but frameworks use different keys (OPENAI_API_KEY_BAES, etc.) during execution.

**Critical question:** Does the CSV data come from querying with the admin key? If so, does it show ALL organization usage, or filtered by the querying key?

From the OpenAI docs:
> "api_key_ids array Optional - Return only usage for these API keys"

This means: Without filtering, we get ALL usage for the entire organization in that time window!

### 5. Time Window Isolation is CRITICAL

**Scenario:**
- BAeS run: 21:41:05 - 21:44:44
- ChatDev run (different experiment): 21:42:00 - 21:45:30

**Query BAeS run (21:41:05-21:44:44) returns buckets:**
```
21:41:00-21:42:00: BAeS only
21:42:00-21:43:00: BAeS + ChatDev mixed! ❌
21:43:00-21:44:00: BAeS + ChatDev mixed! ❌
21:44:00-21:45:00: BAeS partial + ChatDev
```

**We get contaminated data if runs overlap!**

## Validation of Our Solution

### ✅ What Works

1. **Run-level queries with minute buckets:**
   ```python
   params = {
       "start_time": run_start,  # 21:41:05
       "end_time": run_end,      # 21:44:44
       "bucket_width": "1m"
   }
   ```
   Returns all buckets spanning the run, aggregate them = run total ✅

2. **Aggregation logic:**
   Current code sums all results across all buckets ✅

3. **API key filtering:**
   We should add `api_key_ids` parameter to filter to just the framework's key!

### ❌ What Doesn't Work

1. **Per-sprint attribution:**
   Sprints span multiple buckets, buckets contain multiple sprints
   → Impossible to separate! ❌

2. **Daily buckets (current bug):**
   CSV shows minute-level data is available, but our code uses `bucket_width="1d"`
   → Returns daily total for all sprints ❌

3. **Overlapping runs:**
   If multiple frameworks run simultaneously, their tokens mix in shared buckets
   → Need strict time isolation OR api_key filtering ❌

## Recommendations

### Immediate Fixes

1. **Change bucket_width from "1d" to "1m"** (as spec requires)

2. **Add API key filtering** to prevent cross-contamination:
   ```python
   params = {
       "start_time": run_start,
       "end_time": run_end,
       "bucket_width": "1m",
       "api_key_ids": [framework_api_key_id]  # ← ADD THIS
   }
   ```

3. **Update limit parameter:**
   ```python
   "limit": 1440  # 24 hours at 1-minute buckets
   ```

### Spec Updates Needed

Add to **FR-001** or create **FR-011**:
> "System MUST filter Usage API queries by framework-specific api_key_id to prevent cross-contamination when multiple runs execute in overlapping time windows"

Add to **Dependencies** section:
> "Framework-specific API keys must have unique identifiers for usage attribution (OPENAI_API_KEY_BAES, OPENAI_API_KEY_CHATDEV, OPENAI_API_KEY_GHSPEC)"

## Final Validation

The CSV data **confirms**:

✅ Minute-level buckets exist and are the finest granularity  
✅ Buckets align to clock minutes (:00-:59)  
✅ Multiple API keys can appear in same bucket  
✅ Aggregation across bucket results is required  
❌ Sub-minute tracking is impossible  
❌ Per-sprint attribution cannot work reliably  
✅ Run-level totals with bucket aggregation is the correct approach  

**Our spec is validated, with one addition: API key filtering is essential!**
