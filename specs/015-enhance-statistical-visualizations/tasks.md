# Tasks: Enhanced Statistical Visualizations for Paper Generation

**Feature Branch**: `015-enhance-statistical-visualizations`  
**Input**: Design documents from `/specs/015-enhance-statistical-visualizations/`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/visualization_api.md

**Tests**: Not included per NFR-004. Validation through real paper generation at end.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

---

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and verification of existing infrastructure

- [x] T001 [P] Verify matplotlib ≥3.5, seaborn ≥0.12, scipy ≥1.11, numpy ≥1.24 in requirements.txt
- [x] T002 [P] Verify pandas and statsmodels are available in environment
- [x] T003 [P] Read existing `StatisticalVisualizationGenerator` class in `src/paper_generation/statistical_visualizations.py` (lines 1-732)
- [x] T004 [P] Verify VisualizationType enum location in `src/paper_generation/statistical_analyzer.py` or `src/paper_generation/models.py`
- [x] T005 [P] Verify Visualization, MetricDistribution, EffectSize classes are accessible

**Checkpoint**: ✅ All dependencies verified, existing code understood

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Extend VisualizationType enum with 8 new values (EFFECT_PANEL, EFFICIENCY, REGRESSION, OVERLAP, NORMALIZED_COST, RANK, STABILITY, OUTLIER_RUN) in appropriate location
- [x] T007 Create helper method `_magnitude_to_color(magnitude: str) -> str` in `StatisticalVisualizationGenerator` class for effect size color mapping (gray=negligible, green=small, orange=medium, red=large)
- [x] T008 Create helper method `_format_metric_label(metric: str) -> str` in `StatisticalVisualizationGenerator` class for axis labels with units
- [x] T009 Update `_apply_publication_styling()` method to ensure WCAG 2.1 colorblind-accessible palettes are used consistently
- [x] T010 [P] Create RegressionResult dataclass in `src/paper_generation/models.py` with attributes: slope, intercept, r_squared, std_err
- [x] T011 [P] Create RankData dataclass in `src/paper_generation/models.py` with attributes: framework, metric, rank, tied
- [x] T012 [P] Create StabilityMetric dataclass in `src/paper_generation/models.py` with attributes: framework, metric, cv_value, is_stable
- [x] T013 [P] Create OutlierInfo dataclass in `src/paper_generation/models.py` with attributes: run_index, value, is_outlier, iqr_factor

**Checkpoint**: ✅ Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Effect Size Visualization Across All Metrics (Priority: P1) 🎯 MVP

**Goal**: Enable researchers to show effect size magnitudes across all metrics in a single comprehensive faceted panel plot

**Independent Test**: Generate experiment with 3+ frameworks and 5+ metrics, run paper generation, verify faceted effect-size panel created with color-coded magnitudes

### Implementation for User Story 1

- [x] T014 [US1] Implement `generate_effect_size_panel()` method in `StatisticalVisualizationGenerator` class per contracts/visualization_api.md signature
- [x] T015 [US1] In `generate_effect_size_panel()`: Create subplot grid using `plt.subplots(nrows=n_metrics, ncols=1, sharey=True)` with figsize calculated as `(10, 3*n_metrics)`
- [x] T016 [US1] In `generate_effect_size_panel()`: Iterate through metrics and plot effect sizes with color coding using `_magnitude_to_color()` helper
- [x] T017 [US1] In `generate_effect_size_panel()`: Add 95% confidence intervals as error bars when `show_ci=True` using `ax.errorbar()`
- [x] T018 [US1] In `generate_effect_size_panel()`: Implement complete separation markers (|δ| = 1.0) using open circle markers with `fillstyle='none'` when `mark_complete_separation=True`
- [x] T019 [US1] In `generate_effect_size_panel()`: Apply publication styling, add axis labels, metric labels per facet, and legend
- [x] T020 [US1] In `generate_effect_size_panel()`: Generate auto filename `effect_size_panel_{timestamp}.svg`, save to output_dir, create and return Visualization object
- [x] T021 [US1] Add edge case handling: empty effect_sizes dict → raise ValueError with descriptive message
- [x] T022 [US1] Add edge case handling: metrics list contains unknown metric → raise ValueError listing valid metrics
- [x] T023 [US1] Add edge case handling: >10 metrics → log warning and create multi-page output or focus on top 10 by variance

**Checkpoint**: ✅ User Story 1 fully functional - effect-size panel plots can be generated independently

---

