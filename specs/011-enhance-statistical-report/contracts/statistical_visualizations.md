# API Contract: StatisticalVisualizationGenerator

**Module**: `src.paper_generation.statistical_visualizations`  
**Class**: `StatisticalVisualizationGenerator`  
**Purpose**: Generate publication-quality statistical visualizations

---

## Class Constructor

### `__init__(self, output_dir: str, style: str = "seaborn-v0_8-colorblind")`

**Description**: Initialize visualization generator with output directory and styling.

**Parameters**:
- `output_dir` (str): Directory for saving SVG files (will be created if doesn't exist)
- `style` (str): Matplotlib style name (default "seaborn-v0_8-colorblind" for accessibility)

**Returns**: None

**Example**:
```python
generator = StatisticalVisualizationGenerator(
    output_dir="output/figures/statistical",
    style="seaborn-v0_8-colorblind"
)
```

---

## Public Methods

### `generate_box_plot(self, metric_name: str, distributions: List[MetricDistribution]) -> Visualization`

**Description**: Create box plot showing median, quartiles, and outliers.

**Parameters**:
- `metric_name` (str): Metric being visualized (for axis labels)
- `distributions` (List[MetricDistribution]): Data for each framework

**Returns**: `Visualization` object with file path and metadata

**Raises**:
- `ValueError`: If distributions list is empty
- `IOError`: If unable to write SVG file

**Example**:
```python
viz = generator.generate_box_plot("execution_time", [dist_chatdev, dist_metagpt])
# Creates: output/figures/statistical/box_plot_execution_time.svg
```

**Plot Specifications**:
- **Box**: Q1 (25th percentile) to Q3 (75th percentile)
- **Line in box**: Median (50th percentile)
- **Whiskers**: Extend to min/max within 1.5*IQR
- **Outliers**: Points beyond whiskers (plotted as circles)
- **X-axis**: Framework names
- **Y-axis**: Metric values with units
- **Figure size**: (10, 6) inches
- **Format**: SVG

**Implementation**:
```python
import matplotlib.pyplot as plt
import seaborn as sns

fig, ax = plt.subplots(figsize=(10, 6))
data = [d.values for d in distributions]
labels = [d.framework_name for d in distributions]

ax.boxplot(data, labels=labels, showfliers=True, patch_artist=True)
ax.set_ylabel(f"{metric_name.replace('_', ' ').title()} (s)")
ax.set_title(f"Distribution Comparison: {metric_name}")
plt.tight_layout()
plt.savefig(output_path, format='svg', bbox_inches='tight')
```

---

### `generate_violin_plot(self, metric_name: str, distributions: List[MetricDistribution]) -> Visualization`

**Description**: Create violin plot showing kernel density estimation with quartile lines.

**Parameters**:
- `metric_name` (str): Metric being visualized
- `distributions` (List[MetricDistribution]): Data for each framework

**Returns**: `Visualization` object

**Example**:
```python
viz = generator.generate_violin_plot("execution_time", distributions)
# Creates: output/figures/statistical/violin_plot_execution_time.svg
```

**Plot Specifications**:
- **Violin shape**: Kernel density estimation (shows distribution shape)
- **White dot**: Median
- **Thick bar**: Interquartile range (Q1-Q3)
- **Thin line**: Adjacent values (min/max within 1.5*IQR)
- **Width**: Scaled to show frequency (wider = more data points at that value)
- **Figure size**: (10, 6) inches

**Implementation**:
```python
fig, ax = plt.subplots(figsize=(10, 6))
data_dict = {d.framework_name: d.values for d in distributions}
df = pd.DataFrame(data_dict)

sns.violinplot(data=df, ax=ax, inner='quartile', palette='colorblind')
ax.set_ylabel(f"{metric_name.replace('_', ' ').title()}")
ax.set_title(f"Distribution Shape: {metric_name}")
plt.tight_layout()
plt.savefig(output_path, format='svg', bbox_inches='tight')
```

---

### `generate_forest_plot(self, metric_name: str, effect_sizes: List[EffectSize]) -> Visualization`

**Description**: Create forest plot showing effect sizes with confidence intervals.

**Parameters**:
- `metric_name` (str): Metric being compared
- `effect_sizes` (List[EffectSize]): Pairwise effect sizes with CIs

**Returns**: `Visualization` object

**Example**:
```python
viz = generator.generate_forest_plot("execution_time", [effect1, effect2, effect3])
# Creates: output/figures/statistical/forest_plot_execution_time.svg
```

**Plot Specifications**:
- **Orientation**: Horizontal (Y-axis = comparisons, X-axis = effect size)
- **Point**: Effect size estimate (circle)
- **Error bars**: 95% confidence interval (horizontal lines)
- **Reference line**: Vertical line at 0 (no effect)
- **Color coding**:
  - Green: Magnitude "small"
  - Orange: Magnitude "medium"
  - Red: Magnitude "large"
  - Gray: Magnitude "negligible"
- **Labels**: Framework comparisons (e.g., "ChatDev vs MetaGPT")
- **Figure size**: (8, len(effect_sizes) * 0.5 + 2) inches (scales with comparisons)

**Implementation**:
```python
fig, ax = plt.subplots(figsize=(8, len(effect_sizes) * 0.5 + 2))

y_positions = range(len(effect_sizes))
labels = [f"{e.frameworks[0]} vs {e.frameworks[1]}" for e in effect_sizes]
values = [e.value for e in effect_sizes]
ci_lower = [e.ci_lower for e in effect_sizes]
ci_upper = [e.ci_upper for e in effect_sizes]
colors = [self._magnitude_to_color(e.magnitude) for e in effect_sizes]

ax.errorbar(values, y_positions, xerr=[
    [v - l for v, l in zip(values, ci_lower)],
    [u - v for u, v in zip(ci_upper, values)]
], fmt='o', color=colors, elinewidth=2, markersize=8)

ax.axvline(x=0, color='black', linestyle='--', linewidth=1)
ax.set_yticks(y_positions)
ax.set_yticklabels(labels)
ax.set_xlabel(f"{effect_sizes[0].measure}")
ax.set_title(f"Effect Sizes: {metric_name}")
plt.tight_layout()
plt.savefig(output_path, format='svg', bbox_inches='tight')
```

---

### `generate_qq_plot(self, metric_name: str, distribution: MetricDistribution, normality_test: AssumptionCheck) -> Visualization`

**Description**: Create quantile-quantile plot for assessing normality.

**Parameters**:
- `metric_name` (str): Metric being tested
- `distribution` (MetricDistribution): Data to plot
- `normality_test` (AssumptionCheck): Shapiro-Wilk test results (for subtitle)

**Returns**: `Visualization` object

**Example**:
```python
viz = generator.generate_qq_plot("execution_time", dist_chatdev, shapiro_result)
# Creates: output/figures/statistical/qq_plot_execution_time_ChatDev.svg
```

**Plot Specifications**:
- **X-axis**: Theoretical quantiles (normal distribution)
- **Y-axis**: Sample quantiles (actual data)
- **Points**: Each data point plotted
- **Reference line**: 45-degree line (y = x)
- **Interpretation**: Points on line → normal distribution, deviations → non-normal
- **Subtitle**: Includes Shapiro-Wilk p-value
- **Figure size**: (6, 6) inches (square for easier interpretation)

**Implementation**:
```python
from scipy import stats

fig, ax = plt.subplots(figsize=(6, 6))
stats.probplot(distribution.values, dist="norm", plot=ax)

ax.set_title(f"Q-Q Plot: {metric_name} ({distribution.framework_name})\n"
             f"Shapiro-Wilk p={normality_test.p_value:.3f}")
ax.set_xlabel("Theoretical Quantiles (Normal Distribution)")
ax.set_ylabel("Sample Quantiles")

# Add interpretation text
if normality_test.passed:
    ax.text(0.05, 0.95, "✅ Appears normal", transform=ax.transAxes,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightgreen'))
else:
    ax.text(0.05, 0.95, "⚠️ Non-normal", transform=ax.transAxes,
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='lightyellow'))

plt.tight_layout()
plt.savefig(output_path, format='svg', bbox_inches='tight')
```

---

### `generate_all_visualizations(self, findings: StatisticalFindings) -> Dict[str, List[Visualization]]`

**Description**: Generate complete set of visualizations for experiment.

**Parameters**:
- `findings` (StatisticalFindings): Complete analysis results

**Returns**: Dictionary mapping metric names to list of visualizations

**Example**:
```python
all_viz = generator.generate_all_visualizations(findings)
# all_viz = {
#     "execution_time": [box_plot, violin_plot, forest_plot, qq_plot_chatdev, ...],
#     "code_quality": [...]
# }
```

**Generated Plots**:
For each metric:
1. **Box plot**: All frameworks comparison
2. **Violin plot**: All frameworks comparison
3. **Forest plot**: All pairwise effect sizes
4. **Q-Q plots**: One per framework (normality check)

**Total plots**: `n_metrics * (3 + n_frameworks)`

---

## Private Helper Methods

### `_magnitude_to_color(self, magnitude: str) -> str`

**Description**: Map effect size magnitude to color for forest plot.

**Parameters**:
- `magnitude` (str): "negligible", "small", "medium", "large"

**Returns**: Matplotlib color name

**Mapping**:
```python
{
    "negligible": "gray",
    "small": "green",
    "medium": "orange",
    "large": "red"
}
```

---

### `_format_metric_label(self, metric_name: str) -> str`

**Description**: Convert snake_case metric name to Title Case with units.

**Parameters**:
- `metric_name` (str): Raw metric name (e.g., "execution_time")

**Returns**: Formatted label (e.g., "Execution Time (s)")

**Unit Detection**:
```python
METRIC_UNITS = {
    "execution_time": "s",
    "api_calls": "count",
    "code_quality": "score",
    "tokens_used": "tokens",
    "cost": "$"
}
```

---

### `_validate_output_path(self, output_path: str) -> None`

**Description**: Ensure output directory exists and path is valid.

**Parameters**:
- `output_path` (str): Intended file path

**Raises**:
- `ValueError`: If path doesn't end with .svg
- `IOError`: If directory creation fails

**Implementation**:
```python
if not output_path.endswith('.svg'):
    raise ValueError("Output must be SVG format")

os.makedirs(os.path.dirname(output_path), exist_ok=True)
```

---

### `_apply_publication_styling(self) -> None`

**Description**: Configure matplotlib for publication-quality output.

**Implementation**:
```python
import matplotlib.pyplot as plt
import seaborn as sns

plt.style.use(self.style)
sns.set_palette("colorblind")
plt.rcParams.update({
    'font.size': 12,
    'font.family': 'Arial',
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'legend.fontsize': 11,
    'figure.dpi': 100,
    'savefig.dpi': 100,
    'savefig.format': 'svg',
    'savefig.bbox': 'tight'
})
```

---

## Styling Constants

### COLOR_PALETTE

**Seaborn "colorblind" palette** (8 colors):
- Blue: #0173B2
- Orange: #DE8F05
- Green: #029E73
- Red: #CC78BC
- Purple: #CA9161
- Brown: #FBAFE4
- Pink: #949494
- Gray: #ECE133

**Accessible for**:
- Deuteranopia (red-green colorblind)
- Protanopia (red-green colorblind)
- Tritanopia (blue-yellow colorblind)

---

### FIGURE_SIZES

**Default sizes** (width, height in inches):
- Box plot: (10, 6)
- Violin plot: (10, 6)
- Forest plot: (8, n_comparisons * 0.5 + 2) - scales dynamically
- Q-Q plot: (6, 6) - square for 45° reference line clarity

---

## Performance Considerations

### Memory Usage
- Each SVG: ~50-200 KB (vector format, compact)
- matplotlib figure: ~5 MB in memory (cleared after saving)
- Recommendation: Generate plots sequentially, not in parallel

### Generation Time
- Box/violin plot: ~0.5 seconds
- Forest plot: ~0.3 seconds
- Q-Q plot: ~0.4 seconds
- **Total for typical experiment** (3 metrics, 3 frameworks): ~12 seconds

---

## Dependencies

- `matplotlib` ≥3.8.0: Core plotting
- `seaborn` ≥0.12.0: Statistical plot templates
- `scipy.stats`: probplot for Q-Q plots
- `numpy`: Array operations for plot data
- `os`: Directory management

---

## Error Handling

### Graceful Degradation

If visualization generation fails:
1. Log error with traceback
2. Return None for that visualization
3. Continue with remaining plots
4. Include warning in report: "Visualization unavailable (error in generation)"

**Example**:
```python
try:
    viz = generator.generate_box_plot(metric_name, distributions)
except Exception as e:
    logger.error(f"Failed to generate box plot for {metric_name}: {e}")
    viz = None
```

---

## Testing Strategy

### Visual Regression Tests

Compare generated SVGs to reference images:
1. Parse SVG XML
2. Check element counts (boxes, lines, text)
3. Validate axis labels and titles
4. Ensure color palette matches

### Data Validation Tests

Ensure plots accurately represent data:
1. Median in box plot matches computed median
2. Whisker extent correct (1.5*IQR)
3. Effect size point position matches value
4. Q-Q plot reference line is 45°

---

**Next**: Main report generator contract and quickstart guide.
