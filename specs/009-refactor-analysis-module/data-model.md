# Data Model: MetricsConfig & Report Generator Refactoring

**Feature**: 009-refactor-analysis-module  
**Phase**: 1 (Design & Contracts)  
**Date**: 2025-10-28

## Entities

### MetricDefinition (Existing - No Changes)

Dataclass representing a single metric's metadata.

**Attributes**:
- `key: str` - Metric identifier (e.g., 'TOK_IN', 'COST_USD')
- `name: str` - Human-readable name
- `description: str` - Detailed description
- `unit: str` - Unit of measurement
- `category: str` - Category for grouping
- `ideal_direction: str` - 'minimize' or 'maximize'
- `data_source: str` - Where data comes from
- `aggregation: str` - How to aggregate across steps
- `display_format: str` - Python format string
- `statistical_test: bool` - Include in statistical tests
- `stopping_rule_eligible: bool` - Use in stopping rules
- `visualization_types: List[str]` - Compatible chart types
- `calculation: Optional[Dict]` - Calculation details for derived metrics
- `status: Optional[str]` - Status (e.g., 'not_implemented') **[NEW FIELD]**
- `reason: Optional[str]` - Reason for status **[NEW FIELD]**

**Methods**:
- `format_value(value: Any) -> str` - Format value using display_format
- `should_invert_for_normalization() -> bool` - Check if minimize metric

**Validation Rules**:
- `key` must be non-empty string
- `ideal_direction` must be 'minimize' or 'maximize'
- `aggregation` must be 'sum', 'mean', 'count', 'none', or 'calculated'

---

### MetricsConfig (Refactored)

Singleton providing centralized metrics configuration.

**State**:
- `config_path: Path` - Path to YAML config file
- `_config: Dict[str, Any]` - Raw config dictionary
- `_metrics: Dict[str, MetricDefinition]` - Parsed metric definitions

**Public Methods** (Simplified API):

```python
def get_all_metrics(self) -> Dict[str, MetricDefinition]:
    """
    Get all metric definitions (unified section).
    
    Returns:
        Dictionary mapping metric keys to MetricDefinition objects
    """
    
def get_metric(self, key: str) -> Optional[MetricDefinition]:
    """
    Get specific metric definition.
    
    Args:
        key: Metric identifier
        
    Returns:
        MetricDefinition if found, None otherwise
    """
    
def get_metrics_by_category(self, category: str) -> Dict[str, MetricDefinition]:
    """
    Filter metrics by category.
    
    Args:
        category: Category name (e.g., 'efficiency', 'cost')
        
    Returns:
        Dictionary of metrics in that category
    """
    
def get_metrics_by_filter(self, **filters) -> Dict[str, MetricDefinition]:
    """
    Flexible filtering by any MetricDefinition attribute.
    
    Args:
        **filters: Attribute name/value pairs to filter by
        
    Returns:
        Dictionary of metrics matching all filters
        
    Examples:
        get_metrics_by_filter(statistical_test=True)
        get_metrics_by_filter(category='efficiency', aggregation='sum')
    """
```

**Removed Methods**:
- ~~`get_reliable_metrics()`~~ - Use `get_all_metrics()` + auto-discovery
- ~~`get_derived_metrics()`~~ - Use `get_metrics_by_filter(data_source='calculated')`
- ~~`get_excluded_metrics()`~~ - Use auto-discovery (metrics without data)

**Private Methods**:

```python
def _load_config(self) -> None:
    """Load YAML config and validate format."""
    
def _parse_metrics(self) -> None:
    """
    Parse unified metrics section into MetricDefinition objects.
    
    Raises:
        ConfigMigrationError: If old 3-subsection format detected
        ConfigValidationError: If required fields missing
    """
    
def _detect_old_config_format(self) -> bool:
    """Check if config uses old reliable/derived/excluded subsections."""
```

---

### ReportSection (Conceptual - Not a Class)

