# Data Model Specification

**Feature**: Enhanced Statistical Report Generation  
**Version**: 1.0  
**Date**: 2025-10-29

## Overview

This document defines the data structures used throughout the statistical analysis and report generation pipeline. All entities are designed for clarity, type safety, and easy serialization to JSON/YAML.

---

## Core Entities

### 1. MetricDistribution

**Purpose**: Represents the distribution of a single metric for a single framework across all runs.

**Fields**:
```python
{
    "metric_name": str,              # e.g., "execution_time"
    "framework_name": str,           # e.g., "ChatDev"
    "values": List[float],           # Raw values from all runs
    "n_runs": int,                   # Number of runs (len(values))
    "mean": float,
    "median": float,
    "std": float,
    "q1": float,                     # 25th percentile
    "q3": float,                     # 75th percentile
    "min": float,
    "max": float,
    "iqr": float,                    # Q3 - Q1
    "cv": float,                     # Coefficient of variation (std/mean)
    "outliers": List[float],         # Values beyond 1.5*IQR from quartiles
    "zero_variance": bool            # True if std == 0
}
```

**Validation Rules**:
- `n_runs >= 2` (minimum for any statistical analysis)
- `values` not empty
- `std >= 0`, `cv >= 0`
- `q1 <= median <= q3`
- `min <= q1 <= q3 <= max`

**Relationships**:
- Input to `AssumptionCheck` (normality testing)
- Input to `StatisticalTest` (when comparing distributions)

---

### 2. AssumptionCheck

**Purpose**: Results of statistical assumption tests (normality, variance homogeneity).

**Fields**:
```python
{
    "test_name": str,                # "Shapiro-Wilk" or "Levene"
    "metric_name": str,
    "frameworks": List[str],         # Frameworks tested
    "statistic": float,              # Test statistic value
    "p_value": float,
    "alpha": float,                  # Significance level (default 0.05)
    "passed": bool,                  # p_value > alpha
    "interpretation": str,           # Plain-language result
    "recommendation": str            # Which test to use given result
}
```

**Examples**:
```python
# Shapiro-Wilk normality test
{
    "test_name": "Shapiro-Wilk",
    "metric_name": "execution_time",
    "frameworks": ["ChatDev"],
    "statistic": 0.92,
    "p_value": 0.35,
    "alpha": 0.05,
    "passed": True,
    "interpretation": "Data appears normally distributed (bell curve)",
    "recommendation": "Parametric tests (t-test, ANOVA) are appropriate"
}

# Levene's test for variance homogeneity
{
    "test_name": "Levene",
    "metric_name": "execution_time",
    "frameworks": ["ChatDev", "MetaGPT"],
    "statistic": 1.23,
    "p_value": 0.28,
    "alpha": 0.05,
    "passed": True,
    "interpretation": "Variance is similar across groups",
    "recommendation": "Standard t-test or ANOVA can be used"
}
```

**Validation Rules**:
- `0 <= p_value <= 1`
- `alpha > 0` (typically 0.05)
- `len(frameworks) >= 1`

---

### 3. StatisticalTest

**Purpose**: Results of hypothesis testing (t-test, Mann-Whitney U, ANOVA, Kruskal-Wallis).

**Fields**:
```python
{
    "test_name": str,                # "Independent t-test", "Mann-Whitney U", etc.
    "metric_name": str,
    "frameworks": List[str],         # 2 for pairwise, 3+ for omnibus
    "test_type": str,                # "parametric" or "non_parametric"
    "statistic": float,              # t, U, F, or H statistic
    "p_value": float,
    "alpha": float,                  # Significance level
    "significant": bool,             # p_value < alpha
    "alternative": str,              # "two-sided", "less", "greater"
    "interpretation": str,           # Plain-language result
    "method_notes": str              # e.g., "Welch's t-test (unequal variance)"
}
```

**Example**:
```python
{
    "test_name": "Mann-Whitney U",
    "metric_name": "execution_time",
    "frameworks": ["ChatDev", "MetaGPT"],
    "test_type": "non_parametric",
    "statistic": 42.5,
    "p_value": 0.032,
    "alpha": 0.05,
    "significant": True,
    "alternative": "two-sided",
    "interpretation": "Significant difference detected (p=0.032)",
    "method_notes": "Used due to non-normal distribution (Shapiro-Wilk p=0.012)"
}
```

**Validation Rules**:
- `0 <= p_value <= 1`
- `len(frameworks) >= 2`
- `test_type in ["parametric", "non_parametric"]`
- `alternative in ["two-sided", "less", "greater"]`

