# API Contract: StatisticalAnalyzer

**Module**: `src.paper_generation.statistical_analyzer`  
**Class**: `StatisticalAnalyzer`  
**Purpose**: Performs comprehensive statistical analysis on experiment run data

---

## Class Constructor

### `__init__(self, config: Dict, random_seed: int = 42)`

**Description**: Initialize statistical analyzer with configuration and random seed.

**Parameters**:
- `config` (Dict): Experiment configuration containing:
  - `alpha` (float, optional): Significance level (default 0.05)
  - `target_power` (float, optional): Desired statistical power (default 0.80)
  - `bootstrap_iterations` (int, optional): Bootstrap resamples (default 10,000)
  - `primary_metric` (str, optional): Primary metric for analysis (default "execution_time")
- `random_seed` (int): Random seed for reproducible bootstrap resampling (default 42)

**Returns**: None

**Raises**: None

**Example**:
```python
config = {"alpha": 0.05, "primary_metric": "execution_time"}
analyzer = StatisticalAnalyzer(config, random_seed=42)
```

---

## Public Methods

### `analyze_experiment(self, run_data: Dict[str, List[Dict]]) -> StatisticalFindings`

**Description**: Perform comprehensive statistical analysis on all metrics across frameworks.

**Parameters**:
- `run_data` (Dict[str, List[Dict]]): Run data organized by framework name
  - Key: framework name (e.g., "ChatDev")
  - Value: List of run dictionaries, each containing metrics (e.g., `{"execution_time": 45.2}`)

**Returns**: `StatisticalFindings` object containing all analysis results

**Raises**:
- `ValueError`: If run_data is empty, has <2 frameworks, or <2 runs per framework
- `StatisticalAnalysisError`: If critical statistical computation fails

**Example**:
```python
run_data = {
    "ChatDev": [{"execution_time": 45.2}, {"execution_time": 47.1}],
    "MetaGPT": [{"execution_time": 78.3}, {"execution_time": 75.9}]
}
findings = analyzer.analyze_experiment(run_data)
```

**Algorithm**:
1. Extract metric distributions for each framework
2. Run assumption checks (Shapiro-Wilk, Levene)
3. Select and perform statistical tests
4. Compute effect sizes with bootstrap CIs
5. Perform power analysis
6. Generate visualizations
7. Create summary findings
8. Return StatisticalFindings object

---

### `compute_metric_distribution(self, metric_name: str, framework_name: str, values: List[float]) -> MetricDistribution`

**Description**: Compute descriptive statistics and detect outliers for a single metric-framework combination.

**Parameters**:
- `metric_name` (str): Name of the metric (e.g., "execution_time")
- `framework_name` (str): Name of the framework (e.g., "ChatDev")
- `values` (List[float]): Raw metric values from all runs

**Returns**: `MetricDistribution` object with descriptive statistics

**Raises**:
- `ValueError`: If values is empty or has <2 elements

**Example**:
```python
values = [45.2, 47.1, 46.8, 44.9, 46.3]
dist = analyzer.compute_metric_distribution("execution_time", "ChatDev", values)
# dist.mean = 46.06, dist.std = 0.83, dist.outliers = []
```

**Implementation Notes**:
- Uses IQR method for outlier detection (values beyond Q1 - 1.5*IQR or Q3 + 1.5*IQR)
- Coefficient of variation (CV) = std / mean (if mean != 0)
- Sets `zero_variance = True` if std == 0

---

### `run_normality_test(self, distribution: MetricDistribution) -> AssumptionCheck`

**Description**: Test if data follows normal distribution using Shapiro-Wilk test.

**Parameters**:
- `distribution` (MetricDistribution): Distribution to test

**Returns**: `AssumptionCheck` object with test results and interpretation

**Raises**:
- `ValueError`: If distribution has <3 values (minimum for Shapiro-Wilk)

**Example**:
```python
check = analyzer.run_normality_test(distribution)
# check.passed = True, check.p_value = 0.35
# check.interpretation = "Data appears normally distributed"
```

**Implementation**:
- Uses `scipy.stats.shapiro(values)`
- Passed if p_value > alpha
- Includes plain-language interpretation
- Recommendation based on result (parametric vs non-parametric tests)

---

### `run_variance_test(self, distributions: List[MetricDistribution]) -> AssumptionCheck`

