# API Contract: BaseAdapter

**Component**: `src/adapters/base_adapter.py`  
**Type**: Abstract Base Class  
**Consumer**: Framework adapters (BAeSAdapter, ChatDevAdapter, GHSpecAdapter)

---

## Method: execute_step

**Purpose**: Execute a single step/sprint in the framework

**Signature**:
```python
@abstractmethod
def execute_step(
    self,
    step_num: int,
    command_text: str
) -> Dict[str, Any]:
    """
    Execute a framework step with timing and interaction tracking.
    
    Args:
        step_num: Step number (1-indexed)
        command_text: Natural language command or prompt for this step
        
    Returns:
        dict: Step metrics (timing and interactions, NO tokens)
        
    Structure:
        {
            'success': bool,              # Step completed successfully
            'duration_seconds': float,    # Execution time
            'start_timestamp': int,       # Unix seconds when started
            'end_timestamp': int,         # Unix seconds when ended
            'hitl_count': int,            # Human interventions
            'retry_count': int            # Retry attempts
        }
        
    Raises:
        RuntimeError: If framework execution fails
        TimeoutError: If execution exceeds timeout
    """
```

**Contract**:
- MUST capture `start_timestamp` BEFORE calling framework subprocess
- MUST capture `end_timestamp` AFTER subprocess returns
- MUST NOT return token counts (removed from return value)
- MUST track timing metrics accurately (duration, timestamps)
- MUST track interaction metrics (HITL count, retries)
- MUST fail immediately if framework execution fails (no silent recovery)

**Breaking Change**: Removed fields from return value:
- `tokens_in` (no longer returned)
- `tokens_out` (no longer returned)
- `api_calls` (no longer returned)
- `cached_tokens` (no longer returned)

---

## Method: validate_api_key (New)

**Purpose**: Validate framework has unique API key configured

**Signature**:
```python
def validate_api_key(self) -> None:
    """
    Validate that framework has unique API key and key ID configured.
    
    Raises:
        KeyError: If API key or key ID environment variable missing
        ValueError: If key ID format invalid
        RuntimeError: If API key is shared with another framework
    """
```

**Behavior**:
1. Check `OPENAI_API_KEY_{FRAMEWORK}` exists
2. Check `OPENAI_API_KEY_{FRAMEWORK}_ID` exists
3. Validate key ID format: `key_[A-Za-z0-9]{12,}`
4. Optionally check uniqueness across frameworks

**Contract**:
- MUST be called during adapter initialization (in `start()`)
- MUST fail immediately if validation fails (no defaults)
- MUST enforce unique API keys per framework (FR-011)

---

## Removed Methods

### ~~fetch_usage_from_openai~~ (DEPRECATED)

**Reason**: Token reconciliation moved to post-run process (UsageReconciler)

**Migration**: Remove calls to this method from adapters. Tokens are now reconciled via:
```python
# OLD (removed):
tokens_in, tokens_out, api_calls, cached_tokens = self.fetch_usage_from_openai(...)

# NEW (post-run reconciliation):
# No action needed in adapter - UsageReconciler handles this after run completes
```

---

## Example Implementation (BAeSAdapter)

```python
class BAeSAdapter(BaseAdapter):
    def start(self) -> None:
        """Initialize adapter and validate configuration."""
        # ... existing initialization ...
        
        # NEW: Validate API key configuration
        self.validate_api_key()
        
    def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
        """Execute BAeS step with timing tracking only."""
        start_time = time.time()
        start_timestamp = int(time.time())  # Captured BEFORE subprocess
        
        try:
            # Execute framework via subprocess
            result = self._execute_kernel_request(
                request=command_text,
                start_servers=(step_num == 1)
            )
            
            success = result.get('success', False)
            
        except Exception as e:
            logger.error(f"Step {step_num} failed: {e}")
            success = False
        
        duration = time.time() - start_time
        end_timestamp = int(time.time())  # Captured AFTER subprocess
        
        # Return timing and interaction metrics ONLY
        return {
            'success': success,
            'duration_seconds': duration,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp,
            'hitl_count': 0,
            'retry_count': 0
            # ✅ NO token fields
        }
```

---

## Environment Variables Contract

Each adapter MUST use framework-specific environment variables:

| Framework | Execution Key | Key ID |
|-----------|--------------|--------|
| BAeS | `OPENAI_API_KEY_BAES` | `OPENAI_API_KEY_BAES_ID` |
| ChatDev | `OPENAI_API_KEY_CHATDEV` | `OPENAI_API_KEY_CHATDEV_ID` |
| GHSpec | `OPENAI_API_KEY_GHSPEC` | `OPENAI_API_KEY_GHSPEC_ID` |

**Validation** (via `validate_api_key()`):
```python
def validate_api_key(self) -> None:
    framework = self.__class__.__name__.replace('Adapter', '').upper()
    
    key_var = f'OPENAI_API_KEY_{framework}'
    key_id_var = f'OPENAI_API_KEY_{framework}_ID'
    
    if not os.getenv(key_var):
        raise KeyError(f"{key_var} environment variable required")
    
    if not os.getenv(key_id_var):
        raise KeyError(f"{key_id_var} environment variable required")
    
    key_id = os.getenv(key_id_var)
    if not re.match(r'^key_[A-Za-z0-9]{12,}$', key_id):
        raise ValueError(f"{key_id_var} has invalid format: {key_id}")
```

---

## Timing Contract

**Critical for accurate run-level reconciliation**:

```python
# CORRECT timing capture:
start_timestamp = int(time.time())  # ← BEFORE subprocess.run()
result = subprocess.run(...)        # ← Framework execution
end_timestamp = int(time.time())    # ← AFTER subprocess.run() returns

# INCORRECT (would miss tokens):
result = subprocess.run(...)
start_timestamp = int(time.time())  # ❌ Too late
end_timestamp = int(time.time())
```

**Rationale**: Timestamps define the query window for Usage API reconciliation. Must capture subprocess execution boundaries accurately.

---

## Breaking Changes Summary

1. **REMOVED**: `fetch_usage_from_openai()` method (use UsageReconciler instead)
2. **CHANGED**: `execute_step()` return value no longer includes token fields
3. **ADDED**: `validate_api_key()` method (must be called in `start()`)
4. **CHANGED**: Adapters must capture `start_timestamp`/`end_timestamp` around subprocess execution

---

## Migration Checklist

For each adapter (BAeSAdapter, ChatDevAdapter, GHSpecAdapter):

- [ ] Remove `fetch_usage_from_openai()` calls from `execute_step()`
- [ ] Update `execute_step()` return dict to remove token fields
- [ ] Add `validate_api_key()` call to `start()` method
- [ ] Verify timestamps captured around subprocess.run()
- [ ] Update tests to not expect token fields from `execute_step()`

---

## Version

**Contract Version**: 2.0.0  
**Breaking**: Yes (method removal, return value change)  
**Compatible With**: metrics.json schema v2.0 (post-fix)
