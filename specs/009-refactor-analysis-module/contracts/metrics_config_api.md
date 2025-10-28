# API Contract: MetricsConfig

**Feature**: 009-refactor-analysis-module  
**Module**: `src.utils.metrics_config`  
**Version**: 2.0.0 (Breaking Changes)

## Overview

Centralized metrics configuration singleton providing read-only access to metric definitions loaded from `experiment.yaml`. Simplified API replaces category-specific getters with unified interface and flexible filtering.

---

## Public API

### Constructor

```python
def __init__(self, config_path: Optional[Path] = None) -> None:
    """
    Initialize metrics configuration.
    
    Args:
        config_path: Path to experiment.yaml (defaults to config.yaml in project root)
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ConfigMigrationError: If old 3-subsection format detected
        ConfigValidationError: If required fields missing
        
    Example:
        config = MetricsConfig()  # Uses default path
        config = MetricsConfig(Path('experiments/exp1/config.yaml'))
    """
```

**Preconditions**:
- Config file exists at specified path
- Config file is valid YAML
- Metrics section uses new unified format (not reliable/derived/excluded subsections)

**Postconditions**:
- All metrics parsed into MetricDefinition objects
- Config format validated
- Ready for queries

---

### get_all_metrics()

```python
def get_all_metrics(self) -> Dict[str, MetricDefinition]:
    """
    Get all metric definitions from unified metrics section.
    
    Returns:
        Dictionary mapping metric keys to MetricDefinition objects.
        Returns a copy to prevent external modification.
        
    Example:
        all_metrics = config.get_all_metrics()
        print(f"Total metrics: {len(all_metrics)}")
        
        for key, metric in all_metrics.items():
            print(f"{key}: {metric.name}")
    """
```

**Preconditions**: None (always succeeds after successful initialization)

**Postconditions**:
- Returns dict with all configured metrics
- Returned dict is a shallow copy (safe to modify)
- Original _metrics dict unchanged

**Performance**: O(n) where n = number of metrics (typically <50)

---

### get_metric()

```python
def get_metric(self, key: str) -> Optional[MetricDefinition]:
    """
    Get specific metric definition by key.
    
    Args:
        key: Metric identifier (e.g., 'TOK_IN', 'COST_USD')
        
    Returns:
        MetricDefinition if metric exists, None otherwise.
        Returns the actual object (not a copy).
        
    Example:
        tok_in = config.get_metric('TOK_IN')
        if tok_in:
            print(f"Unit: {tok_in.unit}")
            formatted = tok_in.format_value(12345)
    """
```

**Preconditions**: None

**Postconditions**:
- Returns None if key not found (no exception)
- Returns MetricDefinition reference if found

**Performance**: O(1) dict lookup

---

### get_metrics_by_category()

```python
def get_metrics_by_category(self, category: str) -> Dict[str, MetricDefinition]:
    """
    Filter metrics by category.
    
    Args:
        category: Category name (e.g., 'efficiency', 'cost', 'interaction')
        
    Returns:
        Dictionary of metrics in specified category.
        Empty dict if no matches.
        
    Example:
        efficiency = config.get_metrics_by_category('efficiency')
        for key, metric in efficiency.items():
            print(f"{metric.name}: {metric.ideal_direction}")
    """
```

**Preconditions**: None (category string can be any value)

**Postconditions**:
- Returns empty dict if category not found
- Returns matching metrics dict if found
- Case-sensitive category matching

**Performance**: O(n) linear scan

---

### get_metrics_by_filter()

```python
def get_metrics_by_filter(self, **filters) -> Dict[str, MetricDefinition]:
    """
    Flexible filtering by any MetricDefinition attribute.
    
    Args:
        **filters: Attribute name/value pairs to match.
                  All filters must match (AND logic).
        
    Returns:
        Dictionary of metrics matching all filters.
        Empty dict if no matches.
        
    Example:
        # Get all statistical test metrics
        stats = config.get_metrics_by_filter(statistical_test=True)
        
        # Get minimize metrics that aggregate by sum
        minimize_sum = config.get_metrics_by_filter(
            ideal_direction='minimize',
            aggregation='sum'
        )
        
        # Get calculated metrics
        derived = config.get_metrics_by_filter(data_source='calculated')
    """
```

**Preconditions**: None

**Postconditions**:
- Returns empty dict if no matches
- Only metrics matching ALL filters returned
- Uses getattr() so any attribute valid

**Performance**: O(n * m) where n=metrics, m=number of filters

---

## Removed Methods (Breaking Changes)

The following methods from v1.x are **REMOVED** in v2.0:

```python
# REMOVED - Use get_all_metrics() + auto-discovery instead
def get_reliable_metrics(self) -> Dict[str, MetricDefinition]:
    ...

# REMOVED - Use get_metrics_by_filter(data_source='calculated') instead
def get_derived_metrics(self) -> Dict[str, MetricDefinition]:
    ...

# REMOVED - Use auto-discovery (metrics without data) instead
def get_excluded_metrics(self) -> Dict[str, MetricDefinition]:
    ...
```

