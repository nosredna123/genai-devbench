# Implementation Plan: Centralized Metrics & Cost Analysis

**Date:** 2025-10-18  
**Scope:** Focus on reliably measured metrics, add cost tracking, and centralize all configuration in `config/experiment.yaml`.

---

## 🎯 Objectives

1. **Centralize configuration** for metrics, pricing, visualizations, and reporting in `config/experiment.yaml`.
2. **Maintain and improve reliable metrics** (TOK_IN, TOK_OUT, API_CALLS, CACHED_TOKENS, T_WALL_seconds, ZDI, UTT).
3. **Introduce COST_USD** metric using OpenAI pricing with cache discounts.
4. **Rename the reporting module** to a more descriptive name and cascade the change through all artifacts that generate or consume analysis outputs.
5. **Audit key metrics and visualizations** to verify correctness of central tendency calculations and anomaly handling (API calls timeline, ZDI, radar chart, token efficiency scatter, API calls evolution).
6. **Ensure reports and charts** dynamically use the centralized configuration, referencing reliable metrics only.
7. **Document unmeasured/partial metrics** as excluded, without attempting to implement them now.

---

## 📦 Configuration Strategy

All experiment settings will live in `config/experiment.yaml`:

```yaml
metrics:
  categories: ...
  reliable_metrics: ...
  derived_metrics: ...
  excluded_metrics: ...
pricing:
  models: ...
visualizations:
  radar_chart: ...
  ...
report:
  sections: ...
```

This unification eliminates additional files (e.g., `metrics.yaml`, `pricing.yaml`) and provides a single source of truth for every subsystem.

---

## 🗺️ Stage Breakdown & Timeline

### **Stage 1 – Config Unification & Loader (10-14h, critical)**

**Objective:** Establish centralized configuration system as single source of truth for all metrics and settings.

#### Task 1.1: Extend experiment.yaml with new sections (2-3h)
- **File:** `config/experiment.yaml`
- **Actions:**
  - Add `metrics` section with subsections: `categories`, `reliable_metrics`, `derived_metrics`, `excluded_metrics`
  - Add `pricing` section with `models` subsection containing OpenAI pricing data
  - Add `visualizations` section defining each chart's config (metrics, type, filename)
  - Add `report` section with `sections` list defining order and enabled state
- **Validation:** YAML syntax valid, all sections parseable
- **Deliverable:** Extended `config/experiment.yaml` with ~300-400 additional lines

#### Task 1.2: Update stopping_rule.metrics references (0.5-1h)
- **File:** `config/experiment.yaml`
- **Actions:**
  - Replace hardcoded metric list in `stopping_rule.metrics` with comment referencing new `metrics.reliable_metrics` section
  - Document that stopping rule should query metrics marked with `stopping_rule_eligible: true` in future
- **Validation:** Config still loads correctly in existing code
- **Deliverable:** Updated stopping_rule section with documentation

#### Task 1.3: Implement MetricsConfig class (4-5h)
- **New File:** `src/utils/metrics_config.py`
- **Actions:**
  - Create `MetricDefinition` dataclass with all metadata fields
  - Implement `MetricsConfig` class with methods:
    - `__init__(config_path)` - loads from experiment.yaml
    - `get_reliable_metrics() -> Dict[str, MetricDefinition]`
    - `get_derived_metrics() -> Dict[str, MetricDefinition]`
    - `get_all_metrics() -> Dict[str, MetricDefinition]`
    - `get_metric(key: str) -> MetricDefinition`
    - `get_metrics_for_statistics() -> List[str]`
    - `get_metrics_by_category(category: str) -> Dict`
    - `get_visualization_config(viz_name: str) -> Dict`
    - `get_excluded_metrics() -> Dict`
    - `format_value(metric_key: str, value: Any) -> str`
    - `validate_metrics_data(data: Dict) -> List[str]`
  - Implement singleton pattern with `get_metrics_config()` function
- **Validation:** All methods return correct data types, config loads without errors
- **Deliverable:** Complete `metrics_config.py` module (~300-400 lines)

