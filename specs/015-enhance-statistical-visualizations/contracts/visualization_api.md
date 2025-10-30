# API Contracts: Statistical Visualization Generator Extensions

**Version**: 1.0.0  
**Date**: 2025-10-30  
**Module**: `src.paper_generation.statistical_visualizations.StatisticalVisualizationGenerator`

This document defines the method signatures for 8 new visualization generation methods to be added to the existing `StatisticalVisualizationGenerator` class.

---

## Design Decisions

### Coexistence with Existing Methods

All new methods are **additive only** - no existing methods are modified or deleted:

- **Existing 4 methods** (box, violin, forest, qq): Unchanged, retained for backward compatibility
- **New 8 methods** (effect panel, efficiency, regression, overlap, normalized cost, rank, stability, outlier run): Pure additions
- **Batch methods**: Two separate methods for clean separation
  - `generate_all_visualizations()`: Existing batch (4 plots)
  - `generate_all_enhanced_visualizations()`: New batch (8 plots)
- **Default behavior**: Paper generator invokes both batches → **12 total plots**

### Complementary Purposes

- **Effect-size panel** complements **forest plot** (overview vs detail)
- **Overlap plot** complements **violin plot** (2-way nuanced vs 3+ way general)
- **Normalized cost plot** complements **box plot** (efficiency metric vs raw values)

---

## Common Parameters (Shared Across Methods)

All visualization methods return `Visualization` objects and accept these optional parameters unless specified:

- **output_filename**: str (optional) - Custom filename for SVG. If not provided, auto-generated from viz type and metric.
- **title**: str (optional) - Override default title. If not provided, auto-generated from metric and comparison.
- **figsize**: Tuple[int, int] (optional) - Figure dimensions in inches. Defaults from `_apply_publication_styling()`.

---

## Method Contracts

### 1. generate_effect_size_panel

**Purpose**: Create faceted panel plot showing effect sizes across all metrics and pairwise comparisons (US1, FR-001, FR-002)

**Signature**:
```python
def generate_effect_size_panel(
    self,
    effect_sizes: Dict[str, List[EffectSize]],
    metrics: Optional[List[str]] = None,
    comparisons: Optional[List[Tuple[str, str]]] = None,
    show_ci: bool = True,
    mark_complete_separation: bool = True
) -> Visualization
```

**Parameters**:
- `effect_sizes`: Dict mapping metric name → list of EffectSize objects for that metric
- `metrics`: Optional list of metrics to include. If None, use all in effect_sizes keys.
- `comparisons`: Optional list of (group_a, group_b) tuples. If None, include all pairwise comparisons.
- `show_ci`: If True, display 95% confidence intervals as error bars
- `mark_complete_separation`: If True, use special markers for |δ| = 1.0

**Returns**: Visualization with viz_type=EFFECT_PANEL

**Raises**:
- `ValueError`: If effect_sizes is empty or metrics list contains unknown metrics
- `StatisticalAnalysisError`: If effect size magnitudes are inconsistent

**Performance**: O(M × C) where M=metrics, C=comparisons. Target <3s for 10 metrics × 3 comparisons.

**Example**:
```python
viz = generator.generate_effect_size_panel(
    effect_sizes={
        'execution_time': [EffectSize(...), EffectSize(...), ...],
        'total_cost_usd': [EffectSize(...), ...],
        ...
    },
    metrics=['execution_time', 'total_cost_usd', 'tokens_total'],
    show_ci=True
)
```

---

### 2. generate_efficiency_plot

**Purpose**: Create cost vs time scatter plot showing framework efficiency quadrants (US2, FR-003, FR-004)

**Signature**:
```python
def generate_efficiency_plot(
    self,
    time_distributions: Dict[str, MetricDistribution],
    cost_distributions: Dict[str, MetricDistribution],
    time_metric: str = "execution_time",
    cost_metric: str = "total_cost_usd",
    use_log_scale: bool = False,
    show_error_bars: bool = True,
    jitter: float = 0.0
) -> Visualization
```

