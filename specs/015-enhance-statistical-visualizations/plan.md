# Implementation Plan: Enhanced Statistical Visualizations for Paper Generation

**Branch**: `015-enhance-statistical-visualizations` | **Date**: 2025-10-30 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/015-enhance-statistical-visualizations/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Enhance the paper generation module with 8 new publication-quality statistical visualizations that move beyond "they differ" to show "why and how strongly they differ." The feature adds effect-size panel plots, cost-performance efficiency analysis, token-to-cost regressions, distribution overlap plots, normalized cost comparisons, multi-metric rankings, coefficient of variation stability analysis, and outlier impact visualizations. All plots are SVG-based (300 DPI), colorblind-friendly, and designed for scientific papers (IEEE/ACM/Springer standards). Technical approach: extend existing `StatisticalVisualizationGenerator` class with new methods using matplotlib/seaborn faceting, regression fitting via scipy/statsmodels, and edge-case handling for zero variance, n=1 groups, and missing data.

## Technical Context

**Language/Version**: Python 3.11+ (matching existing genai-devbench codebase)  
**Primary Dependencies**: matplotlib ≥3.5, seaborn ≥0.12, scipy ≥1.11, numpy ≥1.24, pandas (for data manipulation), statsmodels (for regression statistics)  
**Storage**: File-based (SVG files in `{output_dir}/figures/statistical/`, metadata in Visualization objects)  
**Testing**: pytest with >90% coverage target, integration tests with sample experiment data  
**Target Platform**: Linux/macOS/Windows (platform-independent Python)
**Project Type**: Single project - extension of existing paper generation module  
**Performance Goals**: <5 seconds per plot type for experiments with ≤100 runs per framework, <30 seconds total for all 8 plots  
**Constraints**: SVG files <2 MB each, memory usage <500 MB during batch generation, WCAG 2.1 colorblind-accessible palettes  
**Scale/Scope**: Support up to 10 metrics × 5 frameworks (50 pairwise comparisons in effect-size panel), 500 total data points per plot

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with BAEs Experiment Constitution v1.2.0:

- [x] **Scientific Reproducibility**: Visualizations are deterministic (same data → same SVG). No randomness in plot generation. matplotlib random seed fixed in styling.
- [x] **Clarity & Transparency**: All new methods have docstrings (FR NFR-003). Plot captions self-documenting (SC-008). Edge cases annotated in plots.
- [x] **Open Science**: No proprietary dependencies. Uses open-source matplotlib/seaborn. Output is SVG (open standard).
- [x] **Minimal Dependencies**: Extends existing dependencies (matplotlib, seaborn, scipy already in requirements.txt). No new heavyweight frameworks.
- [N/A] **Deterministic HITL**: Not applicable - visualization generation is fully automated, no human-in-loop clarifications.
- [N/A] **Reproducible Metrics**: Not applicable - this feature visualizes metrics, doesn't compute them. Metrics already verified in StatisticalAnalyzer.
- [N/A] **Version Control Integrity**: Not applicable - visualizations are outputs, not framework code being tested.
- [x] **Automation-First**: Batch generation via single method call (FR-015). Integrates into existing paper generation pipeline.
- [x] **Failure Isolation**: Each visualization saves to unique file path. No shared state between plot generations. Failures in one plot don't affect others.
- [x] **Educational Accessibility**: Plot captions explain what each visualization shows (SC-008). Color-coded magnitudes use standard conventions (SC-009). Code follows PEP 8 (NFR-003).
- [x] **DRY Principle**: Shared styling in `_apply_publication_styling()`. Common utilities (`_format_metric_label`, `_magnitude_to_color`). No duplication across plot methods.
- [x] **No Backward Compatibility Burden**: New methods in existing class. No changes to existing box/violin/forest/QQ plot interfaces. Can evolve independently.
- [x] **Fail-Fast Philosophy**: Edge cases raise exceptions or annotate plots with warnings (FR-014). No silent failures or fallback defaults. Log-scale with zeros → explicit error or symlog.

**Constitution Compliance**: PASS ✅  
**Violations Requiring Justification**: None  
**Re-check After Phase 1**: Required to verify data model and contracts maintain compliance

## Project Structure

### Documentation (this feature)

```
specs/015-enhance-statistical-visualizations/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output: matplotlib faceting, regression best practices
├── data-model.md        # Phase 1 output: Visualization entity structures
├── quickstart.md        # Phase 1 output: How to generate new plot types
├── contracts/           # Phase 1 output: Method signatures for 8 new visualization methods
│   └── visualization_api.yaml  # OpenAPI-style interface documentation
└── checklists/
    └── requirements.md  # Already created - spec quality validation
```

### Source Code (repository root)

```
src/paper_generation/
├── statistical_visualizations.py    # EXTENDS: Add 8 new methods to StatisticalVisualizationGenerator
├── statistical_analyzer.py          # UNCHANGED: Provides input data (EffectSize, MetricDistribution)
├── models.py                         # POSSIBLY EXTENDS: May add new Visualization subclasses if needed
└── exceptions.py                     # UNCHANGED: Existing exception types sufficient

docs/
└── paper_generation/
    └── visualization_gallery.md       # NEW: Visual examples of all 8 plot types with use cases (post-implementation)
```

**Structure Decision**: Single project structure. This is an extension to the existing `src/paper_generation/` module, specifically adding methods to `StatisticalVisualizationGenerator` class. No new modules or packages needed—all 8 visualization types are methods in the existing class following the pattern of `generate_box_plot()`, `generate_violin_plot()`, etc.

**Testing approach**: Manual validation via real paper generation using existing experiment data at project completion.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**No violations detected.** All constitutional principles are satisfied by this feature design.

---

## Phase Completion Summary

### ✅ Phase 0: Outline & Research (COMPLETE)

