# Implementation Plan: Fix Statistical Report Generation Issues

**Branch**: `012-fix-statistical-report` | **Date**: 2025-10-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/012-fix-statistical-report/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature fixes 9 critical statistical issues in the report generation system identified through external peer review:

**Primary Requirements**:
1. **Bootstrap CIs** (P1): Fix mathematically impossible confidence intervals where point estimates fall outside CI bounds
2. **Test Selection** (P1): Add Welch's ANOVA/t-test support for normal data with unequal variances  
3. **Power Analysis** (P1): Implement missing power analysis section with sample size recommendations
4. **Effect Size Alignment** (P2): Match effect size measure to test type (parametric=Cohen's d, non-parametric=Cliff's Delta)
5. **Multiple Comparisons** (P2): Apply Holm-Bonferroni correction when >1 comparison
6. **P-value Formatting** (P3): Use "p < 0.001" instead of "p = 0.0000" for small values
7. **Skewness Emphasis** (P3): Highlight median/IQR for |skewness| > 1.0 instead of mean/SD
8. **Neutral Language** (P3): Remove causal claims ("outperforms") from associative test interpretations

**Technical Approach**:
- Refactor bootstrap resampling to use independent group sampling (not combined array)
- Extend test selection logic to handle 3 cases: (normal+equal var), (normal+unequal var), (non-normal)
- Integrate statsmodels power analysis (TTestIndPower, FTestAnovaPower) with Section 5 report generation
- Add p-value formatter utility and multiple comparison correction wrapper
- Enhance existing StatisticalAnalyzer, DescriptiveStatistics, and EffectSize entities

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: SciPy ≥1.11.0, statsmodels ≥0.14.0, NumPy ≥1.24.0, pytest  
**Storage**: File-based (YAML configs, JSON run data, generated Markdown/LaTeX reports)  
**Testing**: pytest with existing test suite + new statistical validation tests  
**Target Platform**: Linux/macOS development environment, runs via CLI  
**Project Type**: Single project - statistical analysis library extension  
**Performance Goals**: Bootstrap CI <5s per comparison (n≤100), full report <3min (10 metrics × 3 groups)  
**Constraints**: Must maintain backward compatibility with existing report sections 1-7, no breaking API changes to public methods  
**Scale/Scope**: Affects ~1,563 lines in statistical_analyzer.py + 4 related modules, 41 functional requirements, estimated 11 hours implementation

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial Check (Pre-Phase 0)**: ✅ PASS

**Re-check After Phase 1 Design**: ✅ PASS

Verify compliance with BAEs Experiment Constitution v1.2.0:

- [x] **Scientific Reproducibility**: Fixed random seeds already in config, scipy/numpy versions pinned in requirements.txt, bootstrap uses configurable seed parameter
- [x] **Clarity & Transparency**: All modules have docstrings, statistical formulas documented with inline comments, API contracts specify all behaviors
- [x] **Open Science**: Existing code under CC BY 4.0, all dependencies are open-source (scipy, statsmodels, numpy)
- [x] **Minimal Dependencies**: Adding statsmodels (already lightweight, widely-used for power analysis and multiple testing), total dependency count remains minimal
- [N/A] **Deterministic HITL**: No human-in-loop needed for statistical calculations
- [x] **Reproducible Metrics**: Statistical tests are deterministic with fixed seeds, formulas clearly documented in research.md and data-model.md
- [N/A] **Version Control Integrity**: Not applicable (fixing internal statistical module, not framework integration)
- [x] **Automation-First**: All changes integrate with existing `python -m src.paper_generation.paper_generator` CLI, quickstart.md documents automated testing
- [x] **Failure Isolation**: Statistical errors fail-fast with clear exceptions (StatisticalAnalysisError), CI validation in __post_init__ enforces correctness
- [x] **Educational Accessibility**: research.md provides statistical background, quickstart.md has beginner-friendly testing guide, inline comments explain algorithms
- [x] **DRY Principle**: Extracted p-value formatter and CI validation into shared utilities (statistical_helpers.py), no code duplication in bootstrap methods
- [x] **No Backward Compatibility Burden**: Changes are internal implementation fixes, public APIs preserved with optional new parameters (all have defaults)
- [x] **Fail-Fast Philosophy**: Invalid CIs raise exceptions immediately (FR-002 validation), no silent fallbacks or degraded modes, clear error messages with exact values

**Gate Status After Design**: ✅ PASS - All applicable principles satisfied, design enhances constitution compliance

## Project Structure

### Documentation (this feature)

```
specs/012-fix-statistical-report/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (statistical best practices)
├── data-model.md        # Phase 1 output (enhanced entities)
├── quickstart.md        # Phase 1 output (testing & validation guide)
├── contracts/           # Phase 1 output (API contracts for modified methods)
│   └── statistical_analyzer_api.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── paper_generation/
│   ├── statistical_analyzer.py      # PRIMARY - Fix bootstrap CIs, add Welch's tests, power analysis
│   ├── statistical_helpers.py       # ENHANCE - Add p-value formatter, CI validation
│   ├── educational_content.py       # MODIFY - Update language to neutral, effect size explanations
│   ├── section_generator.py         # MODIFY - Add Power Analysis section (Section 5)
│   └── models.py                    # ENHANCE - Add PowerAnalysis, MultipleComparisonCorrection
├── utils/
│   └── statistical_helpers.py       # ENHANCE - Add utility functions (format_pvalue, validate_ci)
└── config/
    └── metrics_config.yaml          # No changes (config already supports all options)

tests/
├── unit/
│   ├── test_bootstrap_ci_fix.py           # NEW - Validate CIs contain point estimates
│   ├── test_welch_test_selection.py       # NEW - Verify correct test selection logic
│   ├── test_power_analysis.py             # NEW - Power calculation accuracy
│   ├── test_pvalue_formatting.py          # NEW - P-value display conventions
│   └── test_multiple_comparisons.py       # NEW - Holm-Bonferroni correction
├── integration/
│   └── test_phase9_statistical_fixes.py   # NEW - End-to-end validation (extends existing phase9 test)
└── fixtures/
    └── synthetic_data_distributions.py    # NEW - Generate known-distribution test data
```

**Structure Decision**: Single project structure maintained. This is a refactoring/bug-fix feature affecting existing statistical analysis modules within `src/paper_generation/`. No new top-level projects or services required. All changes are internal improvements to statistical calculation accuracy.

## Complexity Tracking

*No constitution violations - this section intentionally left empty.*

All changes comply with BAEs Constitution v1.2.0. This is a bug-fix and enhancement feature working within the existing single-project architecture using approved minimal dependencies (scipy, statsmodels, numpy, pytest).