**Parameters**:
- `time_distributions`: Dict mapping framework → MetricDistribution for time metric
- `cost_distributions`: Dict mapping framework → MetricDistribution for cost metric
- `time_metric`: Name of time metric (for axis label)
- `cost_metric`: Name of cost metric (for axis label)
- `use_log_scale`: If True, use symlog scale for x-axis (time)
- `show_error_bars`: If True, show error bars at mean ± 1 std
- `jitter`: Amount of random jitter to add to points (0.0 = none, 0.1 = 10% of range)

**Returns**: Visualization with viz_type=EFFICIENCY

**Raises**:
- `ValueError`: If framework sets don't match between time and cost distributions
- `StatisticalAnalysisError`: If distributions contain zeros and use_log_scale=True without symlog

**Performance**: O(N) where N=total data points across frameworks. Target <2s for 300 points.

**Example**:
```python
viz = generator.generate_efficiency_plot(
    time_distributions={'baes': MetricDistribution(...), 'chatdev': ...},
    cost_distributions={'baes': MetricDistribution(...), 'chatdev': ...},
    use_log_scale=True  # Symlog handles zeros
)
```

---

### 3. generate_regression_plot

**Purpose**: Create scatter plot with framework-specific regression lines for token-to-cost analysis (US3, FR-005, FR-006)

**Signature**:
```python
def generate_regression_plot(
    self,
    x_distributions: Dict[str, MetricDistribution],
    y_distributions: Dict[str, MetricDistribution],
    x_metric: str,
    y_metric: str,
    show_equations: bool = True,
    show_r_squared: bool = True,
    cached_tokens: Optional[Dict[str, MetricDistribution]] = None
) -> Visualization
```

**Parameters**:
- `x_distributions`: Dict mapping framework → MetricDistribution for x-axis (typically tokens_in)
- `y_distributions`: Dict mapping framework → MetricDistribution for y-axis (typically total_cost_usd)
- `x_metric`: Name of x metric (for axis label)
- `y_metric`: Name of y metric (for axis label)
- `show_equations`: If True, annotate with slope/intercept equations
- `show_r_squared`: If True, include R² values in annotations
- `cached_tokens`: Optional dict for 3rd dimension visualization (via marker size or color)

**Returns**: Visualization with viz_type=REGRESSION

**Raises**:
- `ValueError`: If x or y distributions have zero variance (cannot fit regression)
- `StatisticalAnalysisError`: If regression fitting fails (insufficient data, n<3)

**Performance**: O(F × N) where F=frameworks, N=points per framework. Target <3s for 3 frameworks × 100 points.

**Example**:
```python
viz = generator.generate_regression_plot(
    x_distributions={'baes': MetricDistribution(metric_name='tokens_in', ...), ...},
    y_distributions={'baes': MetricDistribution(metric_name='total_cost_usd', ...), ...},
    x_metric='tokens_in',
    y_metric='total_cost_usd',
    show_equations=True
)
```

---

### 4. generate_overlap_plot

**Purpose**: Create 2-way density or violin plot showing distribution overlap for similar groups (US4, FR-007)

**Signature**:
```python
def generate_overlap_plot(
    self,
    distribution_a: MetricDistribution,
    distribution_b: MetricDistribution,
    metric_name: str,
    effect_size: EffectSize,
    p_value: float,
    plot_type: str = "density"
) -> Visualization
```

**Parameters**:
- `distribution_a`: MetricDistribution for first framework
- `distribution_b`: MetricDistribution for second framework
- `metric_name`: Name of metric being compared
- `effect_size`: EffectSize object for this comparison (used in annotation)
- `p_value`: Statistical test p-value (used in annotation)
- `plot_type`: "density" or "violin" visualization style

**Returns**: Visualization with viz_type=OVERLAP

**Raises**:
- `ValueError`: If plot_type not in ["density", "violin"]
- `StatisticalAnalysisError`: If distributions have insufficient data for density estimation (n<5)

**Performance**: O(N) for density estimation. Target <2s for 200 points total.

**Example**:
```python
viz = generator.generate_overlap_plot(
    distribution_a=chatdev_tokens_out,
    distribution_b=ghspec_tokens_out,
    metric_name='tokens_out',
    effect_size=EffectSize(value=0.11, magnitude='negligible', ...),
    p_value=0.03,
    plot_type='density'
)
```

---

### 5. generate_normalized_cost_plot

**Purpose**: Create box plot of cost per 1000 tokens across frameworks (US5, FR-008)

