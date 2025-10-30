# Feature Specification: Enhanced Statistical Visualizations for Paper Generation

**Feature Branch**: `015-enhance-statistical-visualizations`  
**Created**: 2025-10-30  
**Status**: Draft  
**Input**: User description: "Enhance statistical visualizations with advanced comparative plots for paper generation including effect-size panels, efficiency plots, cost-per-token analysis, and multi-metric comparisons"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Effect Size Visualization Across All Metrics (Priority: P1)

A researcher has completed an experiment comparing three frameworks (BAEs, ChatDev, GHSpec) and needs to show reviewers not just that differences are statistically significant, but **how large** those differences are across multiple metrics simultaneously. They want a single comprehensive visualization that shows effect sizes for execution time, cost, API calls, and token usage in one figure.

**Why this priority**: This addresses the most critical reviewer question: "You say all comparisons are significant, but are they *meaningful*?" Effect size is more important than p-values for scientific communication. This is the foundation for the entire visualization enhancement.

**Independent Test**: Can be fully tested by generating an experiment with 3+ frameworks and 5+ metrics, running the paper generation, and verifying a faceted effect-size panel is created with color-coded magnitudes (negligible/small/medium/large) for all pairwise comparisons.

**Acceptance Scenarios**:

1. **Given** an experiment with 3 frameworks and 7 metrics, **When** generating statistical visualizations, **Then** a faceted panel plot is created showing effect sizes (Cliff's δ) for all pairwise comparisons across all metrics
2. **Given** effect sizes ranging from negligible to large, **When** rendering the panel, **Then** each effect is color-coded (gray=negligible, green=small, orange=medium, red=large) with confidence intervals displayed
3. **Given** complete separation (|δ| = 1.0), **When** plotting the effect, **Then** special markers are used to indicate perfect separation with no uncertainty
4. **Given** the generated panel plot, **When** included in a paper, **Then** the visualization clearly shows which metrics have large vs small effects without requiring table lookup

---

### User Story 2 - Cost-Performance Efficiency Analysis (Priority: P1)

A researcher needs to communicate the trade-off story: "BAEs is cheap and fast; ChatDev is slower with medium cost; GHSpec is slower than BAEs and costlier than ChatDev." They want a single plot that makes this immediately obvious to readers, replacing three separate summary tables.

**Why this priority**: This directly addresses the paper's core narrative about framework efficiency. A scatter plot of cost vs time is the clearest way to show multi-dimensional performance in two dimensions, and is essential for executive summaries and conference presentations.

**Independent Test**: Can be fully tested by generating an experiment with frameworks having different cost/time characteristics, running visualization generation, and verifying a scatter plot is created showing clear clustering of frameworks by efficiency profile.

**Acceptance Scenarios**:

1. **Given** an experiment tracking execution_time and total_cost_usd, **When** generating efficiency visualizations, **Then** a scatter plot is created with time on x-axis and cost on y-axis
2. **Given** multiple runs per framework, **When** plotting, **Then** points are optionally jittered or aggregated with error bars to show variability
3. **Given** skewed time distributions, **When** requested, **Then** log-scale x-axis option is available for clearer separation
4. **Given** the efficiency plot, **When** viewing, **Then** each framework's efficiency quadrant is immediately apparent (fast-cheap, fast-expensive, slow-cheap, slow-expensive)

---

### User Story 3 - Token-to-Cost Relationship Analysis (Priority: P2)

A researcher observes that GHSpec costs more than ChatDev even when using similar token volumes, and wants to visualize this systematic overhead. They need a plot showing whether frameworks have different cost-per-token slopes, revealing implementation inefficiencies.

**Why this priority**: This provides deeper analytical insight beyond raw performance metrics. It helps explain *why* one framework is more expensive (higher base cost? higher per-token rate? caching inefficiency?), which is valuable for framework developers and researchers.

**Independent Test**: Can be fully tested by generating an experiment with varying token volumes, running regression visualization, and verifying separate regression lines are fitted per framework with different slopes/intercepts visible.

**Acceptance Scenarios**:

1. **Given** an experiment with tokens_in and total_cost_usd metrics, **When** generating regression visualization, **Then** a scatter plot with framework-specific regression lines is created
2. **Given** different frameworks, **When** fitting regressions, **Then** slope and intercept differences are visually apparent and optionally annotated
3. **Given** the regression plot, **When** two frameworks use similar token volumes, **Then** cost differences are visible as vertical separation between regression lines
4. **Given** cached_tokens data, **When** available, **Then** an option exists to show how caching affects the cost relationship

---

### User Story 4 - Distribution Overlap Visualization for Similar Metrics (Priority: P2)

A researcher has one metric (tokens_out) where ChatDev ≈ GHSpec — the difference is statistically detectable but practically small. They need to visualize this subtle distinction separately from the 3-way comparisons to justify statements like "difference is statistically detectable but practically negligible."

**Why this priority**: Scientific rigor requires acknowledging when effects are small. A focused 2-way comparison plot helps reviewers understand nuance and prevents over-claiming. This builds credibility for the larger claims.

**Independent Test**: Can be fully tested by identifying metric pairs with small effect sizes (|δ| < 0.3), generating focused comparison visualizations, and verifying density overlap is clearly shown.

**Acceptance Scenarios**:

1. **Given** a metric with small effect size between two frameworks, **When** generating overlap visualization, **Then** a 2-density or 2-violin plot is created showing distribution overlap
2. **Given** the overlap plot, **When** viewing, **Then** the degree of distribution overlap is immediately visible through density curve intersection
3. **Given** statistical test results, **When** annotating the plot, **Then** both statistical significance (p-value) and practical significance (effect size) are displayed
4. **Given** near-identical distributions, **When** plotting, **Then** the visualization supports conclusions about practical equivalence

---

### User Story 5 - Normalized Cost-Per-Token Comparison (Priority: P2)

A researcher wants to isolate framework overhead from raw usage volume. They need a visualization showing cost per 1000 tokens across frameworks to demonstrate that GHSpec has higher overhead even after normalizing for volume.

**Why this priority**: This provides a normalized efficiency metric that removes confounds. It's critical for fair comparison when frameworks use different token volumes by design (e.g., one is more verbose but not necessarily less efficient).

**Independent Test**: Can be fully tested by computing cost_per_1k_tokens for all runs, generating box plots, and verifying frameworks are ranked by efficiency rather than raw cost.

**Acceptance Scenarios**:

1. **Given** total_cost_usd and tokens_total metrics, **When** generating normalized cost visualization, **Then** cost per 1000 tokens is computed for each run
2. **Given** normalized costs, **When** plotting, **Then** a box plot compares distributions across frameworks
3. **Given** the normalized plot, **When** a framework uses more tokens but has lower per-token cost, **Then** this efficiency advantage is visible
4. **Given** frameworks with similar raw costs, **When** normalized by tokens, **Then** volume vs efficiency trade-offs become apparent

---

### User Story 6 - Multi-Metric Framework Ranking (Priority: P3)

A researcher wants to show that BAEs consistently ranks #1 across metrics (time, cost, tokens) while ChatDev and GHSpec alternate ranks 2/3. They need a line plot connecting rankings across metrics to show consistency patterns.

**Why this priority**: This provides a high-level summary suitable for discussion sections and presentations. It's less critical than the detailed comparisons but valuable for pattern recognition and narrative building.

**Independent Test**: Can be fully tested by ranking frameworks on 5+ metrics, generating a rank plot, and verifying rank consistency patterns are visible through line trajectories.

**Acceptance Scenarios**:

1. **Given** multiple metrics, **When** generating rank visualization, **Then** each framework is ranked 1-3 per metric (1=best)
2. **Given** rankings, **When** plotting, **Then** metrics appear on x-axis, ranks on y-axis, with framework lines connecting ranks
3. **Given** a framework that consistently outperforms, **When** viewing the plot, **Then** a flat line at rank=1 is visible
4. **Given** frameworks with mixed performance, **When** viewing, **Then** crossing lines show where trade-offs exist

---

### User Story 7 - Coefficient of Variation Stability Analysis (Priority: P3)

A researcher wants to claim not only that BAEs is faster but also more **predictable**. They need a visualization showing variability (coefficient of variation = sd/mean) across frameworks to support stability claims.

**Why this priority**: Stability/predictability is valuable for production deployment decisions. However, it's secondary to core performance metrics, making it suitable for supplementary material or detailed discussion.

**Independent Test**: Can be fully tested by computing CV for each metric per framework, generating a grouped bar plot, and verifying lower CV values are highlighted as better stability.

**Acceptance Scenarios**:

1. **Given** metrics with standard deviations, **When** computing CV, **Then** CV = sd/mean is calculated for each framework-metric combination
2. **Given** CV values, **When** plotting, **Then** a grouped or faceted bar plot compares CV across frameworks
3. **Given** low CV (<0.2) indicating high stability, **When** annotating, **Then** stable frameworks are highlighted
4. **Given** the CV plot, **When** a framework is both faster and more stable, **Then** both advantages are communicated

---

### User Story 8 - Outlier Impact Visualization (Priority: P3)

A researcher observes some long-tail runtimes in ChatDev's box plot and wants to show that "long runtimes are not the norm, but a few high-latency runs inflate the mean." They need a time-series style plot showing individual run values to distinguish systematic slowness from occasional outliers.

**Why this priority**: This provides analytical depth for reviewers who scrutinize data quality. It's important for scientific rigor but not essential for the main narrative, making it appropriate for supplementary figures.

**Independent Test**: Can be fully tested by generating an experiment with outlier runs, creating run-index plots per framework, and verifying outliers are visually distinct from the main distribution.

**Acceptance Scenarios**:

1. **Given** metrics with identified outliers, **When** generating run-index plots, **Then** run number appears on x-axis with metric values on y-axis
2. **Given** separate panels per framework, **When** plotting, **Then** outlier runs are distinguishable from typical performance
3. **Given** high-variance frameworks, **When** viewing the plot, **Then** it's clear whether variance comes from drift, outliers, or inherent variability
4. **Given** the outlier plot, **When** combined with box plots, **Then** reviewers can assess whether summary statistics are representative

---

### Edge Cases

- What happens when a metric has only 2 unique values (e.g., binary success/failure)? → Skip continuous distribution plots, use proportion comparison instead
- What happens when two frameworks have identical performance on a metric? → Show overlapping distributions with annotation indicating practical equivalence
- What happens when regression has zero slope (flat line)? → Annotate with "no relationship detected" and show R² value
- What happens when CV cannot be computed (mean = 0)? → Skip CV for that metric and note in legend
- What happens when a framework has only 1 run (n=1)? → Cannot compute variability; exclude from stability analyses and annotate
- What happens when effect size confidence interval crosses zero? → Use gray/neutral color and annotate "uncertain direction"
- What happens when requesting log-scale but metric contains zeros? → Add small constant (min positive value / 10) or use symlog scale
- What happens when faceted plots have too many metrics (>10)? → Use multi-page output or focus on top N metrics by variance/effect size

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST generate effect-size panel plots showing Cliff's δ (or Cohen's d where appropriate) for all pairwise framework comparisons across all metrics
- **FR-002**: Effect-size panels MUST use color coding (gray=negligible, green=small, orange=medium, red=large) based on standard magnitude thresholds
- **FR-003**: System MUST generate cost-vs-time efficiency scatter plots with framework-specific colors and optional jittering
- **FR-004**: Efficiency plots MUST support optional log-scale transformation for skewed time distributions
- **FR-005**: System MUST generate tokens-to-cost regression plots with separate fitted lines per framework
- **FR-006**: Regression plots MUST display slope/intercept statistics and R² values per framework
- **FR-007**: System MUST generate focused 2-way distribution overlap plots (density or violin) for metric pairs with small effect sizes (|δ| < 0.3)
- **FR-008**: System MUST compute and visualize cost per 1000 tokens as a derived metric
- **FR-009**: System MUST generate multi-metric rank plots showing framework rankings (1-3) connected by lines
- **FR-010**: System MUST compute and visualize coefficient of variation (CV = sd/mean) for stability analysis
- **FR-011**: System MUST generate run-index plots to visualize individual runs and identify outliers
- **FR-012**: All new visualizations MUST be saved as SVG files for publication quality
- **FR-013**: All new visualizations MUST include descriptive titles, axis labels with units, and informative captions
- **FR-014**: System MUST handle edge cases gracefully (zero variance, missing data, n=1 groups) with informative annotations
- **FR-015**: Visualization generator MUST support batch generation of all plot types with a single method call
- **FR-016**: Each visualization MUST return metadata (Visualization object) with file path, title, caption, and groups included
- **FR-017**: System MUST apply consistent publication styling (colorblind-friendly palettes, readable fonts, 300 DPI) across all new plots
- **FR-018**: Effect-size plots MUST show 95% confidence intervals as error bars or shaded regions
- **FR-019**: System MUST detect and specially mark complete separation cases (|δ| = 1.0) in effect-size plots
- **FR-020**: Regression plots MUST support optional inclusion of cached_tokens as a third dimension (via color or size encoding)