**Description**: Test homogeneity of variance across groups using Levene's test.

**Parameters**:
- `distributions` (List[MetricDistribution]): Distributions to compare (2+ groups)

**Returns**: `AssumptionCheck` object with test results

**Raises**:
- `ValueError`: If <2 distributions provided

**Example**:
```python
check = analyzer.run_variance_test([dist_chatdev, dist_metagpt])
# check.passed = True, check.p_value = 0.28
```

**Implementation**:
- Uses `scipy.stats.levene(*[d.values for d in distributions])`
- Passed if p_value > alpha
- Recommendation based on variance homogeneity

---

### `run_statistical_test(self, distributions: List[MetricDistribution], assumptions: List[AssumptionCheck]) -> StatisticalTest`

**Description**: Select and run appropriate statistical test based on assumptions.

**Parameters**:
- `distributions` (List[MetricDistribution]): Distributions to compare
- `assumptions` (List[AssumptionCheck]): Normality and variance test results

**Returns**: `StatisticalTest` object with test results

**Raises**:
- `ValueError`: If <2 distributions, or assumptions don't match distributions

**Example**:
```python
test = analyzer.run_statistical_test([dist_chatdev, dist_metagpt], assumptions)
# test.test_name = "Mann-Whitney U", test.p_value = 0.032
```

**Decision Logic**:
- If n < 3 per group: Skip, return warning
- If zero variance: Skip, explain no variation
- If all normal AND equal variance:
  - 2 groups: Independent t-test
  - 3+ groups: One-way ANOVA
- Else (non-normal OR unequal variance):
  - 2 groups: Mann-Whitney U test
  - 3+ groups: Kruskal-Wallis H test

**Implementation**:
- Uses `scipy.stats.ttest_ind`, `scipy.stats.mannwhitneyu`, `scipy.stats.f_oneway`, `scipy.stats.kruskal`
- Documents method selection in `method_notes` field
- Includes plain-language interpretation

---

### `compute_effect_size(self, dist1: MetricDistribution, dist2: MetricDistribution, test_type: str) -> EffectSize`

**Description**: Compute effect size with bootstrap confidence interval.

**Parameters**:
- `dist1` (MetricDistribution): First distribution
- `dist2` (MetricDistribution): Second distribution
- `test_type` (str): "parametric" or "non_parametric"

**Returns**: `EffectSize` object with measure, value, CI, magnitude

**Raises**: None

**Example**:
```python
effect = analyzer.compute_effect_size(dist_chatdev, dist_metagpt, "parametric")
# effect.measure = "Cohen's d", effect.value = 0.72, effect.magnitude = "medium"
```

**Formulas**:
- **Cohen's d**: `(mean1 - mean2) / pooled_std`
  - pooled_std = sqrt(((n1-1)*std1^2 + (n2-1)*std2^2) / (n1+n2-2))
- **Cliff's delta**: Probability superiority measure

**Bootstrap CI**:
- 10,000 resamples from original data (with replacement)
- Compute effect size for each resample
- 95% CI from 2.5th and 97.5th percentiles

**Magnitude Classification**:
- Cohen's d: <0.2 negligible, 0.2-0.5 small, 0.5-0.8 medium, ≥0.8 large
- Cliff's delta: <0.147 negligible, 0.147-0.33 small, 0.33-0.474 medium, ≥0.474 large

---

### `perform_power_analysis(self, effect: EffectSize, n_per_group: int) -> PowerAnalysis`

**Description**: Compute achieved power and recommend sample size.

**Parameters**:
- `effect` (EffectSize): Observed effect size
- `n_per_group` (int): Current sample size per group

**Returns**: `PowerAnalysis` object with power, recommendations

**Raises**: None

**Example**:
```python
power = analyzer.perform_power_analysis(effect, n_per_group=5)
# power.achieved_power = 0.54, power.recommended_n = 13
```

**Implementation**:
- Uses `statsmodels.stats.power.TTestIndPower` for parametric tests
- Uses simulation for non-parametric tests (conservative estimate)
- Target power = 0.80 (80% chance of detecting effect)
- Recommendation formatted for non-statisticians

---

### `generate_visualization(self, metric_name: str, distributions: List[MetricDistribution], plot_type: str, output_path: str) -> Visualization`

