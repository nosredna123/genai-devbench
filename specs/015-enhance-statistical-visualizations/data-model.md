# Data Model: Enhanced Statistical Visualizations

**Phase**: 1 - Design & Contracts  
**Date**: 2025-10-30  
**Purpose**: Define data structures for 8 new visualization types extending the existing Visualization model

---

## Core Entities

### Visualization (Existing - Reference Only)

**Location**: `src/paper_generation/models.py`  
**Purpose**: Metadata object returned by all visualization generation methods

**Attributes**:
- `viz_type`: VisualizationType enum (BOXPLOT, VIOLIN, FOREST, QQ, **new types added**)
- `metric_name`: str - The metric being visualized
- `file_path`: Path - Absolute path to saved SVG file
- `format`: str - Always "svg" for this feature
- `title`: str - Plot title for paper inclusion
- `caption`: str - Descriptive caption explaining the plot
- `groups`: List[str] - Framework names included in comparison

**Validation Rules** (from FR-016):
- `file_path` must exist after generation
- `caption` must be non-empty and self-explanatory (SC-008)
- `title` must include metric name with units

**State Transitions**: Immutable after creation (dataclass with frozen=True)

---

## New Visualization Types (Extension of VisualizationType Enum)

### VisualizationType Enum Extensions

**Location**: `src/paper_generation/statistical_analyzer.py` (or models.py)

**New Values**:
```python
class VisualizationType(Enum):
    # Existing values
    BOXPLOT = "boxplot"
    VIOLIN = "violin"
    FOREST = "forest"
    QQ = "qq"
    
    # NEW values for this feature
    EFFECT_PANEL = "effect_panel"           # Multi-metric faceted effect sizes
    EFFICIENCY = "efficiency"               # Cost vs time scatter
    REGRESSION = "regression"               # Token-to-cost with fitted lines
    OVERLAP = "overlap"                     # 2-way distribution comparison
    NORMALIZED_COST = "normalized_cost"     # Cost per 1k tokens
    RANK = "rank"                           # Multi-metric rankings
    STABILITY = "stability"                 # Coefficient of variation
    OUTLIER_RUN = "outlier_run"            # Run-index time series
```

---

## Input Data Structures (Existing - Used by New Methods)

### MetricDistribution (Existing)

**Location**: `src/paper_generation/statistical_analyzer.py`

**Attributes**:
- `group_name`: str - Framework name
- `metric_name`: str - Metric being measured
- `values`: np.ndarray - Raw data points
- `n`: int - Sample size
- `mean`: float - Arithmetic mean
- `median`: float - Median value
- `std`: float - Standard deviation
- `min`: float, `max`: float - Range
- `q1`: float, `q3`: float - Quartiles
- `iqr`: float - Interquartile range
- `skewness`: float, `kurtosis`: float - Distribution shape
- `outliers`: List[float] - Values beyond 1.5×IQR

**Usage**: Primary input for all distribution-based plots (box, violin, overlap, normalized cost, outlier runs)

---

### EffectSize (Existing)

**Location**: `src/paper_generation/statistical_analyzer.py`

**Attributes**:
- `group_a`: str, `group_b`: str - Compared frameworks
- `metric`: str - Metric name
- `measure`: EffectSizeMeasure - COHENS_D or CLIFFS_DELTA
- `value`: float - Effect size estimate
- `magnitude`: str - "negligible", "small", "medium", "large"
- `ci_lower`: float, `ci_upper`: float - 95% confidence interval
- `interpretation`: str - Human-readable explanation

**Usage**: Primary input for forest plots and effect-size panels

---

## Derived Data Structures (Computed by New Methods)

### RegressionResult

**Purpose**: Store regression statistics for token-to-cost relationships

**Attributes**:
- `framework`: str - Framework name
- `x_metric`: str - Independent variable (e.g., "tokens_in")
- `y_metric`: str - Dependent variable (e.g., "total_cost_usd")
- `slope`: float - Regression coefficient (cost per token)
- `intercept`: float - Baseline cost
- `r_squared`: float - Goodness of fit (0-1)
- `p_value`: float - Statistical significance of slope
- `n_points`: int - Number of data points used

**Validation Rules** (from FR-006):
- `r_squared` must be in [0, 1]
- `n_points` must be ≥ 3 for meaningful regression
- `slope` and `intercept` must be finite (not NaN or inf)

**Relationships**: One RegressionResult per framework in a regression plot

---

### RankData

**Purpose**: Store framework rankings across multiple metrics

**Attributes**:
- `framework`: str - Framework name
- `metric`: str - Metric being ranked
- `rank`: int - Rank position (1=best, higher=worse)
- `value`: float - Actual metric value (for reference)
- `is_lower_better`: bool - Ranking direction (True for time/cost, False for accuracy)

