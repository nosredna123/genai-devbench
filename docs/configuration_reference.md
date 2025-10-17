# Configuration Reference Guide

**Last Updated:** October 17, 2025  
**Config File:** `config/experiment.yaml`  
**Purpose:** Complete reference for all configuration options

---

## Overview

The `experiment.yaml` file controls all aspects of the BAEs experiment framework, including:
- Model selection
- Framework configurations
- Stopping rules
- Statistical analysis parameters
- File system paths

This document provides a complete reference for all configuration sections and fields.

---

## Complete Configuration Example

```yaml
# Model Configuration (REQUIRED)
model: gpt-4o-mini

# Prompts Directory (REQUIRED)
prompts_dir: config/prompts

# Frameworks Configuration (REQUIRED)
frameworks:
  chatdev:
    repo_url: https://github.com/OpenBMB/ChatDev.git
    commit_hash: 52edb89abc123
    api_key_env: OPENAI_API_KEY
    description: Multi-agent collaborative software development framework
  
  ghspec:
    repo_url: https://github.com/Ueeek/ghspec.git
    commit_hash: 89f4b0bdef456
    api_key_env: ANTHROPIC_API_KEY
    description: GitHub specification-based development workflow
  
  baes:
    repo_url: https://github.com/gesad-lab/baes.git
    commit_hash: 1dd5736ghi789
    api_key_env: OPENAI_API_KEY
    description: Behavior-driven AI engineering system

# Stopping Rule Configuration (REQUIRED)
stopping_rule:
  max_runs: 5
  python_version: "3.11.8"

# Analysis Configuration (REQUIRED)
analysis:
  bootstrap_samples: 10000
  significance_level: 0.05
```

---

## Configuration Sections

### 1. Model Configuration

**Required:** Yes  
**Type:** String  
**Purpose:** Specifies which LLM model to use for the experiment

```yaml
model: gpt-4o-mini
```

**Supported Models:**

| Model ID | Display Name | Provider |
|----------|-------------|----------|
| `gpt-4o-mini` | OpenAI GPT-4 Omni Mini | OpenAI |
| `gpt-4o` | OpenAI GPT-4 Omni | OpenAI |
| `gpt-4-turbo` | OpenAI GPT-4 Turbo | OpenAI |
| `gpt-4` | OpenAI GPT-4 | OpenAI |
| `gpt-3.5-turbo` | OpenAI GPT-3.5 Turbo | OpenAI |

**Validation:**
- Must be present in config
- Will raise `ValueError` if missing
- Model name will be displayed in generated reports

**Error Example:**
```
ValueError: Missing required configuration: 'model' in root config.
Please add 'model' to config/experiment.yaml
```

---

### 2. Prompts Directory

**Required:** Yes  
**Type:** String (path)  
**Purpose:** Path to directory containing step prompt files

```yaml
prompts_dir: config/prompts
```

**Requirements:**
- Directory must exist
- Must contain step files named `step_N.txt` (e.g., `step_1.txt`, `step_2.txt`)
- Step files must be non-empty (first line used as description)
- Can use absolute or relative paths (relative to project root)

**Expected Directory Structure:**
```
config/prompts/
├── step_1.txt
├── step_2.txt
├── step_3.txt
├── step_4.txt
├── step_5.txt
└── step_6.txt
```

**Step File Format:**
```
Requirement Analysis and Planning
# This is the first line (used as description in report)

Additional details about this step...
```

**Validation:**
- Directory existence checked at runtime
- Step files counted dynamically
- Empty directory raises error

**Error Examples:**
```
ValueError: Prompts directory not found: /path/to/prompts
Please ensure the directory exists and path is correct.

ValueError: No step files found in config/prompts
Expected files like: step_1.txt, step_2.txt, etc.
```

---

### 3. Frameworks Configuration

**Required:** Yes  
**Type:** Dictionary  
**Purpose:** Define all frameworks to test in the experiment