Represents a standard report component. All sections always generated.

**Standard Sections** (Order):
1. Executive Summary
2. Foundational Concepts  
3. Metrics Tables (split: with data / without data)
4. Statistical Analysis
5. Cost Breakdown
6. Limitations

**Properties** (per section):
- Name (str)
- Generator function (callable)
- Required data dependencies

---

### FrameworkMetadata (Existing - No Changes)

Framework identification info.

**Attributes**:
- `id: str` - Short identifier
- `name: str` - Full name
- `organization: str` - Maintaining organization
- `description: str` - Brief description

---

### AggregateStatistics (Existing - No Changes)

Computed summary statistics for a metric.

**Attributes**:
- `mean: float`
- `median: float`
- `std_dev: float`
- `ci_lower: float` - 95% confidence interval lower bound
- `ci_upper: float` - 95% confidence interval upper bound
- `n: int` - Sample size

---

## New Validation Entities

### MetricsDiscoveryResult

Result of auto-discovery process.

**Attributes**:
```python
@dataclass
class MetricsDiscoveryResult:
    """Result of scanning run data for metrics."""
    
    metrics_with_data: Set[str]
    """Metrics that have collected data."""
    
    metrics_without_data: Set[str]
    """Configured metrics with no collected data."""
    
    unknown_metrics: Set[str]
    """Metrics in data but not in config (should be empty after validation)."""
    
    run_count: int
    """Number of run files scanned."""
```

---

### ValidationError Hierarchy

```python
class ConfigValidationError(Exception):
    """Raised when required config key is missing or invalid."""
    pass

class ConfigMigrationError(ConfigValidationError):
    """Raised when old config format detected."""
    pass

class MetricsValidationError(Exception):
    """Raised when metrics in data don't match config."""
    pass
```

---

## Configuration Schema

### New Unified Format

```yaml
metrics:
  # All metrics in single section
  TOK_IN:
    name: "Input Tokens"
    description: "Total tokens sent to LLM"
    unit: "tokens"
    category: "efficiency"
    ideal_direction: "minimize"
    data_source: "openai_usage_api"
    aggregation: "sum"
    display_format: "{:,.0f}"
    statistical_test: true
    stopping_rule_eligible: true
    # No status field = implemented and measured
  
  COST_USD:
    name: "Total Cost"
    description: "Total USD cost of API calls"
    unit: "USD"
    category: "cost"
    ideal_direction: "minimize"
    data_source: "calculated"
    aggregation: "calculated"
    display_format: "${:.4f}"
    statistical_test: true
    stopping_rule_eligible: false
    calculation:
      formula: "(TOK_IN - CACHED) * input_price + TOK_OUT * output_price"
  
  AUTR:
    name: "Autonomy Rate"
    description: "Percentage of steps without human intervention"
    unit: "rate"
    category: "interaction"
    ideal_direction: "maximize"
    data_source: "hitl_detector"
    aggregation: "mean"
    display_format: "{:.2%}"
    statistical_test: false
    stopping_rule_eligible: false
    status: "not_implemented"  # Marks as unmeasured
    reason: "Requires HITL detection implementation"
```

### Required Fields (per metric)

- `name` (str)
- `description` (str)
- `unit` (str)
- `category` (str)
- `ideal_direction` (str: 'minimize' | 'maximize')
- `data_source` (str)
- `aggregation` (str: 'sum' | 'mean' | 'count' | 'none' | 'calculated')
- `display_format` (str: Python format string)

### Optional Fields

- `statistical_test` (bool, default: false)
- `stopping_rule_eligible` (bool, default: false)
- `visualization_types` (list of str, default: [])
- `calculation` (dict, required if aggregation='calculated')
- `status` (str, for documentation only)
- `reason` (str, explains status)

---

## State Transitions

### Report Generation Workflow

