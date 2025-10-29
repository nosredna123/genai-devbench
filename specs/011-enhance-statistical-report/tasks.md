# Tasks: Enhanced Statistical Report Generation

**Input**: Design documents from `/specs/011-enhance-statistical-report/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: ❌ NO AUTOMATED TESTS - Validation via real experiment generation only (see Development Workflow in plan.md)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

**Special Requirement**: All validation done by running against `~/projects/uece/baes/baes_benchmarking_20251028_0713` with output to `tmp/test_paper2/`

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4, US5, US6)
- Include exact file paths in descriptions

## Path Conventions
- Single project structure: `src/paper_generation/` for core code
- No test files: `tests/` directory not used for this feature
- Validation output: `tmp/test_paper2/` for manual inspection

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency setup

- [X] T001 Add statistical dependencies to `requirements.txt`: scipy==1.11.0, statsmodels==0.14.0, seaborn==0.12.2, numpy==1.24.3
- [X] T002 Create `src/paper_generation/exceptions.py` with `StatisticalAnalysisError` exception class
- [X] T003 [P] Create output directory structure in validation command: `tmp/test_paper2/` and `tmp/test_paper2/figures/statistical/`

**Validation**: Run `pip install -r requirements.txt` and verify scipy, statsmodels, seaborn, numpy are installed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core data structures and utilities that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T004 Create `src/utils/statistical_helpers.py` with helper functions:
  - `bootstrap_ci(values1, values2, measure_func, n_iterations=10000, seed=42)` → (ci_lower, ci_upper)
  - `cohens_d(values1, values2)` → float
  - `cliffs_delta(values1, values2)` → float
  - `interpret_effect_size(measure, value)` → magnitude string ("negligible", "small", "medium", "large")

- [X] T005 Implement data model entities in `src/paper_generation/statistical_analyzer.py` (as dataclasses):
  - `MetricDistribution` (metric_name, framework_name, values, mean, median, std, q1, q3, min, max, iqr, cv, outliers, zero_variance)
  - `AssumptionCheck` (test_name, metric_name, frameworks, statistic, p_value, alpha, passed, interpretation, recommendation)
  - `StatisticalTest` (test_name, metric_name, frameworks, test_type, statistic, p_value, alpha, significant, alternative, interpretation, method_notes)
  - `EffectSize` (measure, metric_name, frameworks, value, ci_lower, ci_upper, ci_method, magnitude, interpretation, direction)
  - `PowerAnalysis` (metric_name, frameworks, effect_size, current_n, achieved_power, target_power, recommended_n, alpha, power_adequate, interpretation, recommendation)
  - `Visualization` (plot_type, metric_name, frameworks, file_path, format, dimensions, caption, alt_text, embedded_in)
  - `StatisticalFindings` (experiment_name, primary_metric, n_frameworks, n_metrics, n_runs_per_framework, distributions, assumption_checks, statistical_tests, effect_sizes, power_analyses, visualizations, summary, metadata)

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

**Validation**: Run `python -c "from src.paper_generation.statistical_analyzer import MetricDistribution; print('Data models imported successfully')"` and verify no import errors

---

## Phase 3: User Story 1 - Comprehensive Statistical Testing (Priority: P1) 🎯 MVP

**Goal**: Implement rigorous statistical analysis with normality tests, appropriate parametric/non-parametric tests, effect sizes, and proper interpretations

**Independent Test**: Run experiment with 2+ frameworks, verify report includes Shapiro-Wilk tests, appropriate statistical tests (t-test/Mann-Whitney or ANOVA/Kruskal-Wallis), effect sizes (Cohen's d/Cliff's delta), and interpretations

### Implementation for User Story 1

- [X] T006 [P] [US1] Implement `StatisticalAnalyzer` class in `src/paper_generation/statistical_analyzer.py`:
  - Constructor: `__init__(self, config: Dict, random_seed: int = 42)`
  - Method: `analyze_experiment(run_data: Dict) → StatisticalFindings`
  - Method: `compute_metric_distribution(metric_name, framework_name, values) → MetricDistribution`

- [X] T007 [US1] Implement normality testing in `src/paper_generation/statistical_analyzer.py`:
  - Method: `run_normality_test(distribution: MetricDistribution) → AssumptionCheck`
  - Uses `scipy.stats.shapiro(values)`
  - Returns AssumptionCheck with interpretation

- [X] T008 [US1] Implement variance testing in `src/paper_generation/statistical_analyzer.py`:
  - Method: `run_variance_test(distributions: List[MetricDistribution]) → AssumptionCheck`
  - Uses `scipy.stats.levene(*[d.values for d in distributions])`
  - Returns AssumptionCheck for homogeneity of variance

- [X] T009 [US1] Implement test selection logic in `src/paper_generation/statistical_analyzer.py`:
  - Method: `_select_test_method(n_groups, all_normal, equal_variance) → str`
  - Decision tree: n=2 + normal + equal variance → t-test
  - n=2 + (non-normal OR unequal variance) → Mann-Whitney U
  - n≥3 + normal + equal variance → ANOVA
  - n≥3 + (non-normal OR unequal variance) → Kruskal-Wallis

- [X] T010 [US1] Implement statistical tests in `src/paper_generation/statistical_analyzer.py`:
  - Method: `run_statistical_test(distributions, assumptions) → StatisticalTest`
  - Implements: `scipy.stats.ttest_ind()`, `scipy.stats.mannwhitneyu()`
  - Implements: `scipy.stats.f_oneway()`, `scipy.stats.kruskal()`
  - Applies Bonferroni correction for multiple comparisons (3+ groups)

- [X] T011 [US1] Implement effect size calculations in `src/paper_generation/statistical_analyzer.py`:
  - Method: `compute_effect_size(dist1, dist2, test_type) → EffectSize`
  - Calls `cohens_d()` for parametric tests
  - Calls `cliffs_delta()` for non-parametric tests
  - Calls `bootstrap_ci()` for 95% confidence intervals (10,000 iterations)
  - Uses `interpret_effect_size()` for magnitude labels

- [X] T012 [US1] Add zero-variance detection in `compute_metric_distribution()`:
  - Set `zero_variance = True` if `std == 0`
  - Skip statistical tests when zero_variance detected
  - Document reason in interpretation

**Validation**: Run `python src/main.py --experiment ~/projects/uece/baes/baes_benchmarking_20251028_0713 --output-dir tmp/test_paper2/` and verify:
- Shapiro-Wilk test results appear in console/logs
- Appropriate tests selected based on normality
- Effect sizes calculated with CIs
- Zero variance metrics handled gracefully

**Checkpoint**: Core statistical analysis is functional - can detect normality, select tests, calculate effect sizes

---

## Phase 4: User Story 2 - Statistical Power Analysis (Priority: P2)

**Goal**: Provide power analysis showing if experiment has sufficient power to detect meaningful differences and guidance on additional runs needed

**Independent Test**: Generate reports with varying sample sizes (n=2, 5, 10, 30) and verify power calculations present, interpreted correctly, and include recommendations when power insufficient

### Implementation for User Story 2

- [X] T013 [US2] Implement power analysis in `src/paper_generation/statistical_analyzer.py`:
  - Method: `perform_power_analysis(effect: EffectSize, n_per_group: int) → PowerAnalysis`
  - Uses `statsmodels.stats.power.TTestIndPower()` for parametric tests
  - Uses simulation for non-parametric tests (conservative estimate)
  - Calculates achieved power with current sample size
  - Calculates recommended n for target_power=0.80

- [X] T014 [US2] Add power warnings to `StatisticalFindings.summary`:
  - Field: `power_warnings: List[str]` for metrics with achieved_power < 0.70
  - Format warnings as researcher-friendly recommendations
  - Include in summary key_findings when power inadequate

**Validation**: Run experiment generation and inspect `tmp/test_paper2/statistical_report_*.md`:
- Power analysis section exists
- Achieved power calculated for each comparison
- Sample size recommendations present when power < 80%
- Warnings formatted in plain language

**Checkpoint**: Power analysis complete - users can understand if their sample size is adequate

---

## Phase 5: User Story 6 - Educational Explanations (Priority: P1)

**Goal**: Generate didactic "What/Why/How" explanations for all statistical tests, plots, and concepts to make statistics accessible

**Independent Test**: Have non-statistician read report and answer: (1) What does each test measure? (2) Why was it chosen? (3) What do results mean? Success = 90%+ correct answers

**Note**: This is P1 because it's foundational for usability - implemented early alongside US1

### Implementation for User Story 6

- [X] T015 [P] [US6] Create `src/paper_generation/educational_content.py` with `EducationalContentGenerator` class:
  - Constructor: `__init__(self, reading_level: int = 8)`
  - Define `EXPLANATION_TEMPLATES` constant with What/Why/How for: Shapiro-Wilk, Mann-Whitney U, t-test, ANOVA, Kruskal-Wallis, Levene, Cohen's d, Cliff's delta, power analysis

- [X] T016 [US6] Implement test explanations in `educational_content.py`:
  - Method: `explain_statistical_test(test: StatisticalTest) → str`
  - Returns markdown with 📚 What, 💡 Why, 📊 Results, 🎓 How to interpret sections
  - Uses plain language (8th grade reading level)

- [X] T017 [US6] Implement effect size explanations in `educational_content.py`:
  - Method: `explain_effect_size(effect: EffectSize) → str`
  - Returns markdown with 📏 What, 📊 Results, 💡 Real-world analogy, ✅ Practical meaning sections
  - Includes analogies (e.g., height differences between age groups)

- [X] T018 [US6] Implement power analysis explanations in `educational_content.py`:
  - Method: `explain_power_analysis(power: PowerAnalysis) → str`
  - Returns markdown with ⚡ What is power, 📊 Current status, ⚠️ What this means, ✅ Recommendation sections
  - Uses researcher-friendly language

- [X] T019 [US6] Implement analogy generation in `educational_content.py`:
  - Method: `generate_analogy(concept: str, value: float) → str`
  - Database: `ANALOGIES` dict mapping concepts (cohens_d, power, cliffs_delta) to value-specific analogies
  - Returns relatable real-world comparison

- [X] T020 [US6] Implement Quick Start Guide generation in `educational_content.py`:
  - Method: `generate_quick_start_guide(findings: StatisticalFindings) → str`
  - Returns markdown with: Where to Start, If You Want More Details, Skip sections, Icons legend, Key Terms glossary, Common Questions Q&A
  - Formatted as beginner-friendly navigation

- [X] T021 [US6] Implement glossary generation in `educational_content.py`:
  - Method: `generate_glossary() → str`
  - Returns markdown glossary of statistical terms with plain-language definitions
  - Includes: ANOVA, Bonferroni, Box Plot, Cliff's Delta, Cohen's d, CI, p-value, power, etc.

**Validation**: Run experiment and inspect `tmp/test_paper2/statistical_report_summary.md`:
- Every test has "What/Why/How" sections
- Emoji icons used (📚, 💡, 📊, ✅, ⚠️)
- Effect sizes have analogies
- Quick Start Guide at beginning
- Technical terms explained
- Reading level feels accessible (ask colleague to read)

**Checkpoint**: Educational content complete - non-statisticians can understand the reports

---

## Phase 6: User Story 3 Part A - Visualization Generation (Priority: P2)

**Goal**: Generate publication-quality statistical visualizations (box plots, violin plots, forest plots, Q-Q plots) as SVG files

**Independent Test**: Run paper generation and verify statistical figures generated in `output_dir/figures/statistical/`, render correctly as SVG, and show actual experiment data

### Implementation for User Story 3A

- [X] T022 [P] [US3] Create `src/paper_generation/statistical_visualizations.py` with `StatisticalVisualizationGenerator` class:
  - Constructor: `__init__(self, output_dir: str, style: str = "seaborn-v0_8-colorblind")`
  - Method: `_apply_publication_styling()` configuring matplotlib rcParams
  - Method: `_validate_output_path(output_path: str)`
  - Method: `_format_metric_label(metric_name: str) → str` (adds units)
  - Method: `_magnitude_to_color(magnitude: str) → str` (for forest plots)

- [X] T023 [US3] Implement box plot generation in `statistical_visualizations.py`:
  - Method: `generate_box_plot(metric_name, distributions) → Visualization`
  - Uses matplotlib boxplot with `showfliers=True`, `patch_artist=True`
  - Shows median, Q1/Q3, whiskers (1.5×IQR), outliers
  - Saves as SVG to `output_dir/figures/statistical/box_plot_{metric_name}.svg`

- [X] T024 [US3] Implement violin plot generation in `statistical_visualizations.py`:
  - Method: `generate_violin_plot(metric_name, distributions) → Visualization`
  - Uses seaborn violinplot with `inner='quartile'`, `palette='colorblind'`
  - Shows kernel density estimation + quartile lines
  - Saves as SVG to `output_dir/figures/statistical/violin_plot_{metric_name}.svg`

- [X] T025 [US3] Implement forest plot generation in `statistical_visualizations.py`:
  - Method: `generate_forest_plot(metric_name, effect_sizes) → Visualization`
  - Horizontal orientation (Y-axis = comparisons, X-axis = effect size)
  - Point estimates + error bars (95% CI)
  - Vertical reference line at 0
  - Color-coded by magnitude (green/orange/red/gray)
  - Saves as SVG to `output_dir/figures/statistical/forest_plot_{metric_name}.svg`

- [X] T026 [US3] Implement Q-Q plot generation in `statistical_visualizations.py`:
  - Method: `generate_qq_plot(metric_name, distribution, normality_test) → Visualization`
  - Uses `scipy.stats.probplot(values, dist="norm", plot=ax)`
  - 45-degree reference line
  - Subtitle with Shapiro-Wilk p-value
  - Annotation box (✅ Appears normal / ⚠️ Non-normal)
  - Saves as SVG to `output_dir/figures/statistical/qq_plot_{metric_name}_{framework}.svg`

- [X] T027 [US3] Implement batch visualization generation in `statistical_visualizations.py`:
  - Method: `generate_all_visualizations(findings: StatisticalFindings) → Dict[str, List[Visualization]]`
  - For each metric: generates box plot, violin plot, forest plot, Q-Q plots (one per framework)
  - Returns dict mapping metric_name → list of Visualization objects
  - Creates `output_dir/figures/statistical/` directory if needed

**Validation**: Run experiment and verify:
- `tmp/test_paper2/figures/statistical/*.svg` files created
- Open SVG files in browser - render correctly
- Box plots show median, quartiles, outliers
- Violin plots show distribution shapes
- Forest plots show effect sizes with CIs and 0-line
- Q-Q plots show normality assessment with p-values
- All plots use colorblind-friendly palette

**Checkpoint**: All visualization types generate correctly as publication-quality SVGs

---

## Phase 7: User Story 4 - Assumption Validation (Priority: P3)

**Goal**: Transparent reporting of statistical assumptions with diagnostic tests and recommendations when violated

**Independent Test**: Create datasets violating assumptions (skewed data, unequal variances) and verify report detects violations, reports diagnostics (Levene, Shapiro-Wilk), recommends alternatives

### Implementation for User Story 4

- [X] T028 [US4] Add skewness/kurtosis to `MetricDistribution` in `statistical_analyzer.py`:
  - Uses `scipy.stats.skew(values)` and `scipy.stats.kurtosis(values)`
  - Include in `compute_metric_distribution()` method
  - Add to distribution tables in report

- [X] T029 [US4] Add outlier detection to `compute_metric_distribution()`:
  - IQR method: values < Q1 - 1.5×IQR or > Q3 + 1.5×IQR
  - Store in `MetricDistribution.outliers` field
  - Count and report outliers per framework

- [X] T030 [US4] Add assumption violation recommendations:
  - In `run_variance_test()`: If Levene fails, recommend Welch's t-test or non-parametric
  - In `run_normality_test()`: If Shapiro-Wilk fails, suggest log transformation or non-parametric
  - Store recommendations in `AssumptionCheck.recommendation` field

**Validation**: Run experiment and check `tmp/test_paper2/statistical_report_full.md`:
- Skewness and kurtosis reported in descriptive statistics
- Outliers identified in box plots and tables
- Levene test results present for variance homogeneity
- Recommendations provided when assumptions violated (e.g., "Use Welch's t-test due to unequal variances")

**Checkpoint**: Assumption validation complete - violations detected and alternatives recommended

---

## Phase 8: User Story 5 - Reproducible Methodology Documentation (Priority: P3)

**Goal**: Complete documentation of statistical methods used for reproducibility and peer review

**Independent Test**: Review generated report's methodology section for completeness - lists tests, explains choices, documents significance levels and corrections, includes software versions

### Implementation for User Story 5

- [X] T031 [US5] Add metadata to `StatisticalFindings` in `analyze_experiment()`:
  - `metadata.analysis_date`: ISO 8601 timestamp
  - `metadata.scipy_version`: from `scipy.__version__`
  - `metadata.statsmodels_version`: from `statsmodels.__version__`
  - `metadata.random_seed`: bootstrap seed value
  - `metadata.alpha`: significance level (default 0.05)

- [X] T032 [US5] Generate methodology summary in `analyze_experiment()`:
  - `summary.methodology_text`: Pre-formatted text for paper Methodology section
  - Describes: Normality assessment (Shapiro-Wilk), test selection criteria, effect size measures, multiple comparison corrections, bootstrap CI method, significance threshold
  - Includes software versions and seed

**Validation**: Inspect `tmp/test_paper2/statistical_report_full.md`:
- "Statistical Methodology" section exists
- Documents all tests used (Shapiro-Wilk, t-test/Mann-Whitney, ANOVA/Kruskal-Wallis, Levene)
- Explains test selection rationale ("Used due to non-normal distribution...")
- States significance level (α=0.05)
- Documents corrections (Bonferroni for pairwise comparisons)
- Lists library versions (scipy, statsmodels, numpy)
- Documents bootstrap method (10,000 iterations, seed=42)

**Checkpoint**: Methodology documentation complete - analysis is fully reproducible

---

## Phase 9: User Story 3 Part B - Paper Integration (Priority: P2)

**Goal**: Automatically incorporate statistical artifacts into generated paper's Methodology, Results, and Discussion sections

**Independent Test**: Run full paper generation pipeline with `PaperGenerator.generate()` and verify paper includes: embedded statistical figures in Results, "Statistical Analysis" subsection in Methodology, effect sizes in Results text, power limitations in Discussion

### Implementation for User Story 3B

- [X] T033 [US3] Enhance `ExperimentAnalyzer.analyze()` in `src/paper_generation/experiment_analyzer.py`:
  - Import `StatisticalAnalyzer`, `StatisticalVisualizationGenerator`, `EducationalContentGenerator`
  - Instantiate analyzers with config and output_dir
  - Call `statistical_analyzer.analyze_experiment(run_data)` → get StatisticalFindings
  - Call `viz_generator.generate_all_visualizations(findings)` → create SVG files
  - Generate `statistical_report_summary.md` and `statistical_report_full.md` using findings and educational content
  - Return StatisticalFindings in analyzer's return value (or store for PaperGenerator access)

- [X] T034 [US3] Create report generation in `experiment_analyzer.py`:
  - Method: `_generate_statistical_report_summary(findings, educational_content) → str`
  - Markdown structure: Quick Start Guide, Executive Summary, Key Findings (with effect sizes), Critical Visualizations (3-5 embedded), Power Recommendations
  - Save to `output_dir/statistical_report_summary.md`

- [X] T035 [US3] Create full report generation in `experiment_analyzer.py`:
  - Method: `_generate_statistical_report_full(findings, educational_content) → str`
  - Markdown structure: Quick Start, Descriptive Statistics (with skew/kurtosis), Normality Assessment (with Q-Q plots), Assumption Validation (Levene), Statistical Comparisons (tests + effect sizes), Power Analysis, Statistical Methodology, Glossary
  - Embed ALL visualizations inline with educational captions
  - Save to `output_dir/statistical_report_full.md`

- [X] T036 [US3] Enhance `PaperGenerator._load_analyzed_data()` in `src/paper_generation/paper_generator.py`:
  - Read and parse `statistical_report_summary.md` from output_dir
  - Extract structured data into `self.statistical_data` dict with keys:
    - `comparisons`: List of {framework1, framework2, effect_size, ci, p_value, test_type}
    - `primary_metric`: str
    - `visualization_paths`: Dict[str, str] mapping viz types to relative paths
    - `power_warnings`: List[str]
    - `methodology_text`: str (for Methodology section)
    - `key_findings`: List[str] (for Results section)

- [X] T037 [US3] Enhance `PaperGenerator._generate_methodology_section()`:
  - Add "Statistical Analysis" subsection after existing content
  - Insert `self.statistical_data['methodology_text']` with formatting
  - Describe statistical tests, effect sizes, power analysis performed

- [X] T038 [US3] Enhance `PaperGenerator._generate_results_section()`:
  - When describing metric comparisons, include effect sizes and p-values from `self.statistical_data['comparisons']`
  - Embed at least 2 statistical visualizations: box plot for primary metric, forest plot for effect sizes
  - Use relative paths from `self.statistical_data['visualization_paths']`
  - Add figure captions with interpretation guidance

- [X] T039 [US3] Enhance `PaperGenerator._generate_discussion_section()`:
  - If `self.statistical_data['power_warnings']` exists, add "Statistical Limitations" paragraph
  - Mention achieved power and recommended sample sizes
  - Note implications for confidence in conclusions

**Validation**: Run full paper generation and inspect `tmp/test_paper2/paper.md`:
- Methodology section includes "Statistical Analysis" subsection describing tests
- Results section mentions effect sizes (e.g., "Cohen's d = 0.72, medium effect") not just means
- Results section embeds box plot: `![](figures/statistical/box_plot_execution_time.svg)`
- Results section embeds forest plot: `![](figures/statistical/forest_plot_execution_time.svg)`
- Discussion section includes power limitations if warnings exist
- Figure captions explain how to interpret plots
- If PDF generation works, verify both comparative charts AND statistical plots appear

**Checkpoint**: Paper integration complete - generated papers include comprehensive statistical content

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Final improvements affecting multiple user stories

- [X] T040 [P] Add error handling throughout statistical modules:
  - Raise `StatisticalAnalysisError` for critical failures (n<2, all values None)
  - Log warnings for non-critical issues (low power, assumption violations)
  - Graceful handling of edge cases (zero variance, tied ranks)

- [X] T041 Optimize performance for bootstrap resampling:
  - Vectorize with numpy operations
  - Profile with `cProfile` if bootstrap takes >2 seconds per metric
  - Consider reducing to 5,000 iterations if necessary

- [X] T042 [P] Update quickstart.md validation scenarios:
  - Add examples of running against target experiment
  - Document expected output structure
  - Provide interpretation examples

- [X] T043 Final validation against target experiment:
  - Clear `tmp/test_paper2/`
  - Run: `python src/main.py --experiment ~/projects/uece/baes/baes_benchmarking_20251028_0713 --output-dir tmp/test_paper2/`
  - Manually inspect ALL outputs using checklist in plan.md Development Workflow
  - Fix any issues revealed by real-world data

- [X] T044 [P] Documentation updates in `specs/011-enhance-statistical-report/`:
  - Update plan.md with any implementation deviations
  - Document any edge cases encountered in real experiment
  - Add examples from actual generated reports to quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup (T001-T003) - BLOCKS all user stories
- **User Stories (Phase 3-9)**: All depend on Foundational phase completion
  - **Priority order**: US1 (Phase 3) → US6 (Phase 5) → US2 (Phase 4) → US3A (Phase 6) → US3B (Phase 9) → US4 (Phase 7) → US5 (Phase 8)
  - **Recommended sequence** for single developer: P1 stories first (US1, US6), then P2 (US2, US3), then P3 (US4, US5)
- **Polish (Phase 10)**: Depends on all user stories being complete

### User Story Dependencies

- **US1 - Statistical Testing (P1)**: Can start after Foundational - No dependencies on other stories
- **US6 - Educational Content (P1)**: Can start after Foundational - No dependencies on other stories (can run parallel with US1)
- **US2 - Power Analysis (P2)**: Depends on US1 (needs EffectSize and StatisticalTest from US1)
- **US3A - Visualizations (P2)**: Depends on US1 (needs MetricDistribution and statistical test results)
- **US3B - Paper Integration (P2)**: Depends on US1, US6, US3A (needs StatisticalFindings, educational content, visualizations)
- **US4 - Assumption Validation (P3)**: Enhances US1 (adds to existing structures)
- **US5 - Methodology Documentation (P3)**: Depends on US1, US2 (documents what they do)

### Critical Path (Minimum for MVP)

To deliver minimum viable product:
1. Phase 1: Setup (T001-T003)
2. Phase 2: Foundational (T004-T005)
3. Phase 3: US1 - Statistical Testing (T006-T012) - Core statistical analysis
4. Phase 5: US6 - Educational Content (T015-T021) - Makes statistics understandable
5. Phase 6: US3A - Visualizations (T022-T027) - Visual representation
6. Phase 9: US3B - Paper Integration (T033-T039) - Delivers value in generated paper

This gives you: Statistical tests, effect sizes, educational explanations, visualizations, and paper integration.

### Parallel Opportunities

**Within Foundational Phase**:
- T004 (statistical helpers) and T005 (data models) can run in parallel if different developers

**Within US1**:
- T006 (StatisticalAnalyzer class) must complete first
- Then T007 (normality), T008 (variance), T009 (test selection) can run in parallel
- Then T010 (statistical tests), T011 (effect sizes), T012 (zero variance) sequential

**Within US6**:
- T015 (class + templates) must complete first
- Then T016-T021 can run in parallel (different methods)

**Across User Stories** (if multiple developers):
- US1 and US6 can run fully in parallel (independent P1 stories)
- Once US1 complete: US2, US3A, US4 can run in parallel
- US3B must wait for US1, US6, US3A completion
- US5 can run in parallel with US3B (both document completed work)

---

## Parallel Example: Phase 2 Foundational

```bash
# Developer 1:
Task T004: "Create statistical_helpers.py with bootstrap_ci, cohens_d, cliffs_delta, interpret_effect_size"

# Developer 2 (in parallel):
Task T005: "Implement data model entities (MetricDistribution, StatisticalTest, EffectSize, etc.) as dataclasses"

# Merge when both complete
```

---

## Parallel Example: User Story 6 (Educational Content)

```bash
# After T015 completes, all these can run in parallel:

# Developer 1:
Task T016: "Implement explain_statistical_test()"
Task T017: "Implement explain_effect_size()"

# Developer 2:
Task T018: "Implement explain_power_analysis()"
Task T019: "Implement generate_analogy()"

# Developer 3:
Task T020: "Implement generate_quick_start_guide()"
Task T021: "Implement generate_glossary()"

# Merge when all complete
```

---

## Implementation Strategy

### MVP First (Phases 1-3, 5, 6, 9)
Deliver core value: Statistical testing, educational content, visualizations, paper integration
- Estimated tasks: ~35 tasks
- Delivers: Fully functional statistical reports + enhanced papers

### Incremental Additions (Phases 4, 7, 8)
Add rigor: Power analysis, assumption validation, methodology documentation
- Estimated tasks: ~9 tasks
- Delivers: Publication-ready scientific rigor

### Polish (Phase 10)
Refinement: Error handling, performance, documentation
- Estimated tasks: ~5 tasks
- Delivers: Production quality

**Total Tasks**: 44 tasks (no test tasks - validation via real experiment only)

---

## Success Metrics

After completing all tasks, the following should be true:

✅ **Functionality**:
- Run `python src/main.py --experiment ~/projects/uece/baes/baes_benchmarking_20251028_0713 --output-dir tmp/test_paper2/` succeeds
- `tmp/test_paper2/statistical_report_summary.md` contains <300 lines with key findings, 3-5 visualizations, Quick Start Guide
- `tmp/test_paper2/statistical_report_full.md` contains 800-1200 lines with all statistical content, visualizations, glossary
- `tmp/test_paper2/figures/statistical/` contains box plots, violin plots, forest plots, Q-Q plots as SVG files
- `tmp/test_paper2/paper.md` includes statistical methodology, embedded visualizations, effect sizes in results, power limitations in discussion

✅ **Quality**:
- All statistical test selections are appropriate (parametric for normal, non-parametric for non-normal)
- Effect sizes calculated correctly (Cohen's d, Cliff's delta) with bootstrap CIs
- Power analysis recommends sample sizes for 80% power
- Educational explanations use 8th grade reading level (validated by colleague review)
- Visualizations render correctly in browser as SVGs
- Paper LaTeX/PDF compilation includes both comparative and statistical figures

✅ **Validation** (Manual Checklist from plan.md):
- [ ] Reports generated with no template placeholders
- [ ] Visualizations show actual experiment data (not empty/errors)
- [ ] p-values between 0 and 1
- [ ] Effect sizes have magnitude labels
- [ ] "What/Why/How" explanations present for all tests
- [ ] Quick Start Guide at beginning of summary report
- [ ] Paper includes statistical methodology subsection
- [ ] Paper Results mentions effect sizes
- [ ] Paper Discussion mentions power limitations (if warnings exist)

**Validation Time**: ~10 minutes per complete run to inspect all outputs

---

**Next Steps**: Begin with Phase 1 (Setup) to install dependencies, then Phase 2 (Foundational) to create data structures. After foundation is ready, implement US1 and US6 in parallel for maximum value delivery.
