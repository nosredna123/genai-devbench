# API Key Architecture

## Overview

This project uses a **two-tier API key system** to separate execution permissions from usage tracking permissions.

## API Key Tiers

### 1. Admin Key (Organization-Level) 🔑

**Environment Variable**: `OPEN_AI_KEY_ADM`

**Purpose**: Query the OpenAI Usage API for token counting across all frameworks

**Permissions Required**:
- Organization-level access
- Can query `/v1/organization/usage/completions` endpoint
- Can view usage data for entire organization

**Used By**:
- `BaseAdapter.fetch_usage_from_openai()` method
- All framework adapters (ChatDev, GHSpec, BAEs) for token tracking

**Why Organization-Level?**
The Usage API endpoint (`/v1/organization/usage/completions`) requires organization-level permissions that standard project keys don't have.

---

### 2. Framework Keys (Project-Level) 🔐

**Environment Variables**:
- `OPENAI_API_KEY_CHATDEV` - ChatDev framework
- `OPENAI_API_KEY_GHSPEC` - GitHub Spec-kit framework
- `OPENAI_API_KEY_BAES` - BAEs framework

**Purpose**: Execute framework-specific LLM operations

**Permissions Required**:
- Standard project-level access
- Can call chat completions, embeddings, etc.
- **Cannot** query Usage API (lacks org permissions)

**Used By**:
- Individual frameworks for their LLM operations
- ChatDev: Passed via `OPENAI_API_KEY` environment variable
- GHSpec: TBD
- BAEs: TBD

**Why Separate Keys?**
- Enables independent tracking per framework
- Allows separate billing/quota management
- Isolates framework-specific API usage

## Key Usage Flow

```
┌─────────────────────────────────────────────────────────────┐
│ Experiment Execution                                        │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │ Framework Execution           │
         │ (e.g., ChatDev)               │
         │                               │
         │ Uses: OPENAI_API_KEY_CHATDEV  │ ← Framework Key
         │                               │    (project-level)
         │ - Chat completions            │
         │ - Embeddings                  │
         │ - Other LLM operations        │
         └───────────────────────────────┘
                         │
                         ▼
         ┌───────────────────────────────┐
         │ Token Counting                │
         │ (BaseAdapter)                 │
         │                               │
         │ Uses: OPEN_AI_KEY_ADM         │ ← Admin Key
         │                               │    (org-level)
         │ - Query Usage API             │
         │ - Get token counts            │
         │ - Aggregate metrics           │
         └───────────────────────────────┘
```

## Configuration

### .env File

```bash
# Admin Key (for overall usage tracking)
OPEN_AI_KEY_ADM=sk-svcacct-VziaonHkns...

# BAEs Framework
OPENAI_API_KEY_BAES=sk-proj-OpISHqiUYt...

# ChatDev Framework
OPENAI_API_KEY_CHATDEV=sk-proj-GvVfYDPs8a...

# GitHub Spec-kit Framework
OPENAI_API_KEY_GHSPEC=sk-proj-2-llx3yW6Ce...
```

### Code Usage

**Framework Execution** (uses framework key):
```python
# In chatdev_adapter.py
env = os.environ.copy()
env['OPENAI_API_KEY'] = os.getenv(self.config.get('api_key_env'))
# ChatDev uses this key for LLM operations
```

**Token Counting** (uses admin key):
```python
# In chatdev_adapter.py (and all other adapters)
tokens_in, tokens_out = self.fetch_usage_from_openai(
    api_key_env_var='OPEN_AI_KEY_ADM',  # Always use admin key
    start_timestamp=self._step_start_time,
    end_timestamp=end_timestamp,
    model=model_config
)
```

## Verification

### Test Admin Key Permissions

```bash
# Verify admin key can access Usage API
curl "https://api.openai.com/v1/organization/usage/completions?start_time=1728476220&limit=1" \
  -H "Authorization: Bearer $OPEN_AI_KEY_ADM"
```

**Expected**: JSON response with usage data

**If 403 Forbidden**: Key lacks organization permissions

### Test Framework Key (Should Fail)