## Phase 4: User Story 2 - Cost-Performance Efficiency Analysis (Priority: P1) 🎯 MVP

**Goal**: Enable researchers to visualize cost vs time trade-offs in a single scatter plot showing efficiency quadrants

**Independent Test**: Generate experiment with frameworks having different cost/time profiles, run visualization, verify scatter plot shows clear clustering by efficiency

### Implementation for User Story 2

- [x] T024 [US2] Implement `generate_efficiency_plot()` method in `StatisticalVisualizationGenerator` class per contracts/visualization_api.md signature
- [x] T025 [US2] In `generate_efficiency_plot()`: Create figure and axis, set up scatter plot with framework-specific colors from colorblind palette
- [x] T026 [US2] In `generate_efficiency_plot()`: Plot mean values per framework with optional jittering using `np.random.normal(mean, jitter*range)`
- [x] T027 [US2] In `generate_efficiency_plot()`: Add error bars when `show_error_bars=True` using mean ± 1 std via `ax.errorbar()`
- [x] T028 [US2] In `generate_efficiency_plot()`: Implement log-scale option using `ax.set_xscale('symlog', linthresh=1.0)` when `use_log_scale=True`
- [x] T029 [US2] In `generate_efficiency_plot()`: Add axis labels with units, title, legend with framework names
- [x] T030 [US2] In `generate_efficiency_plot()`: Apply publication styling, save as `efficiency_{time_metric}_vs_{cost_metric}.svg`, return Visualization object
- [x] T031 [US2] Add edge case handling: framework mismatch between time and cost distributions → raise ValueError
- [x] T032 [US2] Add edge case handling: zero variance in either metric → log warning and plot points without error bars

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently - researchers can generate effect panels and efficiency plots

---

## Phase 5: User Story 3 - Token-to-Cost Relationship Analysis (Priority: P2)

**Goal**: Enable researchers to visualize framework-specific cost structures through regression analysis

**Independent Test**: Generate experiment with varying token volumes, run regression visualization, verify separate regression lines per framework

### Implementation for User Story 3

- [x] T033 [US3] Implement `generate_regression_plot()` method in `StatisticalVisualizationGenerator` class per contracts/visualization_api.md signature
- [x] T034 [US3] In `generate_regression_plot()`: Create figure and axis, set up scatter plot with framework-specific colors
- [x] T035 [US3] In `generate_regression_plot()`: For each framework, fit linear regression using `scipy.stats.linregress()` on x and y values
- [x] T036 [US3] In `generate_regression_plot()`: Store regression results in RegressionResult objects (slope, intercept, r_squared, std_err)
- [x] T037 [US3] In `generate_regression_plot()`: Plot scatter points and overlay regression lines per framework
- [x] T038 [US3] In `generate_regression_plot()`: Annotate with equations (y = mx + b) when `show_equations=True`
- [x] T039 [US3] In `generate_regression_plot()`: Annotate with R² values when `show_r_squared=True`
- [x] T040 [US3] In `generate_regression_plot()`: If cached_tokens provided, encode as third dimension via marker size or color gradient
- [x] T041 [US3] In `generate_regression_plot()`: Add axis labels with units, title, legend, apply publication styling
- [x] T042 [US3] In `generate_regression_plot()`: Save as `regression_{x_metric}_vs_{y_metric}.svg`, return Visualization object
- [x] T043 [US3] Add edge case handling: n<3 for any framework → skip that framework with log warning
- [x] T044 [US3] Add edge case handling: zero variance in x or y → raise ValueError (cannot fit regression)
- [x] T045 [US3] Add edge case handling: zero slope (flat line) → annotate "no relationship detected" and show R² value

**Checkpoint**: User Stories 1, 2, AND 3 should all work independently - complete P1 and P2 functionality for MVP+

---

## Phase 6: User Story 4 - Distribution Overlap Visualization (Priority: P2)

**Goal**: Enable researchers to show nuanced 2-way comparisons when effect sizes are small but statistically significant

**Independent Test**: Identify metric pairs with small effect sizes (|δ| < 0.3), generate overlap visualizations, verify density overlap shown

### Implementation for User Story 4

