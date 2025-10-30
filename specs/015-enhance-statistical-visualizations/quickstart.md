# Quickstart: Enhanced Statistical Visualizations

**Purpose**: Get started generating the 8 new visualization types in under 5 minutes  
**Audience**: Researchers, paper generators, contributors  
**Prerequisites**: Existing paper generation pipeline with `StatisticalAnalyzer` results

---

## 30-Second Quickstart

### Generate All 12 Plots (Default Behavior)

```python
from paper_generation.statistical_visualizations import StatisticalVisualizationGenerator
from pathlib import Path

# Initialize generator
vis_gen = StatisticalVisualizationGenerator()

# Load your statistical findings
findings = load_statistical_findings()  # Your StatisticalFindings object
output_dir = Path("output/figures/statistical")

# Generate ALL 12 plots (4 existing + 8 new)
all_visualizations = []

# Existing 4 plots (box, violin, forest, qq)
all_visualizations.extend(
    vis_gen.generate_all_visualizations(findings, output_dir)
)

# New 8 plots (effect panel, efficiency, regression, overlap, 
#              normalized cost, rank, stability, outlier run)
all_visualizations.extend(
    vis_gen.generate_all_enhanced_visualizations(findings, output_dir)
)

# Result: 12 SVG files in output_dir + metadata in all_visualizations list
```

### Generate Only New Enhanced Plots

```python
# If you only want the 8 new visualizations
enhanced_only = vis_gen.generate_all_enhanced_visualizations(
    findings=findings,
    output_dir=output_dir
)

# Result: 8 SVG files in output_dir
```

---

## 📊 Individual Plot Generation

### 1. Effect Size Panel (Priority 1)

Shows **how large** differences are across all metrics in one figure.

```python
# Automatically generates from findings
effect_panel = viz_gen.generate_effect_size_panel(
    effect_sizes=findings.effect_sizes_by_metric,  # Dict[metric, List[EffectSize]]
    metrics=['execution_time', 'total_cost_usd', 'tokens_total'],  # Optional filter
    show_ci=True,  # Show confidence intervals
    mark_complete_separation=True  # Special markers for |δ| = 1.0
)

# Use in paper
print(effect_panel.title)   # "Effect Sizes Across Metrics"
print(effect_panel.caption) # Self-explanatory description
```

**When to use**: Main results figure showing magnitude of all differences.

---

### 2. Cost-Performance Efficiency Plot (Priority 1)

Shows the "cheap & fast vs slow & expensive" story at a glance.

```python
efficiency = viz_gen.generate_efficiency_plot(
    time_distributions={
        'baes': findings.get_distribution('baes', 'execution_time'),
        'chatdev': findings.get_distribution('chatdev', 'execution_time'),
        'ghspec': findings.get_distribution('ghspec', 'execution_time'),
    },
    cost_distributions={
        'baes': findings.get_distribution('baes', 'total_cost_usd'),
        'chatdev': findings.get_distribution('chatdev', 'total_cost_usd'),
        'ghspec': findings.get_distribution('ghspec', 'total_cost_usd'),
    },
    use_log_scale=True,  # For skewed distributions
    show_error_bars=True  # Mean ± 1 SD
)
```

**When to use**: Executive summary, conference presentations, highlighting trade-offs.

---

### 3. Token-to-Cost Regression (Priority 2)

Reveals systematic overhead differences between frameworks.

```python
regression = viz_gen.generate_regression_plot(
    x_distributions={fwk: findings.get_distribution(fwk, 'tokens_in') for fwk in frameworks},
    y_distributions={fwk: findings.get_distribution(fwk, 'total_cost_usd') for fwk in frameworks},
    x_metric='tokens_in',
    y_metric='total_cost_usd',
    show_equations=True,  # Annotate slope/intercept
    show_r_squared=True   # Display goodness of fit
)
```

**When to use**: Explaining *why* one framework costs more (higher base or per-token rate).

---

### 4. Distribution Overlap (Priority 2)

Shows nuance for metrics where differences are small.

```python
overlap = viz_gen.generate_overlap_plot(
    distribution_a=findings.get_distribution('chatdev', 'tokens_out'),
    distribution_b=findings.get_distribution('ghspec', 'tokens_out'),
    metric_name='tokens_out',
    effect_size=findings.get_effect_size('chatdev', 'ghspec', 'tokens_out'),
    p_value=0.03,
    plot_type='density'  # or 'violin'
)
```

**When to use**: Supporting claims of "statistically different but practically similar."

---

### 5. Normalized Cost (Priority 2)

Fair comparison removing volume confounds.

```python
normalized = viz_gen.generate_normalized_cost_plot(
    cost_distributions={fwk: findings.get_distribution(fwk, 'total_cost_usd') for fwk in frameworks},
    tokens_distributions={fwk: findings.get_distribution(fwk, 'tokens_total') for fwk in frameworks}
)
# Automatically computes cost per 1000 tokens
```

**When to use**: Isolating efficiency from raw usage volume.

---

### 6. Multi-Metric Ranking (Priority 3)

Shows consistency patterns across metrics.

```python
rankings = viz_gen.generate_rank_plot(
    distributions={
        'baes': {
            'execution_time': findings.get_distribution('baes', 'execution_time'),
            'total_cost_usd': findings.get_distribution('baes', 'total_cost_usd'),
            'tokens_total': findings.get_distribution('baes', 'tokens_total'),
        },
        # ... repeat for other frameworks
    },
    metrics=['execution_time', 'total_cost_usd', 'tokens_total'],
    lower_is_better={'execution_time': True, 'total_cost_usd': True, 'tokens_total': True}
)
```

