# Configuration Validation System

**Last Updated:** October 17, 2025  
**Module:** `src/analysis/statistics.py`  
**Purpose:** Strict validation to prevent silent configuration errors

---

## Overview

The validation system provides three helper functions that enforce strict configuration requirements when generating statistical reports. These functions replace dangerous `.get()` patterns with explicit validation that **fails loudly** when configuration is incomplete or incorrect.

### Why Strict Validation?

**The Problem:**
```python
# ❌ DANGEROUS: Silent wrong behavior
model = config.get('model', 'gpt-4o-mini')  # Typo → uses wrong model silently!
frameworks = config.get('frameworks', {})    # Missing → empty report, no error!
```

**The Solution:**
```python
# ✅ SAFE: Explicit validation with clear errors
model = _require_config_value(config, 'model')
frameworks = _require_config_value(config, 'frameworks')
```

### Key Principle

> **"Fail loudly early" beats "work silently wrong"**

If configuration is wrong, we want to know **immediately** with a **clear error message**, not discover it hours later when analyzing incorrect reports.

---

## Validation Functions

### 1. `_require_config_value()`

**Purpose:** Extract required top-level configuration values with clear error messages.

**Signature:**
```python
def _require_config_value(config: dict, key: str, context: str = 'root config') -> Any
```

**Parameters:**
- `config` (dict): The configuration dictionary to search
- `key` (str): The required key to extract
- `context` (str, optional): Context description for error message. Default: 'root config'

**Returns:**
- The value associated with `key` if present

**Raises:**
- `ValueError`: If `key` is not found in `config`

**Usage Example:**
```python
from src.analysis.statistics import _require_config_value

# Load config
config = load_experiment_config('config/experiment.yaml')

# Extract required values
model = _require_config_value(config, 'model')
frameworks = _require_config_value(config, 'frameworks')
prompts_dir = _require_config_value(config, 'prompts_dir')

print(f"Using model: {model}")
```

**Error Example:**
```python
config = {}  # Empty config

try:
    model = _require_config_value(config, 'model')
except ValueError as e:
    print(e)
    # Output:
    # Missing required configuration: 'model' in root config.
    # Please add 'model' to config/experiment.yaml
```

**When to Use:**
- Extracting top-level configuration keys
- When the key is required for operation
- When you want to provide helpful error messages

**When NOT to Use:**
- For optional configuration values (use `.get()` with sensible defaults)
- For nested configuration (use `_require_nested_config()` instead)

---

### 2. `_require_nested_config()`

**Purpose:** Extract required nested configuration values with path-aware error messages.

**Signature:**
```python
def _require_nested_config(config: dict, *keys: str) -> Any
```

**Parameters:**
- `config` (dict): The root configuration dictionary
- `*keys` (str): Variable number of keys representing the path to the value

**Returns:**
- The value at the nested path if all keys exist

**Raises:**
- `ValueError`: If any key in the path is missing, with full path shown in error

**Usage Example:**
```python
from src.analysis.statistics import _require_nested_config

# Extract nested values
max_runs = _require_nested_config(config, 'stopping_rule', 'max_runs')
python_version = _require_nested_config(config, 'stopping_rule', 'python_version')
bootstrap_samples = _require_nested_config(config, 'analysis', 'bootstrap_samples')
significance = _require_nested_config(config, 'analysis', 'significance_level')

print(f"Running {max_runs} iterations with Python {python_version}")
print(f"Using {bootstrap_samples} bootstrap resamples at {significance} significance")
```

**Error Example:**
```python
config = {
    'stopping_rule': {
        'max_runs': 5
        # 'python_version' is missing!
    }
}

try:
    version = _require_nested_config(config, 'stopping_rule', 'python_version')
except ValueError as e:
    print(e)
    # Output:
    # Missing required configuration: 'stopping_rule.python_version'.
    # Please ensure config structure is complete.
```

**Path Resolution:**

The function walks through the config dictionary following the key path:

```python
# For: _require_nested_config(config, 'a', 'b', 'c')
# Checks:
# 1. config['a'] exists and is a dict
# 2. config['a']['b'] exists and is a dict
# 3. config['a']['b']['c'] exists
# Returns: config['a']['b']['c']
```

**When to Use:**
- Extracting deeply nested configuration values
- When you need path information in error messages
- When intermediate keys must also exist

**When NOT to Use:**
- For top-level keys (use `_require_config_value()` instead)
- For optional nested values (use `.get()` chain with defaults)

---

### 3. `_validate_framework_config()`

**Purpose:** Validate that framework configuration contains all required fields.

**Signature:**
```python
def _validate_framework_config(fw_key: str, fw_config: dict) -> None
```

**Parameters:**
- `fw_key` (str): The framework identifier (for error messages)
- `fw_config` (dict): The framework configuration dictionary to validate

**Returns:**
- `None` (validation-only function)

**Raises:**
- `ValueError`: If any required field is missing, listing all missing fields

**Required Fields:**
- `repo_url` (str): Git repository URL
- `commit_hash` (str): Git commit hash or tag
- `api_key_env` (str): Environment variable name for API key

