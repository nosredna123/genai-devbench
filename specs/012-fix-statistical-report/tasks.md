# Tasks: Fix Statistical Report Generation Issues

**Input**: Design documents from `/specs/012-fix-statistical-report/`  
**Branch**: `012-fix-statistical-report`  
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/statistical_analyzer_api.md

**Tests**: Test tasks are NOT included per feature specification - tests will be added in polish phase

**Organization**: Tasks grouped by user story (8 stories, priorities P1-P3) to enable independent implementation and testing

## Format: `[ID] [P?] [Story] Description`
- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1-US8)
- File paths use single-project structure (`src/`, `tests/`)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and dependency updates

- [X] T001 [P] Verify statsmodels ≥0.14.0, scipy ≥1.11.0, numpy ≥1.24.0 in `requirements.txt`
- [X] T002 [P] Add research.md, data-model.md, contracts/ references to `.specify/` tracking files

**Checkpoint**: Dependencies verified, documentation indexed

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core utilities and data models that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T003 [P] Add PowerAnalysis dataclass to `src/paper_generation/models.py` with all 15 fields per data-model.md
- [X] T004 [P] Add MultipleComparisonCorrection dataclass to `src/paper_generation/models.py` with all 10 fields per data-model.md
- [X] T005 [P] Create `format_pvalue()` utility in `src/utils/statistical_helpers.py` implementing APA 7th edition rules (FR-027 to FR-029)
- [X] T006 [P] Create `validate_ci()` utility in `src/utils/statistical_helpers.py` to check CI contains point estimate (FR-002)
- [X] T007 Enhance StatisticalTest dataclass in `src/paper_generation/statistical_analyzer.py` with 7 new fields (pvalue_raw, pvalue_adjusted, correction_method, test_rationale, assumptions_checked, achieved_power, recommended_n)
- [X] T008 Enhance EffectSize dataclass in `src/paper_generation/statistical_analyzer.py` with 4 new fields (bootstrap_iterations, ci_method, ci_valid, test_type_alignment) and add __post_init__ validation
- [X] T009 Enhance MetricDistribution dataclass in `src/paper_generation/statistical_analyzer.py` with 3 new fields (skewness_flag, primary_summary, summary_explanation) and add __post_init__ skewness classification

**Checkpoint**: Foundation ready - all data models defined, utilities available, user story implementation can begin in parallel

---

## Phase 3: User Story 1 - Accurate Confidence Intervals (Priority: P1) 🎯 MVP

**Goal**: Fix mathematically impossible bootstrap CIs where point estimates fall outside CI bounds

**Independent Test**: Generate statistical report with bootstrap effect sizes and verify every CI contains its point estimate (run validation from quickstart.md workflow 2)

### Implementation for User Story 1

- [X] T010 [US1] Refactor `_bootstrap_confidence_interval()` in `src/paper_generation/statistical_analyzer.py` (lines ~1112-1165) to use independent group resampling per contract specification
- [X] T011 [US1] Update `_bootstrap_confidence_interval()` to accept n_iterations parameter (default 10,000) and random_seed for reproducibility (FR-003)
- [X] T012 [US1] Modify `_bootstrap_confidence_interval()` to return 3-tuple (ci_lower, ci_upper, ci_valid) instead of 2-tuple
- [X] T013 [US1] Add CI validation in `_bootstrap_confidence_interval()` that raises StatisticalAnalysisError if ci_lower > point_estimate or ci_upper < point_estimate (FR-002)
- [X] T014 [US1] Update all callers of `_bootstrap_confidence_interval()` in StatisticalAnalyzer to handle new 3-tuple return and set EffectSize.ci_valid field
- [X] T015 [US1] Add fallback logic in `_bootstrap_confidence_interval()` for bootstrap failures (all samples identical) per FR-004 error handling

**Checkpoint**: Bootstrap CIs now mathematically valid with independent group resampling, all CIs contain point estimates

---

## Phase 4: User Story 2 - Appropriate Test Selection (Priority: P1)