- [x] T046 [US4] Implement `generate_overlap_plot()` method in `StatisticalVisualizationGenerator` class per contracts/visualization_api.md signature
- [x] T047 [US4] In `generate_overlap_plot()`: Create figure and axis for 2-way comparison
- [x] T048 [US4] In `generate_overlap_plot()`: If plot_type="density", use seaborn `kdeplot()` for each distribution with alpha=0.5 for transparency
- [x] T049 [US4] In `generate_overlap_plot()`: If plot_type="violin", create 2-way violin plot using matplotlib `violinplot()`
- [x] T050 [US4] In `generate_overlap_plot()`: Compute overlap coefficient using KDE integration (area of min(density_a, density_b))
- [x] T051 [US4] In `generate_overlap_plot()`: Annotate plot with effect size value, p-value, and overlap coefficient
- [x] T052 [US4] In `generate_overlap_plot()`: Add shaded region showing overlap area when plot_type="density"
- [x] T053 [US4] In `generate_overlap_plot()`: Add axis labels, title, legend with group names, apply publication styling
- [x] T054 [US4] In `generate_overlap_plot()`: Save as `overlap_{metric_name}_{group_a}_vs_{group_b}.svg`, return Visualization object
- [x] T055 [US4] Add edge case handling: identical distributions → annotate "practical equivalence" with overlap ≈ 1.0
- [x] T056 [US4] Add edge case handling: n=1 for either group → cannot compute KDE, raise ValueError

**Checkpoint**: User Stories 1-4 complete - all P1 and half of P2 priority features functional

---

## Phase 7: User Story 5 - Normalized Cost-Per-Token Comparison (Priority: P2)

**Goal**: Enable researchers to show cost efficiency normalized by token usage

**Independent Test**: Compute cost_per_1k_tokens, generate box plots, verify frameworks ranked by efficiency

### Implementation for User Story 5

- [x] T057 [US5] Implement `generate_normalized_cost_plot()` method in `StatisticalVisualizationGenerator` class per contracts/visualization_api.md signature
- [x] T058 [US5] In `generate_normalized_cost_plot()`: For each framework, compute normalized_cost = (cost / tokens_total) * 1000 for all runs
- [x] T059 [US5] In `generate_normalized_cost_plot()`: Create MetricDistribution objects for normalized cost per framework
- [x] T060 [US5] In `generate_normalized_cost_plot()`: Create box plot using matplotlib `boxplot()` showing normalized costs across frameworks
- [x] T061 [US5] In `generate_normalized_cost_plot()`: Color boxes using framework-specific colors from colorblind palette
- [x] T062 [US5] In `generate_normalized_cost_plot()`: Mark outliers using 1.5×IQR threshold (consistent with existing box plots)
- [x] T063 [US5] In `generate_normalized_cost_plot()`: Add axis labels ("Cost per 1000 tokens (USD)", "Framework"), title, apply publication styling
- [x] T064 [US5] In `generate_normalized_cost_plot()`: Save as `normalized_cost_per_1k_tokens.svg`, return Visualization object
- [x] T065 [US5] Add edge case handling: tokens_total = 0 for any run → skip that run with log warning
- [x] T066 [US5] Add edge case handling: all frameworks have identical normalized costs → annotate "no efficiency difference detected"

**Checkpoint**: User Stories 1-5 complete - all P1 and P2 priority features functional

---

## Phase 8: User Story 6 - Multi-Metric Framework Ranking (Priority: P3)

**Goal**: Enable researchers to show ranking consistency patterns across metrics

**Independent Test**: Rank frameworks on 5+ metrics, generate rank plot, verify rank patterns visible through line trajectories

### Implementation for User Story 6

- [x] T067 [US6] Implement `generate_rank_plot()` method in `StatisticalVisualizationGenerator` class per contracts/visualization_api.md signature
- [x] T068 [US6] In `generate_rank_plot()`: For each metric, rank frameworks based on mean values (configurable lower_is_better per metric)
- [x] T069 [US6] In `generate_rank_plot()`: Store rankings in RankData objects with tie handling (average rank for ties)
- [x] T070 [US6] In `generate_rank_plot()`: Create line plot with metrics on x-axis (categorical), ranks on y-axis (1 to N)
- [x] T071 [US6] In `generate_rank_plot()`: Plot framework lines connecting ranks across metrics with framework-specific colors
- [x] T072 [US6] In `generate_rank_plot()`: Add markers at each metric-rank intersection for clarity
- [x] T073 [US6] In `generate_rank_plot()`: Invert y-axis (rank 1 at top) for intuitive reading
- [x] T074 [US6] In `generate_rank_plot()`: Add axis labels, title, legend with framework names, apply publication styling
- [x] T075 [US6] In `generate_rank_plot()`: Save as `framework_rankings_across_metrics.svg`, return Visualization object
- [x] T076 [US6] Add edge case handling: single metric → skip (ranking plot requires multiple metrics for patterns)
- [x] T077 [US6] Add edge case handling: all frameworks tied on all metrics → annotate "no ranking difference"

