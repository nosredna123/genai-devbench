# API Contract: Report Generator (Refactored)

**Feature**: 009-refactor-analysis-module  
**Module**: `src.analysis.report_generator`  
**Version**: 2.0.0 (Breaking Changes)

## Overview

Statistical report generation module refactored to eliminate all hardcoded metric lists and implement fully dynamic, config-driven report generation with fail-fast validation.

---

## Key Changes from v1.x

### Removed

- ❌ Hardcoded `RELIABLE_METRICS` set (line 609)
- ❌ Calls to `metrics_config.get_reliable_metrics()` (lines 2148, 2758)
- ❌ Permissive `.get()` calls with defaults
- ❌ Manual metric categorization

### Added

- ✅ Auto-discovery of metrics from run data
- ✅ Strict validation helpers (`_require_config_value`, `_require_nested_config`)
- ✅ Dynamic limitations section generation
- ✅ Fail-fast error handling

---

## Main Entry Point

### generate_statistical_report()

```python
def generate_statistical_report(
    experiment_dir: Path,
    output_file: Path,
    metrics_config: MetricsConfig
) -> None:
    """
    Generate comprehensive statistical analysis report.
    
    Args:
        experiment_dir: Path to experiment directory with runs/
        output_file: Path where markdown report will be written
        metrics_config: Loaded MetricsConfig instance
        
    Raises:
        ConfigValidationError: If required config keys missing
        MetricsValidationError: If unknown metrics in run data
        FileNotFoundError: If experiment dir or run files missing
        
    Report Sections (Always Generated):
        1. Executive Summary
        2. Foundational Concepts
        3. Metrics Tables (with data / without data)
        4. Statistical Analysis
        5. Cost Breakdown
        6. Limitations
        
    Example:
        config = MetricsConfig('config/experiment.yaml')
        generate_statistical_report(
            experiment_dir=Path('experiments/exp1'),
            output_file=Path('reports/analysis.md'),
            metrics_config=config
        )
    ```

**Preconditions**:
- `experiment_dir/runs/*/metrics.json` files exist
- metrics_config loaded and validated
- All metrics in run data exist in metrics_config

**Postconditions**:
- Report file written to output_file
- All standard sections present
- Only metrics with data in analysis tables
- Metrics without data in limitations section

---

## New Helper Functions

### _discover_metrics_with_data()

```python
def _discover_metrics_with_data(
    run_files: List[Path],
    metrics_config: MetricsConfig
) -> MetricsDiscoveryResult:
    """
    Auto-discover which metrics have collected data.
    
    Args:
        run_files: List of paths to metrics.json files
        metrics_config: MetricsConfig instance
        
    Returns:
        MetricsDiscoveryResult with:
            - metrics_with_data: Set of keys with collected data
            - metrics_without_data: Set of configured keys with no data
            - unknown_metrics: Set of keys in data but not config (should be empty)
            - run_count: Number of run files scanned
            
    Raises:
        MetricsValidationError: If unknown_metrics non-empty
        
    Example:
        result = _discover_metrics_with_data(run_files, config)
        print(f"Measured: {result.metrics_with_data}")
        print(f"Unmeasured: {result.metrics_without_data}")
    ```

**Algorithm**:
1. Scan all run files
2. Collect union of all metric keys from aggregate_metrics
3. Validate all data keys exist in config (fail if unknown)
4. Partition into with_data / without_data sets
5. Return discovery result

**Performance**: O(r * m) where r=runs, m=avg metrics per run

---

### _require_config_value()

```python
def _require_config_value(config: Dict, key: str, context: str) -> Any:
    """
    Get required config value with fail-fast validation.
    
    Args:
        config: Configuration dictionary
        key: Required key name
        context: Human-readable context for error messages
        
    Returns:
        Config value (guaranteed non-None)
        
    Raises:
        ConfigValidationError: If key missing or value is None
        
    Error Message Format:
        Missing required config key '{key}' in {context}.
        Expected keys: [list of actual keys]
        Add '{key}' to your experiment.yaml under {context}.
        
    Example:
        name = _require_config_value(framework, 'name', 'frameworks.autogpt')
        # If missing, raises clear error with fix suggestion
    ```

**Replaces**: `config.get(key, default)` calls

**Rationale**: Fail-fast principle - no silent defaults that mask config errors

---

### _require_nested_config()

```python
def _require_nested_config(config: Dict, path: List[str]) -> Any:
    """
    Get nested config value with path-aware error messages.
    
    Args:
        config: Root configuration dictionary
        path: List of keys forming path (e.g., ['metrics', 'TOK_IN', 'name'])
        
    Returns:
        Value at specified path
        
    Raises:
        ConfigValidationError: If any key in path missing
        
    Example:
        # Get experiment.frameworks[0].name
        name = _require_nested_config(
            config, 
            ['experiment', 'frameworks', 0, 'name']
        )
    ```

---

### _generate_limitations_section()

```python
def _generate_limitations_section(
    metrics_config: MetricsConfig,
    metrics_without_data: Set[str]
) -> List[str]:
    """
    Generate limitations section listing unmeasured metrics.
    
    Args:
        metrics_config: MetricsConfig instance
        metrics_without_data: Set of metric keys with no collected data
        
    Returns:
        List of markdown lines for limitations section
        
    Content:
        - Lists each unmeasured metric
        - Shows status and reason from config
        - Explains why data not collected
        
    Example Output:
        ## Limitations
        
        **Unmeasured Metrics**: The following metrics are defined but have no collected data:
        
        - **Autonomy Rate** (`AUTR`): Requires HITL detection implementation
        - **Code Quality** (`CODE_QUAL`): Static analyzer integration pending
    ```

