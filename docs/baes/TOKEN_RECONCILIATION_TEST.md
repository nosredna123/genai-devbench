# Token Reconciliation Test Plan

**Date**: October 16, 2025  
**Run ID**: 801758a3-dbda-4fc5-8d7f-fd1c916d7617  
**Objective**: Test token tracking and reconciliation workflow from scratch

---

## Executive Summary

Fresh BAEs experiment completed successfully to test token reconciliation.

**Status**: ✅ Experiment Complete | ⏳ Awaiting Reconciliation (30+ min delay)

---

## Experiment Results

### Run Overview
- **Run ID**: `801758a3-dbda-4fc5-8d7f-fd1c916d7617`
- **Start Time**: 2025-10-16T12:29:31.455006Z
- **End Time**: 2025-10-16T12:33:29.940848Z
- **Duration**: 3m 58s (238.5 seconds)
- **Status**: All 6 steps completed successfully ✅

### Step Performance

| Step | Task | Duration | Status | Tokens |
|------|------|----------|--------|--------|
| 1 | Create CRUD entities | 121.8s | ✅ | 0 (pending) |
| 2 | Add enrollment | 41.6s | ✅ | 0 (pending) |
| 3 | Teacher assignment | 56.2s | ✅ | 0 (pending) |
| 4 | Validation | 4.8s | ✅ | 0 (pending) |
| 5 | Pagination | 6.8s | ✅ | 0 (pending) |
| 6 | User Interface | 7.3s | ✅ | 0 (pending) |

### Aggregate Metrics

```json
{
  "UTT": 6,           // Total tasks: 6
  "HIT": 0,           // Human interventions: 0
  "AUTR": 1.0,        // Autonomy: 100%
  "HEU": 0,           // Human effort: 0
  "TOK_IN": 0,        // ⏳ Pending reconciliation
  "TOK_OUT": 0,       // ⏳ Pending reconciliation
  "T_WALL_seconds": 238.49,
  "ZDI": 48,          // Zero-downtime incidents
  "verification_status": "pending"
}
```

---

## Token Reconciliation Test

### The Problem
Previous BAEs runs consistently showed `TOK_IN: 0` and `TOK_OUT: 0` despite:
- ✅ Code being successfully generated
- ✅ All steps completing
- ✅ OpenAI API being used (OPENAI_API_KEY_BAES configured)

### Root Cause Hypotheses

**Hypothesis 1: OpenAI Usage API Delay**
- OpenAI Usage API has 5-60 minute reporting delay
- Data may not be available immediately after run completes
- Need to wait 30+ minutes before reconciliation

**Hypothesis 2: API Key Permissions**
- OPENAI_API_KEY_BAES may lack `api.usage.read` scope
- Usage API requires specific permission to read token data
- Default API keys may not have this enabled

**Hypothesis 3: Timestamp Format Issues**
- Previous reconciliation attempts showed 400 errors
- Error pattern: `start_time=1760612579.9374144&end_time=1760612579.9392114`
- OpenAI API may reject microsecond-level time windows
- Need to verify proper timestamp formatting (Unix epoch with appropriate granularity)

**Hypothesis 4: API Key Isolation**
- OPENAI_API_KEY_BAES is separate from OPENAI_API_KEY_USAGE_TRACKING
- Reconciliation script uses OPENAI_API_KEY_USAGE_TRACKING to query usage
- Different API keys may not track each other's usage

### Test Plan

#### Phase 1: Wait Period ⏳
**Timing**: 30-60 minutes after run completion (12:33 UTC)  
**Action**: Allow OpenAI Usage API to process and make data available  
**Expected**: Data becomes queryable via Usage API

#### Phase 2: Run Reconciliation 🔄
**Command**: `bash runners/reconcile_usage.sh`  
**Expected Outcomes**:

**✅ Success Case**:
```json
{
  "status": "verified",
  "total_tokens_in": 50000,  // Actual token count
  "total_tokens_out": 15000,  // Actual token count
  "verification_message": "Data stable across X minute interval"
}
```