```bash
# Verify framework key CANNOT access Usage API
curl "https://api.openai.com/v1/organization/usage/completions?start_time=1728476220&limit=1" \
  -H "Authorization: Bearer $OPENAI_API_KEY_CHATDEV"
```

**Expected**: 403 Forbidden (this is correct!)

Framework keys should NOT have org permissions.

## Common Issues

### Issue: Token counting returns (0, 0)

**Cause**: Using framework key instead of admin key

**Solution**:
```python
# ❌ Wrong - framework key lacks permissions
tokens_in, tokens_out = self.fetch_usage_from_openai(
    api_key_env_var='OPENAI_API_KEY_CHATDEV',  # Wrong!
    ...
)

# ✅ Correct - admin key has org permissions
tokens_in, tokens_out = self.fetch_usage_from_openai(
    api_key_env_var='OPEN_AI_KEY_ADM',  # Correct!
    ...
)
```

### Issue: 403 Forbidden when querying Usage API

**Cause**: API key lacks organization-level permissions

**Solution**: Use `OPEN_AI_KEY_ADM` instead of framework-specific keys

### Issue: Want to track usage per framework

**Current Behavior**: All frameworks use same admin key, so Usage API shows aggregated usage

**Future Solution**: 
- Option 1: Use time windows to isolate framework usage
- Option 2: Create separate organizations per framework (overkill)
- Option 3: Use OpenAI's project-based billing (when available)

**Recommended**: Use time windows (already implemented in `fetch_usage_from_openai()`)

## Best Practices

### 1. Never Hard-Code API Keys ❌

```python
# ❌ BAD
api_key = "sk-proj-..."
```

### 2. Always Use Environment Variables ✅

```python
# ✅ GOOD
api_key = os.getenv('OPEN_AI_KEY_ADM')
```

### 3. Use Correct Key for Each Purpose

| Purpose | Key | Permissions |
|---------|-----|-------------|
| LLM Operations | `OPENAI_API_KEY_CHATDEV` | Project-level |
| Token Counting | `OPEN_AI_KEY_ADM` | Org-level |

### 4. Document Key Requirements

When adding new adapters, document which keys they need:

```python
class NewAdapter(BaseAdapter):
    """
    Adapter for New Framework.
    
    Required Environment Variables:
    - OPENAI_API_KEY_NEW: For LLM operations (project-level)
    - OPEN_AI_KEY_ADM: For token counting (org-level, inherited)
    """
```

## Security

### .env File

- ✅ Listed in `.gitignore`
- ✅ Never committed to repository
- ✅ Each developer has their own copy

### .env.example File

- ✅ Template with placeholder values
- ✅ Safe to commit to repository
- ✅ Documents required variables

```bash
# .env.example (safe to commit)
OPEN_AI_KEY_ADM=sk-your-admin-api-key-here
OPENAI_API_KEY_CHATDEV=sk-your-chatdev-api-key-here
```

## Migration Guide

### For Existing Adapters

If your adapter currently uses framework key for token counting:

**Before**:
```python
tokens_in, tokens_out = self.fetch_usage_from_openai(
    api_key_env_var=self.config.get('api_key_env'),  # Wrong
    ...
)
```

**After**:
```python
tokens_in, tokens_out = self.fetch_usage_from_openai(
    api_key_env_var='OPEN_AI_KEY_ADM',  # Correct
    ...
)
```

### For New Adapters

When creating a new adapter:

1. Add framework-specific key to `.env`:
   ```bash
   OPENAI_API_KEY_NEWFRAMEWORK=sk-proj-...
   ```

2. Use framework key for LLM operations:
   ```python
   env['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY_NEWFRAMEWORK')
   ```

3. Use admin key for token counting:
   ```python
   tokens_in, tokens_out = self.fetch_usage_from_openai(
       api_key_env_var='OPEN_AI_KEY_ADM',
       ...
   )
   ```

## Summary

✅ **Admin Key (`OPEN_AI_KEY_ADM`)**:
- Organization-level permissions
- Used for Usage API queries
- Shared across all frameworks
- Required for token counting

✅ **Framework Keys** (`OPENAI_API_KEY_*`):
- Project-level permissions
- Used for LLM operations
- One per framework
- Enable independent tracking

This architecture separates concerns and enables both independent framework execution and centralized usage tracking.