**Usage Example:**
```python
from src.analysis.statistics import _validate_framework_config

frameworks = config['frameworks']

for fw_key, fw_config in frameworks.items():
    # Validate each framework
    _validate_framework_config(fw_key, fw_config)
    
    # If we get here, config is valid
    print(f"✓ {fw_key} configuration valid")
    print(f"  Repository: {fw_config['repo_url']}")
    print(f"  Commit: {fw_config['commit_hash']}")
    print(f"  API Key: {fw_config['api_key_env']}")
```

**Error Example:**
```python
fw_config = {
    'repo_url': 'https://github.com/example/repo.git',
    # Missing: commit_hash and api_key_env
}

try:
    _validate_framework_config('chatdev', fw_config)
except ValueError as e:
    print(e)
    # Output:
    # Framework 'chatdev' configuration incomplete.
    # Missing: commit_hash, api_key_env
```

**When to Use:**
- Before processing framework configurations
- In loops that iterate over multiple frameworks
- When you want to validate all frameworks upfront

**When NOT to Use:**
- For validating single fields (just access directly: `fw_config['repo_url']`)
- If framework config is optional

---

## Usage Patterns

### Pattern 1: Validate Everything Upfront

**Best Practice:** Validate all required config at the start of your function.

```python
def generate_statistical_report(run_data: dict, output_file: str, config: dict):
    """Generate report with strict config validation"""
    
    # Validate all required config upfront
    model = _require_config_value(config, 'model')
    frameworks = _require_config_value(config, 'frameworks')
    prompts_dir = _require_config_value(config, 'prompts_dir')
    
    max_runs = _require_nested_config(config, 'stopping_rule', 'max_runs')
    python_version = _require_nested_config(config, 'stopping_rule', 'python_version')
    
    bootstrap_samples = _require_nested_config(config, 'analysis', 'bootstrap_samples')
    significance_level = _require_nested_config(config, 'analysis', 'significance_level')
    
    # Validate each framework
    for fw_key, fw_config in frameworks.items():
        _validate_framework_config(fw_key, fw_config)
    
    # If we get here, all config is valid - proceed with report generation
    # ...
```

**Benefits:**
- All errors caught immediately
- No partial processing with invalid config
- Clear error messages guide user to fix config

### Pattern 2: Validate File System Resources

**Best Practice:** Validate that files/directories exist after config validation.

```python
def generate_statistical_report(run_data: dict, output_file: str, config: dict):
    # First: Validate config
    prompts_dir = _require_config_value(config, 'prompts_dir')
    
    # Then: Validate file system
    if not os.path.exists(prompts_dir):
        raise ValueError(
            f"Prompts directory not found: {prompts_dir}\n"
            f"Please ensure the directory exists and path is correct."
        )
    
    if not os.path.isdir(prompts_dir):
        raise ValueError(
            f"Prompts path is not a directory: {prompts_dir}\n"
            f"Please provide a valid directory path."
        )
    
    # Check for step files
    step_files = [f for f in os.listdir(prompts_dir) 
                  if f.startswith('step_') and f.endswith('.txt')]
    
    if not step_files:
        raise ValueError(
            f"No step files found in {prompts_dir}\n"
            f"Expected files like: step_1.txt, step_2.txt, etc."
        )
    
    # Now we know config AND file system are valid
    # ...
```

### Pattern 3: Error Handling in Scripts

**Best Practice:** Catch validation errors and show user-friendly messages.

```python
#!/usr/bin/env python3
"""Run statistical analysis with validation"""

import sys
from src.analysis.statistics import generate_statistical_report
from src.orchestrator.config_loader import load_experiment_config

def main():
    try:
        # Load config
        config = load_experiment_config('config/experiment.yaml')
        
        # Load run data
        run_data = load_run_data('runs/')
        
        # Generate report (validation happens inside)
        generate_statistical_report(run_data, 'analysis_output/report.md', config)
        
        print("✓ Report generated successfully!")
        return 0
        
    except ValueError as e:
        # Validation error - show clear message
        print(f"Configuration Error: {e}", file=sys.stderr)
        print("\nPlease fix the configuration and try again.", file=sys.stderr)
        return 1
        
    except FileNotFoundError as e:
        # File not found - show helpful message
        print(f"File Error: {e}", file=sys.stderr)
        return 1
        
    except Exception as e:
        # Unexpected error - show full traceback
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 2

if __name__ == '__main__':
    sys.exit(main())
```

---

## Common Validation Errors

### Error: Missing Top-Level Key

```
ValueError: Missing required configuration: 'model' in root config.
Please add 'model' to config/experiment.yaml
```

**Solution:** Add the missing key to your config file:

```yaml
model: gpt-4o-mini
```

### Error: Missing Nested Key

```
ValueError: Missing required configuration: 'stopping_rule.max_runs'.
Please ensure config structure is complete.
```

**Solution:** Add the nested structure:

```yaml
stopping_rule:
  max_runs: 5
  python_version: "3.11.8"
```

### Error: Incomplete Framework Config

