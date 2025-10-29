# Phase 0: Research & Decision Documentation

**Feature**: Enhanced Statistical Report Generation  
**Date**: 2025-10-29  
**Status**: Complete

## Overview

This document consolidates research findings for implementing comprehensive statistical analysis in the genai-devbench paper generation pipeline. All "NEEDS CLARIFICATION" items from Technical Context have been resolved through best practices research.

---

## 1. Statistical Testing Library Selection

### Decision: scipy.stats

**Rationale**:
- Industry-standard for scientific Python computing
- Peer-reviewed implementations of statistical tests (Shapiro-Wilk, Mann-Whitney U, Kruskal-Wallis, t-test, ANOVA, Levene)
- Extensive documentation and validation
- Active maintenance (part of SciPy ecosystem)
- Wide adoption in academic research (ensures reproducibility)

**Alternatives Considered**:
1. **statsmodels.stats**: More comprehensive but heavier dependency, overlaps with scipy for basic tests
2. **Custom implementations**: Rejected due to mathematical complexity and lack of peer review
3. **R via rpy2**: Rejected due to additional runtime dependency and complexity

**Version**: scipy ≥1.9.0 (introduces improved handling of tied ranks in non-parametric tests)

---

## 2. Statistical Power Analysis Library

### Decision: statsmodels.stats.power

**Rationale**:
- Canonical library for statistical power analysis in Python
- Implements validated formulas for t-tests, ANOVA, non-parametric tests
- Provides effect size to sample size calculations
- Well-documented with academic references
- Integrates naturally with scipy test results

**Alternatives Considered**:
1. **pwr (R package via rpy2)**: Rejected due to additional runtime dependency
2. **Custom power calculations**: Rejected due to complexity of power formulas and risk of errors
3. **pingouin**: Good alternative but less widely adopted, statsmodels is more established

**Version**: statsmodels ≥0.14.0 (stable API, comprehensive power analysis tools)

---

## 3. Visualization Library Selection

### Decision: matplotlib + seaborn

**Rationale**:
- **matplotlib**: Already in dependencies (3.8.0), publication-quality output, SVG support
- **seaborn**: Built on matplotlib, simplifies statistical visualizations (violin plots, box plots), colorblind-friendly palettes, kernel density estimation
- Mature and stable APIs
- Extensive customization for publication requirements
- Wide adoption ensures example code availability

**Alternatives Considered**:
1. **plotly**: Interactive but not suitable for static PDF generation in papers
2. **Altair**: Modern declarative syntax but less control over publication details
3. **matplotlib alone**: Possible but seaborn significantly simplifies statistical plots and ensures best practices

**Versions**: 
- matplotlib ≥3.8.0 (already present)
- seaborn ≥0.12.0 (stable API, modern color palettes)

---

## 4. Effect Size Measures

### Decision: Cohen's d (parametric) + Cliff's delta (non-parametric)

**Rationale**:
- **Cohen's d**: Standard for parametric comparisons, interpretable thresholds (0.2/0.5/0.8), widely recognized in research
- **Cliff's delta**: Non-parametric alternative, robust to outliers, appropriate for Mann-Whitney U and Kruskal-Wallis contexts
- Both have established interpretation guidelines
- Complementary: covers both distributional assumptions

**Implementation**:
- Cohen's d: `(mean1 - mean2) / pooled_std`
- Cliff's delta: Probability that random value from group 1 > group 2 minus reverse probability
- Bootstrap CIs: 10,000 resamples for stable confidence interval estimation

**Alternatives Considered**:
1. **Glass's delta**: Uses control group SD only, not applicable (no control group in framework comparison)
2. **Hedges' g**: Bias-corrected Cohen's d, unnecessary for n>10 (typical in our context)
3. **r (correlation)**: Not directly applicable to group comparisons

---

## 5. Bootstrap Resampling Strategy

### Decision: 10,000 iterations with numpy.random.choice

**Rationale**:
- 10,000 iterations provides stable CI estimates (standard in statistical literature)
- numpy's vectorized operations ensure performance (<2 sec per metric-framework)
- Fixed random seed (numpy.random.seed) ensures reproducibility
- Percentile method for CI construction (simple, non-parametric)