**Validation Rules** (from FR-009):
- `rank` must be in [1, n_frameworks]
- No ties (use average rank if values are identical)
- Ranking direction must be consistent with metric semantics

**Relationships**: Forms NxM matrix where N=frameworks, M=metrics. Each cell is one RankData.

---

### StabilityMetric

**Purpose**: Store coefficient of variation for stability analysis

**Attributes**:
- `framework`: str - Framework name
- `metric`: str - Metric being analyzed
- `cv`: float - Coefficient of variation (σ/μ)
- `mean`: float - Mean value (for context)
- `std`: float - Standard deviation (for context)
- `n`: int - Sample size
- `is_stable`: bool - True if CV < 0.20 threshold (SC-012)

**Validation Rules** (from FR-010):
- `cv` must be non-negative (or NaN if mean=0)
- `is_stable` computed as `cv < 0.20`
- If `mean` ≈ 0, `cv` = NaN and `is_stable` = False

**Relationships**: One StabilityMetric per framework-metric combination

---

### OutlierInfo

**Purpose**: Identify and mark outlier runs in time-series plots

**Attributes**:
- `run_index`: int - Sequential run number
- `value`: float - Metric value for this run
- `is_outlier`: bool - True if beyond 1.5×IQR fences
- `fence_lower`: float - Lower bound (Q1 - 1.5×IQR)
- `fence_upper`: float - Upper bound (Q3 + 1.5×IQR)

**Validation Rules** (from research R8):
- Outlier detection uses Tukey fences (1.5×IQR)
- Consistent with box plot outlier identification
- `run_index` must be sequential and start from 0 or 1

**Relationships**: List[OutlierInfo] for each framework in an outlier run plot

---

## Method Return Types

All 8 new visualization methods return `Visualization` objects with appropriate `viz_type`:

| Method | viz_type | Additional Metadata |
|--------|----------|---------------------|
| `generate_effect_size_panel()` | EFFECT_PANEL | `groups` = all frameworks, `metric_name` = "multi" |
| `generate_efficiency_plot()` | EFFICIENCY | `groups` = all frameworks, `metric_name` = "cost_vs_time" |
| `generate_regression_plot()` | REGRESSION | `groups` = all frameworks, `metric_name` = x_metric |
| `generate_overlap_plot()` | OVERLAP | `groups` = [group_a, group_b], `metric_name` = specific metric |
| `generate_normalized_cost_plot()` | NORMALIZED_COST | `groups` = all frameworks, `metric_name` = "cost_per_1k_tokens" |
| `generate_rank_plot()` | RANK | `groups` = all frameworks, `metric_name` = "multi" |
| `generate_stability_plot()` | STABILITY | `groups` = all frameworks, `metric_name` = "cv" |
| `generate_outlier_run_plot()` | OUTLIER_RUN | `groups` = [single framework], `metric_name` = specific metric |

---

## Data Flow

```
StatisticalAnalyzer
    ↓ (produces)
MetricDistribution[] + EffectSize[]
    ↓ (input to)
StatisticalVisualizationGenerator
    ↓ (computes derived data)
RegressionResult / RankData / StabilityMetric / OutlierInfo
    ↓ (renders to)
SVG file + Visualization metadata
    ↓ (consumed by)
PaperGenerator (includes in markdown/LaTeX)
```

---

## Edge Case Handling in Data Model

### Zero Variance Distributions
- `MetricDistribution.std` = 0 → Cannot compute CV, mark as NaN
- Regression with zero variance in X or Y → Skip that framework, annotate plot

### Single-Run Frameworks (n=1)
- `MetricDistribution.n` = 1 → Cannot compute quartiles or CV
- Exclude from stability and outlier plots
- Annotate in visualizations: "N/A (n=1)"

### Complete Separation (|δ| = 1.0)
- `EffectSize.value` = ±1.0 and `ci_lower` = `ci_upper` = ±1.0
- Special marker in effect-size panels (open circle, no error bar)

### Missing Data
- If metric not present for a framework → exclude from that plot
- If all frameworks missing a metric → skip that metric entirely
- Log warnings for transparency

---

## Validation Summary

All data structures enforce:
1. **Type safety**: Use Python type hints (NFR-003)
2. **Bounds checking**: Values in valid ranges (e.g., R² ∈ [0,1])
3. **NaN handling**: Explicit NaN for undefined values (not zeros or placeholders)
4. **Fail-fast**: Invalid data raises exceptions immediately (Constitution XIII)

**Next Phase**: Define method contracts (API signatures) in `contracts/` directory.