**Signature**:
```python
def generate_normalized_cost_plot(
    self,
    cost_distributions: Dict[str, MetricDistribution],
    tokens_distributions: Dict[str, MetricDistribution],
    cost_metric: str = "total_cost_usd",
    tokens_metric: str = "tokens_total"
) -> Visualization
```

**Parameters**:
- `cost_distributions`: Dict mapping framework → MetricDistribution for cost
- `tokens_distributions`: Dict mapping framework → MetricDistribution for tokens
- `cost_metric`: Name of cost metric (for reference)
- `tokens_metric`: Name of tokens metric (for reference)

**Returns**: Visualization with viz_type=NORMALIZED_COST

**Raises**:
- `ValueError`: If any tokens values are zero (division by zero)
- `StatisticalAnalysisError`: If cost and tokens distributions have mismatched sample sizes

**Performance**: O(N) for normalization. Target <2s for 300 points.

**Example**:
```python
viz = generator.generate_normalized_cost_plot(
    cost_distributions={'baes': MetricDistribution(...), ...},
    tokens_distributions={'baes': MetricDistribution(...), ...}
)
```

---

### 6. generate_rank_plot

**Purpose**: Create line plot showing framework rankings across metrics (US6, FR-009)

**Signature**:
```python
def generate_rank_plot(
    self,
    distributions: Dict[str, Dict[str, MetricDistribution]],
    metrics: List[str],
    lower_is_better: Dict[str, bool]
) -> Visualization
```

**Parameters**:
- `distributions`: Nested dict: framework → metric → MetricDistribution
- `metrics`: List of metrics to include in ranking (x-axis order)
- `lower_is_better`: Dict mapping metric → bool (True for time/cost, False for accuracy)

**Returns**: Visualization with viz_type=RANK

**Raises**:
- `ValueError`: If metrics list is empty or contains unknown metrics
- `StatisticalAnalysisError`: If distributions have ties that cannot be resolved

**Performance**: O(F × M) where F=frameworks, M=metrics. Target <2s for 5 frameworks × 10 metrics.

**Example**:
```python
viz = generator.generate_rank_plot(
    distributions={
        'baes': {'execution_time': MetricDistribution(...), 'total_cost_usd': ...},
        'chatdev': {'execution_time': ..., 'total_cost_usd': ...},
        ...
    },
    metrics=['execution_time', 'total_cost_usd', 'tokens_total'],
    lower_is_better={'execution_time': True, 'total_cost_usd': True, 'tokens_total': True}
)
```

---

### 7. generate_stability_plot

**Purpose**: Create bar plot of coefficient of variation for stability analysis (US7, FR-010)

**Signature**:
```python
def generate_stability_plot(
    self,
    distributions: Dict[str, Dict[str, MetricDistribution]],
    metrics: List[str],
    cv_threshold: float = 0.20
) -> Visualization
```

**Parameters**:
- `distributions`: Nested dict: framework → metric → MetricDistribution
- `metrics`: List of metrics to include in CV calculation
- `cv_threshold`: Threshold for "highly stable" annotation (default 0.20 per SC-012)

**Returns**: Visualization with viz_type=STABILITY

**Raises**:
- `ValueError`: If any metric has mean=0 across all frameworks (CV undefined)
- `StatisticalAnalysisError`: If distributions have insufficient variance information

**Performance**: O(F × M) for CV computation. Target <2s for 5 frameworks × 10 metrics.

**Example**:
```python
viz = generator.generate_stability_plot(
    distributions={
        'baes': {'execution_time': MetricDistribution(...), ...},
        'chatdev': {'execution_time': ..., ...},
        ...
    },
    metrics=['execution_time', 'total_cost_usd'],
    cv_threshold=0.20
)
```

---

### 8. generate_outlier_run_plot

**Purpose**: Create run-index time series plot to identify outliers (US8, FR-011)

**Signature**:
```python
def generate_outlier_run_plot(
    self,
    distribution: MetricDistribution,
    framework: str,
    metric_name: str,
    mark_outliers: bool = True
) -> Visualization
```

**Parameters**:
- `distribution`: MetricDistribution containing raw values for this framework
- `framework`: Name of framework being analyzed
- `metric_name`: Name of metric being plotted
- `mark_outliers`: If True, highlight outliers (1.5×IQR) in red