### Key Entities

- **EffectSizePanel**: Multi-metric faceted visualization showing all pairwise effect sizes; attributes: metrics (list), comparisons (list of tuples), effect_sizes (dict), magnitudes (dict), confidence_intervals (dict)
- **EfficiencyPlot**: Cost-vs-time scatter with framework clustering; attributes: time_metric, cost_metric, use_log_scale (bool), jitter_amount (float)
- **RegressionPlot**: Token-to-cost relationship with framework-specific lines; attributes: x_metric, y_metric, regression_params (dict per framework), r_squared (dict)
- **OverlapPlot**: 2-way distribution comparison for similar groups; attributes: metric_name, group_a, group_b, effect_size (float), p_value (float)
- **NormalizedCostPlot**: Cost per 1000 tokens comparison; attributes: derived_metric (cost_per_1k_tokens), distributions (list)
- **RankPlot**: Framework rankings across metrics; attributes: metrics (list), frameworks (list), rankings (dict)
- **StabilityPlot**: Coefficient of variation comparison; attributes: cv_values (dict per framework per metric), threshold (float for "stable")
- **OutlierPlot**: Run-index visualization; attributes: metric_name, framework, run_indices (list), values (list), outlier_indices (list)

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Researchers can generate all 8 new visualization types from a single experiment run in under 30 seconds total processing time
- **SC-002**: Effect-size panel plots correctly display all pairwise comparisons for experiments with up to 10 metrics and 5 frameworks
- **SC-003**: Generated SVG files are publication-ready at 300 DPI without requiring external editing tools
- **SC-004**: Cost-vs-time efficiency plots make framework performance quadrants (fast-cheap, slow-expensive, etc.) immediately distinguishable to viewers
- **SC-005**: Token-to-cost regression plots correctly identify and visualize different cost structures (R² > 0.7 when strong relationship exists)
- **SC-006**: All visualizations handle edge cases (zero variance, n=1, missing data) without crashing and include informative annotations
- **SC-007**: Generated plots use colorblind-friendly palettes verified against accessibility guidelines (WCAG 2.1 contrast ratios)
- **SC-008**: Visualization captions provide sufficient context that readers can interpret plots without referring to paper text
- **SC-009**: Effect size magnitudes (negligible/small/medium/large) align with statistical conventions (Cliff's δ thresholds: 0.11, 0.28, 0.43)
- **SC-010**: Batch visualization generation produces consistent styling across all plot types (fonts, colors, sizes)
- **SC-011**: Rank plots correctly show consistency patterns (e.g., flat line for consistently top-ranked framework)
- **SC-012**: CV stability plots highlight frameworks with CV < 0.20 as "highly stable" per standard definitions
- **SC-013**: All 12 plots (4 existing + 8 new) are generated by default in paper generation workflow
- **SC-014**: No existing visualization methods are deleted or modified (backward compatibility maintained)

## Assumptions *(mandatory)*

- Experiments provide metrics in standard format (execution_time, total_cost_usd, tokens_in, tokens_out, tokens_total, api_calls, cached_tokens)
- Statistical analysis (effect sizes, p-values, confidence intervals) has been performed before visualization generation
- Matplotlib 3.5+, seaborn 0.12+, and scipy 1.11+ are available in the environment
- Output directory has write permissions for creating SVG files
- Experiments have at least 2 frameworks and 1 metric (minimum viable data)
- For regression plots, token and cost data are numeric and non-negative
- Coefficient of variation is meaningful (assumes metrics are ratio-scale with meaningful zero point)
- Rank plots assume "lower is better" for cost/time metrics and "higher is better" where appropriate (configurable)
- Paper generation workflow calls visualization generator after statistical analysis is complete
- Generated visualizations are intended for scientific papers (IEEE, ACM, Springer style guides)

## Dependencies *(mandatory)*

- Existing `StatisticalVisualizationGenerator` class in `src/paper_generation/statistical_visualizations.py`
- Statistical analysis results from `StatisticalAnalyzer` (effect sizes, distributions, test results)
- Experiment run data in JSON format with required metrics
- Existing publication styling configuration (colorblind palette, 300 DPI SVG output)
- `Visualization` model class for metadata return values
- `MetricDistribution` and `EffectSize` classes for input data structures

## Scope *(mandatory)*

### In Scope

- Implementation of 8 new visualization generation methods in existing `StatisticalVisualizationGenerator` class
- Effect-size panel plots with faceting by metric
- Cost-vs-time efficiency scatter plots with log-scale option
- Token-to-cost regression plots with framework-specific lines
- Distribution overlap plots for 2-way comparisons
- Normalized cost-per-1k-tokens box plots
- Multi-metric rank plots with connected lines
- Coefficient of variation stability plots
- Run-index outlier visualization plots
- Batch generation method for all plot types
- Edge case handling (zero variance, n=1, missing data)
- Publication-quality SVG output with consistent styling
- Informative captions and axis labels
- Color-coded effect size magnitudes
- Confidence interval visualization
- Complete separation markers (|δ| = 1.0)

### Out of Scope

- Interactive visualizations (D3.js, Plotly) — static SVG only
- Radar/spider plots — deferred to future enhancement
- PCA/biplot visualizations — deferred to future enhancement  
- Runtime decomposition by subtask — requires data not currently collected
- Correlation heatmaps — deferred to future enhancement
- Gardner-Altman estimation plots — deferred to future enhancement
- Automated plot selection based on venue (IEEE/ACM style variants) — use manual selection
- Multi-page PDF output for large faceted plots — single-page SVG only
- Animation or time-series visualizations
- 3D plots or surface plots
- Machine learning model visualizations (ROC curves, confusion matrices)
- Cost modeling beyond linear regression (polynomial, non-parametric)
- Statistical power visualizations
- Bayesian posterior visualizations

## Non-Functional Requirements

- **NFR-001**: Visualization generation must complete in under 5 seconds per plot type for experiments with up to 100 runs per framework
- **NFR-002**: Generated SVG files must be under 2 MB each for efficient loading in papers/web
- **NFR-003**: Code must include docstrings following Google style guide for all new methods
- **NFR-004**: All new visualization methods must be validated through real paper generation with actual experiment data
- **NFR-005**: Error messages must clearly indicate which metric/framework caused failure and suggest resolution
- **NFR-006**: Visualization code must be modular to allow easy addition of new plot types in future
- **NFR-007**: Memory usage must not exceed 500 MB during batch generation of all visualization types
