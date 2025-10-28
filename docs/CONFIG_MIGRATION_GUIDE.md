# Configuration Migration Guide

**Feature**: 009-refactor-analysis-module  
**Status**: Active - Migration Required for New Experiments  
**Last Updated**: 2025-10-28

## Overview

This guide helps you migrate from the old 3-subsection metrics format to the new unified metrics configuration format introduced in Feature 009.

## Why Migrate?

The new format provides:

1. **Dynamic Discovery**: Metrics are auto-discovered from run data - no hardcoded lists
2. **Better Documentation**: Each metric has `status` and `reason` fields explaining why it's unmeasured
3. **Flexible Filtering**: Use `get_metrics_by_filter()` to select metrics by any attribute
4. **Fail-Fast Validation**: Clear errors if config doesn't match run data
5. **Cleaner API**: Single `get_all_metrics()` instead of three separate methods

## What Changed?

### Old Format (Deprecated)

The old format divided metrics into three subsections:

```yaml
metrics:
  reliable_metrics:
    TOK_IN:
      name: "Input Tokens"
      key: "TOK_IN"
      category: "tokens"
      # ...
    
  derived_metrics:
    COST_USD:
      name: "Total Cost (USD)"
      key: "COST_USD"
      category: "cost"
      # ...
  
  excluded_metrics:
    AUTR:
      name: "Automation Rate"
      key: "AUTR"
      category: "quality"
      # ...
```

**Problems**:
- Hardcoded distinction between "reliable" vs "derived" vs "excluded"
- Difficult to understand why metrics are excluded
- No way to track measurement status dynamically

### New Format (Required)

The new format uses a single unified section with optional `status` and `reason` fields:

```yaml
metrics:
  # Measured metrics (no status field)
  TOK_IN:
    name: "Input Tokens"
    key: "TOK_IN"
    category: "tokens"
    unit: "tokens"
    display_format: "{:,.0f}"
    description: "Total input tokens sent to LLM"
  
  # Derived metrics
  COST_USD:
    name: "Total Cost (USD)"
    key: "COST_USD"
    category: "cost"
    unit: "$"
    display_format: "${:.2f}"
    description: "Total API cost"
    status: "derived"
    reason: "Calculated from token counts and pricing"
  
  # Unmeasured metrics with reason
  AUTR:
    name: "Automation Rate"
    key: "AUTR"
    category: "quality"
    unit: "%"
    display_format: "{:.1f}%"
    description: "Percentage of steps completed without errors"
    status: "unmeasured"
    reason: "Requires manual code review - not yet automated"
```

**Benefits**:
- Single source of truth for all metrics
- Clear documentation of why metrics are unmeasured
- Auto-discovery determines which metrics have data
- Supports dynamic filtering by any attribute

## Migration Steps

### Step 1: Backup Your Config

```bash
cp config/experiment.yaml config/experiment.yaml.backup
```

### Step 2: Identify Your Metrics Sections

Open `config/experiment.yaml` and find the `metrics:` section. It should have three subsections:
- `reliable_metrics`
- `derived_metrics`
- `excluded_metrics`

### Step 3: Merge Into Single Section

Create a new `metrics:` section with all metrics at the same level:

**Before**:
```yaml
metrics:
  reliable_metrics:
    TOK_IN:
      name: "Input Tokens"
      # ...
  
  derived_metrics:
    COST_USD:
      name: "Total Cost"
      # ...
  
  excluded_metrics:
    AUTR:
      name: "Automation Rate"
      # ...
```

**After**:
```yaml
metrics:
  TOK_IN:
    name: "Input Tokens"
    key: "TOK_IN"
    category: "tokens"
    unit: "tokens"
    display_format: "{:,.0f}"
    description: "Total input tokens sent to LLM"
  
  COST_USD:
    name: "Total Cost"
    key: "COST_USD"
    category: "cost"
    unit: "$"
    display_format: "${:.2f}"
    description: "Total API cost"
    status: "derived"
    reason: "Calculated from TOK_IN, TOK_OUT, CACHED_TOKENS using pricing config"
  
  AUTR:
    name: "Automation Rate"
    key: "AUTR"
    category: "quality"
    unit: "%"
    display_format: "{:.1f}%"
    description: "Percentage of steps completed without errors"
    status: "unmeasured"
    reason: "Requires manual code review - not yet automated"
```

### Step 4: Add Status/Reason Fields

For metrics that were in:

- **`reliable_metrics`**: No `status` field needed (these are measured)
- **`derived_metrics`**: Add `status: "derived"` and explain calculation in `reason`
- **`excluded_metrics`**: Add `status: "unmeasured"` and explain why in `reason`

### Step 5: Validate Required Fields

Ensure each metric has:

- ✅ `name`: Human-readable metric name
- ✅ `key`: Unique identifier (matches data keys)
- ✅ `category`: Grouping (e.g., "tokens", "quality", "cost")
- ✅ `unit`: Display unit (e.g., "tokens", "%", "$")
- ✅ `display_format`: Python format string (e.g., `"{:,.0f}"`, `"{:.2f}%"`)
- ✅ `description`: What the metric measures
- ⚠️ `status`: Optional - only for derived/unmeasured metrics
- ⚠️ `reason`: Optional - only if `status` is set

### Step 6: Test Your Config

```bash
# Load config to check for errors
python -c "from src.utils.metrics_config import get_metrics_config; config = get_metrics_config(); print(f'Loaded {len(config.get_all_metrics())} metrics')"
```

If you see a `ConfigMigrationError`, the old format was detected. Follow the error message to fix it.

## Common Migration Scenarios

### Scenario 1: Simple Measured Metric

**Before** (in `reliable_metrics`):
```yaml
TOK_OUT:
  name: "Output Tokens"
  key: "TOK_OUT"
  category: "tokens"
  unit: "tokens"
  display_format: "{:,.0f}"
```

**After** (top-level in `metrics`):
```yaml
TOK_OUT:
  name: "Output Tokens"
  key: "TOK_OUT"
  category: "tokens"
  unit: "tokens"
  display_format: "{:,.0f}"
  description: "Total output tokens generated by LLM"
  # No status field - this is a measured metric
```

### Scenario 2: Derived Metric

**Before** (in `derived_metrics`):
```yaml
API_CALLS:
  name: "API Calls"
  key: "API_CALLS"
  category: "performance"
  unit: "calls"
  display_format: "{:,.0f}"
```

**After** (top-level with status):
```yaml
API_CALLS:
  name: "API Calls"
  key: "API_CALLS"
  category: "performance"
  unit: "calls"
  display_format: "{:,.0f}"
  description: "Total number of LLM API calls made"
  status: "derived"
  reason: "Counted from API interaction logs during execution"
```

### Scenario 3: Unmeasured Metric

**Before** (in `excluded_metrics`):
```yaml
MC:
  name: "Maintainability Compliance"
  key: "MC"
  category: "quality"
  unit: "%"
  display_format: "{:.1f}%"
```

**After** (top-level with reason):
```yaml
MC:
  name: "Maintainability Compliance"
  key: "MC"
  category: "quality"
  unit: "%"
  display_format: "{:.1f}%"
  description: "Code maintainability score"
  status: "unmeasured"
  reason: "Requires static analysis tool integration - not implemented"
```

### Scenario 4: Partially Measured Metric

**Before** (in `excluded_metrics`):
```yaml
HIT:
  name: "Hit Rate"
  key: "HIT"
  category: "quality"
  unit: "%"
  display_format: "{:.1f}%"
```

**After** (document partial measurement):
```yaml
HIT:
  name: "Hit Rate"
  key: "HIT"
  category: "quality"
  unit: "%"
  display_format: "{:.1f}%"
  description: "Test pass rate for generated code"
  status: "partial"
  reason: "Only measured for frameworks with test suite integration (BAEs, ChatDev)"
```

## Validation & Error Messages

### ConfigMigrationError

If you see this error:

```
ConfigMigrationError: Old metrics config format detected!

Found these deprecated subsections: reliable_metrics, derived_metrics, excluded_metrics

The metrics configuration format has changed. Please migrate to the new unified format.

Migration guide: docs/CONFIG_MIGRATION_GUIDE.md
```

**Solution**: Follow this guide to merge your subsections into a single `metrics:` section.

### MetricsValidationError

If you see this error:

```
MetricsValidationError: Unknown metrics found in run data: ['NEW_METRIC']

These metrics appear in the data but are not defined in experiment.yaml metrics section.
```

**Solution**: Add the missing metrics to your config under the unified `metrics:` section.

### ConfigValidationError

If you see this error:

```
ConfigValidationError: Missing required config key 'display_format' in metrics.TOK_IN
```

**Solution**: Add the missing required field to your metric definition.

## Example: Full Migration

### Before (Old Format)

```yaml
# config/experiment.yaml (OLD)
metrics:
  reliable_metrics:
    TOK_IN:
      name: "Input Tokens"
      key: "TOK_IN"
      category: "tokens"
      unit: "tokens"
      display_format: "{:,.0f}"
    
    TOK_OUT:
      name: "Output Tokens"
      key: "TOK_OUT"
      category: "tokens"
      unit: "tokens"
      display_format: "{:,.0f}"
  
  derived_metrics:
    COST_USD:
      name: "Total Cost"
      key: "COST_USD"
      category: "cost"
      unit: "$"
      display_format: "${:.2f}"
  
  excluded_metrics:
    AUTR:
      name: "Automation Rate"
      key: "AUTR"
      category: "quality"
      unit: "%"
      display_format: "{:.1f}%"
    
    MC:
      name: "Maintainability"
      key: "MC"
      category: "quality"
      unit: "%"
      display_format: "{:.1f}%"
```