**Goal**: Select statistical test matching data characteristics (normality + variance equality) using three-way decision tree

**Independent Test**: Generate reports for synthetic datasets with known characteristics (normal/equal-var, normal/unequal-var, non-normal) and verify correct test selection (quickstart.md workflow 3)

### Implementation for User Story 2

- [X] T016 [US2] Implement `_select_statistical_test()` method in `src/paper_generation/statistical_analyzer.py` per contract specification with three-way logic
- [X] T017 [US2] Add Shapiro-Wilk normality check (scipy.stats.shapiro) for each group in `_select_statistical_test()` with alpha=0.05 threshold (FR-005)
- [X] T018 [US2] Add Levene's variance equality test (scipy.stats.levene) in `_select_statistical_test()` with alpha=0.05 threshold (FR-005)
- [X] T019 [US2] Implement pairwise (k=2) decision tree: normal+equal→T_TEST, normal+unequal→WELCH_T, non-normal→MANN_WHITNEY (FR-009 to FR-011)
- [X] T020 [US2] Implement multi-group (k≥3) decision tree: normal+equal→ANOVA, normal+unequal→WELCH_ANOVA, non-normal→KRUSKAL_WALLIS (FR-006 to FR-008)
- [X] T021 [US2] Add scipy.stats Welch's ANOVA implementation (use custom f_oneway with equal_var=False or statsmodels) for WELCH_ANOVA case (FR-007)
- [X] T022 [US2] Update `_perform_statistical_test()` in StatisticalAnalyzer to call `_select_statistical_test()` and set test_rationale field (FR-012)
- [X] T023 [US2] Populate StatisticalTest.assumptions_checked dict with {normality: bool, equal_variance: bool} from selection logic

**Checkpoint**: Test selection now uses three-way logic, Welch's tests available for normal+unequal variance scenarios

---

## Phase 5: User Story 3 - Power Analysis Insights (Priority: P1)

**Goal**: Implement missing power analysis section with achieved power for each test and sample size recommendations

**Independent Test**: Generate full report and verify dedicated "Power Analysis" section appears with power metrics and recommendations (quickstart.md workflow 4)

### Implementation for User Story 3

- [X] T024 [US3] Implement `_calculate_power_analysis()` method in `src/paper_generation/statistical_analyzer.py` per contract specification (NEW METHOD)
- [X] T025 [US3] Add TTestIndPower calculations in `_calculate_power_analysis()` for T_TEST, WELCH_T, MANN_WHITNEY test types using statsmodels (FR-016, FR-019)
- [X] T026 [US3] Add FTestAnovaPower calculations in `_calculate_power_analysis()` for ANOVA, WELCH_ANOVA, KRUSKAL_WALLIS test types using statsmodels (FR-016, FR-019)
- [X] T027 [US3] Implement solve_power for achieved power calculation in `_calculate_power_analysis()` given effect size and sample sizes
- [X] T028 [US3] Implement solve_power for recommended_n calculation in `_calculate_power_analysis()` when achieved_power < target_power (default 0.80) (FR-018)
- [X] T029 [US3] Add error handling in `_calculate_power_analysis()` for edge cases: n<5 (indeterminate), extreme effect sizes (d>5)
- [X] T030 [US3] Update `_perform_statistical_test()` to call `_calculate_power_analysis()` after each test and populate StatisticalTest.achieved_power, recommended_n, power_adequate fields
- [X] T031 [US3] Create `_generate_power_analysis_section()` method in `src/paper_generation/section_generator.py` that produces Section 5 markdown/LaTeX (FR-017)
- [X] T032 [US3] Add power analysis table to `_generate_power_analysis_section()` showing comparison_id, effect_size, achieved_power, adequacy_flag for all tests
- [X] T033 [US3] Add sample size recommendations subsection to `_generate_power_analysis_section()` showing recommended_n when power < 0.80 (FR-018)
- [X] T034 [US3] Update `generate_full_report()` in section_generator.py to include Section 5 (Power Analysis) after Section 4 (Effect Sizes)