**❌ Failure Case 1: Data Not Available**
```json
{
  "status": "data_not_available",
  "total_tokens_in": 0,
  "total_tokens_out": 0,
  "message": "No token data available from Usage API yet"
}
```
**Action**: Wait longer, retry in 30 minutes

**❌ Failure Case 2: API Error**
```
"Failed to fetch usage from OpenAI API: 400 Bad Request"
```
**Action**: Investigate API key permissions and timestamp formatting

**❌ Failure Case 3: Wrong API Key**
```json
{
  "total_tokens_in": 0,
  "total_tokens_out": 0
}
```
**Reason**: OPENAI_API_KEY_USAGE_TRACKING can't see OPENAI_API_KEY_BAES usage  
**Action**: Modify reconciliation to use correct API key

#### Phase 3: Analysis 🔍
**Actions**:
1. Compare with ChatDev/GHSpec runs (they show verified tokens)
2. Check if API key mismatch is the issue
3. Verify timestamp formatting in API requests
4. Test with manual OpenAI Usage API query

---

## Known Good Reference Data

For comparison, these runs successfully tracked tokens:

| Run ID | Framework | Tokens In | Tokens Out | Status |
|--------|-----------|-----------|------------|--------|
| d7982980 | ChatDev | 264,373 | 76,824 | ✅ Verified |
| d8d76027 | ChatDev | 217,055 | 74,482 | ✅ Verified |
| 02b41485 | GHSpec | 59,040 | 23,542 | ✅ Verified |
| d95b777a | GHSpec | 2,503 | 925 | ✅ Verified |

**Key Question**: Why do ChatDev/GHSpec work but BAEs doesn't?

**Possible Answer**: Different API keys
- ChatDev/GHSpec may use OPENAI_API_KEY_USAGE_TRACKING
- BAEs uses OPENAI_API_KEY_BAES
- Reconciliation script queries with OPENAI_API_KEY_USAGE_TRACKING
- Can't see usage from OPENAI_API_KEY_BAES

---

## Next Steps

### Immediate (After 30 min wait)
1. ⏰ Wait until ~13:05 UTC (30 minutes after completion)
2. 🔄 Run `bash runners/reconcile_usage.sh`
3. 📊 Check if tokens are now populated
4. 📝 Document results

### If Tokens Still Show 0
1. Check API key configuration:
   ```bash
   echo $OPENAI_API_KEY_BAES
   echo $OPENAI_API_KEY_USAGE_TRACKING
   ```
2. Verify API key permissions on OpenAI dashboard
3. Test manual API query with curl:
   ```bash
   curl https://api.openai.com/v1/organization/usage/completions \
     -H "Authorization: Bearer $OPENAI_API_KEY_USAGE_TRACKING" \
     -G \
     --data-urlencode "start_time=1760617771" \
     --data-urlencode "end_time=1760618010" \
     --data-urlencode "bucket_width=1d"
   ```
4. Investigate reconciler code for API key usage
5. Consider using same API key for both execution and tracking

### If Reconciliation Succeeds
1. ✅ Verify token counts are reasonable
2. 📊 Compare with typical ChatDev/GHSpec token usage
3. 📝 Document successful reconciliation workflow
4. 🎉 Mark token tracking issue as resolved

---

## Timeline

- **12:29 UTC**: Experiment started
- **12:33 UTC**: Experiment completed
- **13:05 UTC**: Earliest reconciliation attempt (30 min)
- **13:33 UTC**: Recommended reconciliation time (60 min)

---

## Success Criteria

✅ **Pass**: Tokens > 0 after reconciliation  
❌ **Fail**: Tokens still 0 after 60+ minutes  
⚠️ **Partial**: API errors but can diagnose root cause

---

**Next Action**: Wait until 13:05 UTC, then run reconciliation script

**Author**: GitHub Copilot  
**Status**: ⏳ IN PROGRESS