**Artifacts Generated**:
- ✅ `research.md` - 8 research tasks resolving technical unknowns
  - R1: Matplotlib faceting (plt.subplots with shared axes)
  - R2: Complete separation markers (open circles, no error bars)
  - R3: Log-scale for zeros (SymLogScale with linthresh=1.0)
  - R4: Regression annotations (ax.text with transAxes coordinates)
  - R5: CV edge cases (return np.nan, annotate "N/A")
  - R6: Color accessibility (seaborn colorblind + WCAG verification)
  - R7: Memory management (plt.close in finally blocks)
  - R8: Outlier detection (1.5×IQR consistency with box plots)

**Key Decisions**:
- Use `plt.subplots()` for faceting (fine control, no new deps)
- SymLogScale for log-transformed data with zeros
- Fail-fast for undefined CV (mean=0) rather than fallback values
- 1.5×IQR outlier detection for consistency with existing box plots

---

### ✅ Phase 1: Design & Contracts (COMPLETE)

**Artifacts Generated**:
- ✅ `data-model.md` - Entity definitions and validation rules
  - Extended VisualizationType enum with 8 new values
  - Defined derived structures: RegressionResult, RankData, StabilityMetric, OutlierInfo
  - Documented edge case handling in data model
- ✅ `contracts/visualization_api.md` - Method signatures for 8 new methods
  - generate_effect_size_panel()
  - generate_efficiency_plot()
  - generate_regression_plot()
  - generate_overlap_plot()
  - generate_normalized_cost_plot()
  - generate_rank_plot()
  - generate_stability_plot()
  - generate_outlier_run_plot()
  - generate_all_enhanced_visualizations() (batch method)
- ✅ `quickstart.md` - Getting started guide with examples
- ✅ Agent context updated via `.specify/scripts/bash/update-agent-context.sh copilot`

**Constitution Re-Check**: ✅ PASS
- All constitutional principles maintained through design phase
- No backward compatibility burden introduced
- Fail-fast error handling in contracts
- DRY maintained through shared utilities

---

### ✅ Redundancy Analysis & Design Decisions (COMPLETE)

**Analysis Date**: 2025-10-30

After analyzing the existing 4 visualization methods, the following design decisions were confirmed:

1. **Effect-size panel + Forest plots**: **KEEP BOTH**
   - **Effect-size panel**: Multi-metric faceted overview for cross-metric comparison
   - **Forest plot**: Per-metric detailed view with confidence intervals
   - **Rationale**: Different granularities serve complementary purposes

2. **Overlap + Violin plots**: **KEEP BOTH**
   - **Overlap plot**: 2-way focused comparison with overlap coefficients and small effect detection
   - **Violin plot**: 3+ group general distribution comparison
   - **Rationale**: Different use cases (nuanced 2-way vs general multi-way)

3. **Normalized cost + Box plots**: **KEEP BOTH**
   - **Normalized cost**: Derived efficiency metric (cost per unit output)
   - **Box plot**: Raw cost distributions
   - **Rationale**: Different metrics (efficiency vs absolute values)

4. **Batch method strategy**: **TWO SEPARATE METHODS**
   - `generate_all_visualizations()`: Existing 4 plots (box, violin, forest, qq)
   - `generate_all_enhanced_visualizations()`: New 8 plots (effect panel, efficiency, regression, overlap, normalized cost, rank, stability, outlier run)
   - **Rationale**: Clean separation, backward compatibility, opt-in for enhanced features

5. **Default paper generator behavior**: **ALL 12 PLOTS ALWAYS**
   - Paper generator will invoke both batch methods
   - Total output: 12 visualization types per paper generation run
   - **Rationale**: Comprehensive analysis suite for scientific papers

**Implementation Impact**:
- **No deletions**: All existing methods remain unchanged
- **No updates**: Existing methods retain their current behavior
- **Pure addition**: 8 new methods + 1 new batch method added
- **Total methods**: 12 visualization methods + 2 batch methods

---

## Next Steps

**Command to continue**: `/speckit.tasks`

This will:
1. Break down the 8 visualization methods into implementable tasks
2. Assign priorities based on user story rankings (P1, P2, P3)
3. Define acceptance criteria per task
4. Estimate complexity and dependencies

**Estimated Implementation Timeline** (after tasks phase):
- **Week 1**: P1 visualizations (effect-size panel, efficiency plot) - core implementation
- **Week 2**: P2 visualizations (regression, overlap, normalized cost) - analytical plots
- **Week 3**: P3 visualizations (rank, stability, outlier runs) - supplementary plots
- **Week 4**: Documentation, edge case refinement, real paper generation validation

**Total Effort**: ~4 weeks (assuming 1 developer, part-time 50%)

**Validation**: Single comprehensive test at end using real experiment data from `~/projects/uece/baes/baes_benchmarking_20251028_0713`

---

## Implementation Notes for Developer

### Extension Points
1. **New plot types**: Add to VisualizationType enum, implement generate_X_plot() method
2. **Custom color schemes**: Override in _apply_publication_styling()
3. **New derived metrics**: Define in data-model.md, compute in method

### Testing Strategy
**Validation approach**: Real paper generation with actual experiment data (post-implementation)
- Manual validation of all 8 plot types with BAEs vs ChatDev vs GHSpec data
- Visual inspection of SVG outputs for publication quality
- Edge case verification through diverse experiment scenarios

### Documentation Requirements
1. **Docstrings**: Google style for all new methods (NFR-003)
2. **Examples**: Add to quickstart.md for each plot type
3. **Gallery**: Create visualization_gallery.md with rendered examples
4. **Paper integration**: Document in paper generation workflow

---

**Planning Phase Complete** ✅  
**Ready for**: Task breakdown (`/speckit.tasks`) and implementation