**Migration**:
- `get_reliable_metrics()` → `get_all_metrics()` (report generator does auto-discovery)
- `get_derived_metrics()` → `get_metrics_by_filter(aggregation='calculated')`
- `get_excluded_metrics()` → No direct replacement (handled by discovery logic)

---

## Error Handling

### ConfigMigrationError

Raised when old 3-subsection format detected.

```python
# Example old format that triggers error:
metrics:
  reliable_metrics:
    TOK_IN: {...}  # ← Old format!
```

**Error Message**:
```
ConfigMigrationError: Detected old config format with reliable_metrics/derived_metrics/excluded_metrics subsections.

Please migrate to new unified format. See docs/CONFIG_MIGRATION_GUIDE.md

Quick migration:
  OLD: metrics:
         reliable_metrics:
           TOK_IN: {...}
  NEW: metrics:
         TOK_IN: {...}
```

**Recovery**: Migrate config using guide in `quickstart.md`

---

### ConfigValidationError

Raised when required fields missing.

```python
# Example invalid config:
metrics:
  TOK_IN:
    name: "Input Tokens"
    # Missing: display_format, unit, category, etc.
```

**Error Message**:
```
ConfigValidationError: Missing required config key 'display_format' in metrics.TOK_IN.
Expected keys: ['name', 'description']
Add 'display_format' to your experiment.yaml under metrics.TOK_IN.
```

**Recovery**: Add missing fields as indicated

---

## Thread Safety

**NOT thread-safe**. MetricsConfig is designed for single-threaded use during report generation. If concurrent access needed, wrap in lock.

---

## Example Usage

### Basic Query

```python
from src.utils.metrics_config import MetricsConfig

# Load config
config = MetricsConfig('config/experiment.yaml')

# Get all metrics
all_metrics = config.get_all_metrics()
print(f"Configured metrics: {len(all_metrics)}")

# Get specific metric
cost = config.get_metric('COST_USD')
if cost:
    value = 12.3456
    print(f"Formatted: {cost.format_value(value)}")  # "$12.3456"
```

### Category Filtering

```python
# Get all efficiency metrics
efficiency = config.get_metrics_by_category('efficiency')

for key, metric in efficiency.items():
    print(f"{metric.name}:")
    print(f"  Unit: {metric.unit}")
    print(f"  Goal: {metric.ideal_direction}")
```

### Advanced Filtering

```python
# Get all metrics eligible for stopping rules
stopping_metrics = config.get_metrics_by_filter(
    stopping_rule_eligible=True
)

# Get all maximize metrics that use statistical tests
maximize_stats = config.get_metrics_by_filter(
    ideal_direction='maximize',
    statistical_test=True
)
```

---

## Contract Guarantees

### Invariants

1. **Singleton Behavior**: One config per file path
2. **Immutable After Load**: Config doesn't change after initialization
3. **Key Uniqueness**: Metric keys are unique within config
4. **Format Validation**: Only new unified format accepted

### Performance Guarantees

- `get_all_metrics()`: O(n) copy operation
- `get_metric(key)`: O(1) lookup
- `get_metrics_by_category(cat)`: O(n) scan
- `get_metrics_by_filter(**filters)`: O(n * m) scan
- Initialization: O(n) parse all metrics

Where n = number of metrics (typically <50), m = number of filters (typically <3)

### Memory Guarantees

- Single config instance per file
- All metrics kept in memory (small footprint, typically <100KB)
- get_all_metrics() creates shallow copy (minimal overhead)

---

## Testing Contract

### Unit Tests Required

```python
def test_load_valid_config():
    """Test successful load of new format config."""
    
def test_reject_old_format():
    """Test ConfigMigrationError raised for old format."""
    
def test_missing_required_field():
    """Test ConfigValidationError for missing fields."""
    
def test_get_all_metrics():
    """Test get_all_metrics() returns all metrics."""
    
def test_get_metric_exists():
    """Test get_metric() returns metric when exists."""
    
def test_get_metric_not_exists():
    """Test get_metric() returns None when not exists."""
    
def test_get_metrics_by_category():
    """Test category filtering."""
    
def test_get_metrics_by_filter():
    """Test flexible filtering."""
    
def test_metric_definition_format_value():
    """Test MetricDefinition.format_value()."""
```

---

## Version History

- **v2.0.0** (2025-10-28): Breaking changes - removed subsection methods, unified metrics section
- **v1.x**: Original implementation with reliable/derived/excluded subsections

---

## See Also

- Data Model: `data-model.md`
- Migration Guide: `quickstart.md`
- Report Generator Contract: `contracts/report_generator_api.md`
