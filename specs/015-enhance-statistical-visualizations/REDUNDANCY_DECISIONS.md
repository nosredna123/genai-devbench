# Redundancy Analysis & Design Decisions

**Date**: 2025-10-30  
**Feature**: 015-enhance-statistical-visualizations  
**Context**: Analysis of relationship between existing 4 visualization methods and new 8 methods

---

## Executive Summary

After comprehensive analysis, **NO TRUE REDUNDANCY** was found between existing and new visualization methods. All methods serve complementary purposes with different granularities, focuses, or metrics. The implementation will be **purely additive** with no deletions or modifications to existing code.

---

## Decision Matrix

| Question | Decision | Rationale |
|----------|----------|-----------|
| Effect-size panel + Forest plots | **KEEP BOTH** | Different granularities: panel for cross-metric overview, forest for per-metric detail |
| Overlap + Violin plots | **KEEP BOTH** | Different use cases: overlap for 2-way nuanced comparison, violin for 3+ way general |
| Normalized cost + Box plots | **KEEP BOTH** | Different metrics: normalized for efficiency, box for absolute values |
| Batch method strategy | **TWO SEPARATE** | `generate_all_visualizations()` (4 existing) + `generate_all_enhanced_visualizations()` (8 new) |
| Default paper generation | **ALL 12 PLOTS** | Comprehensive analysis suite invokes both batch methods |

---

## Detailed Analysis

### 1. Effect-Size Panel vs Forest Plot

**Existing**: `generate_forest_plot(metric: str)`
- **Scope**: Single metric at a time
- **Purpose**: Detailed per-metric effect size visualization with CIs
- **Use case**: Deep dive into specific metric comparisons

**New**: `generate_effect_size_panel(effect_sizes: Dict[str, List[EffectSize]])`
- **Scope**: All metrics in faceted grid
- **Purpose**: Cross-metric overview for comparative analysis
- **Use case**: Quick identification of strong effects across metrics

**Verdict**: **COMPLEMENTARY** - Different granularities, both needed for comprehensive analysis

---

### 2. Overlap Plot vs Violin Plot

**Existing**: `generate_violin_plot(metric: str)`
- **Scope**: 3+ groups general comparison
- **Purpose**: Show full distribution shapes for all frameworks
- **Use case**: Multi-way distribution comparison

**New**: `generate_overlap_plot(metric: str, group_a: str, group_b: str)`
- **Scope**: 2-way focused comparison
- **Purpose**: Nuanced analysis of small effects with overlap coefficient
- **Use case**: When effect size is small (|δ| < 0.3) but p-value is significant

**Verdict**: **DIFFERENT USE CASES** - Violin for general overview, overlap for focused 2-way analysis

---

### 3. Normalized Cost vs Box Plot

**Existing**: `generate_box_plot(metric: str)` where metric = "total_cost_usd"
- **Scope**: Raw cost distributions
- **Purpose**: Show absolute cost values and outliers
- **Use case**: Direct cost comparison

**New**: `generate_normalized_cost_plot()` where metric = cost_per_1000_tokens
- **Scope**: Derived efficiency metric
- **Purpose**: Show cost normalized by output (tokens)
- **Use case**: Efficiency comparison when frameworks produce different amounts of output

**Verdict**: **DIFFERENT METRICS** - Raw cost vs efficiency, both valuable for different analyses

---

### 4. Batch Method Strategy

**Option A (REJECTED)**: Single combined batch method
- ❌ Breaks backward compatibility
- ❌ Forces users to generate all 12 even if only classic 4 needed
- ❌ Mixing concerns (original vs enhanced)

**Option B (CHOSEN)**: Two separate batch methods
- ✅ Clean separation: `generate_all_visualizations()` (existing 4) + `generate_all_enhanced_visualizations()` (new 8)
- ✅ Backward compatible: existing calls unchanged
- ✅ Opt-in: users can choose which suite to generate
- ✅ Follows Single Responsibility Principle

**Option C (REJECTED)**: Three methods (original + new + combined)
- ❌ Unnecessary complexity
- ❌ Duplication of logic
- ❌ More methods to maintain