**Checkpoint**: User Stories 1-6 complete - all P1, P2, and partial P3 features functional

---

## Phase 9: User Story 7 - Coefficient of Variation Stability Analysis (Priority: P3)

**Goal**: Enable researchers to show framework predictability/stability through CV analysis

**Independent Test**: Compute CV per metric per framework, generate grouped bar plot, verify lower CV highlighted as better stability

### Implementation for User Story 7

- [x] T078 [US7] Implement `generate_stability_plot()` method in `StatisticalVisualizationGenerator` class per contracts/visualization_api.md signature
- [x] T079 [US7] In `generate_stability_plot()`: For each framework and metric, compute CV = std / mean
- [x] T080 [US7] In `generate_stability_plot()`: Store in StabilityMetric objects with is_stable flag (CV < 0.20)
- [x] T081 [US7] In `generate_stability_plot()`: Create grouped or faceted bar plot with frameworks on x-axis, CV on y-axis
- [x] T082 [US7] In `generate_stability_plot()`: Use different bars/colors per metric within each framework group
- [x] T083 [US7] In `generate_stability_plot()`: Add horizontal line at CV=0.20 marking stability threshold
- [x] T084 [US7] In `generate_stability_plot()`: Highlight bars with CV<0.20 with distinct border or pattern
- [x] T085 [US7] In `generate_stability_plot()`: Add axis labels ("Coefficient of Variation", "Framework"), title, legend, apply publication styling
- [x] T086 [US7] In `generate_stability_plot()`: Save as `stability_coefficient_of_variation.svg`, return Visualization object
- [x] T087 [US7] Add edge case handling: mean = 0 → CV undefined, return np.nan and annotate "N/A" in plot
- [x] T088 [US7] Add edge case handling: n=1 → std=0, CV=0, annotate "single run, variance unknown"

**Checkpoint**: User Stories 1-7 complete - all P1, P2, and most P3 features functional

---

## Phase 10: User Story 8 - Outlier Impact Visualization (Priority: P3)

**Goal**: Enable researchers to distinguish systematic slowness from occasional outliers through run-index plots

**Independent Test**: Generate experiment with outlier runs, create run-index plots, verify outliers visually distinct from main distribution

### Implementation for User Story 8

- [x] T089 [US8] Implement `generate_outlier_run_plot()` method in `StatisticalVisualizationGenerator` class per contracts/visualization_api.md signature
- [ ] T090 [US8] In `generate_outlier_run_plot()`: Create subplot grid with one panel per framework using `plt.subplots()`
- [ ] T091 [US8] In `generate_outlier_run_plot()`: For each framework, plot run indices (1, 2, 3...) on x-axis and metric values on y-axis
- [ ] T092 [US8] In `generate_outlier_run_plot()`: Identify outliers using 1.5×IQR threshold (consistent with box plots)
- [x] T089 [US8] Implement `generate_outlier_run_plot()` method in `StatisticalVisualizationGenerator` class per contracts/visualization_api.md signature
- [x] T090 [US8] In `generate_outlier_run_plot()`: Create figure and faceted axis (one subplot per framework)
- [x] T091 [US8] In `generate_outlier_run_plot()`: For each framework, plot run_index (x-axis) vs metric_value (y-axis) as scatter
- [x] T092 [US8] In `generate_outlier_run_plot()`: Identify outliers using IQR method (Q1 - 1.5×IQR, Q3 + 1.5×IQR)
- [x] T093 [US8] In `generate_outlier_run_plot()`: Store in OutlierInfo objects with run_index, value, is_outlier flag
- [x] T094 [US8] In `generate_outlier_run_plot()`: Plot normal runs as blue circles, outliers as red triangles with larger markers
- [x] T095 [US8] In `generate_outlier_run_plot()`: Add horizontal lines showing median and quartiles for reference
- [x] T096 [US8] In `generate_outlier_run_plot()`: Add axis labels ("Run Index", metric label with units), facet titles (framework names), apply publication styling
- [x] T097 [US8] In `generate_outlier_run_plot()`: Save as `outlier_runs_{metric_name}.svg`, return Visualization object
- [x] T098 [US8] Add edge case handling: no outliers detected → annotate "no outliers (1.5×IQR)"
- [x] T099 [US8] Add edge case handling: all runs are outliers (unusual data quality) → log warning and plot all as outliers