#### Task 1.4: Create unit tests for MetricsConfig (2-3h)
- **New File:** `tests/unit/test_metrics_config.py`
- **Test Cases:**
  - `test_metrics_config_loads()` - config loads successfully
  - `test_reliable_metrics_structure()` - all metrics have required fields
  - `test_get_metrics_for_statistics()` - filters correctly by statistical_test flag
  - `test_metric_formatting()` - formats values according to display_format
  - `test_metrics_by_category()` - filters by category correctly
  - `test_excluded_metrics()` - returns excluded metrics with reasons
  - `test_validate_metrics_data()` - catches missing/wrong-type metrics
  - `test_singleton_pattern()` - get_metrics_config returns same instance
- **Validation:** All tests pass with 100% coverage of MetricsConfig class
- **Deliverable:** Complete test file (~200-250 lines)

#### Task 1.5: Document metrics configuration schema (1-2h)
- **New File:** `docs/METRICS_CONFIG_SCHEMA.md`
- **Actions:**
  - Document all fields for reliable_metrics, derived_metrics, excluded_metrics
  - Provide examples for each metric type
  - Explain aggregation types, ideal_direction values, visualization types
  - Show how to add new metrics
- **Validation:** Documentation accurate and complete
- **Deliverable:** Schema reference document

### **Stage 2 – Cost Calculation & Aggregation (8-10h, high)**

**Objective:** Implement cost tracking with OpenAI pricing and cache discounts, integrate into metrics collection.

#### Task 2.1: Implement CostCalculator class (3-4h)
- **New File:** `src/utils/cost_calculator.py`
- **Actions:**
  - Create `CostCalculator` class that reads pricing from experiment.yaml
  - Implement `calculate_cost(model, tokens_in, tokens_out, cached_tokens)` method:
    - Calculate uncached input cost (full price)
    - Calculate cached input cost (50% discount)
    - Calculate output cost (no discount)
    - Calculate total cost
    - Calculate cache savings
    - Return dict with breakdown: `{input_cost, cached_cost, output_cost, total_cost, cache_savings}`
  - Implement `get_model_pricing(model: str)` helper method
  - Add comprehensive docstrings with pricing examples
- **Validation:** Cost calculations match manual calculations for known inputs
- **Deliverable:** Complete `cost_calculator.py` module (~150-200 lines)

#### Task 2.2: Create unit tests for CostCalculator (2h)
- **New File:** `tests/unit/test_cost_calculator.py`
- **Test Cases:**
  - `test_cost_calculation_gpt4o_mini()` - verify cost with known values
  - `test_cache_discount_applied()` - confirm 50% discount on cached tokens
  - `test_cache_savings_calculation()` - verify savings math
  - `test_zero_tokens()` - handle edge case of zero tokens
  - `test_all_cached()` - all input tokens from cache
  - `test_no_cache()` - no cached tokens
  - `test_unknown_model()` - raises appropriate error
  - `test_multiple_models()` - works for gpt-4o, o1-mini, o1-preview
- **Validation:** All tests pass, edge cases covered
- **Deliverable:** Complete test file (~150-180 lines)

#### Task 2.3: Update MetricsCollector to use CostCalculator (2-3h)
- **File:** `src/orchestrator/metrics_collector.py`
- **Actions:**
  - Add `model` parameter to `__init__`
  - Initialize `MetricsConfig` and `CostCalculator` instances
  - Update `get_aggregate_metrics()`:
    - Build result dict using only `metrics.reliable_metrics` keys
    - Call `cost_calculator.calculate_cost()` for COST_USD
    - Add COST_BREAKDOWN to result
    - Calculate derived metrics using config formulas
  - Implement `_calculate_derived_metric(metric_def, data)` helper
  - Remove hardcoded metric lists
- **Validation:** Metrics collector outputs match expected structure
- **Deliverable:** Updated `metrics_collector.py` with config-driven logic

#### Task 2.4: Update Runner to pass model parameter (0.5-1h)
- **File:** `src/orchestrator/runner.py`
- **Actions:**
  - Pass `model=self.config['model']` when initializing MetricsCollector
  - Verify model name is correctly propagated
- **Validation:** Runner initializes collector with correct model
- **Deliverable:** Updated runner initialization