**Description**: Generate statistical visualization and save as SVG.

**Parameters**:
- `metric_name` (str): Metric being visualized
- `distributions` (List[MetricDistribution]): Data to plot
- `plot_type` (str): "box_plot", "violin_plot", "forest_plot", or "qq_plot"
- `output_path` (str): Relative path for SVG file

**Returns**: `Visualization` object with metadata

**Raises**:
- `ValueError`: If plot_type invalid or output_path doesn't end with .svg
- `IOError`: If file write fails

**Example**:
```python
viz = analyzer.generate_visualization(
    "execution_time",
    [dist_chatdev, dist_metagpt],
    "violin_plot",
    "figures/statistical/violin_execution_time.svg"
)
```

**Plot Specifications**:
- **Box Plot**: Median, Q1/Q3, whiskers (1.5*IQR), outliers
- **Violin Plot**: KDE + quartile lines
- **Forest Plot**: Effect sizes with 95% CIs (horizontal)
- **Q-Q Plot**: Sample quantiles vs theoretical normal quantiles

**Styling**:
- Seaborn "colorblind" palette
- Figure size: (10, 6) inches
- DPI: 100 (vector format, DPI nominal)
- Font: Arial, 12pt
- SVG format (scalable, markdown/LaTeX compatible)

---

## Private Helper Methods

### `_select_test_method(self, n_groups: int, all_normal: bool, equal_variance: bool) -> str`

**Description**: Determine appropriate statistical test based on assumptions.

**Parameters**:
- `n_groups` (int): Number of groups to compare
- `all_normal` (bool): Are all groups normally distributed?
- `equal_variance` (bool): Do groups have equal variance?

**Returns**: Test method name ("t-test", "mann-whitney", "anova", "kruskal-wallis")

**Algorithm**:
```
IF n_groups == 2:
    IF all_normal AND equal_variance:
        RETURN "t-test"
    ELSE:
        RETURN "mann-whitney"
ELIF n_groups >= 3:
    IF all_normal AND equal_variance:
        RETURN "anova"
    ELSE:
        RETURN "kruskal-wallis"
```

---

### `_bootstrap_effect_size(self, values1: List[float], values2: List[float], measure: str, n_iterations: int) -> Tuple[float, float]`

**Description**: Compute bootstrap confidence interval for effect size.

**Parameters**:
- `values1`, `values2` (List[float]): Raw data from two groups
- `measure` (str): "cohens_d" or "cliffs_delta"
- `n_iterations` (int): Number of bootstrap resamples (default 10,000)

**Returns**: Tuple of (ci_lower, ci_upper) for 95% CI

**Algorithm**:
1. Initialize random generator with seed
2. For i in 1..n_iterations:
   - Resample values1 and values2 with replacement
   - Compute effect size for resampled data
   - Store result
3. Return 2.5th and 97.5th percentiles

---

### `_format_plain_language(self, technical_term: str, context: Dict) -> str`

**Description**: Convert technical statistical term to plain language.

**Parameters**:
- `technical_term` (str): Statistical jargon (e.g., "p-value", "effect size")
- `context` (Dict): Contextual information for personalized explanation

**Returns**: Plain-language explanation string

**Example**:
```python
explanation = analyzer._format_plain_language(
    "p-value",
    {"value": 0.032, "test": "Mann-Whitney U"}
)
# "3.2% chance this difference happened by random luck"
```

---

## Error Handling

Custom exception: `StatisticalAnalysisError`

**Raised when**:
- Insufficient data for analysis (n < 2)
- All values identical (zero variance prevents most tests)
- Critical scipy/statsmodels computation fails

**Example**:
```python
try:
    findings = analyzer.analyze_experiment(run_data)
except StatisticalAnalysisError as e:
    logger.error(f"Statistical analysis failed: {e}")
    # Fall back to basic descriptive statistics
```

---

## Dependencies

- `scipy.stats`: shapiro, levene, ttest_ind, mannwhitneyu, f_oneway, kruskal
- `statsmodels.stats.power`: TTestIndPower
- `numpy`: random.default_rng, percentile, array operations
- `dataclasses`: For entity definitions

---

## Thread Safety

**Not thread-safe**: Random number generator state is shared. For parallel execution, create separate `StatisticalAnalyzer` instances with different seeds.

---

**Next**: Educational content generator contract.
