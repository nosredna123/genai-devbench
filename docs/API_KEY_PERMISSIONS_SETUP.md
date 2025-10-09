# API Key Permissions Setup Guide

## Issue: 401 Unauthorized - Missing `api.usage.read` Scope

### Error Message

```
{
  "error": {
    "message": "You have insufficient permissions for this operation. Missing scopes: api.usage.read. 
                Check that you have the correct role in your organization, and if you're using a restricted 
                API key, that it has the necessary scopes.",
    "type": "invalid_request_error",
    "param": null,
    "code": null
  }
}
```

### Root Cause

The `OPEN_AI_KEY_ADM` API key (service account key) does not have the **`api.usage.read`** scope required to access the OpenAI Usage API endpoint (`/v1/organization/usage/completions`).

---

## Solution

You have **two options**:

### Option 1: Grant Scope to Existing Service Account (Recommended)

1. **Go to OpenAI Platform**: https://platform.openai.com/settings/organization/api-keys

2. **Find the service account key**:
   - Look for the key starting with `sk-svcacct-...`
   - Current key: `sk-svcacct-VziaonHkns7QevkViR0L...`

3. **Edit the key permissions**:
   - Click on the key name
   - Find the "Permissions" or "Scopes" section
   - **Enable**: `api.usage.read` scope
   - Save changes

4. **Test the fix**:
   ```bash
   source .venv/bin/activate
   set -a && source .env && set +a
   python test_usage_api.py
   ```

### Option 2: Create New Service Account with Correct Scope

1. **Go to OpenAI Platform**: https://platform.openai.com/settings/organization/api-keys

2. **Create new service account**:
   - Click "Create new secret key"
   - Select "Service account" type
   - Name: `baes-usage-tracker` (or similar)
   - **Required scopes**:
     - ✅ `api.usage.read` - Access usage API
   - Optional scopes:
     - `api.organization.read` - Read organization details
   - Click "Create secret key"

3. **Copy the new key** (starts with `sk-svcacct-...`)

4. **Update `.env` file**:
   ```bash
   # Replace the old key with the new one
   OPEN_AI_KEY_ADM=sk-svcacct-<your-new-key-here>
   ```

5. **Test the fix**:
   ```bash
   source .venv/bin/activate
   set -a && source .env && set +a
   python test_usage_api.py
   ```

---

## Verification Steps

### 1. Test API Key Directly

```bash
source .venv/bin/activate
set -a && source .env && set +a

# Test Usage API access
curl "https://api.openai.com/v1/organization/usage/completions?start_time=1728476220&limit=1" \
  -H "Authorization: Bearer $OPEN_AI_KEY_ADM"
```

**Expected (Success)**:
```json
{
  "object": "page",
  "data": [
    {
      "object": "bucket",
      "start_time": 1728432000,
      "end_time": 1728518400,
      "results": [...]
    }
  ],
  "has_more": false
}
```

**Expected (Failure - before fix)**:
```json
{
  "error": {
    "message": "You have insufficient permissions for this operation. Missing scopes: api.usage.read...",
    "type": "invalid_request_error"
  }
}
```

### 2. Run Test Script

```bash
python test_usage_api.py
```

**Expected Output (After Fix)**:
```
================================================================================
Testing OpenAI Usage API Token Counting
================================================================================

Querying usage for last hour:
  Start: 1728476220 (Wed Oct  9 11:17:00 2025)
  End:   1728479820 (Wed Oct  9 12:17:00 2025)
  Model: gpt-5-mini
  API Key Env: OPEN_AI_KEY_ADM (admin key with org permissions)

Results:
  Input tokens:  12,345
  Output tokens: 5,678
  Total tokens:  18,023

  Estimated cost: $0.0145
    Input:  $0.0031
    Output: $0.0114

✅ SUCCESS: Token counting working!
```

### 3. Run Smoke Test

```bash
./run_tests.sh smoke
```

After the test completes, check that token counts appear in the output instead of zeros.

---

## Required API Key Scopes

### Admin Key (`OPEN_AI_KEY_ADM`)

**Required Scopes**:
- ✅ **`api.usage.read`** - Read organization usage data (Usage API)

**Optional but Recommended**:
- `api.organization.read` - Read organization details

**Not Required**:
- ❌ `api.model.request` - Make model requests (handled by framework keys)
- ❌ `api.fine_tuning.read/write` - Fine-tuning operations

### Framework Keys (e.g., `OPENAI_API_KEY_CHATDEV`)

**Required Scopes**:
- ✅ **`api.model.request`** - Make chat completions, embeddings, etc.

**Not Required**:
- ❌ `api.usage.read` - Usage API access (handled by admin key)
- ❌ `api.organization.read` - Organization details

---

## Troubleshooting

### Issue: Still getting 401 after granting scope

**Possible causes**:
1. Scope change not yet propagated (wait 1-2 minutes)
2. Wrong API key in `.env` file
3. `.env` file not loaded

**Debug steps**:
```bash
# 1. Verify the key is loaded
echo $OPEN_AI_KEY_ADM

# 2. Check if it starts with sk-svcacct-
# Should output: sk-svcacct-VziaonHkns7QevkViR0L...

# 3. Reload environment
set -a && source .env && set +a

# 4. Test again
python test_usage_api.py
```

### Issue: Getting different error

**Error**: `403 Forbidden`

**Cause**: User doesn't have org admin permissions

**Solution**: Ask organization admin to:
1. Grant you "Owner" or "Admin" role in the organization
2. Or create the service account key for you with correct scopes

---

**Error**: `429 Too Many Requests`

**Cause**: Rate limit exceeded

**Solution**: Wait a few seconds and retry. Usage API has generous rate limits.

---

## Reference

### OpenAI Platform URLs

- **API Keys Management**: https://platform.openai.com/settings/organization/api-keys
- **Usage Dashboard**: https://platform.openai.com/usage
- **API Documentation**: https://platform.openai.com/docs/api-reference/usage

### Key Formats

- **Service Account**: `sk-svcacct-...` (recommended for server/automation)
- **Project Key**: `sk-proj-...` (for specific projects, less permissions)
- **User Key**: `sk-...` (legacy, not recommended)

### Scope Names

- `api.usage.read` - Read usage data (required for this project)
- `api.organization.read` - Read org details
- `api.model.request` - Make API calls to models
- `api.fine_tuning.read` - Read fine-tuning jobs
- `api.fine_tuning.write` - Create fine-tuning jobs

---

## Summary

✅ **To enable token counting**:
1. Grant `api.usage.read` scope to `OPEN_AI_KEY_ADM`
2. Test with: `python test_usage_api.py`
3. Verify tokens appear in smoke test

⚠️ **Important**: Without this scope, token counting will return (0, 0) but experiments will still run successfully. Token counting is non-blocking.