```yaml
frameworks:
  framework_key:
    repo_url: <string>
    commit_hash: <string>
    api_key_env: <string>
    description: <string>  # Optional
```

**Field Descriptions:**

#### `repo_url` (REQUIRED)
- **Type:** String (URL)
- **Purpose:** Git repository URL for the framework
- **Format:** HTTPS or SSH Git URL
- **Example:** `https://github.com/OpenBMB/ChatDev.git`

#### `commit_hash` (REQUIRED)
- **Type:** String
- **Purpose:** Specific Git commit to use
- **Format:** Full commit hash (40 chars) or short form (7+ chars)
- **Example:** `52edb89abc123` or `52edb89abc123def456789012345678901234567`
- **Display:** Shown as 7-character short form in reports

#### `api_key_env` (REQUIRED)
- **Type:** String
- **Purpose:** Environment variable name containing API key
- **Format:** Valid environment variable name (uppercase, underscores)
- **Example:** `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- **Usage:** Framework will read this env var at runtime

#### `description` (OPTIONAL)
- **Type:** String
- **Purpose:** Human-readable framework description
- **Example:** `Multi-agent collaborative software development framework`
- **Usage:** Displayed in "Frameworks Under Test" section of reports

**Complete Example:**
```yaml
frameworks:
  chatdev:
    repo_url: https://github.com/OpenBMB/ChatDev.git
    commit_hash: 52edb89abc123def456789012345678901234567
    api_key_env: OPENAI_API_KEY
    description: Multi-agent collaborative software development framework using role-playing
```

**Validation:**
- All three required fields must be present
- Framework key must match keys used in run data
- Multiple frameworks supported (tested alphabetically)

**Error Examples:**
```
ValueError: Missing required configuration: 'frameworks' in root config.
Please add 'frameworks' to config/experiment.yaml

ValueError: Framework 'chatdev' configuration incomplete.
Missing: commit_hash, api_key_env
```

---

### 4. Stopping Rule Configuration

**Required:** Yes  
**Type:** Dictionary  
**Purpose:** Define experiment stopping criteria and execution environment

```yaml
stopping_rule:
  max_runs: <integer>
  python_version: <string>
```

**Field Descriptions:**

#### `max_runs` (REQUIRED)
- **Type:** Integer
- **Purpose:** Maximum number of iterations per framework
- **Range:** Positive integer (typically 3-10)
- **Example:** `5`
- **Usage:** Displayed in "Experimental Setup" section

#### `python_version` (REQUIRED)
- **Type:** String
- **Purpose:** Python version used for experiment execution
- **Format:** Version string like `"3.11.8"` or `"3.11"`
- **Example:** `"3.11.8"`
- **Display:** Extracted as `X.Y` format (e.g., "3.11" from "3.11.8")
- **Note:** Must be quoted in YAML to preserve as string

**Complete Example:**
```yaml
stopping_rule:
  max_runs: 5
  python_version: "3.11.8"
```

**Validation:**
- Both fields are required
- Will raise `ValueError` if either missing
- Python version extracted with regex pattern `(\d+\.\d+)`

**Error Examples:**
```
ValueError: Missing required configuration: 'stopping_rule.max_runs'.
Please ensure config structure is complete.

ValueError: Missing required configuration: 'stopping_rule.python_version'.
Please ensure config structure is complete.
```

---

### 5. Analysis Configuration

**Required:** Yes  
**Type:** Dictionary  
**Purpose:** Configure statistical analysis parameters

```yaml
analysis:
  bootstrap_samples: <integer>
  significance_level: <float>