**Best Practices**:
- Use `numpy.random.default_rng(seed)` for modern random number generation
- Store seed in experiment config or report metadata
- Validate convergence by checking CI stability across seed changes
- Document bootstrap method in report methodology section

**Alternatives Considered**:
1. **1,000 iterations**: Too few for stable CIs (high variance)
2. **100,000 iterations**: Unnecessarily slow, diminishing returns
3. **BCa (bias-corrected accelerated)**: More accurate but computationally expensive, overkill for our sample sizes

---

## 6. Markdown Report Generation Best Practices

### Decision: Template-based generation with f-strings

**Rationale**:
- Python f-strings provide readable template interpolation
- Keep templates as string constants in code (not external files) for simpler deployment
- Use helper functions for repetitive sections (tables, visualizations, explanations)
- Validate markdown syntax programmatically (check heading hierarchy, relative paths)

**Structure Pattern**:
```python
def _generate_section(title: str, data: Dict) -> str:
    return f"""
## {title}

📚 **What is this?**
{data['what']}

📊 **Results**
{data['results']}

💡 **How to interpret?**
{data['interpretation']}
"""
```

**Best Practices**:
- Use consistent emoji icons for visual navigation (📚, 💡, ⚠️, ✅, 🎓)
- Escape special markdown characters in data values
- Use relative paths for image embedding (`figures/statistical/plot.svg`)
- Include alt text for accessibility
- Validate image file existence before generating markdown

---

## 7. Educational Content Generation

### Decision: Template library with analogy database

**Rationale**:
- Create reusable templates for "What/Why/How" explanations
- Maintain analogy database mapping concepts to relatable examples
- Use Flesch-Kincaid grade level scoring to validate 8th grade reading level
- Provide multiple explanation variants (technical, simple, analogy) and select based on context

**Implementation Strategy**:
```python
EXPLANATIONS = {
    'shapiro_wilk': {
        'what': "Checks if your data follows a bell curve (normal distribution)",
        'why': "Determines which statistical tests are appropriate",
        'how': "p > 0.05 = normal, p < 0.05 = not normal",
        'analogy': "Like checking if test scores follow typical pattern: most B/C, fewer A/F"
    },
    'cohens_d': {
        'what': "Measures HOW MUCH two groups differ in standard deviations",
        'why': "Statistical significance ≠ practical importance",
        'how': "0.2=small, 0.5=medium, 0.8=large",
        'analogy': "d=0.8 is like height difference between 13 and 18 year-olds"
    }
}
```

**Readability Validation**:
- Use `textstat` library (optional dependency for development) to compute Flesch-Kincaid score
- Target: Grade 8-10 for core explanations
- Technical terms always accompanied by plain-language definition on first use

---

## 8. Statistical Test Selection Logic

### Decision: Decision tree based on normality + sample size

**Algorithm**:
```
IF n < 3 per group:
    SKIP tests, show descriptive stats, warn insufficient data
ELIF zero_variance detected:
    SKIP tests, explain why (no variation = no difference to test)
ELSE:
    Run Shapiro-Wilk normality test
    IF all groups normal (p > 0.05) AND Levene's test passes (equal variance):
        IF 2 groups: Independent t-test + Cohen's d
        IF 3+ groups: One-way ANOVA + post-hoc t-tests (Bonferroni) + Cohen's d
    ELSE (non-normal OR unequal variance):
        IF 2 groups: Mann-Whitney U test + Cliff's delta
        IF 3+ groups: Kruskal-Wallis H + post-hoc Mann-Whitney (Bonferroni) + Cliff's delta
```

**Rationale**:
- Conservative approach: prefer non-parametric when assumptions violated
- Bonferroni correction controls family-wise error rate
- Document decision rationale in report for transparency

**Edge Cases**:
- Tied ranks: scipy handles via midrank method (documented in methodology)
- Unequal sample sizes: Use Welch's t-test or Mann-Whitney U (both handle unbalanced designs)
- Multimodal distributions: Warn in report, show violin plots, suggest subgroup analysis

---

## 9. Visualization Best Practices

### Decision: SVG format with seaborn styling