```
ValueError: Framework 'chatdev' configuration incomplete.
Missing: commit_hash, api_key_env
```

**Solution:** Add all required framework fields:

```yaml
frameworks:
  chatdev:
    repo_url: https://github.com/OpenBMB/ChatDev.git
    commit_hash: 52edb89abc123
    api_key_env: OPENAI_API_KEY
```

### Error: Prompts Directory Not Found

```
ValueError: Prompts directory not found: /path/to/prompts
Please ensure the directory exists and path is correct.
```

**Solution:** 
1. Check the path in config is correct
2. Ensure the directory exists: `mkdir -p config/prompts`
3. Add step files: `step_1.txt`, `step_2.txt`, etc.

---

## Testing Validation

The test suite includes comprehensive validation testing:

```bash
# Run validation tests only
pytest tests/unit/test_report_generation.py -k "validation" -v

# Expected output:
# test_missing_model_raises_error PASSED
# test_missing_frameworks_raises_error PASSED
# test_missing_nested_config PASSED
# test_missing_stopping_rule PASSED
# test_incomplete_framework_config PASSED
# test_framework_missing_field PASSED
# test_nonexistent_prompts_dir PASSED
# test_framework_not_in_config PASSED
# test_missing_analysis_section PASSED
# test_invalid_nested_path PASSED
```

See `tests/unit/test_report_generation.py` for complete test examples.

---

## Migration Guide

### Migrating from `.get()` to Strict Validation

**Before (Dangerous):**
```python
def process_config(config):
    model = config.get('model', 'gpt-4o-mini')  # Silent fallback
    max_runs = config.get('stopping_rule', {}).get('max_runs', 100)  # Silent fallback
```

**After (Safe):**
```python
def process_config(config):
    model = _require_config_value(config, 'model')
    max_runs = _require_nested_config(config, 'stopping_rule', 'max_runs')
```

**Considerations:**
1. **Required vs Optional:** Only use strict validation for truly required values
2. **Default Values:** If a sensible default exists, `.get()` is acceptable
3. **Error Messages:** Strict validation provides better errors for required values

### When to Keep `.get()` with Defaults

Some values have sensible defaults and are truly optional:

```python
# Optional with sensible default - keep .get()
verbose = config.get('verbose', False)
timeout = config.get('timeout', 300)
output_format = config.get('format', 'markdown')
```

### When to Use Strict Validation

Use strict validation when:
- The value is required for correct operation
- No sensible default exists
- Wrong value would cause silent errors
- You want to validate configuration upfront

```python
# Required - use strict validation
model = _require_config_value(config, 'model')
api_key = _require_config_value(config, 'api_key')
frameworks = _require_config_value(config, 'frameworks')
```

---

## Best Practices

### 1. Validate Early, Fail Fast
```python
# ✓ GOOD: Validate at function entry
def process(config):
    value = _require_config_value(config, 'key')
    # ... rest of processing

# ✗ BAD: Validate late
def process(config):
    # ... lots of processing
    value = config['key']  # Might crash here after work done
```

### 2. Provide Context in Error Messages
```python
# ✓ GOOD: Context helps debugging
model = _require_config_value(config, 'model', 'experiment config')

# ✗ ACCEPTABLE: Less context but still clear
model = _require_config_value(config, 'model')
```

### 3. Group Related Validations
```python
# ✓ GOOD: Related validations together
# Stopping rule config
max_runs = _require_nested_config(config, 'stopping_rule', 'max_runs')
python_version = _require_nested_config(config, 'stopping_rule', 'python_version')

# Analysis config
bootstrap = _require_nested_config(config, 'analysis', 'bootstrap_samples')
significance = _require_nested_config(config, 'analysis', 'significance_level')
```

### 4. Validate All Frameworks Upfront
```python
# ✓ GOOD: Validate all frameworks before processing
frameworks = _require_config_value(config, 'frameworks')
for fw_key, fw_config in frameworks.items():
    _validate_framework_config(fw_key, fw_config)

# Now process (we know all are valid)
for fw_key, fw_config in frameworks.items():
    process_framework(fw_key, fw_config)
```

### 5. Document Validation Requirements
```python
def generate_report(config: dict) -> str:
    """
    Generate statistical report from config.
    
    Required config keys:
    - model (str): LLM model identifier
    - frameworks (dict): Framework configurations
    - stopping_rule.max_runs (int): Maximum iterations
    - analysis.bootstrap_samples (int): Bootstrap sample count
    
    Raises:
        ValueError: If required config is missing
    """
    # Validation...
```

---

## Related Documentation

- [Configuration Reference](./configuration_reference.md) - Complete config schema
- [Troubleshooting Guide](./troubleshooting.md) - Common errors and solutions
- [Test Documentation](../tests/unit/test_report_generation.py) - Validation test examples

---

**Questions or Issues?**

If you encounter validation errors or have questions about configuration:
1. Check the error message - it should indicate what's missing
2. Review [configuration_reference.md](./configuration_reference.md) for correct schema
3. See [troubleshooting.md](./troubleshooting.md) for common issues
4. Run tests: `pytest tests/unit/test_report_generation.py -v`
