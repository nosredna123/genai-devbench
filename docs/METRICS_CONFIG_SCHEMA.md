# Metrics Configuration Schema

**Version:** 1.0.0  
**Date:** 2025-10-19  
**Location:** `config/experiment.yaml` (metrics section)

---

## Overview

The metrics configuration provides a centralized definition for all experiment metrics. This ensures consistency across:
- Data collection (orchestrator)
- Statistical analysis (report generator)
- Visualizations (charts and plots)
- Cost calculation

All metrics are defined in `config/experiment.yaml` under the `metrics` section with complete metadata.

---

## Schema Structure

### Top-Level Sections

```yaml
metrics:
  categories:         # Metric groupings for organization
  reliable_metrics:   # Directly measured metrics (7 metrics)
  derived_metrics:    # Calculated from other metrics (1 metric)
  excluded_metrics:   # Unmeasured or unreliable metrics (8 metrics)
```

---

## Categories

Defines logical groupings for metrics with visual styling.

### Schema

```yaml
categories:
  - name: <category_name>
    description: <category_description>
    color: <hex_color>
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Category identifier (e.g., "efficiency", "interaction", "cost") |
| `description` | string | Yes | Human-readable description |
| `color` | string | Yes | Hex color code for visualizations (e.g., "#4A90E2") |

### Example

```yaml
categories:
  - name: efficiency
    description: "Token usage, API calls, and execution time"
    color: "#4A90E2"
  - name: interaction
    description: "Automation and human intervention patterns"
    color: "#E27B4A"
  - name: cost
    description: "Actual USD costs based on OpenAI pricing"
    color: "#50C878"
```

---

## Reliable Metrics

Metrics with complete, trustworthy data capture.

### Schema

```yaml
reliable_metrics:
  <METRIC_KEY>:
    name: <display_name>
    description: <detailed_description>
    unit: <unit_of_measurement>
    category: <category_name>
    ideal_direction: <minimize|maximize>
    data_source: <source_identifier>
    aggregation: <sum|mean|count|direct>
    display_format: <python_format_string>
    statistical_test: <true|false>
    stopping_rule_eligible: <true|false>
    visualization_types:
      - <viz_type_1>
      - <viz_type_2>
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Human-readable display name |
| `description` | string | Yes | Detailed explanation of what the metric measures |
| `unit` | string | Yes | Unit of measurement (e.g., "tokens", "seconds", "USD") |
| `category` | string | Yes | Category name (must match a defined category) |
| `ideal_direction` | enum | Yes | Optimization direction: `minimize` or `maximize` |
| `data_source` | string | Yes | Where data comes from (e.g., "openai_usage_api") |
| `aggregation` | enum | Yes | How to aggregate across steps: `sum`, `mean`, `count`, `direct` |
| `display_format` | string | Yes | Python format string (e.g., `"{:,.0f}"`, `"${:.4f}"`) |
| `statistical_test` | boolean | Yes | Include in statistical comparisons (Kruskal-Wallis, etc.) |
| `stopping_rule_eligible` | boolean | Yes | Use in stopping rule convergence checks |
| `visualization_types` | array | No | List of compatible chart types |

### Aggregation Types

- **`sum`**: Sum values across all steps (e.g., total tokens)
- **`mean`**: Average values across steps (e.g., average duration)
- **`count`**: Count occurrences (e.g., number of steps)
- **`direct`**: Use value as-is (e.g., wall-clock time already aggregated)

### Visualization Types

- `radar`: Radar/spider chart
- `timeline`: Step-by-step timeline
- `boxplot`: Distribution boxplot
- `scatter`: Scatter plot
- `evolution`: Multi-step evolution chart

### Example

```yaml
reliable_metrics:
  TOK_IN:
    name: "Input Tokens"
    description: "Total prompt tokens sent to OpenAI API"
    unit: "tokens"
    category: efficiency
    ideal_direction: minimize
    data_source: "openai_usage_api"
    aggregation: sum
    display_format: "{:,.0f}"
    statistical_test: true
    stopping_rule_eligible: true
    visualization_types:
      - radar
      - timeline
      - boxplot
      - scatter
```

---

## Derived Metrics

Metrics calculated from other metrics using formulas.

### Schema

```yaml
derived_metrics:
  <METRIC_KEY>:
    name: <display_name>
    description: <detailed_description>
    unit: <unit_of_measurement>
    category: <category_name>
    ideal_direction: <minimize|maximize>
    data_source: "calculated"
    aggregation: "calculated"
    display_format: <python_format_string>
    statistical_test: <true|false>
    stopping_rule_eligible: <true|false>
    visualization_types:
      - <viz_type_1>
    calculation:
      formula: <calculation_formula>
      dependencies:
        - <METRIC_KEY_1>
        - <METRIC_KEY_2>
      pricing_source: <optional_pricing_ref>
```

### Additional Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `calculation.formula` | string | Yes | Human-readable formula description |
| `calculation.dependencies` | array | Yes | List of metric keys required for calculation |
| `calculation.pricing_source` | string | No | Reference to pricing config (e.g., "pricing.models") |

### Example

```yaml
derived_metrics:
  COST_USD:
    name: "Total Cost"
    description: "Total USD cost with cache discount applied"
    unit: "USD"
    category: cost
    ideal_direction: minimize
    data_source: "calculated"
    aggregation: "calculated"
    display_format: "${:.4f}"
    statistical_test: true
    stopping_rule_eligible: true
    visualization_types:
      - radar
      - boxplot
      - timeline
    calculation:
      formula: "(TOK_IN - CACHED_TOKENS) * input_price + CACHED_TOKENS * cached_price + TOK_OUT * output_price"
      dependencies:
        - TOK_IN
        - TOK_OUT
        - CACHED_TOKENS
      pricing_source: "pricing.models"
```

