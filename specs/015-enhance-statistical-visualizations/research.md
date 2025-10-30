# Research: Enhanced Statistical Visualizations

**Phase**: 0 - Outline & Research  
**Date**: 2025-10-30  
**Purpose**: Resolve technical unknowns and establish best practices for implementing 8 new visualization types

---

## Research Tasks

### R1: Matplotlib Faceting Best Practices for Multi-Metric Panels

**Question**: What's the best approach for creating faceted effect-size panels showing 7 metrics × 3 pairwise comparisons in a single figure?

**Decision**: Use `matplotlib.pyplot.subplots()` with `nrows` and `ncols` calculated from metric count. Share y-axis across facets for comparisons.

**Rationale**:
- `plt.subplots()` provides fine-grained control over layout and is already used in existing codebase
- Seaborn's `FacetGrid` is tempting but adds complexity for mixed plot types (forest plots with CIs)
- Sharing y-axis (`sharey=True`) enables visual comparison of effect sizes across metrics
- GridSpec allows uneven layouts if some metrics need more space

**Alternatives Considered**:
- **Seaborn FacetGrid**: More declarative but less flexible for custom error bars and complete separation markers
- **Plotly subplots**: Interactive but violates FR-012 (SVG-only requirement)
- **Separate plots stitched with ImageMagick**: Fragile, adds external dependency

**Implementation Pattern**:
```python
def generate_effect_size_panel(self, metrics: List[str], effect_sizes: Dict[str, List[EffectSize]]):
    n_metrics = len(metrics)
    fig, axes = plt.subplots(nrows=n_metrics, ncols=1, figsize=(10, 3*n_metrics), sharey=True)
    for i, metric in enumerate(metrics):
        ax = axes[i] if n_metrics > 1 else axes
        # Plot effect sizes for this metric on ax
```