---

### 4. EffectSize

**Purpose**: Quantifies the magnitude of difference between groups.

**Fields**:
```python
{
    "measure": str,                  # "Cohen's d" or "Cliff's delta"
    "metric_name": str,
    "frameworks": Tuple[str, str],   # (group1, group2)
    "value": float,                  # Effect size value
    "ci_lower": float,               # 95% CI lower bound
    "ci_upper": float,               # 95% CI upper bound
    "ci_method": str,                # "bootstrap" (10,000 iterations)
    "magnitude": str,                # "negligible", "small", "medium", "large"
    "interpretation": str,           # Plain-language explanation with analogy
    "direction": str                 # "group1 > group2" or "group1 < group2"
}
```

**Magnitude Thresholds**:
- **Cohen's d**: |d| < 0.2 negligible, 0.2-0.5 small, 0.5-0.8 medium, ≥0.8 large
- **Cliff's delta**: |δ| < 0.147 negligible, 0.147-0.33 small, 0.33-0.474 medium, ≥0.474 large

**Example**:
```python
{
    "measure": "Cohen's d",
    "metric_name": "execution_time",
    "frameworks": ("ChatDev", "MetaGPT"),
    "value": 0.72,
    "ci_lower": 0.28,
    "ci_upper": 1.16,
    "ci_method": "bootstrap (10,000 iterations)",
    "magnitude": "medium",
    "interpretation": "ChatDev is 0.72 standard deviations faster than MetaGPT (medium effect, like the height difference between 13 and 16 year-olds)",
    "direction": "ChatDev < MetaGPT"
}
```

**Validation Rules**:
- `-inf < value < inf` (can be negative)
- `ci_lower <= value <= ci_upper`
- `magnitude in ["negligible", "small", "medium", "large"]`

---

### 5. PowerAnalysis

**Purpose**: Statistical power and sample size recommendations.

**Fields**:
```python
{
    "metric_name": str,
    "frameworks": List[str],
    "effect_size": float,            # Observed effect size (Cohen's d or Cliff's delta)
    "current_n": int,                # Current sample size per group
    "achieved_power": float,         # 0-1 (e.g., 0.65 = 65%)
    "target_power": float,           # Recommended (0.80)
    "recommended_n": int,            # Sample size needed for target power
    "alpha": float,                  # Significance level
    "power_adequate": bool,          # achieved_power >= target_power
    "interpretation": str,           # Plain-language explanation
    "recommendation": str            # Action to take
}
```

**Example**:
```python
{
    "metric_name": "execution_time",
    "frameworks": ["ChatDev", "MetaGPT"],
    "effect_size": 0.72,
    "current_n": 5,
    "achieved_power": 0.54,
    "target_power": 0.80,
    "recommended_n": 13,
    "alpha": 0.05,
    "power_adequate": False,
    "interpretation": "Only 54% chance of detecting this effect with current sample size",
    "recommendation": "⚠️ Increase to 13 runs per framework to achieve 80% power (reliable detection)"
}
```

**Validation Rules**:
- `0 <= achieved_power <= 1`
- `0 < target_power < 1`
- `current_n >= 2`
- `recommended_n >= current_n`

---

### 6. Visualization

**Purpose**: Metadata for generated statistical plots.

**Fields**:
```python
{
    "plot_type": str,                # "box_plot", "violin_plot", "forest_plot", "qq_plot"
    "metric_name": str,
    "frameworks": List[str],
    "file_path": str,                # Relative path (e.g., "figures/statistical/box_plot_execution_time.svg")
    "format": str,                   # "svg"
    "dimensions": Tuple[int, int],   # (width, height) in pixels
    "caption": str,                  # Plain-language caption for paper
    "alt_text": str,                 # Accessibility text
    "embedded_in": List[str]         # Sections where used: ["results", "appendix"]
}
```

**Example**:
```python
{
    "plot_type": "violin_plot",
    "metric_name": "execution_time",
    "frameworks": ["ChatDev", "MetaGPT", "CrewAI"],
    "file_path": "figures/statistical/violin_plot_execution_time.svg",
    "format": "svg",
    "dimensions": (800, 600),
    "caption": "Distribution of execution times shows ChatDev (median 45s) significantly faster than MetaGPT (median 78s, p=0.032, d=0.72)",
    "alt_text": "Violin plot comparing execution time distributions for ChatDev, MetaGPT, and CrewAI",
    "embedded_in": ["results"]
}
```