**Returns**: Visualization with viz_type=OUTLIER_RUN

**Raises**:
- `ValueError`: If distribution has <3 runs (insufficient for outlier detection)
- `StatisticalAnalysisError`: If metric values are all identical (zero IQR)

**Performance**: O(N) for outlier detection. Target <1s for 100 runs.

**Example**:
```python
viz = generator.generate_outlier_run_plot(
    distribution=chatdev_execution_time,
    framework='chatdev',
    metric_name='execution_time',
    mark_outliers=True
)
```

---

## Batch Generation Method

### generate_all_enhanced_visualizations

**Purpose**: Generate all 8 visualization types in one call for comprehensive analysis (FR-015)

**Signature**:
```python
def generate_all_enhanced_visualizations(
    self,
    findings: 'StatisticalFindings',
    include_types: Optional[List[VisualizationType]] = None
) -> Dict[VisualizationType, List[Visualization]]
```

**Parameters**:
- `findings`: StatisticalFindings object containing all analyzed data
- `include_types`: Optional filter list. If None, generate all 8 types.

**Returns**: Dict mapping viz type → list of Visualization objects (some types may produce multiple plots)

**Raises**:
- `StatisticalAnalysisError`: If findings object is incomplete or invalid

**Performance**: <30 seconds for all 8 types per SC-001. Runs methods sequentially with progress logging.

**Example**:
```python
all_viz = generator.generate_all_enhanced_visualizations(
    findings=statistical_analyzer.analyze_experiment(experiment_data)
)
# Returns:
# {
#   VisualizationType.EFFECT_PANEL: [Visualization(...)],
#   VisualizationType.EFFICIENCY: [Visualization(...)],
#   ...
# }
```

---

## Error Handling Patterns

All methods follow Constitution principle XIII (Fail-Fast):

1. **Invalid input**: Raise ValueError with descriptive message
2. **Insufficient data**: Raise StatisticalAnalysisError with minimum n requirement
3. **Edge cases**: Annotate plot + log warning (don't fail unless critical)
4. **File I/O errors**: Propagate immediately, don't retry

**Example error messages**:
```python
raise ValueError(
    f"Regression requires n≥3, but framework '{framework}' has n={n}. "
    f"Cannot fit meaningful regression line."
)

raise StatisticalAnalysisError(
    f"Metric '{metric}' has zero variance (std=0) for all frameworks. "
    f"Cannot compute coefficient of variation. Check data quality."
)
```

---

## Paper Generator Integration

### Complete Suite Invocation (Default Behavior)

The paper generator will invoke **both batch methods** to produce all 12 plots:

```python
# In paper generator workflow
visualizations = []

# Generate existing 4 plots (box, violin, forest, qq)
visualizations.extend(
    vis_generator.generate_all_visualizations(findings, output_dir)
)

# Generate new 8 plots (effect panel, efficiency, regression, overlap, 
#                        normalized cost, rank, stability, outlier run)
visualizations.extend(
    vis_generator.generate_all_enhanced_visualizations(findings, output_dir)
)

# Total: 12 visualization types
```

---

## Validation Notes

All methods will be verified through **real paper generation** using the validation dataset at:
```
~/projects/uece/baes/baes_benchmarking_20251028_0713
```

This validation approach replaces traditional unit tests and provides comprehensive end-to-end verification.

The final implementation will ensure:
- ✅ No existing methods deleted or modified
- ✅ All 12 plots generated by default in paper generation
- ✅ Clean separation via two batch methods
- ✅ Backward compatibility maintained

---

## Validation Contract

All generated Visualization objects MUST satisfy:

1. **File exists**: `viz.file_path.exists() == True`
2. **Valid SVG**: File is valid SVG (parseable XML)
3. **Size constraint**: `viz.file_path.stat().st_size < 2_000_000` (2 MB per NFR-002)
4. **Caption quality**: `len(viz.caption) >= 50` characters (self-explanatory per SC-008)
5. **Metadata complete**: All required fields non-None

**Validation approach**: These constraints will be verified through real paper generation using experiment data from `~/projects/uece/baes/baes_benchmarking_20251028_0713` at project completion.

---

## Version History

- **1.0.0** (2025-10-30): Initial API definition for 8 new visualization methods