```

**Field Descriptions:**

#### `bootstrap_samples` (REQUIRED)
- **Type:** Integer
- **Purpose:** Number of bootstrap resamples for statistical tests
- **Range:** Typically 1,000 - 10,000 (more = more accurate but slower)
- **Example:** `10000`
- **Display:** Shown with thousand separator (10,000) in reports
- **Recommendation:** 10,000 for publication-quality results

#### `significance_level` (REQUIRED)
- **Type:** Float
- **Purpose:** Significance level for statistical tests (alpha)
- **Range:** 0.0 - 1.0 (typically 0.01, 0.05, or 0.10)
- **Example:** `0.05`
- **Display:** Converted to confidence level (1 - alpha) × 100%
  - `0.05` → 95% confidence intervals
  - `0.01` → 99% confidence intervals
- **Recommendation:** 0.05 (standard in research)

**Complete Example:**
```yaml
analysis:
  bootstrap_samples: 10000
  significance_level: 0.05
```

**Display in Reports:**
```
Statistical analysis performed using 10,000 bootstrap resamples
with 95% confidence intervals.
```

**Validation:**
- Both fields are required
- Bootstrap samples must be positive integer
- Significance level should be between 0 and 1

**Error Examples:**
```
ValueError: Missing required configuration: 'analysis.bootstrap_samples'.
Please ensure config structure is complete.

ValueError: Missing required configuration: 'analysis.significance_level'.
Please ensure config structure is complete.
```

---

## Configuration Schema Summary

```yaml
# Top-level required fields
model: string                    # Required
prompts_dir: string              # Required
frameworks: dict                 # Required
stopping_rule: dict              # Required
analysis: dict                   # Required

# Framework schema (all fields required except description)
frameworks:
  <framework_key>:
    repo_url: string             # Required
    commit_hash: string          # Required
    api_key_env: string          # Required
    description: string          # Optional

# Stopping rule schema (all fields required)
stopping_rule:
  max_runs: integer              # Required
  python_version: string         # Required

# Analysis schema (all fields required)
analysis:
  bootstrap_samples: integer     # Required
  significance_level: float      # Required
```

---

## Minimal Valid Configuration

This is the absolute minimum configuration required:

```yaml
model: gpt-4o-mini
prompts_dir: config/prompts

frameworks:
  test_fw:
    repo_url: https://github.com/test/repo.git
    commit_hash: abc123
    api_key_env: TEST_KEY

stopping_rule:
  max_runs: 5
  python_version: "3.11"

analysis:
  bootstrap_samples: 10000
  significance_level: 0.05
```

---

## Common Configuration Examples

### Example 1: Single Framework, Quick Testing

```yaml
model: gpt-3.5-turbo
prompts_dir: config/prompts

frameworks:
  chatdev:
    repo_url: https://github.com/OpenBMB/ChatDev.git
    commit_hash: 52edb89
    api_key_env: OPENAI_API_KEY

stopping_rule:
  max_runs: 3
  python_version: "3.11"

analysis:
  bootstrap_samples: 1000      # Fewer samples for faster analysis
  significance_level: 0.05
```

### Example 2: Multiple Frameworks, Publication Quality

```yaml
model: gpt-4o
prompts_dir: config/prompts

frameworks:
  chatdev:
    repo_url: https://github.com/OpenBMB/ChatDev.git
    commit_hash: 52edb89abc123
    api_key_env: OPENAI_API_KEY
    description: Multi-agent collaborative framework
  
  ghspec:
    repo_url: https://github.com/Ueeek/ghspec.git
    commit_hash: 89f4b0bdef456
    api_key_env: ANTHROPIC_API_KEY
    description: Specification-based development
  
  baes:
    repo_url: https://github.com/gesad-lab/baes.git
    commit_hash: 1dd5736ghi789
    api_key_env: OPENAI_API_KEY
    description: Behavior-driven engineering

stopping_rule:
  max_runs: 10                   # More runs for robust statistics
  python_version: "3.11.8"

analysis:
  bootstrap_samples: 10000       # Maximum accuracy
  significance_level: 0.01       # Stricter significance (99% CI)
```

### Example 3: Development/Debugging Configuration

```yaml
model: gpt-4o-mini               # Cheaper model for testing
prompts_dir: config/prompts