### After (New Format)

```yaml
# config/experiment.yaml (NEW)
metrics:
  # Measured metrics - collected directly from run data
  TOK_IN:
    name: "Input Tokens"
    key: "TOK_IN"
    category: "tokens"
    unit: "tokens"
    display_format: "{:,.0f}"
    description: "Total input tokens sent to LLM across all API calls"
  
  TOK_OUT:
    name: "Output Tokens"
    key: "TOK_OUT"
    category: "tokens"
    unit: "tokens"
    display_format: "{:,.0f}"
    description: "Total output tokens generated by LLM across all API calls"
  
  # Derived metrics - calculated from other metrics
  COST_USD:
    name: "Total Cost (USD)"
    key: "COST_USD"
    category: "cost"
    unit: "$"
    display_format: "${:.2f}"
    description: "Total API cost based on token usage and model pricing"
    status: "derived"
    reason: "Calculated from TOK_IN, TOK_OUT, CACHED_TOKENS using pricing config"
  
  # Unmeasured metrics - defined but not collected
  AUTR:
    name: "Automation Rate"
    key: "AUTR"
    category: "quality"
    unit: "%"
    display_format: "{:.1f}%"
    description: "Percentage of steps completed without human intervention"
    status: "unmeasured"
    reason: "Requires manual code review to determine automation - not yet automated"
  
  MC:
    name: "Maintainability Compliance"
    key: "MC"
    category: "quality"
    unit: "%"
    display_format: "{:.1f}%"
    description: "Code maintainability score based on static analysis"
    status: "unmeasured"
    reason: "Requires static analysis tool integration (pylint/radon) - not implemented"
```

## Troubleshooting

### Issue: "I migrated but still get ConfigMigrationError"

**Check**: Did you remove the subsection keys (`reliable_metrics`, `derived_metrics`, `excluded_metrics`)?

The metrics should be directly under `metrics:`, not nested under subsections.

### Issue: "Metrics missing from report"

**Check**: Does your run data contain these metrics?

The new system only shows metrics with collected data. Check `metrics.json` files in your run directories. Metrics without data appear in the "Limitations" section of the report.

### Issue: "Report shows 'Unknown metrics' error"

**Check**: Are all metrics in your run data defined in config?

Every metric key in your `metrics.json` files must have a corresponding entry in the unified `metrics:` section.

### Issue: "Missing required field errors"

**Check**: Does each metric have all required fields?

Required: `name`, `key`, `category`, `unit`, `display_format`, `description`  
Optional: `status`, `reason` (only for derived/unmeasured metrics)

## Advanced: Custom Status Values

While `status: "unmeasured"` and `status: "derived"` are most common, you can use custom values:

```yaml
HIT:
  name: "Hit Rate"
  key: "HIT"
  category: "quality"
  unit: "%"
  display_format: "{:.1f}%"
  description: "Test pass rate"
  status: "partial"  # Custom status
  reason: "Only measured for frameworks with test integration (BAEs, ChatDev)"

ZDI:
  name: "Zero-Defect Index"
  key: "ZDI"
  category: "quality"
  unit: "score"
  display_format: "{:.2f}"
  description: "Code quality score"
  status: "experimental"  # Custom status
  reason: "New metric under evaluation - may change in future releases"
```

## Getting Help

- **Documentation**: See `docs/configuration_reference.md` for full config schema
- **Examples**: Check `config_sets/default/experiment_template.yaml` for complete example
- **Errors**: All validation errors include fix suggestions and file paths
- **Support**: Open an issue if you encounter migration problems

## Migration Checklist

- [ ] Backup current `config/experiment.yaml`
- [ ] Remove `reliable_metrics` subsection - move all metrics to top level
- [ ] Remove `derived_metrics` subsection - move all to top level with `status: "derived"`
- [ ] Remove `excluded_metrics` subsection - move all to top level with `status: "unmeasured"`
- [ ] Add `status` and `reason` fields to derived/unmeasured metrics
- [ ] Add `description` field to all metrics if missing
- [ ] Validate required fields (name, key, category, unit, display_format, description)
- [ ] Test config loading: `python -c "from src.utils.metrics_config import get_metrics_config; get_metrics_config()"`
- [ ] Run experiment and verify report generation
- [ ] Check "Limitations" section shows unmeasured metrics with reasons

## See Also

- `docs/configuration_reference.md` - Complete configuration schema
- `docs/metrics.md` - Metric definitions and measurement methods
- `config_sets/default/experiment_template.yaml` - Reference template with new format
- `specs/009-refactor-analysis-module/spec.md` - Feature specification