**Checkpoint**: Power analysis fully implemented with dedicated report section, achieved power calculated for all tests, sample size recommendations provided

---

## Phase 6: User Story 4 - Aligned Effect Sizes (Priority: P2)

**Goal**: Match effect size measure to statistical test type (parametric→Cohen's d, non-parametric→Cliff's Delta)

**Independent Test**: Generate reports for various data types and verify effect size measure always matches test type used (parametric tests use Cohen's d, non-parametric use Cliff's Delta)

### Implementation for User Story 4

- [X] T035 [US4] Create `_select_effect_size_measure()` method in `src/paper_generation/statistical_analyzer.py` that returns COHENS_D for parametric tests, CLIFFS_DELTA for non-parametric (FR-013, FR-014)
- [X] T036 [US4] Update effect size calculation logic in StatisticalAnalyzer to call `_select_effect_size_measure()` based on TestType from `_select_statistical_test()`
- [X] T037 [US4] Add validation in effect size calculation that raises error if measure doesn't align with test type (FR-015)
- [X] T038 [US4] Set EffectSize.test_type_alignment field to match the TestType used in the comparison
- [X] T039 [US4] Update `_generate_effect_size_interpretation()` in educational_content.py to reference correct measure (d vs δ) based on test type (FR-015)

**Checkpoint**: Effect size measures now strictly aligned with test types, no more Cohen's d with Kruskal-Wallis

---

## Phase 7: User Story 5 - Multiple Comparison Corrections (Priority: P2)

**Goal**: Apply Holm-Bonferroni correction to control family-wise error rate when multiple comparisons performed

**Independent Test**: Generate report with 10+ comparisons and verify adjusted p-values appear with correction method documented (both raw and adjusted p-values visible)

### Implementation for User Story 5

- [X] T040 [US5] Implement `_apply_multiple_comparison_correction()` method in `src/paper_generation/statistical_analyzer.py` per contract specification (NEW METHOD)
- [X] T041 [US5] Add statsmodels.stats.multitest.multipletests call in `_apply_multiple_comparison_correction()` with method="holm" (FR-022)
- [X] T042 [US5] Add conditional logic in `_apply_multiple_comparison_correction()` to skip correction if n_comparisons == 1, set method="none" (FR-026)
- [X] T043 [US5] Add validation in `_apply_multiple_comparison_correction()` that raises error if correction method is "none" when n_comparisons > 1
- [X] T044 [US5] Update `_perform_all_statistical_tests()` in StatisticalAnalyzer to group tests by metric family and call `_apply_multiple_comparison_correction()` per family
- [X] T045 [US5] Populate StatisticalTest.pvalue_raw, pvalue_adjusted, correction_method fields from MultipleComparisonCorrection results
- [X] T046 [US5] Update significance decisions to use pvalue_adjusted instead of raw pvalue when correction applied (FR-023)
- [X] T047 [US5] Update statistical test results tables in section_generator.py to display both raw and adjusted p-values when correction applied (FR-024)
- [X] T048 [US5] Add methodology subsection explaining Holm-Bonferroni correction with citation (Holm 1979) in `_generate_methods_section()` when correction applied (FR-025)

**Checkpoint**: Multiple comparison corrections applied via Holm-Bonferroni, both raw and adjusted p-values reported, methodology documented

---

## Phase 8: User Story 6 - Professional P-value Formatting (Priority: P3)

**Goal**: Format p-values according to APA 7th edition conventions (p < 0.001 for very small values, not "0.0000")

**Independent Test**: Generate reports and grep for "p = 0.0000" (should find zero instances), verify all p-values follow APA format

### Implementation for User Story 6

