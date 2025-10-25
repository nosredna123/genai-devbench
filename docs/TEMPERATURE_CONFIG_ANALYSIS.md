# Temperature Configuration Analysis

**Date**: October 25, 2025  
**Decision**: Keep frameworks with their default temperature settings  
**Rationale**: Compare frameworks as-is for realistic, honest evaluation

## Decision Summary

After analysis, we decided **NOT** to force `temperature=0` across all frameworks. Instead:

✅ **All frameworks use their internal defaults** (may vary)  
✅ **GHSpec uses BaseAdapter default** (temperature=0)  
✅ **Honest methodology** - compares real-world framework behavior  
✅ **Documented limitation** - temperature may vary between frameworks

## Rationale

### Why NOT Force temperature=0?

1. **Realistic Comparison**: Frameworks are compared in their default state, as users would actually use them
2. **Less Invasive**: Avoids patching framework internals or modifying configuration files
3. **Honest Methodology**: Acknowledges that different frameworks have different defaults
4. **Simpler Maintenance**: No need to track and update framework config files
5. **Real Characteristic**: Temperature defaults are part of each framework's design decisions

### Trade-offs Accepted

| Aspect | Impact | Mitigation |
|--------|--------|-----------|
| **Reproducibility** | Frameworks with temp>0 may vary between runs | Document as known limitation; use multiple runs for statistical analysis |
| **Fair Comparison** | Different temperatures affect output quality/creativity | Document temperature settings in methodology; compare frameworks "as designed" |
| **Scientific Rigor** | Less controlled experiment | Trade-off for ecological validity (real-world usage) |

## Current State

| Framework | Temperature Setting | Method | Notes |
|-----------|-------------------|--------|-------|
| **GHSpec** | 0 (default) | `BaseAdapter.call_openai_chat_completion()` | Uses base adapter default |
| **ChatDev** | Framework default (unknown) | Internal OpenAI integration | Likely 0.7-1.0 based on docs |
| **BAeS** | Framework default (unknown) | Internal OpenAI integration | Unknown |

## Implementation Details

### GHSpec Adapter

**Location**: `src/adapters/ghspec_adapter.py:659-665`

```python
return self.call_openai_chat_completion(
    system_prompt=system_prompt,
    user_prompt=user_prompt,
    model="gpt-4o-mini"
    # Note: temperature not specified - uses BaseAdapter default (0 for consistency)
)
```

### BaseAdapter Default

**Location**: `src/adapters/base_adapter.py:211-212`

```python
# Use provided temperature or default to 0 (deterministic)
temp_value = temperature if temperature is not None else 0
```

**Note**: GHSpec gets `temperature=0` because it uses the base adapter method which defaults to 0. This is acceptable because:
- It's the base adapter's design choice
- GHSpec is designed for deterministic spec generation
- It's documented and consistent

## Methodology Documentation

This decision should be documented in experiment methodology:

### Recommended Documentation

```markdown
## Temperature Configuration

The frameworks use their default temperature settings:

- **GHSpec**: temperature=0 (deterministic, via BaseAdapter)
- **ChatDev**: Framework default (estimated 0.7-1.0)
- **BAeS**: Framework default (unknown)

**Rationale**: We compare frameworks in their default state to evaluate
real-world performance. While this means temperature varies between
frameworks, it provides an honest comparison of how developers would
actually use these tools.

**Impact**: Frameworks with temperature>0 may produce slightly different
outputs on repeated runs. This is mitigated by running multiple experiments
and analyzing statistical trends rather than single-run results.
```

## Alternative Approaches Considered

### ❌ Option 1: Force temperature=0 Everywhere
**Rejected because**:
- Requires patching ChatDev's `ChatChainConfig.json`
- Requires patching BAeS internal configuration (may not be exposed)
- Creates maintenance burden
- May break framework functionality
- Doesn't reflect real-world usage

### ❌ Option 2: Add Config Override
**Rejected because**:
- High implementation effort
- Requires modifying framework files or monkey-patching
- Increases complexity
- May have unexpected side effects

### ✅ Option 3: Accept Defaults (CHOSEN)
**Accepted because**:
- Simple to implement
- Honest about limitations
- Compares frameworks as-designed
- Low maintenance
- Realistic evaluation

## Related Files

- `src/adapters/base_adapter.py` - Generic `call_openai_chat_completion()` with default temp=0
- `src/adapters/ghspec_adapter.py` - Uses base adapter (inherits temp=0)
- `src/adapters/chatdev_adapter.py` - Uses internal config (temp unknown)
- `src/adapters/baes_adapter.py` - Uses internal config (temp unknown)
- `docs/chatdev_integration.md:313-328` - Original temperature question
- `docs/REMAINING_HARDCODED_VALUES.md:287-306` - Notes framework defaults

## Conclusion

**Decision**: Keep frameworks with their default temperature settings.  
**Result**: Honest, realistic comparison with documented limitations.  
**Status**: ✅ Implementation complete, documentation updated.