```
1. INIT: Load MetricsConfig from experiment.yaml
   ↓
2. VALIDATE: Check config format (fail if old subsections detected)
   ↓
3. DISCOVER: Scan run files for metrics with data
   ↓
4. VALIDATE: Check all data metrics exist in config (fail if unknown metrics)
   ↓
5. PARTITION: Split metrics into "with data" / "without data" sets
   ↓
6. GENERATE: Create report sections
   - Executive summary (uses metrics with data)
   - Metrics tables (split by partition)
   - Statistical tests (uses metrics with data where statistical_test=true)
   - Cost analysis (uses cost category metrics with data)
   - Limitations (lists metrics without data with status/reason)
   ↓
7. OUTPUT: Write markdown report file
```

### Validation State Machine

```
START
  ↓
[Load Config]
  ↓
[Old Format?] ---YES--→ [Raise ConfigMigrationError] → ABORT
  ↓ NO
[Required Keys Present?] ---NO--→ [Raise ConfigValidationError] → ABORT
  ↓ YES
[Scan Run Data]
  ↓
[Unknown Metrics?] ---YES--→ [Raise MetricsValidationError] → ABORT
  ↓ NO
[Valid Config Ready]
  ↓
CONTINUE TO GENERATION
```

---

## Relationships

```
MetricsConfig (1) ---contains--→ (N) MetricDefinition
      ↓
      discovers
      ↓
MetricsDiscoveryResult
      ↓ uses
      ↓
ReportGenerator
      ↓ creates
      ↓
ReportSection (multiple)
```

---

## Indexing & Queries

**Primary Access Patterns**:

1. Get all metrics: `O(1)` - return cached dict
2. Get metric by key: `O(1)` - dict lookup
3. Filter by category: `O(n)` - iterate and filter
4. Filter by any attribute: `O(n)` - iterate and filter
5. Discover metrics with data: `O(m * k)` where m=runs, k=avg metrics per run

**No database/indexing needed** - all in-memory operations on small datasets (typically <50 metrics, <100 runs).

---

## Validation Rules

### MetricsConfig Validation

```python
# Format validation
assert 'metrics' in config, "Missing 'metrics' section"
assert not any(k in config['metrics'] for k in ['reliable_metrics', 'derived_metrics', 'excluded_metrics']), \
    "Old config format detected"

# Per-metric validation
for key, metric_data in config['metrics'].items():
    assert 'name' in metric_data, f"Missing 'name' for metric {key}"
    assert 'display_format' in metric_data, f"Missing 'display_format' for metric {key}"
    assert metric_data.get('ideal_direction') in ['minimize', 'maximize'], \
        f"Invalid ideal_direction for metric {key}"
    
    if metric_data.get('aggregation') == 'calculated':
        assert 'calculation' in metric_data, \
            f"Metric {key} with aggregation='calculated' must have 'calculation' field"
```

### Metrics Discovery Validation

```python
# All metrics in data must be in config
config_keys = set(metrics_config.get_all_metrics().keys())
data_keys = set(run_data['aggregate_metrics'].keys())

unknown = data_keys - config_keys
assert not unknown, f"Unknown metrics in run data: {unknown}"
```

---

## Migration Path

**Old Format** (3 subsections):
```yaml
metrics:
  reliable_metrics:
    TOK_IN: {...}
  derived_metrics:
    COST_USD: {...}
  excluded_metrics:
    AUTR: {...}
```

**New Format** (unified):
```yaml
metrics:
  TOK_IN: {...}
  COST_USD: {...}
  AUTR: {... + status: "not_implemented", reason: "..."}
```

**Migration Steps**:
1. Merge all subsections into single metrics dict
2. Add `status` field to metrics previously in `excluded_metrics`
3. Remove subsection keys
4. Validate with new MetricsConfig

---

## References

- Spec: `/specs/009-refactor-analysis-module/spec.md`
- Research: `/specs/009-refactor-analysis-module/research.md`
- Current Implementation: `src/utils/metrics_config.py`