**Checkpoint**: User Stories 1-8 complete - all 8 visualization types fully functional

---

## Phase 11: Batch Generation and Integration

**Purpose**: Implement batch generation method and integrate with paper generation workflow

- [x] T100 Implement `generate_all_enhanced_visualizations()` batch method in `StatisticalVisualizationGenerator` class per contracts/visualization_api.md
- [x] T101 In `generate_all_enhanced_visualizations()`: Call all 8 individual methods sequentially with try/except for graceful degradation
- [x] T102 In `generate_all_enhanced_visualizations()`: Log progress for each visualization type being generated
- [x] T103 In `generate_all_enhanced_visualizations()`: Collect all Visualization objects in list and return
- [x] T104 In `generate_all_enhanced_visualizations()`: Handle edge case where data is unavailable for certain plot types (e.g., no regression data) by skipping with log message
- [x] T105 Locate paper generation workflow entry point (likely in `src/paper_generation/` module)
- [x] T106 Update paper generator to invoke BOTH `generate_all_visualizations()` (existing 4) and `generate_all_enhanced_visualizations()` (new 8) per REDUNDANCY_DECISIONS.md
- [x] T107 Verify paper generator collects all 12 Visualization objects in combined list
- [x] T108 Ensure paper generator passes all 12 visualizations to LaTeX template or figure inclusion logic

**Checkpoint**: Batch generation works - all 12 plots generated with single workflow execution

---

## Phase 12: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories and final validation

- [x] T109 [P] Add comprehensive docstrings (Google style) to all 8 new methods per NFR-003
- [x] T110 [P] Add docstrings to 4 new dataclasses (RegressionResult, RankData, StabilityMetric, OutlierInfo)
- [x] T111 [P] Add docstrings to helper methods (_magnitude_to_color, _format_metric_label)
- [x] T112 Review all error messages for clarity and actionability per NFR-005
- [x] T113 Add memory management: ensure `plt.close(fig)` called in finally blocks for all methods per research.md R7
- [x] T114 [P] Update quickstart.md with actual code examples showing how to use all 8 new methods individually
- [x] T115 [P] Update quickstart.md with example of generating all 12 plots via both batch methods
- [x] T116 Performance optimization: Profile batch generation with 100 runs per framework, ensure <30s total per SC-001
- [x] T117 Performance optimization: Check SVG file sizes, ensure <2MB per file per SC-011 and NFR-002
- [x] T118 Performance optimization: Monitor memory usage during batch generation, ensure <500MB per NFR-007
- [ ] T119 **VALIDATION**: Run real paper generation with `~/projects/uece/baes/baes_benchmarking_20251028_0713` dataset (BAEs vs ChatDev vs GHSpec)
- [ ] T120 **VALIDATION**: Verify all 12 SVG files generated in output directory
- [ ] T121 **VALIDATION**: Visual inspection of effect-size panel (faceted, color-coded, CIs shown)
- [ ] T122 **VALIDATION**: Visual inspection of efficiency plot (scatter, quadrants visible)
- [ ] T123 **VALIDATION**: Visual inspection of regression plot (separate lines per framework, R² annotated)
- [ ] T124 **VALIDATION**: Visual inspection of overlap plot (2-way density/violin, overlap coefficient shown)
- [ ] T125 **VALIDATION**: Visual inspection of normalized cost plot (box plot, efficiency ranked)
- [ ] T126 **VALIDATION**: Visual inspection of rank plot (connected lines, patterns visible)
- [ ] T127 **VALIDATION**: Visual inspection of stability plot (CV bars, threshold line at 0.20)
- [ ] T128 **VALIDATION**: Visual inspection of outlier run plot (run indices, outliers marked)
- [ ] T129 **VALIDATION**: Test LaTeX compilation with all 12 generated figures
- [ ] T130 **VALIDATION**: Verify no existing visualizations deleted or modified (backward compatibility per SC-014)
- [x] T131 Code cleanup: Remove any debug print statements, ensure consistent formatting per NFR-003
- [ ] T132 Final commit: "feat: Add 8 enhanced statistical visualizations for paper generation (closes #015)"

**Checkpoint**: Feature complete and validated through real paper generation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phases 3-10)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
  - US1 + US2 are P1 (MVP critical)
  - US3, US4, US5 are P2 (important for comprehensive analysis)
  - US6, US7, US8 are P3 (nice-to-have, supplementary figures)