- [X] T049 [US6] Update all p-value display locations in `src/paper_generation/section_generator.py` to use `format_pvalue()` utility (FR-027)
- [X] T050 [US6] Update statistical test result tables to format p-values using `format_pvalue()` (FR-028)
- [X] T051 [US6] Update interpretation text generation to format p-values using `format_pvalue()` (FR-029)
- [X] T052 [US6] Search codebase for hardcoded p-value formatting patterns (f"{p:.3f}", f"{p:.4f}") and replace with `format_pvalue()` calls
- [X] T053 [US6] Update educational content templates in `src/paper_generation/educational_content.py` to use `format_pvalue()` for example p-values

**Checkpoint**: All p-values formatted consistently per APA 7th edition, zero instances of "p = 0.0000"

---

## Phase 9: User Story 7 - Emphasis on Robust Summary Statistics (Priority: P3)

**Goal**: Emphasize median/IQR over mean/SD for highly skewed metrics (|skewness| > 1.0)

**Independent Test**: Generate report for highly skewed metric and verify median/IQR are prominently featured in summary tables and interpretation text

### Implementation for User Story 7

- [X] T054 [US7] Update descriptive statistics table generation in section_generator.py to bold median/IQR when MetricDistribution.primary_summary == "median" (FR-032)
- [X] T055 [US7] Update descriptive statistics table generation to bold mean/SD when MetricDistribution.primary_summary == "mean"
- [X] T056 [US7] Update interpretation text in `_generate_descriptive_interpretation()` to mention median first when primary_summary == "median" (FR-033)
- [X] T057 [US7] Update interpretation text to mention mean first when primary_summary == "mean"
- [X] T058 [US7] Add skewness warning note in descriptive statistics section when MetricDistribution.skewness_flag == "severe" explaining why median preferred (FR-034)
- [X] T059 [US7] Update educational content in educational_content.py to explain median vs mean choice based on skewness thresholds

**Checkpoint**: Summary statistics emphasis now driven by skewness, median/IQR highlighted for skewed distributions

---

## Phase 10: User Story 8 - Neutral Statistical Language (Priority: P3)

**Goal**: Use descriptive comparative language ("differs from") instead of causal language ("outperforms") in interpretations

**Independent Test**: Generate report and grep for causal terms (outperforms, is better, beats) - should find zero instances, all language is neutral/descriptive

### Implementation for User Story 8

- [X] T060 [US8] Update `_get_interpretation_language()` in educational_content.py per contract specification with neutral phrase dictionary (FR-035 to FR-038)
- [X] T061 [US8] Replace "outperforms" with "shows higher values than" in all interpretation templates (FR-035)
- [X] T062 [US8] Replace "is better than" with "differs from" or "exceeds" in effect size interpretations (FR-036)
- [X] T063 [US8] Update Cliff's Delta = ±1.000 interpretation to "all observed values in group X exceed those in group Y" instead of "100% certain X beats Y" (FR-037)
- [X] T064 [US8] Update non-significant result interpretation to "insufficient evidence to detect difference" when power < 0.80, avoid "no effect exists" (FR-038)
- [X] T065 [US8] Audit all prose generation methods in section_generator.py and educational_content.py for causal language, replace with neutral phrases
- [X] T066 [US8] Update interpretation templates to reference distributional differences not performance superiority

**Checkpoint**: All interpretations use neutral descriptive language, zero causal claims in associative test reports

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Testing, validation, documentation, and final integration

