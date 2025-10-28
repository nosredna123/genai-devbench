# Quick Start: Refactored Report Generator

**Feature**: 009-refactor-analysis-module  
**Date**: 2025-10-28

## For Existing Users: Configuration Migration

### Overview

The report generator has been refactored to eliminate hardcoded metric lists and implement fully dynamic, config-driven report generation. This requires a one-time configuration migration.

### What Changed

**Before (Old Format)**:
- Metrics divided into 3 subsections: `reliable_metrics`, `derived_metrics`, `excluded_metrics`
- Report generator had hardcoded `RELIABLE_METRICS` set
- Metrics categorization was manual and error-prone

**After (New Format)**:
- Single unified `metrics` section
- Auto-discovery determines which metrics have data
- Metrics without data appear in limitations section
- Zero hardcoded lists

### Migration Steps

#### Step 1: Backup Current Config

```bash
cp config/experiment.yaml config/experiment.yaml.backup
```

#### Step 2: Migrate Metrics Section

**OLD FORMAT** (`config/experiment.yaml`):
```yaml
metrics:
  reliable_metrics:
    TOK_IN:
      name: "Input Tokens"
      display_format: "{:,.0f}"
      unit: "tokens"
      category: "efficiency"
      # ... other fields
      
    TOK_OUT:
      name: "Output Tokens"
      # ...
  
  derived_metrics:
    COST_USD:
      name: "Total Cost"
      # ...
  
  excluded_metrics:
    AUTR:
      name: "Autonomy Rate"
      reason: "HITL detection not implemented"
```

**NEW FORMAT** (merge all subsections):
```yaml
metrics:
  # All metrics in single section
  TOK_IN:
    name: "Input Tokens"
    display_format: "{:,.0f}"
    unit: "tokens"
    category: "efficiency"
    ideal_direction: "minimize"
    data_source: "openai_usage_api"
    aggregation: "sum"
    statistical_test: true
    stopping_rule_eligible: true
    description: "Total tokens sent to LLM across all steps"
    # No status field = implemented metric
    
  TOK_OUT:
    name: "Output Tokens"
    display_format: "{:,.0f}"
    unit: "tokens"
    category: "efficiency"
    ideal_direction: "minimize"
    data_source: "openai_usage_api"
    aggregation: "sum"
    statistical_test: true
    stopping_rule_eligible: true
    description: "Total tokens received from LLM"
    
  COST_USD:
    name: "Total Cost"
    display_format: "${:.4f}"
    unit: "USD"
    category: "cost"
    ideal_direction: "minimize"
    data_source: "calculated"
    aggregation: "calculated"
    statistical_test: true
    stopping_rule_eligible: false
    description: "Total USD cost of API calls"
    calculation:
      formula: "(TOK_IN - CACHED) * input_price + TOK_OUT * output_price"
    
  AUTR:
    name: "Autonomy Rate"
    display_format: "{:.2%}"
    unit: "rate"
    category: "interaction"
    ideal_direction: "maximize"
    data_source: "hitl_detector"
    aggregation: "mean"
    statistical_test: false
    stopping_rule_eligible: false
    description: "Percentage of steps without human intervention"
    status: "not_implemented"  # Mark as not measured
    reason: "Requires HITL detection implementation"
```

#### Step 3: Add Required Fields

Ensure every metric has these required fields:

- `name` - Human-readable name
- `description` - What the metric measures
- `unit` - Unit of measurement
- `category` - Grouping category
- `ideal_direction` - 'minimize' or 'maximize'
- `data_source` - Where data comes from
- `aggregation` - How to aggregate ('sum', 'mean', 'count', 'calculated')
- `display_format` - Python format string

#### Step 4: Mark Unmeasured Metrics

For metrics previously in `excluded_metrics`, add:

```yaml
status: "not_implemented"
reason: "Brief explanation why not measured"
```

#### Step 5: Test Migration

```bash
# Run report generation to validate new config
python -m src.analysis.report_generator
```

**Expected**: Report generates successfully with updated config.

**If you see errors**:
- `ConfigMigrationError`: Old format detected - complete migration steps above
- `ConfigValidationError`: Missing required field - check error message for specific key
- `MetricsValidationError`: Unknown metric in run data - add to config or remove from data

---

## For New Users: Creating an Experiment Config

### Minimal Config

```yaml
# config/experiment.yaml
experiment:
  name: "my_experiment"
  description: "Comparing code generation frameworks"

frameworks:
  - id: "autogpt"
    name: "AutoGPT"
  - id: "chatdev"
    name: "ChatDev"

metrics:
  TOK_IN:
    name: "Input Tokens"
    description: "Tokens sent to LLM"
    unit: "tokens"
    category: "efficiency"
    ideal_direction: "minimize"
    data_source: "openai_usage_api"
    aggregation: "sum"
    display_format: "{:,.0f}"
    statistical_test: true
    stopping_rule_eligible: true
    
  TOK_OUT:
    name: "Output Tokens"
    description: "Tokens received from LLM"
    unit: "tokens"
    category: "efficiency"
    ideal_direction: "minimize"
    data_source: "openai_usage_api"
    aggregation: "sum"
    display_format: "{:,.0f}"
    statistical_test: true
    stopping_rule_eligible: true
```

### Adding a New Metric

1. Add to `metrics` section in `config/experiment.yaml`
2. Provide all required fields (see Step 3 above)
3. If metric has data, it automatically appears in reports
4. If metric has no data, it appears in limitations section

**Example - Adding a quality metric**:

```yaml
CODE_QUALITY:
  name: "Code Quality Score"
  description: "Automated code quality assessment (0-100)"
  unit: "score"
  category: "quality"
  ideal_direction: "maximize"
  data_source: "static_analyzer"
  aggregation: "mean"
  display_format: "{:.1f}"
  statistical_test: true
  stopping_rule_eligible: false
  status: "planned"  # If not yet collecting data
  reason: "Static analyzer integration in progress"
```