- **Batch & Integration (Phase 11)**: Depends on all 8 user stories (US1-US8) being complete
- **Polish (Phase 12)**: Depends on Phase 11 completion

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 3 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 4 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 5 (P2)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 6 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 7 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 8 (P3)**: Can start after Foundational (Phase 2) - No dependencies on other stories

**All user stories are independently implementable and testable!**

### Within Each User Story

- Tasks within a story are sequential unless marked [P]
- Core implementation → edge case handling → checkpoint validation

### Parallel Opportunities

- All Setup tasks (T001-T005) marked [P] can run in parallel
- Foundational dataclass creation tasks (T010-T013) marked [P] can run in parallel
- Once Foundational phase completes, all 8 user stories can start in parallel (if team capacity allows)
- Polish documentation tasks (T109-T111, T114-T115) marked [P] can run in parallel
- Validation visual inspection tasks (T121-T128) can be parallelized

---

## Parallel Example: After Foundational Phase Complete

```bash
# All 8 user stories can start simultaneously (if team has 8 developers):
Developer A: Phase 3 (US1 - Effect Size Panel)
Developer B: Phase 4 (US2 - Efficiency Plot)
Developer C: Phase 5 (US3 - Regression Plot)
Developer D: Phase 6 (US4 - Overlap Plot)
Developer E: Phase 7 (US5 - Normalized Cost)
Developer F: Phase 8 (US6 - Rank Plot)
Developer G: Phase 9 (US7 - Stability Plot)
Developer H: Phase 10 (US8 - Outlier Run Plot)

# Or sequential for single developer (priority order):
1. US1 + US2 (P1 - MVP critical) → Validate → Demo
2. US3 + US4 + US5 (P2 - comprehensive) → Validate → Demo
3. US6 + US7 + US8 (P3 - supplementary) → Validate → Demo
4. Batch integration → Full validation
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only - Both P1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Effect-size panel)
4. Complete Phase 4: User Story 2 (Efficiency plot)
5. **STOP and VALIDATE**: Generate test plots for US1 and US2
6. If working, can demonstrate MVP with 2 new visualization types

### Incremental Delivery (Priority-Based)

1. Complete Setup + Foundational → Foundation ready
2. Add US1 + US2 (P1) → Validate independently → 2 new plots working (MVP!)
3. Add US3 + US4 + US5 (P2) → Validate independently → 5 new plots total
4. Add US6 + US7 + US8 (P3) → Validate independently → All 8 new plots complete
5. Add Batch integration → All 12 plots (4 existing + 8 new) working
6. Final validation with real paper generation

### Parallel Team Strategy

With 2-3 developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - **Sprint 1**: Dev A: US1, Dev B: US2 (P1 features in parallel)
   - **Sprint 2**: Dev A: US3, US4; Dev B: US5 (P2 features)
   - **Sprint 3**: Dev A: US6, US7; Dev B: US8 (P3 features)
   - **Sprint 4**: Dev A: Batch integration, Dev B: Documentation
   - **Sprint 5**: Team: Real paper generation validation

---

## Task Summary

- **Total Tasks**: 132
- **Setup**: 5 tasks
- **Foundational**: 8 tasks (BLOCKING)
- **User Story 1 (P1)**: 10 tasks (T014-T023)
- **User Story 2 (P1)**: 9 tasks (T024-T032)
- **User Story 3 (P2)**: 13 tasks (T033-T045)
- **User Story 4 (P2)**: 11 tasks (T046-T056)
- **User Story 5 (P2)**: 10 tasks (T057-T066)
- **User Story 6 (P3)**: 11 tasks (T067-T077)
- **User Story 7 (P3)**: 11 tasks (T078-T088)
- **User Story 8 (P3)**: 11 tasks (T089-T099)
- **Batch & Integration**: 9 tasks (T100-T108)
- **Polish & Validation**: 24 tasks (T109-T132)

**Parallel Opportunities**: 13 tasks marked [P] across Setup, Foundational, and Polish phases

**MVP Scope**: Setup + Foundational + US1 + US2 = 32 tasks (24% of total) delivers 2 critical visualizations

**Full Feature**: All 132 tasks = 8 new visualization types + batch generation + real paper validation

---

## Notes

- No test tasks per NFR-004 - validation through real paper generation only
- [P] tasks = different files/sections, no dependencies
- [Story] label (US1-US8) maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each user story checkpoint
- Stop at any checkpoint to validate story independently
- File path: `src/paper_generation/statistical_visualizations.py` for all implementations
- Validation dataset: `~/projects/uece/baes/baes_benchmarking_20251028_0713`