**Rationale**:
- SVG: Vector format, scalable, small file size, works in markdown/LaTeX/PDF
- Seaborn: Enforces best practices (appropriate scales, colorblind palettes, statistical annotations)
- 300 DPI equivalent quality for PDF compilation
- Consistent styling across all plots

**Plot-Specific Practices**:

1. **Box Plots**:
   - Show median (line), Q1/Q3 (box), whiskers (1.5×IQR), outliers (dots)
   - Label axes with units
   - Use seaborn.boxplot with `showfliers=True`

2. **Violin Plots**:
   - Kernel density estimation with quartile lines
   - Mirror symmetry for readability
   - seaborn.violinplot with `inner='quartile'`

3. **Forest Plots**:
   - Horizontal layout (easier to read long framework names)
   - Point estimate + 95% CI error bars
   - Vertical line at 0 (no effect)
   - Color-coded thresholds for small/medium/large effects

4. **Q-Q Plots**:
   - Theoretical quantiles (X) vs sample quantiles (Y)
   - 45-degree reference line
   - scipy.stats.probplot
   - Include Shapiro-Wilk p-value in title

**Color Palette**: seaborn 'colorblind' palette (8 distinct colors, accessible)

---

## 10. Paper Generation Pipeline Integration

### Decision: Two-phase integration (analysis → paper)

**Phase 1 (Step 1)**: ExperimentAnalyzer enhancement
- Generate statistical reports and visualizations
- Return structured `StatisticalFindings` object with parseable data
- Save reports as `statistical_report_summary.md` and `statistical_report_full.md`

**Phase 2 (Steps 2-3)**: PaperGenerator enhancement
- Load and parse `statistical_report_summary.md` in `_load_analyzed_data()`
- Extract key findings (effect sizes, p-values, power warnings)
- Inject content into Methodology ("Statistical Analysis" subsection)
- Embed visualizations in Results section
- Add power limitations to Discussion section

**Data Flow**:
```
ExperimentAnalyzer.analyze()
  ↓ generates
statistical_report_summary.md (parseable markdown)
  ↓ loaded by
PaperGenerator._load_analyzed_data()
  ↓ parsed into
self.statistical_data = {
    'comparisons': [...],  # effect sizes, CIs, p-values
    'primary_metric': 'execution_time',
    'visualization_paths': {...},
    'power_warnings': [...],
    'methodology_text': "...",
    'key_findings': [...]
}
  ↓ used by
_generate_methodology_section() → adds statistical analysis subsection
_generate_results_section() → embeds visualizations + effect sizes
_generate_discussion_section() → adds power limitations paragraph
```

**Best Practices**:
- Keep statistical analysis logic in ExperimentAnalyzer (separation of concerns)
- PaperGenerator only consumes, doesn't recompute
- Fail gracefully: if statistical report missing, paper generation continues with basic content

---

## Dependencies Summary

Final dependency list to add to `requirements.txt`:

```
scipy==1.11.0
statsmodels==0.14.0
seaborn==0.12.2
numpy==1.24.3
```

All are open-source, actively maintained, and widely adopted in scientific Python community.

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Bootstrap resampling too slow | Analysis takes >60 sec | Limit to 10,000 iterations, use numpy vectorization |
| Reading level too technical | Users confused | Validate with Flesch-Kincaid, user testing with 90%+ comprehension target |
| Visualization rendering issues in PDF | Figures broken in paper | Test LaTeX compilation early, use SVG with fallback to PNG |
| Statistical test selection wrong | Invalid conclusions | Document decision tree, add validation tests with known datasets |
| Backward compatibility breaks | Existing experiments fail | Graceful fallback to basic stats if enhanced analysis fails |

---

## Next Steps (Phase 1)

1. Generate `data-model.md` defining entities (MetricDistribution, StatisticalTest, EffectSize, PowerAnalysis, StatisticalFindings)
2. Generate API contracts in `contracts/` for statistical method signatures
3. Create `quickstart.md` for using enhanced statistical reports
4. Update agent context with new technologies (scipy, statsmodels, seaborn)

---

**Research Complete**: All technical decisions documented. Ready for Phase 1 design.