frameworks:
  test_framework:
    repo_url: https://github.com/local/test.git
    commit_hash: HEAD
    api_key_env: TEST_API_KEY

stopping_rule:
  max_runs: 1                    # Single run for quick tests
  python_version: "3.11"

analysis:
  bootstrap_samples: 100         # Minimal for speed
  significance_level: 0.05
```

---

## Configuration Best Practices

### 1. Use Version Control for Config

```bash
# Track config changes in git
git add config/experiment.yaml
git commit -m "Update experiment config for new model"
```

### 2. Validate Before Running

```python
# Test config loading
from src.orchestrator.config_loader import load_experiment_config

try:
    config = load_experiment_config('config/experiment.yaml')
    print("✓ Configuration valid")
except ValueError as e:
    print(f"✗ Configuration error: {e}")
```

### 3. Document Configuration Changes

```yaml
# Add comments to explain non-obvious choices
model: gpt-4o-mini              # Using mini for cost control
analysis:
  bootstrap_samples: 5000       # Reduced from 10000 for faster iteration
  significance_level: 0.05
```

### 4. Use Environment Variables for Secrets

```yaml
# ✓ GOOD: Reference environment variable
frameworks:
  chatdev:
    api_key_env: OPENAI_API_KEY

# ✗ BAD: Never put actual keys in config
frameworks:
  chatdev:
    api_key: sk-abc123...        # DON'T DO THIS!
```

### 5. Keep Framework Descriptions Concise

```yaml
# ✓ GOOD: Brief, descriptive
description: Multi-agent collaborative software development

# ✗ BAD: Too verbose
description: This is a framework that uses multiple AI agents to collaborate on software development tasks through role-playing and iterative refinement...
```

---

## Configuration Validation Checklist

Before running experiments, verify:

- [ ] `model` is specified and valid
- [ ] `prompts_dir` exists and contains step files
- [ ] Each framework has all required fields (`repo_url`, `commit_hash`, `api_key_env`)
- [ ] `stopping_rule.max_runs` is positive integer
- [ ] `stopping_rule.python_version` is quoted string
- [ ] `analysis.bootstrap_samples` is positive integer (typically 1000+)
- [ ] `analysis.significance_level` is float between 0 and 1
- [ ] All referenced environment variables are set
- [ ] Repository URLs are accessible
- [ ] Commit hashes exist in repositories

**Quick Validation:**
```bash
# Run validation tests
pytest tests/unit/test_report_generation.py -v
```

---

## Troubleshooting Configuration Issues

See [troubleshooting.md](./troubleshooting.md) for detailed solutions to common configuration problems.

**Quick Reference:**

| Error Message | Solution |
|--------------|----------|
| Missing required configuration: 'model' | Add `model:` key to config |
| Missing required configuration: 'frameworks' | Add `frameworks:` section |
| Framework configuration incomplete | Add missing fields to framework |
| Prompts directory not found | Check `prompts_dir` path exists |
| No step files found | Add `step_N.txt` files to prompts dir |

---

## Related Documentation

- [Validation System](./validation_system.md) - Validation functions reference
- [Troubleshooting Guide](./troubleshooting.md) - Common errors and fixes
- [README](../README.md) - Getting started guide

---

## Configuration File Location

**Default:** `config/experiment.yaml`

**Loading in Code:**
```python
from src.orchestrator.config_loader import load_experiment_config

config = load_experiment_config('config/experiment.yaml')
```

**Environment Override:**
```bash
# Use different config file
export BAES_CONFIG=config/experiment_debug.yaml
python runners/run_experiment.py
```

---

**Need Help?**

If you're having configuration issues:
1. Check error messages - they indicate what's missing
2. Review this reference for correct field names
3. See [troubleshooting.md](./troubleshooting.md) for common issues
4. Run validation tests: `pytest tests/unit/test_report_generation.py -v`
