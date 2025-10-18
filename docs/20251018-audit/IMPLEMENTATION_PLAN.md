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

- **Extend** `config/experiment.yaml` with new sections (`metrics`, `pricing`, `visualizations`, `report`).
- **Replace** the metric list in `stopping_rule.metrics` with references to centralized definitions (use the metrics section). 
- **Implement** `MetricsConfig` loader (`src/utils/metrics_config.py`) that:
  - Reads the experiment config.
  - Parses reliable, derived, and excluded metrics into structured objects.
  - Provides helper functions for formatting, lookup, filtering, and validation.
- **Add tests** (`tests/unit/test_metrics_config.py`) to ensure schema integrity and formatting utilities.

### **Stage 2 – Cost Calculation & Aggregation (8-10h, high)**

- **Implement** `CostCalculator` (`src/utils/cost_calculator.py`) that reads pricing from the unified config.
- **Update** `MetricsCollector` to:
  - Initialize with `MetricsConfig` and `CostCalculator`.
  - Aggregate only metrics defined in `metrics.reliable_metrics`.
  - Compute derived metrics via config definitions.
- **Update** orchestrator runner to pass model information into the collector.
- **Write unit tests** (`tests/unit/test_cost_calculator.py`) covering cache discounts and edge cases.

### **Stage 3 – Data-Driven Report Generator & Module Rename (12-16h, critical)**

- **Rename** `src/analysis/statistics.py` to `src/analysis/report_generator.py` (or equivalently descriptive name) and update all imports, CLI entry points, scripts (e.g., `runners/analyze_results.sh`), and tests referencing the old module.
- **Refactor** the renamed module to:
  - Drive section order and visibility with `report.sections` from the config.
  - Generate metric definition tables, aggregate statistics, and statistical tests using only metrics from the config.
  - Add a cost analysis section defined by the "cost" category.
  - Auto-generate the limitations section from `metrics.excluded_metrics`.
- **Update associated artifacts** such as documentation references, module docstrings, and `__all__` exports to reflect the new name.
- **Ensure** statistical tests run only on metrics flagging `statistical_test: true`.

### **Stage 4 – Visualization Factory (6-8h, medium)**

- **Refactor** `src/analysis/visualizations.py` to:
  - Use a `VisualizationFactory` that reads `visualizations` from config.
  - Create charts (radar, scatter, bar, stacked, timeline) dynamically with metric metadata.
  - Add cost-specific charts (cost breakdown, cost vs. speed, cache savings).
- **Update** existing plots to remove hardcoded metric names and use short titles/units from config.

### **Stage 5 – Metrics & Visualization Validation (8-12h, high)**

- **Audit API Calls Timeline** computation ensuring step values use configured aggregation (mean/median) across verified runs instead of last-run sampling. Update metric aggregation rules in config if needed.
- **Investigate ZDI metric capture** end-to-end (adapter outputs → metrics collector → report) to confirm correctness, add logging/tests, and document findings.
- **Review Radar Chart** scaling and data sources:
  - Confirm BAEs zero values and fix normalization/metric selection.
  - Evaluate percent-based scale; adjust normalization or config to display user-friendly percentages.
  - Validate axis scaling formulas against configuration.
- **Analyze Token Efficiency Scatter**:
  - Verify why all points sit above diagonal; confirm expected relationship or fix axis mapping.
  - Resolve zero-value artifacts by filtering to verified runs and enforcing minimum thresholds.
- **Inspect API Calls Evolution Across Steps** chart to understand ghspec step 6 zeros; fix data extraction if missing values, and ensure fallback/NA handling is explicit.
- **Document resolutions** and update visualization config/tests accordingly.

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