**Validation Rules**:
- `plot_type in ["box_plot", "violin_plot", "forest_plot", "qq_plot"]`
- `format == "svg"`
- `file_path` ends with `.svg`

---

### 7. StatisticalFindings (Top-Level Container)

**Purpose**: Aggregates all statistical analysis results for a single experiment.

**Fields**:
```python
{
    "experiment_name": str,
    "primary_metric": str,           # Most important metric for comparison
    "n_frameworks": int,
    "n_metrics": int,
    "n_runs_per_framework": Dict[str, int],
    "distributions": Dict[str, List[MetricDistribution]],
        # Key: metric_name, Value: list of distributions (one per framework)
    "assumption_checks": Dict[str, List[AssumptionCheck]],
        # Key: metric_name, Value: list of checks (Shapiro-Wilk per framework, Levene overall)
    "statistical_tests": Dict[str, List[StatisticalTest]],
        # Key: metric_name, Value: list of pairwise/omnibus tests
    "effect_sizes": Dict[str, List[EffectSize]],
        # Key: metric_name, Value: list of effect sizes (all pairwise)
    "power_analyses": Dict[str, List[PowerAnalysis]],
        # Key: metric_name, Value: list of power analyses (all pairwise)
    "visualizations": Dict[str, List[Visualization]],
        # Key: metric_name, Value: list of plots
    "summary": {
        "key_findings": List[str],   # 3-5 bullet points for executive summary
        "power_warnings": List[str], # Metrics with inadequate power
        "methodology_text": str,     # Pre-formatted text for paper Methodology section
        "limitations_text": str      # Pre-formatted text for paper Discussion section
    },
    "metadata": {
        "analysis_date": str,        # ISO 8601 timestamp
        "scipy_version": str,
        "statsmodels_version": str,
        "random_seed": int,          # For bootstrap reproducibility
        "alpha": float               # Significance level used throughout
    }
}
```

**Example Structure**:
```python
{
    "experiment_name": "multi_agent_comparison",
    "primary_metric": "execution_time",
    "n_frameworks": 3,
    "n_metrics": 5,
    "n_runs_per_framework": {"ChatDev": 5, "MetaGPT": 5, "CrewAI": 5},
    "distributions": {
        "execution_time": [
            MetricDistribution(...),  # ChatDev
            MetricDistribution(...),  # MetaGPT
            MetricDistribution(...)   # CrewAI
        ]
    },
    "assumption_checks": {
        "execution_time": [
            AssumptionCheck(test_name="Shapiro-Wilk", frameworks=["ChatDev"], ...),
            AssumptionCheck(test_name="Shapiro-Wilk", frameworks=["MetaGPT"], ...),
            AssumptionCheck(test_name="Levene", frameworks=["ChatDev", "MetaGPT", "CrewAI"], ...)
        ]
    },
    "statistical_tests": {
        "execution_time": [
            StatisticalTest(test_name="Kruskal-Wallis H", frameworks=["ChatDev", "MetaGPT", "CrewAI"], ...),
            StatisticalTest(test_name="Mann-Whitney U", frameworks=["ChatDev", "MetaGPT"], ...),
            StatisticalTest(test_name="Mann-Whitney U", frameworks=["ChatDev", "CrewAI"], ...),
            StatisticalTest(test_name="Mann-Whitney U", frameworks=["MetaGPT", "CrewAI"], ...)
        ]
    },
    "effect_sizes": {
        "execution_time": [
            EffectSize(frameworks=("ChatDev", "MetaGPT"), value=0.72, ...),
            EffectSize(frameworks=("ChatDev", "CrewAI"), value=0.45, ...),
            EffectSize(frameworks=("MetaGPT", "CrewAI"), value=-0.27, ...)
        ]
    },
    "power_analyses": {
        "execution_time": [
            PowerAnalysis(frameworks=["ChatDev", "MetaGPT"], achieved_power=0.54, ...),
            ...
        ]
    },
    "visualizations": {
        "execution_time": [
            Visualization(plot_type="violin_plot", ...),
            Visualization(plot_type="forest_plot", ...)
        ]
    },
    "summary": {
        "key_findings": [
            "ChatDev significantly faster than MetaGPT (p=0.032, d=0.72, medium effect)",
            "No significant difference between MetaGPT and CrewAI (p=0.15)",
            "⚠️ Power analysis: 13 runs recommended for reliable detection (currently 5)"
        ],
        "power_warnings": ["execution_time", "code_quality"],
        "methodology_text": "Statistical Analysis\n\nWe assessed...",
        "limitations_text": "The current sample size (n=5)..."
    },
    "metadata": {
        "analysis_date": "2025-10-29T14:32:00Z",
        "scipy_version": "1.11.0",
        "statsmodels_version": "0.14.0",
        "random_seed": 42,
        "alpha": 0.05
    }
}
```