#### Task 2.5: Add cost fields to metrics.json output (0.5h)
- **Files:** Review `src/orchestrator/runner.py`, `src/orchestrator/metrics_collector.py`
- **Actions:**
  - Ensure COST_USD appears in step_metrics.json
  - Ensure COST_USD appears in aggregate metrics.json
  - Ensure COST_BREAKDOWN appears in aggregate metrics.json
- **Validation:** Run experiment and verify cost fields present in output
- **Deliverable:** Cost metrics in all output files

### **Stage 3 – Data-Driven Report Generator & Module Rename (12-16h, critical)**

**Objective:** Rename statistics module, refactor to use centralized config, generate all sections dynamically.

#### Task 3.1: Rename statistics.py to report_generator.py (1-2h)
- **File Operations:**
  - Rename `src/analysis/statistics.py` → `src/analysis/report_generator.py`
  - Update imports in:
    - `runners/analyze_results.sh` (or Python entry point)
    - `src/analysis/__init__.py`
    - `tests/unit/test_statistics.py` → `tests/unit/test_report_generator.py`
    - Any documentation referencing the old name
  - Update module docstring to reflect new name
- **Validation:** All imports resolve, tests still run
- **Deliverable:** Renamed module with all references updated

#### Task 3.2: Refactor report generator to use config sections (4-5h)
- **File:** `src/analysis/report_generator.py`
- **Actions:**
  - Update `StatisticalReport.__init__` to load `MetricsConfig`
  - Implement config-driven `generate()` method:
    - Read `report.sections` from config
    - Sort by `order` field
    - Call corresponding `_generate_*` methods
    - Skip sections where `enabled: false`
  - Remove hardcoded section ordering
  - Add section validation (warn if method missing)
- **Validation:** Report generates all expected sections
- **Deliverable:** Config-driven report generator core

#### Task 3.3: Implement dynamic metric definitions table (2-3h)
- **File:** `src/analysis/report_generator.py`
- **Method:** `_generate_metric_definitions()`
- **Actions:**
  - Read `metrics.reliable_metrics` from config
  - Generate markdown table with columns: Metric, Name, Description, Unit, Ideal, Source
  - Use ideal_direction icons: lower=↓, higher=↑, neutral=—
  - Add derived metrics section if present
  - Format using metric metadata (no hardcoded values)
- **Validation:** Table contains exactly configured metrics
- **Deliverable:** Dynamic metric definitions generator

#### Task 3.4: Implement dynamic aggregate statistics table (2-3h)
- **File:** `src/analysis/report_generator.py`
- **Method:** `_generate_aggregate_statistics()`
- **Actions:**
  - Read `metrics.reliable_metrics` to get column list
  - Iterate over frameworks and metrics from config
  - Use `metrics_config.format_value()` for formatting
  - Calculate bootstrap CI for each metric
  - Build table dynamically with configured metrics only
  - Add performance indicators (🟢🟡🔴) based on ideal_direction
- **Validation:** Table shows only configured metrics with correct formatting
- **Deliverable:** Dynamic statistics table generator

#### Task 3.5: Implement config-driven statistical tests (2-3h)
- **File:** `src/analysis/report_generator.py`
- **Method:** `_generate_statistical_tests()`
- **Actions:**
  - Get test metrics via `metrics_config.get_metrics_for_statistics()`
  - Only run Kruskal-Wallis for metrics with `statistical_test: true`
  - Skip UTT and other constant metrics automatically
  - Use metric metadata for section headers and descriptions
  - Generate pairwise comparisons only for tested metrics
- **Validation:** Tests run only on configured metrics
- **Deliverable:** Config-driven statistical testing

#### Task 3.6: Implement cost analysis section (1-2h)
- **File:** `src/analysis/report_generator.py`
- **Method:** `_generate_cost_analysis()`
- **Actions:**
  - Get cost metrics via `metrics_config.get_metrics_by_category('cost')`
  - Generate cost comparison table
  - Calculate cost per step, cost per 1000 tokens
  - Show cache savings analysis
  - Use metric formatting from config
- **Validation:** Cost section appears with all cost-category metrics
- **Deliverable:** Dynamic cost analysis section

#### Task 3.7: Implement auto-generated limitations section (1h)
- **File:** `src/analysis/report_generator.py`
- **Method:** `_generate_limitations()`
- **Actions:**
  - Read `metrics.excluded_metrics` from config
  - Group by category
  - Generate markdown with metric name, reason, requirements
  - Auto-document what's not measured and why