---

## Excluded Metrics

Metrics that are not measured or unreliable, documented for reference.

### Schema

```yaml
excluded_metrics:
  <METRIC_KEY>:
    name: <display_name>
    reason: <exclusion_reason>
    original_formula: <optional_formula>
    status: <not_measured|partial_measurement>
```

### Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Human-readable name |
| `reason` | string | Yes | Explanation of why metric is excluded |
| `original_formula` | string | No | Original calculation formula (for reference) |
| `status` | enum | Yes | Measurement status: `not_measured` or `partial_measurement` |

### Example

```yaml
excluded_metrics:
  AUTR:
    name: "Autonomy Rate"
    reason: "Hardcoded HITL detection always returns 0"
    original_formula: "1 - (HIT / 6)"
    status: partial_measurement
```

---

## Complete Example

```yaml
metrics:
  categories:
    - name: efficiency
      description: "Token usage, API calls, and execution time"
      color: "#4A90E2"
  
  reliable_metrics:
    TOK_IN:
      name: "Input Tokens"
      description: "Total prompt tokens sent to OpenAI API"
      unit: "tokens"
      category: efficiency
      ideal_direction: minimize
      data_source: "openai_usage_api"
      aggregation: sum
      display_format: "{:,.0f}"
      statistical_test: true
      stopping_rule_eligible: true
      visualization_types:
        - radar
        - timeline
        - boxplot
  
  derived_metrics:
    COST_USD:
      name: "Total Cost"
      description: "Total USD cost with cache discount applied"
      unit: "USD"
      category: cost
      ideal_direction: minimize
      data_source: "calculated"
      aggregation: "calculated"
      display_format: "${:.4f}"
      statistical_test: true
      stopping_rule_eligible: true
      visualization_types:
        - radar
        - boxplot
      calculation:
        formula: "(TOK_IN - CACHED_TOKENS) * input_price + CACHED_TOKENS * cached_price + TOK_OUT * output_price"
        dependencies:
          - TOK_IN
          - TOK_OUT
          - CACHED_TOKENS
        pricing_source: "pricing.models"
  
  excluded_metrics:
    AUTR:
      name: "Autonomy Rate"
      reason: "Hardcoded HITL detection always returns 0"
      original_formula: "1 - (HIT / 6)"
      status: partial_measurement
```

---

## Usage in Code

### Loading Configuration

```python
from src.utils.metrics_config import get_metrics_config

# Get singleton instance
config = get_metrics_config()

# Get all reliable metrics
reliable = config.get_reliable_metrics()

# Get a specific metric
tok_in = config.get_metric('TOK_IN')
print(tok_in.name)  # "Input Tokens"
print(tok_in.unit)  # "tokens"
```

### Filtering Metrics

```python
# Get metrics for statistical testing
stats_metrics = config.get_metrics_for_statistics()

# Get metrics for stopping rule
stopping_metrics = config.get_metrics_for_stopping_rule()

# Get metrics by category
efficiency_metrics = config.get_metrics_by_category('efficiency')
```

### Formatting Values

```python
# Format a value according to metric's display format
formatted = config.format_value('TOK_IN', 1234567)
print(formatted)  # "1,234,567"

formatted = config.format_value('COST_USD', 0.1234)
print(formatted)  # "$0.1234"
```

### Validation

```python
# Validate metrics data
data = {
    'TOK_IN': 1000,
    'TOK_OUT': 500,
    'API_CALLS': 10,
    # ...
}
errors = config.validate_metrics_data(data)
if errors:
    print("Validation errors:", errors)
```

---

## Adding New Metrics

To add a new metric:

1. **Decide metric type**: Reliable (measured) or Derived (calculated)

2. **Add to appropriate section** in `config/experiment.yaml`:

```yaml
reliable_metrics:
  NEW_METRIC:
    name: "New Metric Name"
    description: "What this metric measures"
    unit: "units"
    category: efficiency  # or interaction, cost
    ideal_direction: minimize  # or maximize
    data_source: "where_data_comes_from"
    aggregation: sum  # or mean, count, direct
    display_format: "{:.2f}"
    statistical_test: true
    stopping_rule_eligible: false
    visualization_types:
      - boxplot
```

3. **Update data collection** in `src/orchestrator/metrics_collector.py` to capture the new metric

4. **Add tests** to verify the metric is correctly loaded and formatted

5. **Update documentation** to explain the metric's meaning and use

---

## Best Practices

1. **Use descriptive keys**: Metric keys should be uppercase with underscores (e.g., `TOK_IN`, `API_CALLS`)

2. **Provide clear descriptions**: Users should understand what the metric measures without looking at code

3. **Choose appropriate aggregation**: Match the aggregation type to how the metric is collected
   - Token counts → `sum`
   - Step durations → `mean`
   - Total steps → `count`
   - Wall-clock time → `direct`

4. **Set ideal_direction correctly**: This affects radar chart scaling
   - Costs, time, errors → `minimize`
   - Cache hits, success rates → `maximize`

5. **Use consistent formatting**: Match the display format to the metric's precision
   - Large integers → `"{:,.0f}"` (with thousands separator)
   - Currency → `"${:.4f}"`
   - Percentages → `"{:.1f}%"`
   - Times → `"{:.1f}"`

6. **Document exclusions**: Keep excluded metrics in config for reference with clear reasons

---

## Related Configuration

See also:
- **Pricing Configuration**: `docs/20251018-audit/PRICING_CONFIG_SCHEMA.md`
- **Visualization Configuration**: `docs/20251018-audit/VISUALIZATION_CONFIG_SCHEMA.md`
- **Report Configuration**: `docs/20251018-audit/REPORT_CONFIG_SCHEMA.md`