**Dynamic Generation**: Content changes based on actual run data, no manual updates needed

---

## Modified Functions

### _generate_executive_summary()

**Changes**:
- ❌ Removed hardcoded RELIABLE_METRICS set
- ✅ Uses metrics_with_data from discovery
- ✅ Filters to only metrics with actual data

**Signature** (unchanged):
```python
def _generate_executive_summary(
    frameworks_data: Dict[str, List[Dict[str, float]]],
    run_counts: Dict[str, int]
) -> List[str]:
```

---

### _generate_metric_table_from_config()

**Changes**:
- ❌ Removed `category='reliable'` parameter
- ❌ Removed `metrics_config.get_reliable_metrics()` call
- ✅ Uses `metrics_config.get_all_metrics()` + filtering by data availability

**New Signature**:
```python
def _generate_metric_table_from_config(
    metrics_config: MetricsConfig,
    metrics_with_data: Set[str]
) -> List[str]:
    """
    Generate metric definition table for metrics with collected data.
    
    Only includes metrics that have data in run files.
    """
```

---

## Validation Strategy

### Config Validation

All config access uses fail-fast helpers:

```python
# OLD (permissive):
name = framework.get('name', 'Unknown')  # Silent default

# NEW (fail-fast):
name = _require_config_value(framework, 'name', 'frameworks.autogpt')
```

### Metrics Validation

All metrics in data must exist in config:

```python
config_keys = set(metrics_config.get_all_metrics().keys())
data_keys = {key for run in runs for key in run['aggregate_metrics']}

unknown = data_keys - config_keys
if unknown:
    raise MetricsValidationError(
        f"Unknown metrics in run data: {unknown}\n"
        f"Add these metrics to experiment.yaml or remove from run data."
    )
```

---

## Error Messages

### Example 1: Missing Config Key

```
ConfigValidationError: Missing required config key 'name' in frameworks.autogpt.
Expected keys: ['id', 'organization', 'description']
Add 'name' to your experiment.yaml under frameworks.autogpt.
```

### Example 2: Unknown Metric

```
MetricsValidationError: Unknown metrics in run data: {'OLD_METRIC', 'DEPRECATED'}

These metrics appear in metrics.json but not in experiment.yaml metrics section.

Options:
  1. Add metric definitions to experiment.yaml
  2. Remove metrics from run data files
  3. Check for typos (metric keys are case-sensitive)
```

### Example 3: Old Config Format

```
ConfigMigrationError: Detected old config format with reliable_metrics subsection.

See docs/CONFIG_MIGRATION_GUIDE.md for migration instructions.

Quick fix: Merge all subsections into single metrics section.
```

---

## Report Structure

All reports contain these sections in order:

1. **Executive Summary**
   - Overview of experiment
   - Framework run counts
   - Key metric ranges

2. **Foundational Concepts**
   - Statistical methods explanation
   - Metric definitions table (with data)
   
3. **Metrics Tables**
   - Aggregate statistics (only metrics with data)
   - Grouped by category
   
4. **Statistical Analysis**
   - Kruskal-Wallis tests
   - Pairwise comparisons
   - Effect sizes
   
5. **Cost Breakdown**
   - Token costs
   - Cost per framework
   
6. **Limitations**
   - Unmeasured metrics (auto-generated)
   - Scope boundaries

---

## Performance

### Benchmarks

- Report generation: <30 seconds for 50 runs × 3 frameworks
- Metric discovery: <1 second for 100 run files
- Config validation: <100ms

### Optimizations

- Single-pass file scanning for discovery
- Cached metrics dict in MetricsConfig
- Batch statistical computations

---

## Testing Requirements

### Unit Tests

```python
def test_discover_metrics_with_data():
    """Test auto-discovery finds correct metrics."""
    
def test_discover_metrics_fails_on_unknown():
    """Test validation error for unknown metrics."""
    
def test_require_config_value_present():
    """Test _require_config_value returns value when present."""
    
def test_require_config_value_missing():
    """Test _require_config_value raises when missing."""
    
def test_generate_limitations_section():
    """Test limitations section lists unmeasured metrics."""
```

### Integration Tests

```python
def test_report_generation_end_to_end():
    """Test complete report generation with new config format."""
    
def test_report_fails_on_old_config():
    """Test old config format triggers migration error."""
    
def test_report_with_mixed_metrics():
    """Test report with some metrics having data, some not."""
```

---

## Migration from v1.x

### Step 1: Update Config Format

Merge subsections into unified metrics section (see `quickstart.md`).

### Step 2: Update Client Code

```python
# OLD:
reliable = config.get_reliable_metrics()
for key in reliable:
    ...

# NEW:
all_metrics = config.get_all_metrics()
discovery = _discover_metrics_with_data(run_files, config)
for key in discovery.metrics_with_data:
    ...
```

### Step 3: Remove Hardcoded Lists

Delete all `RELIABLE_METRICS` sets and similar hardcoded metric lists from client code.

---

## See Also

- MetricsConfig Contract: `contracts/metrics_config_api.md`
- Migration Guide: `quickstart.md`
- Data Model: `data-model.md`
- Research: `research.md`