---

## Common Tasks

### Task 1: Generate Report

```bash
# From repo root
python -m src.analysis.report_generator \
  --experiment-dir experiments/my_experiment \
  --output reports/analysis.md
```

### Task 2: Validate Config

```python
from src.utils.metrics_config import MetricsConfig

# Load and validate config
config = MetricsConfig('config/experiment.yaml')

# Check all metrics loaded
all_metrics = config.get_all_metrics()
print(f"Loaded {len(all_metrics)} metrics")

# Filter by category
efficiency_metrics = config.get_metrics_by_category('efficiency')
print(f"Efficiency metrics: {list(efficiency_metrics.keys())}")
```

### Task 3: Check Which Metrics Have Data

```python
from pathlib import Path
import json

# Scan run files
run_files = Path('experiments/my_experiment/runs').glob('*/metrics.json')
all_data_metrics = set()

for run_file in run_files:
    with open(run_file) as f:
        data = json.load(f)
        all_data_metrics.update(data.get('aggregate_metrics', {}).keys())

print(f"Metrics with data: {all_data_metrics}")
```

---

## Validation Commands

Before running a full experiment, validate your configuration:

### Quick Validation

```bash
# Test config loads without errors
python -c "from src.utils.metrics_config import MetricsConfig; mc = MetricsConfig('config/experiment.yaml'); print(f'✅ Config valid: {len(mc.get_all_metrics())} metrics loaded')"
```

### Check for Old Format

```bash
# Detect if old format is still present
python -c "
from src.utils.metrics_config import MetricsConfig
try:
    MetricsConfig('config/experiment.yaml')
    print('✅ Using new unified format')
except Exception as e:
    if 'old' in str(e).lower():
        print('❌ Old format detected - migration required')
    else:
        print(f'❌ Config error: {e}')
"
```

### List All Configured Metrics

```bash
# See all metrics in your config
python -c "from src.utils.metrics_config import get_metrics_config; mc = get_metrics_config('config/experiment.yaml'); print('\n'.join(f'{k}: {v.name}' for k,v in mc.get_all_metrics().items()))"
```

### Check Metrics by Status

```bash
# List metrics by implementation status
python -c "
from src.utils.metrics_config import get_metrics_config
mc = get_metrics_config('config/experiment.yaml')
measured = [k for k, v in mc.get_all_metrics().items() if v.status != 'unmeasured']
unmeasured = [k for k, v in mc.get_all_metrics().items() if v.status == 'unmeasured']
print(f'Measured: {measured}')
print(f'Unmeasured: {unmeasured}')
"
```

---

## Troubleshooting

### Error: "Old config format detected"

**Cause**: Config still uses `reliable_metrics`, `derived_metrics`, or `excluded_metrics` subsections.

**Solution**: Follow migration steps above. Merge all subsections into single `metrics` section.

---

### Error: "Missing required config key 'name' in metrics.TOK_IN"

**Cause**: Metric definition missing required field.

**Solution**: Add all required fields (see Step 3 in migration guide).

---

### Error: "Unknown metrics in run data: {'OLD_METRIC'}"

**Cause**: Run data contains metric not defined in current config.

**Solution**: 
- **Option A**: Add metric definition to `config/experiment.yaml`
- **Option B**: Remove old metric data from run files
- **Option C**: Acceptable if renaming - document in config with old name

---

### Metric appears in limitations section but should have data

**Cause**: Metric defined in config but no data collected in runs.

**Debug**:
1. Check run files: `cat experiments/*/runs/*/metrics.json | grep METRIC_KEY`
2. Verify metric key matches exactly (case-sensitive)
3. Check if metric collector is enabled
4. Review metric `data_source` field - is data source active?

---

### Report generation is slow

**Expected Performance**: <30 seconds for 50 runs across 3 frameworks

**If slower**:
1. Check number of runs: `find experiments/*/runs -name metrics.json | wc -l`
2. Check metrics count: `grep -c '^\s\s[A-Z_]+:' config/experiment.yaml`
3. Profile: `python -m cProfile -o report.prof -m src.analysis.report_generator`

---

## Best Practices

### ✅ DO

- Keep metric keys short and descriptive (e.g., `TOK_IN`, `COST_USD`)
- Use consistent units within categories
- Mark unmeasured metrics with `status` and `reason`
- Document calculations in `description` field
- Test config changes with `--dry-run` flag

### ❌ DON'T

- Use spaces or special characters in metric keys
- Duplicate metric definitions
- Leave `description` field empty (aids understanding)
- Mix measurement scales (e.g., tokens and MB in same category)
- Change metric keys without updating run data

---

## Migration Checklist

- [ ] Backup current `config/experiment.yaml`
- [ ] Merge `reliable_metrics`, `derived_metrics`, `excluded_metrics` into single `metrics` section
- [ ] Add all required fields to each metric
- [ ] Mark unmeasured metrics with `status: "not_implemented"` and `reason`
- [ ] Remove old subsection keys (`reliable_metrics`, etc.)
- [ ] Test report generation: `python -m src.analysis.report_generator`
- [ ] Verify all expected metrics appear in report
- [ ] Check limitations section lists unmeasured metrics correctly
- [ ] Commit updated config to version control

---

## Example Complete Config

See `config_sets/default/experiment.yaml` for a full working example with all standard metrics defined.

---

## Support

**Documentation**: `/docs/CONFIG_MIGRATION_GUIDE.md` (comprehensive guide)  
**Issues**: Report config validation errors with full error message  
**Constitution**: Breaking changes acceptable per principle XII (No Backward Compatibility Burden)