- **Validation:** Limitations section lists all excluded metrics
- **Deliverable:** Auto-generated limitations documentation

#### Task 3.8: Update report generator tests (1-2h)
- **File:** `tests/unit/test_report_generator.py`
- **Actions:**
  - Update test imports and class names
  - Add test for config-driven section generation
  - Add test for metric filtering
  - Add test for dynamic table generation
  - Mock MetricsConfig for isolated testing
- **Validation:** All tests pass with updated module name
- **Deliverable:** Updated test suite

### **Stage 4 – Visualization Factory (6-8h, medium)**

**Objective:** Refactor visualization system to generate all charts dynamically from config metadata.

#### Task 4.1: Create VisualizationFactory class (2-3h)
- **File:** `src/analysis/visualizations.py`
- **Actions:**
  - Create `VisualizationFactory` class
  - Implement `__init__(runs_by_framework)` with MetricsConfig loading
  - Implement `generate_all(output_dir)` that iterates `visualizations` config
  - Add `_get_metric_label(metric_key)` helper using config metadata
  - Add `_normalize_data(data, metrics)` for radar chart scaling
  - Implement chart type routing based on `chart_type` field
- **Validation:** Factory initializes and routes to correct chart methods
- **Deliverable:** VisualizationFactory core class

#### Task 4.2: Refactor radar chart to use config (1-2h)
- **File:** `src/analysis/visualizations.py`
- **Method:** `_create_radar_chart(name, config, output_dir)`
- **Actions:**
  - Read metrics list from `config['metrics']`
  - Validate metrics exist via `metrics_config.get_metric()`
  - Use metric metadata for axis labels (short_name + unit)
  - Apply normalization if `config['normalize'] == true`
  - Save to `config['filename']`
  - Remove all hardcoded metric names
- **Validation:** Radar chart uses only configured metrics
- **Deliverable:** Config-driven radar chart

#### Task 4.3: Refactor token efficiency scatter (1h)
- **File:** `src/analysis/visualizations.py`
- **Method:** `_create_scatter_plot(name, config, output_dir)`
- **Actions:**
  - Read x_axis, y_axis, color, size from config
  - Use metric labels from config
  - Filter to verified runs only
  - Apply minimum thresholds to eliminate zeros
  - Add diagonal reference line if appropriate
- **Validation:** Scatter uses config metrics, no zero artifacts
- **Deliverable:** Config-driven scatter plot

#### Task 4.4: Create cost breakdown visualization (1-2h)
- **File:** `src/analysis/visualizations.py`
- **Method:** `_create_stacked_bar(name, config, output_dir)`
- **Actions:**
  - Create stacked bar chart for cost components
  - Show input_cost, cached_cost, output_cost per framework
  - Add cache savings as negative bar or annotation
  - Use cost metric formatting from config
  - Color-code by component type
- **Validation:** Cost breakdown chart displays correctly
- **Deliverable:** New cost breakdown visualization

#### Task 4.5: Update timeline/evolution charts (1-2h)
- **File:** `src/analysis/visualizations.py`
- **Method:** `_create_line(name, config, output_dir)`
- **Actions:**
  - Read metrics from `config['metrics']`
  - Calculate mean/median per step (not last run value)
  - Use metric labels and formatting from config
  - Handle missing values gracefully (NA, not zero)
  - Add error bands (confidence intervals) if configured
- **Validation:** Timeline shows aggregated values, no sampling bias
- **Deliverable:** Config-driven timeline charts

#### Task 4.6: Remove hardcoded metric references (0.5-1h)
- **File:** `src/analysis/visualizations.py`
- **Actions:**
  - Search for all hardcoded metric names (TOK_IN, AUTR, etc.)
  - Replace with config lookups
  - Remove unused helper functions
  - Clean up imports
- **Validation:** No hardcoded metric strings remain
- **Deliverable:** Fully config-driven visualization module

### **Stage 5 – Metrics & Visualization Validation (8-12h, high)**

**Objective:** Investigate and fix identified issues in metrics calculation and chart generation.