---

### 5. Default Paper Generation Behavior

**Option A (REJECTED)**: Just classic 4 plots
- ❌ Defeats purpose of this feature
- ❌ Users wouldn't benefit from enhanced visualizations

**Option B (REJECTED)**: Just new 8 plots
- ❌ Loses valuable existing plots (box/violin are standard)
- ❌ Breaking change for existing workflows

**Option C (REJECTED)**: User configurable
- ❌ Added complexity for minimal benefit
- ❌ Requires config schema changes
- ❌ Risk of misconfiguration

**Option D (CHOSEN)**: All 12 plots always
- ✅ Comprehensive analysis suite
- ✅ Backward compatible (existing 4 still generated)
- ✅ Full value from new feature
- ✅ Simple implementation: invoke both batch methods
- ✅ Aligns with "comprehensive scientific paper" goal

---

## Implementation Impact

### Code Changes

**No Deletions**:
- All 4 existing methods remain unchanged
- `generate_all_visualizations()` remains unchanged

**No Updates**:
- Existing method signatures unchanged
- Existing method behavior unchanged
- Existing file paths unchanged

**Pure Additions**:
- 8 new visualization methods
- 1 new batch method (`generate_all_enhanced_visualizations()`)
- Supporting helper methods if needed

### Total Method Count

**Before**: 4 visualization methods + 1 batch = 5 methods  
**After**: 12 visualization methods + 2 batches = 14 methods

**Breakdown**:
- **Existing (unchanged)**: box, violin, forest, qq, generate_all_visualizations
- **New**: effect_panel, efficiency, regression, overlap, normalized_cost, rank, stability, outlier_run, generate_all_enhanced_visualizations

### Paper Generator Integration

```python
# Paper generation workflow (pseudocode)
def generate_paper(experiment_data):
    # ... statistical analysis ...
    findings = statistical_analyzer.analyze(experiment_data)
    
    # Generate ALL 12 visualizations
    visualizations = []
    
    # Existing 4 plots
    visualizations.extend(
        vis_gen.generate_all_visualizations(findings, output_dir)
    )
    
    # New 8 plots
    visualizations.extend(
        vis_gen.generate_all_enhanced_visualizations(findings, output_dir)
    )
    
    # Total: 12 SVG files + metadata
    return visualizations
```

---

## Constitution Compliance

All decisions verified against BAEs Experiment Constitution v1.2.0:

- ✅ **No Backward Compatibility Burden** (Principle XII): Existing methods unchanged, pure additive design
- ✅ **DRY Principle** (Principle XI): Two separate batches avoid duplication while maintaining separation
- ✅ **Fail-Fast Philosophy** (Principle XIII): Both methods fail independently, isolation maintained
- ✅ **Scientific Reproducibility** (Principle I): All 12 plots deterministic, same data → same output
- ✅ **Minimal Dependencies** (Principle IV): No new dependencies added, reuses matplotlib/seaborn

---

## Validation Plan

All decisions will be validated through **real paper generation** using:

**Dataset**: `~/projects/uece/baes/baes_benchmarking_20251028_0713`  
**Frameworks**: BAEs vs ChatDev vs GHSpec  
**Expected Output**: 12 SVG files (4 existing + 8 new)

**Validation Criteria**:
1. All 12 plots generated without errors
2. No existing plots changed or deleted
3. New plots provide complementary insights to existing ones
4. Total generation time <60 seconds
5. All SVG files <2MB and render in LaTeX

---

## Next Steps

1. ✅ Update `plan.md` with redundancy analysis section
2. ✅ Update `contracts/visualization_api.md` with design decisions and paper integration
3. ✅ Update `spec.md` with SC-013 and SC-014 (backward compatibility criteria)
4. ✅ Update `quickstart.md` with "all 12 plots" example
5. ⏳ Proceed to Phase 2 (Tasks) via `/speckit.tasks` command
6. ⏳ Implementation of 8 new methods
7. ⏳ Real paper generation validation

---

**Status**: Redundancy analysis COMPLETE ✅  
**Ready for**: Task breakdown and implementation