**References**:
- Matplotlib documentation: [Subplots](https://matplotlib.org/stable/gallery/subplots_axes_and_figures/subplots_demo.html)
- Existing codebase: `generate_forest_plot()` uses similar pattern

---

### R2: Handling Complete Separation (|δ| = 1.0) in Effect Size Plots

**Question**: How to visually distinguish complete separation (no overlap between distributions) from large but incomplete effects?

**Decision**: Use hollow/open markers (e.g., `marker='o', fillstyle='none'`) with thick edge color for |δ| = 1.0 cases. No error bars since CI is [1.0, 1.0].

**Rationale**:
- Complete separation is qualitatively different from "just very large" effects
- Open markers are visually distinctive and used in scientific literature to indicate special conditions
- Omitting error bars when width=0 avoids visual clutter and signals certainty
- Red color maintains magnitude coding while shape change adds semantic layer

**Alternatives Considered**:
- **Asterisk markers**: Too small, hard to see in dense panels
- **Different color (e.g., black)**: Breaks magnitude-based color scheme
- **Text annotations**: Clutters plot, doesn't scale to many comparisons

**Implementation Pattern**:
```python
if abs(effect_size.value) == 1.0:
    ax.errorbar(..., marker='o', fillstyle='none', linewidth=2, markersize=8)
else:
    ax.errorbar(..., marker='o', fillstyle='full', markersize=6)
```

**References**:
- Scientific visualization best practices: Tufte's "The Visual Display of Quantitative Information"
- Matplotlib markers: [Marker reference](https://matplotlib.org/stable/api/markers_api.html)

---

### R3: Log-Scale X-Axis for Skewed Time Distributions

**Question**: How to handle zeros when log-transforming execution time for efficiency scatter plots?

**Decision**: Use `matplotlib.scale.SymLogScale` (symmetric log) with `linthresh` parameter. Falls back to linear near zero, log elsewhere.

**Rationale**:
- SymLog handles zeros gracefully without adding arbitrary constants
- Maintains sign information (can handle negative values if needed)
- Standard solution in scientific plotting for data spanning orders of magnitude
- `linthresh` can be set to 1.0 second (smallest meaningful time difference)

**Alternatives Considered**:
- **Add constant (e.g., +0.1)**: Arbitrary, distorts data, misleading
- **Drop zeros**: Loses data, unacceptable
- **Separate log and linear plots**: Duplicates figure, increases page count
- **Log-transform data before plotting**: Harder to annotate with original values

**Implementation Pattern**:
```python
if use_log_scale:
    ax.set_xscale('symlog', linthresh=1.0)  # Linear within ±1 second
    ax.set_xlabel(f'{metric_label} (log scale)')
```

**References**:
- Matplotlib scales: [SymLogScale documentation](https://matplotlib.org/stable/api/scale_api.html#matplotlib.scale.SymLogScale)
- Example in ecology data: [Log-scale best practices](https://www.nature.com/articles/nmeth.2173)

---

### R4: Regression Slope/Intercept Annotation Placement

**Question**: Where to place slope/intercept/R² annotations in token-to-cost regression plots without overlapping data?

**Decision**: Use `ax.text()` with `transform=ax.transAxes` for relative positioning (0.05, 0.95 = top-left). One annotation box per framework.

**Rationale**:
- `transAxes` coordinate system (0-1 range) is independent of data scale
- Top-left/top-right corners typically have less data density
- Can check data bounds and dynamically choose least-crowded corner if needed
- Consistent placement aids comparison across figures

**Alternatives Considered**:
- **Absolute data coordinates**: Breaks when data range changes
- **Matplotlib's `AnchoredText`**: More complex API, overkill for simple text
- **Legend with regression params**: Confuses legend purpose (identification vs statistics)
- **Separate table below plot**: Harder to visually associate with lines

**Implementation Pattern**:
```python
for i, framework in enumerate(frameworks):
    # Position annotations vertically stacked in top-right
    y_pos = 0.95 - (i * 0.08)
    ax.text(0.70, y_pos, f'{framework}: y={slope:.4f}x + {intercept:.3f}, R²={r2:.3f}',
            transform=ax.transAxes, fontsize=9, bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
```

**References**:
- Matplotlib text positioning: [Text properties and layout](https://matplotlib.org/stable/tutorials/text/text_props.html)

---

### R5: Coefficient of Variation Edge Cases (Mean = 0)

**Question**: How to handle CV calculation when mean is exactly zero (division by zero)?

**Decision**: Skip CV for that metric-framework combination. Annotate plot with "N/A (mean=0)" and log warning.

**Rationale**:
- CV is mathematically undefined at mean=0
- Substituting 0 or ∞ misleads readers
- Explicit N/A maintains scientific rigor per Constitution principle XIII (Fail-Fast)
- CV is meaningful only for ratio-scale data with meaningful zero anyway

**Alternatives Considered**:
- **Use median instead of mean**: Changes definition of CV, not standard
- **Report as infinity**: Technically correct but visually problematic in bar charts
- **Compute on log-transformed data**: Changes interpretation, assumes log-normal distribution

**Implementation Pattern**:
```python
def compute_cv(values):
    mean = np.mean(values)
    if abs(mean) < 1e-10:  # Effectively zero
        logger.warning(f"CV undefined for metric with mean={mean}")
        return np.nan
    return np.std(values) / mean

# In plotting:
if np.isnan(cv):
    ax.text(x_pos, 0, 'N/A', ha='center', va='bottom')
```

**References**:
- Statistical definition: [Coefficient of Variation](https://en.wikipedia.org/wiki/Coefficient_of_variation)
- Appropriate use cases: Brown, C. E. (1998). "Applied Multivariate Statistics in Geohydrology"

---

### R6: Color-Blind Accessible Palette Verification

**Question**: How to verify color palette meets WCAG 2.1 contrast requirements for accessibility?

**Decision**: Use Seaborn's `colorblind` palette (already in codebase). Verify programmatically with `colorspacious` library for WCAG AA compliance (4.5:1 contrast ratio).

**Rationale**:
- Seaborn colorblind palette designed by experts for accessibility
- Programmatic verification ensures compliance rather than manual checking
- WCAG AA standard (4.5:1) is achievable and recognized
- Already using this palette in existing visualizations (consistency)

**Alternatives Considered**:
- **Manual visual check**: Subjective, error-prone
- **Okabe-Ito palette**: Excellent but would break visual consistency with existing plots
- **Viridis**: Good for continuous data but we need categorical (framework) encoding
- **WCAG AAA (7:1)**: Too restrictive for colored markers on white background

**Implementation Pattern**:
```python
# In _apply_publication_styling():
sns.set_palette("colorblind")

# Verification (in tests):
from colorspacious import deltaE
palette = sns.color_palette("colorblind", 8)
# Check each color against white background
for color in palette:
    contrast_ratio = compute_contrast(color, (1, 1, 1))  # white
    assert contrast_ratio >= 4.5, f"Color {color} fails WCAG AA"
```

**References**:
- WCAG 2.1 Guidelines: [Contrast ratio requirements](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- Seaborn palettes: [Choosing color palettes](https://seaborn.pydata.org/tutorial/color_palettes.html)

---

### R7: Memory Management for Large Faceted Plots

**Question**: How to prevent memory bloat when generating multiple large faceted plots in batch mode?

**Decision**: Explicitly close figures with `plt.close(fig)` after saving. Use context managers where possible.

**Rationale**:
- Matplotlib holds figures in memory until explicitly closed
- Batch generation of 8 plots can accumulate memory
- `plt.close(fig)` releases memory immediately
- NFR-007 requires <500 MB total memory usage

**Alternatives Considered**:
- **Let garbage collector handle it**: Too slow, unpredictable
- **Use `plt.ioff()` (interactive mode off)**: Already set with `matplotlib.use('Agg')`
- **Render to bytes and clear**: More complex, same result

**Implementation Pattern**:
```python
def generate_effect_size_panel(self, ...):
    fig, axes = plt.subplots(...)
    try:
        # ... plotting code ...
        output_path = self._validate_output_path(filename)
        plt.savefig(output_path, format='svg', bbox_inches='tight')
        return Visualization(...)
    finally:
        plt.close(fig)  # Ensure cleanup even if error occurs
```

**References**:
- Matplotlib FAQ: [How to prevent memory leaks](https://matplotlib.org/stable/users/prev_whats_new/whats_new_1.5.html#memory-leak-fixes)

---

### R8: Outlier Detection Consistency with Box Plots

**Question**: Should outlier identification in run-index plots use the same 1.5×IQR rule as box plots?

**Decision**: Yes. Use `scipy.stats.iqr()` and identify outliers as values beyond Q1 - 1.5×IQR or Q3 + 1.5×IQR. Highlight with red color.

**Rationale**:
- Consistency with existing box plot outlier markers (red dots)
- 1.5×IQR is standard statistical convention (Tukey's fences)
- Readers can cross-reference box plots and run-index plots
- Defensible in peer review as standard practice

**Alternatives Considered**:
- **Standard deviation (±2σ or ±3σ)**: Assumes normality, inappropriate for skewed distributions
- **Z-score threshold**: Same normality assumption
- **Modified Z-score (median absolute deviation)**: More robust but less recognizable to readers
- **No outlier marking**: Misses opportunity to highlight data quality issues

**Implementation Pattern**:
```python
def identify_outliers(values):
    q1, q3 = np.percentile(values, [25, 75])
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr
    return (values < lower_fence) | (values > upper_fence)

# In plotting:
outlier_mask = identify_outliers(run_values)
ax.scatter(indices[outlier_mask], run_values[outlier_mask], color='red', s=60, zorder=5, label='Outliers')
```

**References**:
- Tukey, J. W. (1977). "Exploratory Data Analysis"
- Existing implementation: `generate_box_plot()` in statistical_visualizations.py

---

## Summary of Technical Decisions

| Aspect | Technology/Pattern | Justification |
|--------|-------------------|---------------|
| Faceting | `plt.subplots()` with shared axes | Fine control, existing pattern, no new dependencies |
| Complete separation markers | Open circles, no error bars | Visually distinctive, semantically appropriate |
| Log-scale for zeros | `SymLogScale` with `linthresh=1.0` | Handles zeros gracefully, standard solution |
| Regression annotations | `ax.text()` with `transAxes` | Position-independent, clear, customizable |
| CV edge cases | Return `np.nan`, annotate "N/A" | Mathematically honest, fail-fast compliance |
| Color accessibility | Seaborn colorblind palette + verification | Already in use, WCAG 2.1 compliant |
| Memory management | `plt.close(fig)` in finally block | Prevents leaks, meets NFR-007 |
| Outlier detection | 1.5×IQR (Tukey fences) | Consistent with box plots, standard practice |

**Next Phase**: Proceed to Phase 1 (Design & Contracts) to define data models and method signatures.