- [ ] T067 [P] Create `tests/unit/test_bootstrap_ci_fix.py` validating FR-001 to FR-004 (independent resampling, CI validity)
- [ ] T068 [P] Create `tests/unit/test_welch_test_selection.py` validating FR-005 to FR-012 (three-way decision tree)
- [ ] T069 [P] Create `tests/unit/test_power_analysis.py` validating FR-016 to FR-021 (statsmodels integration)
- [X] T070 [P] Create `tests/unit/test_pvalue_formatting.py` validating FR-027 to FR-029 (APA conventions) ✅ **14/14 PASSED**
- [ ] T071 [P] Create `tests/unit/test_multiple_comparisons.py` validating FR-022 to FR-026 (Holm-Bonferroni)
- [ ] T072 [P] Create `tests/unit/test_effect_size_alignment.py` validating FR-013 to FR-015 (parametric/non-parametric matching)
- [ ] T073 [P] Create `tests/unit/test_skewness_emphasis.py` validating FR-030 to FR-034 (median/IQR emphasis)
- [X] T074 [P] Create `tests/unit/test_neutral_language.py` validating FR-035 to FR-038 (descriptive phrases) ✅ **14/14 PASSED**
- [ ] T075 Create `tests/integration/test_statistical_report_fixes.py` end-to-end validation of all 8 user stories with synthetic datasets
- [ ] T076 Create `tests/fixtures/synthetic_data_distributions.py` with normal/equal-var, normal/unequal-var, non-normal, skewed test data
- [ ] T077 Run quickstart.md validation workflows (5 workflows) and verify all success criteria met
- [ ] T078 [P] Update `docs/metrics.md` with power analysis section documentation
- [ ] T079 [P] Update `CHANGELOG.md` with Feature 012 summary (9 fixes, statsmodels dependency)
- [ ] T080 Code review and refactoring pass for statistical_analyzer.py (ensure no regressions)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - **BLOCKS all user stories**
- **User Stories (Phase 3-10)**: All depend on Foundational phase completion
  - US1 (Bootstrap CIs) can start immediately after Phase 2
  - US2 (Test Selection) can start immediately after Phase 2
  - US3 (Power Analysis) depends on US1 and US2 completion (needs working tests + effect sizes)
  - US4 (Effect Size Alignment) depends on US2 completion (needs test selection logic)
  - US5 (Multiple Comparisons) can start after Phase 2 (independent of other stories)
  - US6 (P-value Formatting) can start after Phase 2 (independent of other stories)
  - US7 (Skewness Emphasis) can start after Phase 2 (independent of other stories)
  - US8 (Neutral Language) can start after Phase 2 (independent of other stories)
- **Polish (Phase 11)**: Depends on all P1/P2 user stories complete (US1-US5), P3 stories optional

### User Story Dependencies

```
Phase 2 (Foundation)
    ├─> US1 (Bootstrap CIs) [P1] ──┐
    ├─> US2 (Test Selection) [P1] ─┼─> US3 (Power Analysis) [P1] ──> Polish
    ├─> US4 (Effect Size Alignment) [P2] ─────────────────────────┘
    ├─> US5 (Multiple Comparisons) [P2] ──────────────────────────> Polish
    ├─> US6 (P-value Formatting) [P3] ─────────────────────────────> Polish (optional)
    ├─> US7 (Skewness Emphasis) [P3] ──────────────────────────────> Polish (optional)
    └─> US8 (Neutral Language) [P3] ───────────────────────────────> Polish (optional)
```

### Critical Path (Minimum for MVP)

1. Phase 1 (Setup) - 30 minutes
2. Phase 2 (Foundational) - 2 hours
3. Phase 3 (US1 - Bootstrap CIs) - 2 hours
4. Phase 4 (US2 - Test Selection) - 2 hours  
5. Phase 5 (US3 - Power Analysis) - 3 hours
6. Phase 6 (US4 - Effect Size Alignment) - 1.5 hours
7. Phase 7 (US5 - Multiple Comparisons) - 2 hours
8. Phase 11 (Polish - P1/P2 tests only) - 2 hours

**Total MVP Time**: ~15 hours (covers all P1 and P2 user stories)

### Parallel Opportunities

**Within Phase 2 (Foundational)**:
- T003, T004, T005, T006 can all run in parallel (different new files)
- T007, T008, T009 sequential (same file statistical_analyzer.py)

**After Phase 2 Completes**:
- US1 (T010-T015), US2 (T016-T023), US5 (T040-T048), US6 (T049-T053), US7 (T054-T059), US8 (T060-T066) can all start in parallel
- US3 must wait for US1 + US2
- US4 must wait for US2

