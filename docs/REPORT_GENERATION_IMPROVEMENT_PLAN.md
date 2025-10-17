# Report Generation Improvement Plan

**Date:** October 17, 2025  
**Objective:** Make statistical report generation fully dynamic and configuration-driven  
**Status:** 📋 Planning Phase

## Executive Summary

The current `statistics.py` contains **45+ hardcoded values** that should be read dynamically from `config/experiment.yaml`. This plan systematically identifies all hardcoded elements and proposes a phased implementation to make the report generation flexible, maintainable, and configuration-driven.

## Current Hardcoded Values Analysis

### 1. **Configuration Values** (High Priority)

#### 1.1 Model Configuration
**Lines:** 859, 860, 899, 907, 935, 944, 955, 956
```python
# HARDCODED:
"- Model: `gpt-4o-mini` (OpenAI GPT-4 Omni Mini)"
"- Temperature: Framework default (typically 0.7-1.0)"
"- Model filter: `models=[\"gpt-4o-mini\"]`"

# SHOULD BE:
model = config['model']  # "gpt-4o-mini"
f"- Model: `{model}` (from config)"
```

**Impact:** If model changes (e.g., to `o1-mini`), report becomes inaccurate

#### 1.2 Random Seed
**Lines:** 832, 876
```python
# HARDCODED:
"- Random seed fixed at 42 for frameworks that support deterministic execution"
"- Fixed seed: `random_seed: 42`"

# SHOULD BE:
seed = config['random_seed']  # 42
f"- Random seed fixed at {seed} for frameworks that support deterministic execution"
```

#### 1.3 Timeouts
**Lines:** 873
```python
# HARDCODED:
"- 10-minute timeout per step (`step_timeout_seconds: 600`)"

# SHOULD BE:
timeout = config['timeouts']['step_timeout_seconds']  # 600
timeout_minutes = timeout // 60
f"- {timeout_minutes}-minute timeout per step (`step_timeout_seconds: {timeout}`)"
```

#### 1.4 Stopping Rule Parameters
**Lines:** 838, 839, 980, 978
```python
# HARDCODED:
"- Stopping rule: Continue until CI half-width ≤ 10% of mean (max 100 runs per framework)"
"- Bootstrap confidence intervals (10,000 resamples)"
"- **Bootstrap CI**: 95% confidence intervals with 10,000 resamples"

# SHOULD BE:
max_runs = config['stopping_rule']['max_runs']  # 100
ci_level = config['stopping_rule']['confidence_level']  # 0.95
max_hw_pct = config['stopping_rule']['max_half_width_pct']  # 10
bootstrap_samples = 10000  # From bootstrap function parameter

f"- Stopping rule: Continue until CI half-width ≤ {max_hw_pct}% of mean (max {max_runs} runs per framework)"
f"- Bootstrap confidence intervals ({bootstrap_samples:,} resamples)"
f"- **Bootstrap CI**: {int(ci_level*100)}% confidence intervals with {bootstrap_samples:,} resamples"
```

### 2. **Framework Metadata** (High Priority)

#### 2.1 Framework Descriptions
**Lines:** 797-811
```python
# HARDCODED:
"**1. ChatDev** (OpenBMB/ChatDev)"
"- Multi-agent collaborative framework with role-based AI agents"
"- Repository: `github.com/OpenBMB/ChatDev` (commit: `52edb89`)"

"**2. GHSpec** (GitHub Spec-Kit)"
"- Repository: `github.com/github/spec-kit` (commit: `89f4b0b`)"

"**3. BAEs** (Business Autonomous Entities)"
"- Repository: `github.com/gesad-lab/baes_demo` (commit: `1dd5736`)"

# SHOULD BE:
frameworks_config = config['frameworks']
for i, (fw_name, fw_config) in enumerate(frameworks_config.items(), 1):
    repo_url = fw_config['repo_url']
    commit = fw_config['commit_hash'][:7]
    description = FRAMEWORK_DESCRIPTIONS.get(fw_name, "Framework description")
    
    lines.append(f"**{i}. {fw_name.title()}**")
    lines.append(f"- {description}")
    lines.append(f"- Repository: `{repo_url}` (commit: `{commit}`)")
```

**Issue:** Framework descriptions are scattered and duplicated

#### 2.2 API Key Names
**Lines:** 865
```python
# HARDCODED:
"- API keys: `OPENAI_API_KEY_BAES`, `OPENAI_API_KEY_CHATDEV`, `OPENAI_API_KEY_GHSPEC`"

# SHOULD BE:
api_keys = [fw_config['api_key_env'] for fw_config in config['frameworks'].values()]
f"- API keys: {', '.join([f'`{key}`' for key in api_keys])}"
```

### 3. **Experimental Protocol** (Medium Priority)

#### 3.1 Task Sequence Steps
**Lines:** 845-850
```python
# HARDCODED:
"1. **Step 1**: Create CRUD application (Student/Course/Teacher with FastAPI + SQLite)"
"2. **Step 2**: Add enrollment relationship (many-to-many Student-Course)"
"3. **Step 3**: Add teacher assignment (many-to-one Course-Teacher)"
"4. **Step 4**: Implement validation and error handling"
"5. **Step 5**: Add pagination and filtering to all endpoints"
"6. **Step 6**: Create comprehensive web UI for all operations"

# SHOULD BE:
# Read from prompts directory or add to config
prompts_dir = Path(config['prompts_dir'])
steps = []
for i in range(1, 7):
    prompt_file = prompts_dir / f"step_{i}.txt"
    if prompt_file.exists():
        with open(prompt_file) as f:
            first_line = f.readline().strip()
            steps.append(f"{i}. **Step {i}**: {first_line}")
```

#### 3.2 Python Version
**Lines:** 870
```python
# HARDCODED:
"- Python 3.11+ isolated virtual environments per framework"

# SHOULD BE:
# Add to config or detect dynamically
python_version = config.get('python_version', '3.11+')
f"- Python {python_version} isolated virtual environments per framework"
```

### 4. **Statistical Parameters** (Medium Priority)

#### 4.1 Bootstrap Sample Count
**Lines:** 256, 837, 978
```python
# HARDCODED in function:
def bootstrap_aggregate_metrics(..., n_bootstrap: int = 10000):

# SHOULD BE:
# Add to config
bootstrap_config = config.get('analysis', {}).get('bootstrap_samples', 10000)
```

#### 4.2 Confidence Level
**Lines:** 978, 837
```python
# HARDCODED:
"95% confidence intervals"

# SHOULD BE:
ci_level = config['stopping_rule']['confidence_level']
f"{int(ci_level*100)}% confidence intervals"
```

#### 4.3 Significance Level
**Throughout comparisons, p < 0.05 is hardcoded**
```python
# SHOULD BE:
alpha = config.get('analysis', {}).get('significance_level', 0.05)
```

### 5. **Commit Hashes Display** (Low Priority)

#### 5.1 Full Commit Hashes
**Lines:** 994-996
```python
# HARDCODED:
"- ChatDev: `52edb89997b4312ad27d8c54584d0a6c59940135`"
"- GHSpec: `89f4b0b38a42996376c0f083d47281a4c9196761`"
"- BAEs: `1dd573633a98b8baa636c200bc1684cec7a8179f`"

# SHOULD BE:
for fw_name, fw_config in config['frameworks'].items():
    commit = fw_config['commit_hash']
    lines.append(f"- {fw_name.title()}: `{commit}`")
```

## Implementation Plan

### Phase 1: Configuration Loading Infrastructure (Priority: HIGH)
**Estimated Time:** 2 hours

#### Changes:
1. **Add config parameter to `generate_statistical_report()`**
   ```python
   def generate_statistical_report(
       frameworks_data: Dict[str, List[Dict[str, float]]],
       config: Optional[Dict[str, Any]] = None,
       output_path: str = "analysis_output/report.md"
   ) -> None:
       """Generate comprehensive statistical report with dynamic configuration."""
       if config is None:
           from src.orchestrator.config_loader import load_config
           config = load_config()
   ```

2. **Update all callers** (mainly in analysis scripts)
   - `analyze.py` or equivalent
   - Any test files

3. **Add config validation** for required report fields

#### Files Modified:
- `src/analysis/statistics.py` (function signature)
- Scripts that call `generate_statistical_report()`

### Phase 2: Dynamic Model & Environment Configuration (Priority: HIGH)
**Estimated Time:** 3 hours

#### Changes:
1. **Extract model information dynamically**
   ```python
   model = config.get('model', 'gpt-4o-mini')
   model_display_name = MODEL_DISPLAY_NAMES.get(model, model)
   
   MODEL_DISPLAY_NAMES = {
       'gpt-4o-mini': 'OpenAI GPT-4 Omni Mini',
       'o1-mini': 'OpenAI O1 Mini',
       'o1-preview': 'OpenAI O1 Preview'
   }
   ```

2. **Dynamic timeout formatting**
   ```python
   timeout_sec = config['timeouts']['step_timeout_seconds']
   timeout_min = timeout_sec // 60
   ```

3. **Dynamic random seed**
   ```python
   seed = config['random_seed']
   ```

#### Files Modified:
- `src/analysis/statistics.py` (lines 859-876)

### Phase 3: Framework Metadata Integration (Priority: HIGH)
**Estimated Time:** 4 hours

#### Changes:
1. **Create framework descriptions database**
   ```python
   FRAMEWORK_DESCRIPTIONS = {
       'baes': {
           'full_name': 'Business Autonomous Entities',
           'description': 'API-based autonomous business entity framework',
           'details': 'Kernel-mediated request processing with specialized entities'
       },
       'chatdev': {
           'full_name': 'ChatDev (OpenBMB/ChatDev)',
           'description': 'Multi-agent collaborative framework with role-based AI agents',
           'details': 'Waterfall-inspired workflow with distinct phases (design, coding, testing, documentation)'
       },
       'ghspec': {
           'full_name': 'GHSpec (GitHub Spec-Kit)',
           'description': 'Specification-driven development framework',
           'details': 'Four-phase workflow: specification → planning → task breakdown → implementation'
       }
   }
   ```

2. **Generate frameworks section dynamically**
   ```python
   def _generate_frameworks_section(config: Dict) -> List[str]:
       lines = ["### 🎯 Frameworks Under Test", ""]
       
       for i, (fw_name, fw_config) in enumerate(config['frameworks'].items(), 1):
           fw_info = FRAMEWORK_DESCRIPTIONS.get(fw_name, {})
           repo_url = fw_config['repo_url']
           commit = fw_config['commit_hash'][:7]
           
           lines.append(f"**{i}. {fw_info.get('full_name', fw_name.title())}**")
           lines.append(f"- {fw_info.get('description', 'Framework description')}")
           if 'details' in fw_info:
               lines.append(f"- {fw_info['details']}")
           lines.append(f"- Repository: `{repo_url}` (commit: `{commit}`)")
           lines.append("")
       
       return lines
   ```

#### Files Modified:
- `src/analysis/statistics.py` (lines 793-813)
- New file: `src/analysis/framework_metadata.py`

### Phase 4: Stopping Rule Parameterization (Priority: HIGH)
**Estimated Time:** 2 hours

#### Changes:
1. **Extract all stopping rule parameters**
   ```python
   stopping_rule = config['stopping_rule']
   max_runs = stopping_rule['max_runs']
   min_runs = stopping_rule['min_runs']
   ci_level = stopping_rule['confidence_level']
   max_hw_pct = stopping_rule['max_half_width_pct']
   ```

2. **Update all references** (lines 838, 839, 978, 980)

3. **Dynamic progress calculation**
   ```python
   status_parts = [
       f"{fw} ({count}/{max_runs})" 
       for fw, count in run_counts.items()
   ]
   ```

#### Files Modified:
- `src/analysis/statistics.py` (lines 834-840, 975-982)

### Phase 5: Bootstrap Configuration (Priority: MEDIUM)
**Estimated Time:** 2 hours

#### Changes:
1. **Add analysis configuration section to YAML**
   ```yaml
   # Analysis configuration
   analysis:
     bootstrap_samples: 10000
     significance_level: 0.05
     confidence_level: 0.95  # Mirrors stopping_rule for consistency
     effect_size_thresholds:
       negligible: 0.147
       small: 0.330
       medium: 0.474
   ```

2. **Update bootstrap function calls**
   ```python
   analysis_config = config.get('analysis', {})
   n_bootstrap = analysis_config.get('bootstrap_samples', 10000)
   
   aggregated = bootstrap_aggregate_metrics(runs, n_bootstrap=n_bootstrap)
   ```

3. **Dynamic significance level in tests**
   ```python
   alpha = analysis_config.get('significance_level', 0.05)
   significant = p_value < alpha
   ```

#### Files Modified:
- `config/experiment.yaml` (new section)
- `src/analysis/statistics.py` (bootstrap calls, significance tests)

### Phase 6: Task Sequence Auto-Discovery (Priority: MEDIUM)
**Estimated Time:** 3 hours

#### Changes:
1. **Read step descriptions from prompt files**
   ```python
   def _load_task_sequence(config: Dict) -> List[str]:
       prompts_dir = Path(config['prompts_dir'])
       steps = []
       
       step_num = 1
       while True:
           prompt_file = prompts_dir / f"step_{step_num}.txt"
           if not prompt_file.exists():
               break
           
           with open(prompt_file, 'r') as f:
               # Extract first meaningful line or full content
               content = f.read().strip()
               first_line = content.split('\n')[0].strip()
               steps.append({
                   'number': step_num,
                   'summary': first_line[:100],  # Truncate if too long
                   'full_text': content
               })
           step_num += 1
       
       return steps
   ```

2. **Format steps dynamically**
   ```python
   lines.append("All frameworks execute the **identical six-step evolution scenario**:")
   lines.append("")
   
   for step in task_steps:
       lines.append(f"{step['number']}. **Step {step['number']}**: {step['summary']}")
   ```

#### Files Modified:
- `src/analysis/statistics.py` (lines 841-852)

### Phase 7: Framework-Specific Metadata Enhancement (Priority: LOW)
**Estimated Time:** 2 hours

#### Changes:
1. **Extract API keys dynamically**
   ```python
   api_keys = [
       fw['api_key_env'] 
       for fw in config['frameworks'].values()
   ]
   lines.append(f"- API keys: {', '.join([f'`{key}`' for key in api_keys])}")
   ```

2. **Dynamic commit hash display**
   ```python
   lines.append("**Commit Hashes**:")
   for fw_name, fw_config in config['frameworks'].items():
       commit = fw_config['commit_hash']
       lines.append(f"- {fw_name.title()}: `{commit}`")
   ```

#### Files Modified:
- `src/analysis/statistics.py` (lines 865, 994-996)

### Phase 8: Python Version Detection (Priority: LOW)
**Estimated Time:** 1 hour

#### Changes:
1. **Add Python version to config or detect**
   ```python
   import sys
   
   # Option 1: From config
   python_version = config.get('python_version', f'{sys.version_info.major}.{sys.version_info.minor}+')
   
   # Option 2: Detect from system
   python_version = f"{sys.version_info.major}.{sys.version_info.minor}+"
   
   lines.append(f"- Python {python_version} isolated virtual environments per framework")
   ```

#### Files Modified:
- `src/analysis/statistics.py` (line 870)
- `config/experiment.yaml` (optional)

## Benefits of Implementation

### 1. **Maintainability**
- ✅ Single source of truth (config file)
- ✅ No need to update multiple hardcoded values
- ✅ Changes propagate automatically to report

### 2. **Flexibility**
- ✅ Easy to run experiments with different models
- ✅ Adjust stopping rules without code changes
- ✅ Support different timeout configurations

### 3. **Accuracy**
- ✅ Report always matches actual experiment configuration
- ✅ No risk of outdated hardcoded values
- ✅ Commit hashes always correct

### 4. **Extensibility**
- ✅ Easy to add new frameworks
- ✅ Support additional models without code changes
- ✅ Configuration-driven customization

### 5. **Testing**
- ✅ Can generate reports with test configurations
- ✅ Verify report generation with different settings
- ✅ Reproducible test scenarios

## Testing Strategy

### Unit Tests
```python
def test_report_generation_with_custom_config():
    config = {
        'model': 'o1-mini',
        'random_seed': 123,
        'stopping_rule': {'max_runs': 50, 'min_runs': 10, ...},
        'frameworks': {...}
    }
    
    report = generate_statistical_report(frameworks_data, config)
    
    assert 'o1-mini' in report
    assert 'max 50 runs' in report
    assert 'seed: 123' in report
```

### Integration Tests
1. Generate report with default config
2. Generate report with custom config
3. Verify all dynamic values appear correctly
4. Compare with baseline report

### Regression Tests
1. Ensure existing reports still generate correctly
2. Verify backward compatibility
3. Test with missing config values (fallbacks)

## Migration Strategy

### Backward Compatibility
```python
def generate_statistical_report(
    frameworks_data: Dict[str, List[Dict[str, float]]],
    config: Optional[Dict[str, Any]] = None,
    output_path: str = "analysis_output/report.md"
) -> None:
    """
    Generate statistical report with optional configuration.
    
    If config is None, loads from default path (backward compatible).
    """
    if config is None:
        try:
            from src.orchestrator.config_loader import load_config
            config = load_config()
        except Exception as e:
            logger.warning(f"Could not load config: {e}, using defaults")
            config = _get_default_config()
```

### Rollout Plan
1. **Phase 1-4**: Critical hardcoded values → High priority
2. **Phase 5-6**: Statistical parameters → Medium priority
3. **Phase 7-8**: Nice-to-have improvements → Low priority

### Validation
- Run on existing data before/after each phase
- Compare generated reports (should be identical for Phase 1-4)
- Document any intentional changes

## Risk Assessment

### Low Risk
- Adding config parameter (optional, backward compatible)
- Reading existing config values
- Dynamic string formatting

### Medium Risk
- Changing bootstrap parameters (could affect CI widths slightly)
- Modifying significance levels (changes statistical tests)

### Mitigation
- Make all new parameters optional with sensible defaults
- Extensive testing before merging
- Document breaking changes clearly

## Success Metrics

1. **Code Quality**
   - Reduce hardcoded values from 45+ to <5
   - Improve code maintainability score

2. **Functionality**
   - All reports generate successfully
   - Dynamic values match config
   - Tests pass at 100%

3. **User Experience**
   - Report generation time unchanged
   - Report format/quality improved
   - Configuration easier to modify

## Timeline Estimate

| Phase | Priority | Hours | Dependencies |
|-------|----------|-------|--------------|
| Phase 1 | HIGH | 2 | None |
| Phase 2 | HIGH | 3 | Phase 1 |
| Phase 3 | HIGH | 4 | Phase 1 |
| Phase 4 | HIGH | 2 | Phase 1 |
| Phase 5 | MEDIUM | 2 | Phase 1 |
| Phase 6 | MEDIUM | 3 | Phase 1 |
| Phase 7 | LOW | 2 | Phase 3 |
| Phase 8 | LOW | 1 | None |
| **Phase 9** | **CRITICAL** | **3** | **Phases 1-8** |
| **Total** | | **24 hours** | |

**Testing & Documentation:** +4 hours  
**Total Project Time:** ~28 hours (~3.5 working days)

## Phase 9: Review and Eliminate Dangerous Fallbacks (CRITICAL PRIORITY)

**⚠️ CRITICAL CONCERN:** Fallback values can mask configuration/run problems by silently using defaults instead of failing fast.

### Problem Statement

Current implementation uses fallback values that could hide serious issues:

1. **Model Configuration:**
   ```python
   model_name = config.get('model', 'gpt-4o-mini')  # ❌ Silently defaults
   ```
   **Risk:** User thinks they're using gpt-4o, but actually using gpt-4o-mini due to typo in config.

2. **Framework Descriptions:**
   ```python
   framework_descriptions = {
       'chatdev': {'full_name': 'ChatDev', ...}  # ❌ Hardcoded fallback
   }
   ```
   **Risk:** Config points to wrong framework, but report shows correct description, masking the issue.

3. **Config Loading:**
   ```python
   except Exception as e:
       logger.warning(f"Failed to load config, using defaults: {e}")
       config = {}  # ❌ Silently continues with empty config
   ```
   **Risk:** Config file corrupted/missing, but report generates with wrong values.

### Implementation Plan

#### Step 1: Audit All Fallbacks (1 hour)

Search for all `.get()` calls with defaults and `try/except` blocks:

```bash
# Find all fallback patterns
grep -n "\.get(" src/analysis/statistics.py
grep -n "try:" src/analysis/statistics.py | grep -A 5 "config"
```

**List to audit:**
- Model name fallback
- Framework metadata fallbacks
- Stopping rule parameters
- Bootstrap parameters
- Significance levels
- Timeout values
- Any other config.get() with defaults

#### Step 2: Create Validation Functions (1 hour)

Add strict validation helpers:

```python
def _require_config_value(config: Dict, key: str, description: str) -> Any:
    """
    Get required config value or raise ValueError.
    
    Args:
        config: Configuration dictionary
        key: Config key to retrieve
        description: Human-readable description for error message
        
    Returns:
        Config value
        
    Raises:
        ValueError: If key missing or None
    """
    if key not in config:
        raise ValueError(
            f"Missing required configuration: '{key}' ({description}). "
            f"Please check config/experiment.yaml"
        )
    value = config[key]
    if value is None:
        raise ValueError(
            f"Configuration '{key}' is None ({description}). "
            f"Please set a valid value in config/experiment.yaml"
        )
    return value

def _require_framework_field(
    fw_config: Dict, 
    framework: str, 
    field: str, 
    description: str
) -> Any:
    """Get required framework config field or raise ValueError."""
    if field not in fw_config:
        raise ValueError(
            f"Missing required field '{field}' for framework '{framework}' "
            f"({description}). Please check config/experiment.yaml"
        )
    value = fw_config[field]
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(
            f"Invalid '{field}' for framework '{framework}' ({description}). "
            f"Please set a valid value in config/experiment.yaml"
        )
    return value
```

#### Step 3: Replace Permissive Code (1 hour)

**Before (Phase 1-3):**
```python
# ❌ Silently defaults - masks problems
model_name = config.get('model', 'gpt-4o-mini')

fw_config = frameworks_config.get(fw_key, {})
repo_url = fw_config.get('repo_url', '')
commit_hash = fw_config.get('commit_hash', 'unknown')
```

**After (Phase 9):**
```python
# ✅ Fails fast - exposes problems immediately
model_name = _require_config_value(config, 'model', 'LLM model name')

fw_config = frameworks_config.get(fw_key)
if not fw_config:
    raise ValueError(
        f"Framework '{fw_key}' found in run data but not in config. "
        f"Please add configuration for '{fw_key}' in config/experiment.yaml"
    )

repo_url = _require_framework_field(fw_config, fw_key, 'repo_url', 'Git repository URL')
commit_hash = _require_framework_field(fw_config, fw_key, 'commit_hash', 'Git commit hash')
```

#### Step 4: Handle Framework Descriptions

**Option A: Remove Fallback (Recommended)**
```python
# Remove hardcoded framework_descriptions dictionary
# Require all metadata in config

# In config/experiment.yaml:
frameworks:
  chatdev:
    repo_url: "..."
    commit_hash: "..."
    full_name: "ChatDev"
    org: "OpenBMB/ChatDev"
    description:
      - "Multi-agent collaborative framework..."
      - "Waterfall-inspired workflow..."
```

**Option B: Keep as Documentation (If config approach too heavy)**
```python
# Keep framework_descriptions but warn if not in config
if 'full_name' not in fw_config:
    logger.warning(
        f"Framework '{fw_key}' missing 'full_name' in config, "
        f"using fallback description. Consider adding to config/experiment.yaml"
    )
```

#### Step 5: Update Config Loader

Replace permissive config loading:

```python
# Before: ❌ Silently continues with empty config
if config is None:
    try:
        config = load_config()
    except Exception as e:
        logger.warning(f"Failed to load config, using defaults: {e}")
        config = {}

# After: ✅ Fails fast if config missing
if config is None:
    try:
        config = load_config()
    except FileNotFoundError:
        raise ValueError(
            "Configuration file not found: config/experiment.yaml. "
            "Cannot generate report without configuration."
        )
    except Exception as e:
        raise ValueError(
            f"Failed to load configuration: {e}. "
            f"Please check config/experiment.yaml for errors."
        )
```

### Benefits

1. **Fail Fast:** Errors surface immediately, not in production
2. **Clear Messages:** User knows exactly what's wrong and where
3. **Data Integrity:** Report always matches actual experiment setup
4. **No Silent Errors:** Eliminates "silent wrong behavior"
5. **Easier Debugging:** Configuration problems caught early

### Testing Strategy

1. **Test Missing Config:**
   - Remove config file → should raise clear error
   - Remove model field → should raise "Missing required configuration: 'model'"

2. **Test Missing Framework Fields:**
   - Remove repo_url → should raise framework-specific error
   - Remove commit_hash → should raise with framework name

3. **Test Invalid Values:**
   - Set model to empty string → should raise validation error
   - Set commit_hash to None → should raise validation error

4. **Test Valid Config:**
   - Normal config → should work exactly as before
   - All required fields present → no errors

### Migration Impact

**Breaking Change:** Yes - report generation will fail if config incomplete

**Mitigation:**
1. Add comprehensive config validation to runner scripts
2. Update documentation with required config fields
3. Provide clear error messages pointing to solution
4. Test all existing workflows before merging

### Code Examples

```python
# Complete Phase 9 implementation in generate_statistical_report():

def generate_statistical_report(...):
    # Phase 1: Config loading (STRICT)
    if config is None:
        try:
            config = load_config()
            logger.info("Loaded configuration from config/experiment.yaml")
        except FileNotFoundError:
            raise ValueError(
                "Configuration file not found: config/experiment.yaml. "
                "Report generation requires valid configuration."
            )
        except Exception as e:
            raise ValueError(f"Failed to load configuration: {e}")
    
    # Phase 2: Model config (STRICT)
    model_name = _require_config_value(config, 'model', 'LLM model name')
    
    # Phase 3: Framework metadata (STRICT)
    frameworks_config = config.get('frameworks', {})
    
    for fw_key in frameworks_data.keys():
        if fw_key not in frameworks_config:
            raise ValueError(
                f"Framework '{fw_key}' in run data but not in config. "
                f"Add to config/experiment.yaml under 'frameworks.{fw_key}'"
            )
        
        fw_config = frameworks_config[fw_key]
        repo_url = _require_framework_field(fw_config, fw_key, 'repo_url', 'repository URL')
        commit_hash = _require_framework_field(fw_config, fw_key, 'commit_hash', 'commit hash')
        # ... etc
```

## Conclusion

This improvement plan systematically addresses all hardcoded values in the report generation, making it:
- **Configuration-driven**: All experimental parameters from config
- **Maintainable**: Single source of truth
- **Flexible**: Easy to run different experiments
- **Accurate**: Report always matches actual configuration
- **Extensible**: Easy to add frameworks/models

The phased approach allows incremental improvements with continuous validation, minimizing risk while maximizing value.

## Next Steps

1. ✅ **Approve this plan** (stakeholder review)
2. 🔄 **Implement Phase 1** (config infrastructure)
3. 🔄 **Implement Phases 2-4** (high priority items)
4. 📝 **Create PR with comprehensive tests**
5. ✅ **Review and merge**
6. 🔄 **Implement remaining phases** (if time permits)

---

**Document Version:** 1.0  
**Last Updated:** October 17, 2025  
**Author:** System Analysis