**When to use**: Discussion section, showing overall consistency or trade-offs.

---

### 7. Stability Analysis (Priority 3)

Claims about predictability backed by CV.

```python
stability = viz_gen.generate_stability_plot(
    distributions={
        'baes': {metric: findings.get_distribution('baes', metric) for metric in metrics},
        'chatdev': {metric: findings.get_distribution('chatdev', metric) for metric in metrics},
    },
    metrics=['execution_time', 'total_cost_usd'],
    cv_threshold=0.20  # "Highly stable" threshold
)
```

**When to use**: Supplementary material, production deployment arguments.

---

### 8. Outlier Run Plot (Priority 3)

Distinguish outliers from systematic issues.

```python
outliers = viz_gen.generate_outlier_run_plot(
    distribution=findings.get_distribution('chatdev', 'execution_time'),
    framework='chatdev',
    metric_name='execution_time',
    mark_outliers=True  # Highlight 1.5×IQR outliers in red
)
```

**When to use**: Data quality validation, reviewer scrutiny responses.

---

## 🎨 Customization Examples

### Custom Colors (While Maintaining Accessibility)

```python
# In your script before generating plots
import seaborn as sns
custom_palette = sns.color_palette("colorblind", 8)
sns.set_palette(custom_palette)

# Then generate plots normally - they'll use custom palette
viz_gen = StatisticalVisualizationGenerator(output_dir="papers/my_paper/")
```

### Custom Figure Sizes

```python
# Override default figsize for specific plots
effect_panel = viz_gen.generate_effect_size_panel(
    effect_sizes=findings.effect_sizes_by_metric,
    figsize=(12, 16)  # Wider and taller for many metrics
)
```

### Filtering Metrics for Focused Plots

```python
# Only show top 3 most impactful metrics
top_metrics = ['execution_time', 'total_cost_usd', 'api_calls']

effect_panel = viz_gen.generate_effect_size_panel(
    effect_sizes=findings.effect_sizes_by_metric,
    metrics=top_metrics  # Filter to these only
)
```

---

## 🔧 Troubleshooting

### "ValueError: Regression requires n≥3"

**Cause**: One framework has only 1-2 runs.  
**Fix**: Exclude that framework or collect more data.

```python
# Filter out frameworks with insufficient data
valid_frameworks = {
    fwk: dist for fwk, dist in all_distributions.items()
    if dist.n >= 3
}

regression = viz_gen.generate_regression_plot(
    x_distributions=valid_frameworks,
    y_distributions=valid_frameworks,
    ...
)
```

### "StatisticalAnalysisError: CV undefined (mean=0)"

**Cause**: Metric has zero mean (rare edge case).  
**Fix**: Skip CV for that metric. The plot will annotate with "N/A".

```python
# CV computation automatically handles this
stability = viz_gen.generate_stability_plot(
    distributions=all_distributions,
    metrics=['execution_time', 'total_cost_usd']  # Exclude problematic metrics
)
```

### SVG files >2 MB

**Cause**: Too many data points or complex faceting.  
**Fix**: Aggregate data or split into multiple plots.

```python
# Split effect panel into two figures
effect_panel_1 = viz_gen.generate_effect_size_panel(
    effect_sizes=findings.effect_sizes_by_metric,
    metrics=metrics[:5]  # First 5 metrics
)

effect_panel_2 = viz_gen.generate_effect_size_panel(
    effect_sizes=findings.effect_sizes_by_metric,
    metrics=metrics[5:]  # Remaining metrics
)
```

---

## 📖 Integration with Paper Generator

### Automatic Inclusion in Papers

The paper generator automatically discovers and includes visualizations:

```python
# In paper_generator.py
from src.paper_generation.paper_generator import PaperGenerator

generator = PaperGenerator(output_dir="papers/my_paper/")
generator.generate_full_paper(
    experiment_data=experiment_data,
    include_visualizations=True  # Automatically generates and embeds all plots
)
```

### Manual Inclusion in Markdown

```markdown
## Results

Figure 1 shows the effect sizes across all metrics:

![](figures/statistical/effect_panel_multi.svg)

*Figure 1: Effect sizes for all pairwise comparisons. Color indicates magnitude
(gray=negligible, green=small, orange=medium, red=large).*
```

---

## ⚡ Performance Tips

### Batch Generation (Recommended)

```python
# Faster than calling each method individually
all_plots = viz_gen.generate_all_enhanced_visualizations(findings)
```

### Parallel Generation (Advanced)

```python
from concurrent.futures import ThreadPoolExecutor

# Generate plots in parallel (thread-safe)
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = {
        executor.submit(viz_gen.generate_effect_size_panel, findings.effect_sizes_by_metric),
        executor.submit(viz_gen.generate_efficiency_plot, time_dists, cost_dists),
        # ... other plots
    }
    results = [f.result() for f in futures]
```

---

## 📚 Next Steps

1. **Explore examples**: See `docs/paper_generation/visualization_gallery.md` for visual examples
2. **Read contracts**: Review `contracts/visualization_api.md` for full API details
3. **Check tests**: See `tests/paper_generation/test_statistical_visualizations.py` for usage patterns
4. **Customize**: Extend `StatisticalVisualizationGenerator` for domain-specific plots

**Questions?** Open an issue or check existing documentation in `docs/`.