**Within Phase 11 (Polish)**:
- All unit test creation (T067-T074) can run in parallel
- T078, T079 can run in parallel with tests
- T075-T077, T080 are sequential (depend on implementation complete)

---

## Parallel Example: After Foundation Complete

**Launch these user stories simultaneously** (if team capacity allows):

```bash
# Developer 1: Bootstrap CIs (US1)
Task: "Refactor _bootstrap_confidence_interval() with independent resampling"
Files: src/paper_generation/statistical_analyzer.py (lines 1112-1165)

# Developer 2: Test Selection (US2)  
Task: "Implement _select_statistical_test() with three-way logic"
Files: src/paper_generation/statistical_analyzer.py (new method)

# Developer 3: Multiple Comparisons (US5)
Task: "Implement _apply_multiple_comparison_correction()"
Files: src/paper_generation/statistical_analyzer.py (new method)

# Developer 4: P-value Formatting (US6)
Task: "Replace all p-value formatting with format_pvalue() calls"
Files: src/paper_generation/section_generator.py

# Developer 5: Skewness Emphasis (US7)
Task: "Update tables to bold median/IQR when primary_summary=median"
Files: src/paper_generation/section_generator.py

# Developer 6: Neutral Language (US8)
Task: "Update _get_interpretation_language() with neutral phrases"
Files: src/paper_generation/educational_content.py
```

**After US1 + US2 complete, Developer 1 can start US3 (Power Analysis)**

---

## Implementation Strategy

### MVP Scope (Recommended First Deliverable)

**Include**: User Stories 1-5 (all P1 and P2 priorities)
- US1: Accurate Bootstrap CIs (P1) - Critical mathematical fix
- US2: Appropriate Test Selection (P1) - Essential statistical rigor
- US3: Power Analysis Insights (P1) - Critical for result interpretation
- US4: Aligned Effect Sizes (P2) - Important methodological consistency
- US5: Multiple Comparison Corrections (P2) - Important for credibility

**Estimated MVP Time**: ~15 hours

**MVP Validation**: Run quickstart.md workflows 1-4, verify all P1/P2 success criteria met

### Phase 2 Enhancement (Optional Quality Improvements)

**Include**: User Stories 6-8 (all P3 priorities)
- US6: Professional P-value Formatting (P3) - Publication polish
- US7: Emphasis on Robust Statistics (P3) - Improved data quality communication  
- US8: Neutral Statistical Language (P3) - Scientific accuracy

**Estimated Phase 2 Time**: +4 hours

**Total Feature Time**: ~19 hours (complete implementation)

### Incremental Delivery Plan

1. **Week 1**: Phases 1-2 (Foundation) + US1-US2 → Working bootstrap + test selection
2. **Week 2**: US3-US5 → Complete MVP (all P1/P2 stories)
3. **Week 3**: US6-US8 + Polish → Full feature with all enhancements

---

## Task Summary

- **Total Tasks**: 80
- **Setup Tasks**: 2 (Phase 1)
- **Foundational Tasks**: 7 (Phase 2)
- **User Story 1 Tasks**: 6 (Bootstrap CIs - P1)
- **User Story 2 Tasks**: 8 (Test Selection - P1)
- **User Story 3 Tasks**: 11 (Power Analysis - P1)
- **User Story 4 Tasks**: 5 (Effect Size Alignment - P2)
- **User Story 5 Tasks**: 9 (Multiple Comparisons - P2)
- **User Story 6 Tasks**: 5 (P-value Formatting - P3)
- **User Story 7 Tasks**: 6 (Skewness Emphasis - P3)
- **User Story 8 Tasks**: 7 (Neutral Language - P3)
- **Polish Tasks**: 14 (Phase 11)

**Parallel Opportunities**: 25 tasks marked [P] can run in parallel with others

**Independent Test Criteria**: Each user story has clear validation criteria from quickstart.md

**Suggested MVP Scope**: User Stories 1-5 (39 implementation tasks + 7 foundational = 46 tasks total for MVP)