#### Task 5.1: Audit API Calls Timeline aggregation (1-2h)
- **Investigation:**
  - Review how API_CALLS timeline values are computed per step
  - Check if using last run value vs mean/median across runs
  - Examine code in `src/analysis/visualizations.py` for timeline generation
- **Actions:**
  - Update timeline to use mean/median aggregation from config (`aggregation` field)
  - Add tests to verify aggregation method is applied correctly
  - Document aggregation strategy in `docs/VISUALIZATION_VALIDATION_LOG.md`
- **Validation:** Timeline shows average values, not single-run samples
- **Deliverable:** Fixed timeline aggregation + documentation

#### Task 5.2: Investigate ZDI metric capture (2-3h)
- **Investigation:**
  - Trace ZDI calculation from adapter output through metrics collector
  - Review `src/orchestrator/metrics_collector.py` ZDI computation
  - Check step timing capture in adapters
  - Verify ZDI appears correctly in step_metrics.json and metrics.json
- **Actions:**
  - Add debug logging for ZDI calculation points
  - Add unit tests for ZDI aggregation logic
  - Verify against manual calculation from timestamps
  - Document findings in validation log
- **Fixes (if needed):**
  - Correct idle time calculation if formula is wrong
  - Fix timing capture if timestamps are missing
  - Update aggregation if sum is incorrect
- **Validation:** ZDI values match manual calculations
- **Deliverable:** Verified or fixed ZDI calculation + tests + documentation

#### Task 5.3: Debug Radar Chart - BAEs zero values (1-2h)
- **Investigation:**
  - Check why BAEs shows zeros on radar chart
  - Review normalization logic in `src/analysis/visualizations.py`
  - Verify BAEs data is loaded correctly for chart
  - Check if metrics are filtered incorrectly
- **Actions:**
  - Add logging to show raw values before normalization
  - Verify metric selection includes BAEs data
  - Fix normalization if dividing by zero or wrong max value
  - Document root cause in validation log
- **Validation:** BAEs shows actual values on radar chart
- **Deliverable:** Fixed radar chart with BAEs data visible

#### Task 5.4: Improve Radar Chart scaling (1-2h)
- **Investigation:**
  - Review current normalization approach (0-1 scale)
  - Evaluate user request for percentage scale
  - Check if scale formula matches ideal_direction properly
- **Actions:**
  - Add config option for scale type: `scale: "normalized"` vs `scale: "percentage"`
  - Implement percentage formatter (0-100% instead of 0-1)
  - Update axis labels to show percentage if configured
  - Validate scale matches metric ideal_direction (invert if needed)
- **Validation:** Radar chart uses readable scale (percentages or normalized)
- **Deliverable:** Configurable radar chart scaling

#### Task 5.5: Analyze Token Efficiency Scatter anomalies (1-2h)
- **Investigation:**
  - Understand why all points above diagonal (TOK_OUT > TOK_IN?)
  - Identify source of zero values in scatter plot
  - Review filtering of verified vs non-verified runs
- **Actions:**
  - Add filtering to exclude runs with `verification_status != 'verified'`
  - Add minimum threshold (e.g., TOK_IN > 0, TOK_OUT > 0)
  - Recalculate diagonal line equation if wrong
  - Document expected relationship (is above-diagonal correct?)
  - Add data quality checks before plotting
- **Validation:** Scatter shows only verified runs, no zeros, correct relationship
- **Deliverable:** Fixed scatter plot + documented expected pattern

#### Task 5.6: Fix API Calls Evolution - ghspec step 6 zeros (1-2h)
- **Investigation:**
  - Check if ghspec step 6 data is missing in runs
  - Review data extraction for evolution chart
  - Verify step numbering (1-6 vs 0-5)
  - Check for missing value handling (None vs 0)
- **Actions:**
  - Add explicit NA/missing value handling (show gap vs zero)
  - Fix data extraction if step indexing is off
  - Add validation to warn if step data is missing
  - Document whether zeros are real or missing data
- **Validation:** Chart shows correct values or clear missing data indicator
- **Deliverable:** Fixed evolution chart + missing data handling