**Validation Rules**:
- All metric names consistent across all dictionaries
- Number of distributions per metric == n_frameworks
- Effect sizes and power analyses only for pairwise comparisons (n_frameworks choose 2)
- `0 < alpha < 1`

---

## Data Flow

```
ExperimentAnalyzer.analyze()
  ↓
1. Load run data → compute MetricDistribution for each (metric, framework)
  ↓
2. Run AssumptionCheck (Shapiro-Wilk, Levene)
  ↓
3. Select appropriate StatisticalTest based on assumptions
  ↓
4. Compute EffectSize for all pairwise comparisons
  ↓
5. Run PowerAnalysis for all pairwise comparisons
  ↓
6. Generate Visualization (box/violin/forest/qq plots)
  ↓
7. Aggregate into StatisticalFindings
  ↓
8. Serialize to statistical_report_summary.md
  ↓
PaperGenerator._load_analyzed_data()
  ↓
9. Parse statistical_report_summary.md
  ↓
10. Extract key findings, visualizations, methodology text
  ↓
11. Inject into paper sections
```

---

## Serialization Format

All entities are serializable to JSON/YAML. Example:

**statistical_findings.json**:
```json
{
  "experiment_name": "multi_agent_comparison",
  "primary_metric": "execution_time",
  "distributions": { ... },
  "effect_sizes": {
    "execution_time": [
      {
        "measure": "Cohen's d",
        "frameworks": ["ChatDev", "MetaGPT"],
        "value": 0.72,
        "ci_lower": 0.28,
        "ci_upper": 1.16,
        "magnitude": "medium"
      }
    ]
  }
}
```

---

## Type Hints

Python type definitions for all entities:

```python
from typing import List, Dict, Tuple, Literal
from dataclasses import dataclass

@dataclass
class MetricDistribution:
    metric_name: str
    framework_name: str
    values: List[float]
    n_runs: int
    mean: float
    median: float
    std: float
    q1: float
    q3: float
    min: float
    max: float
    iqr: float
    cv: float
    outliers: List[float]
    zero_variance: bool

@dataclass
class AssumptionCheck:
    test_name: Literal["Shapiro-Wilk", "Levene"]
    metric_name: str
    frameworks: List[str]
    statistic: float
    p_value: float
    alpha: float
    passed: bool
    interpretation: str
    recommendation: str

@dataclass
class StatisticalTest:
    test_name: str
    metric_name: str
    frameworks: List[str]
    test_type: Literal["parametric", "non_parametric"]
    statistic: float
    p_value: float
    alpha: float
    significant: bool
    alternative: Literal["two-sided", "less", "greater"]
    interpretation: str
    method_notes: str

@dataclass
class EffectSize:
    measure: Literal["Cohen's d", "Cliff's delta"]
    metric_name: str
    frameworks: Tuple[str, str]
    value: float
    ci_lower: float
    ci_upper: float
    ci_method: str
    magnitude: Literal["negligible", "small", "medium", "large"]
    interpretation: str
    direction: str

@dataclass
class PowerAnalysis:
    metric_name: str
    frameworks: List[str]
    effect_size: float
    current_n: int
    achieved_power: float
    target_power: float
    recommended_n: int
    alpha: float
    power_adequate: bool
    interpretation: str
    recommendation: str

@dataclass
class Visualization:
    plot_type: Literal["box_plot", "violin_plot", "forest_plot", "qq_plot"]
    metric_name: str
    frameworks: List[str]
    file_path: str
    format: Literal["svg"]
    dimensions: Tuple[int, int]
    caption: str
    alt_text: str
    embedded_in: List[str]

@dataclass
class StatisticalFindings:
    experiment_name: str
    primary_metric: str
    n_frameworks: int
    n_metrics: int
    n_runs_per_framework: Dict[str, int]
    distributions: Dict[str, List[MetricDistribution]]
    assumption_checks: Dict[str, List[AssumptionCheck]]
    statistical_tests: Dict[str, List[StatisticalTest]]
    effect_sizes: Dict[str, List[EffectSize]]
    power_analyses: Dict[str, List[PowerAnalysis]]
    visualizations: Dict[str, List[Visualization]]
    summary: Dict[str, any]
    metadata: Dict[str, any]
```

---

**Next**: Generate API contracts in `contracts/` directory.