#### Task 5.7: Document all findings and resolutions (1-2h)
- **New File:** `docs/VISUALIZATION_VALIDATION_LOG.md`
- **Content:**
  - Issue descriptions for each investigated item
  - Root cause analysis for each issue
  - Implemented fixes with code references
  - Before/after screenshots of charts
  - Lessons learned and best practices
- **Validation:** Complete documentation of all Stage 5 work
- **Deliverable:** Comprehensive validation log

#### Task 5.8: Create visualization regression tests (1-2h)
- **File:** `tests/integration/test_visualization_regression.py`
- **Actions:**
  - Snapshot current chart outputs as baseline
  - Create tests that compare new outputs to baseline
  - Add tests for data filtering (verified runs only)
  - Add tests for aggregation methods (mean/median)
  - Add tests for missing value handling
- **Validation:** Regression tests catch unintended chart changes
- **Deliverable:** Visualization regression test suite

**Estimated Total:** 44-60 hours (5-7 weeks part-time). Stage 1 & 2 deliver quick wins; Stage 3 & 4 add polish and depth; Stage 5 ensures data integrity.

---

## ✅ Completion Criteria

| Stage | Completion Signals |
|-------|--------------------|
| Stage 1 | `config/experiment.yaml` contains full metrics/pricing/report definitions; `MetricsConfig` loads successfully and tests pass. |
| Stage 2 | `COST_USD` appears in metrics JSON; cost breakdown respects cache discounts; cost tests pass. |
| Stage 3 | Report module renamed and imports updated; report sections generated from config; tables contain only configured metrics; limitations reference excluded metrics automatically. |
| Stage 4 | Visualizations read metric lists from config; new cost charts generated; no hardcoded metrics remain in plotting code. |
| Stage 5 | Timeline, radar, scatter, and evolution charts validated; ZDI calculation verified; aggregation rules documented and updated where necessary. |

---

## 🧪 Testing & Validation

- **Unit Tests:** `test_metrics_config.py`, `test_cost_calculator.py`, `test_report_generator.py` (renamed) verifying config parsing, formatting, and cost math; add targeted tests for ZDI aggregation and chart data preparation functions.
- **Integration Tests:** Update end-to-end tests to validate presence of new metrics and cost breakdown.
- **Regression Run:** Execute `runners/analyze_results.sh` and ensure identical outputs for existing reliable metrics plus new cost fields.
- **Visualization Validation:** Capture before/after snapshots for radar, token efficiency scatter, API calls timeline/evolution to confirm fixes and provide audit trail.

---

## 📚 Documentation Deliverables

1. `docs/RELIABLE_METRICS_REFERENCE.md` – derived from config metadata.
2. `docs/COST_CALCULATION_GUIDE.md` – explains pricing and formulas.
3. `docs/ADDING_NEW_METRICS.md` – step-by-step instructions for future metrics.
4. `docs/EXTENDING_VISUALIZATIONS.md` – how to add new charts via config.
5. `docs/VISUALIZATION_VALIDATION_LOG.md` – captures findings/resolutions for radar, scatter, timeline, evolution, and ZDI investigations.
6. `docs/20251018-audit/IMPLEMENTATION_PROGRESS.md` – ongoing status.
7. `docs/20251018-audit/IMPLEMENTATION_COMPLETE.md` – final summary.

---

## 🚨 Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Config schema mistakes | High | Validation via schema-like tests and CI checks. |
| Chart regression | Medium | Snapshot existing charts and compare outputs; manual visual inspection. |
| Pricing changes | Low | Single config location simplifies updates. |
| Backward compatibility | Medium | Provide migration notes for older configs; keep defaults.

---

## 🛠️ Future Enhancements (Optional)

- Add CLI tool to validate config against schema.
- Generate human-readable docs directly from `metrics` section.
- Support multiple cost scenarios (e.g., different providers) via additional config entries.
- Introduce per-framework overrides (if frameworks use different models).

---

## 📌 Next Steps

1. Implement Stage 1 and Stage 2 (2-week target) for immediate value.
2. Run full analysis to confirm metrics and cost outputs.
3. Continue with Stage 3 and Stage 4 for polished reporting under the new module name.
4. Execute Stage 5 investigations, track findings in `docs/VISUALIZATION_VALIDATION_LOG.md`, and feed improvements back into config/tests.

We will adjust the plan further after your review and any additional observations.
