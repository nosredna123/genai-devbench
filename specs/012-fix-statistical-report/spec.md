# Feature Specification: Fix Statistical Report Generation Issues

**Feature Branch**: `012-fix-statistical-report`  
**Created**: 2025-10-29  
**Status**: Draft  
**Input**: User description: "Fix statistical report generation issues: correct bootstrap confidence intervals, add Welch's ANOVA support, implement power analysis, fix p-value formatting, add multiple comparison corrections, and improve effect size calculations"

## User Scenarios & Testing

### User Story 1 - Accurate Confidence Intervals (Priority: P1)

Researchers reviewing statistical reports need confidence intervals that mathematically contain their point estimates to make valid inferences about effect sizes.

**Why this priority**: Critical mathematical error - point estimates outside CIs violate fundamental statistical principles and invalidate all effect size interpretations. This undermines the entire report's credibility.

**Independent Test**: Generate a statistical report with bootstrap effect sizes and verify that every confidence interval contains its corresponding point estimate. Delivers trustworthy effect size measurements.

**Acceptance Scenarios**:

1. **Given** two groups with different means, **When** Cohen's d is calculated with bootstrap CI, **Then** the CI lower bound ≤ Cohen's d ≤ CI upper bound
2. **Given** two non-normal groups, **When** Cliff's Delta is calculated with bootstrap CI, **Then** the CI lower bound ≤ Cliff's Delta ≤ CI upper bound
3. **Given** effect size with large magnitude (d > 3.0), **When** bootstrap resampling is performed, **Then** the CI reflects appropriate uncertainty around that magnitude
4. **Given** identical groups (no difference), **When** effect size is calculated, **Then** point estimate is near zero and CI includes zero

---

### User Story 2 - Appropriate Test Selection (Priority: P1)

Researchers need the statistical test to match their data characteristics (normality, variance equality) to ensure valid p-values and maximize statistical power.

**Why this priority**: Using the wrong test (Kruskal-Wallis for normal data) sacrifices statistical power and contradicts stated methodology. Critical for research validity.

**Independent Test**: Generate reports for datasets with known characteristics (all normal, mixed, all non-normal) and verify correct test selection. Delivers scientifically sound test choices.

**Acceptance Scenarios**:

1. **Given** three groups all normally distributed with equal variances, **When** multi-group comparison is performed, **Then** standard ANOVA is selected
2. **Given** three groups all normally distributed with unequal variances, **When** multi-group comparison is performed, **Then** Welch's ANOVA is selected
3. **Given** at least one non-normal group, **When** multi-group comparison is performed, **Then** Kruskal-Wallis test is selected
4. **Given** two groups both normal with equal variances, **When** pairwise comparison is performed, **Then** Student's t-test is selected
5. **Given** two groups both normal with unequal variances, **When** pairwise comparison is performed, **Then** Welch's t-test is selected
6. **Given** at least one non-normal group in pairwise comparison, **When** test is selected, **Then** Mann-Whitney U test is used

---

### User Story 3 - Power Analysis Insights (Priority: P1)

Researchers need to know whether their sample sizes are adequate to detect meaningful effects and understand when non-significant results may be due to insufficient power rather than true absence of effects.

**Why this priority**: Without power analysis, researchers cannot interpret non-significant results or plan future studies. Essential for scientific rigor and reproducibility.

**Independent Test**: Generate a report and verify a dedicated Power Analysis section appears with achieved power for each test and sample size recommendations. Delivers actionable guidance for study design.

**Acceptance Scenarios**:

1. **Given** a statistical comparison is performed, **When** the report is generated, **Then** achieved power is calculated and displayed for that comparison
2. **Given** achieved power is below 80%, **When** recommendations are generated, **Then** specific increased sample size needed to reach 80% power is reported
3. **Given** non-significant result with low power (<50%), **When** interpretation is provided, **Then** warning indicates insufficient power to detect effects
4. **Given** significant result with high power (>80%), **When** interpretation is provided, **Then** confidence in finding is noted
5. **Given** multiple comparisons, **When** Power Analysis section is created, **Then** all comparisons are included with their individual power metrics

---

### User Story 4 - Aligned Effect Sizes (Priority: P2)

Researchers need effect size measures that match the statistical test used (parametric ↔ Cohen's d, non-parametric ↔ Cliff's Delta) for conceptual consistency.

**Why this priority**: Major inconsistency - using Cohen's d with Kruskal-Wallis creates methodological confusion and may give misleading interpretations.

**Independent Test**: Generate reports for various data types and verify effect size measure matches the test type used. Delivers methodologically coherent reports.

**Acceptance Scenarios**:

1. **Given** Student's t-test or ANOVA is used, **When** effect size is calculated, **Then** Cohen's d is reported
2. **Given** Welch's t-test or Welch's ANOVA is used, **When** effect size is calculated, **Then** Cohen's d is reported
3. **Given** Mann-Whitney U or Kruskal-Wallis is used, **When** effect size is calculated, **Then** Cliff's Delta is reported
4. **Given** effect size is reported, **When** educational content is generated, **Then** explanation matches the measure used (d vs δ)

---

### User Story 5 - Multiple Comparison Corrections (Priority: P2)

Researchers performing multiple statistical tests need p-value adjustments to control family-wise error rate and avoid false discoveries.

**Why this priority**: Without correction, ~1 false positive expected per 20 comparisons. Important for research with many metrics to maintain credibility.

**Independent Test**: Generate a report with 10+ comparisons and verify adjusted p-values appear with correction method documented. Delivers defensible significance claims.

**Acceptance Scenarios**:

1. **Given** more than one pairwise comparison, **When** statistical tests are performed, **Then** Holm-Bonferroni correction is applied to p-values
2. **Given** adjusted p-values are calculated, **When** significance is determined, **Then** decisions use adjusted p-values not raw p-values
3. **Given** multiple comparison correction is applied, **When** report is generated, **Then** both raw and adjusted p-values are reported
4. **Given** correction method is used, **When** methodology section is written, **Then** Holm-Bonferroni method is documented
5. **Given** only one comparison is made, **When** p-values are reported, **Then** no correction is applied (not needed)

---

### User Story 6 - Professional P-value Formatting (Priority: P3)

Researchers need p-values formatted according to statistical conventions (p < 0.001 for very small values, not "0.0000") for professional presentation.

**Why this priority**: Moderate issue - improves professionalism but doesn't affect statistical validity. Important for publication standards.

**Independent Test**: Generate reports and verify p-values are formatted correctly throughout. Delivers publication-ready formatting.

**Acceptance Scenarios**:

1. **Given** p-value is less than 0.001, **When** report is formatted, **Then** displayed as "p < 0.001"
2. **Given** p-value is 0.001 or greater, **When** report is formatted, **Then** displayed as "p = 0.XXX" with 3 decimal places
3. **Given** p-value is exactly 0.05, **When** report is formatted, **Then** displayed as "p = 0.050" (not "p = 0.05")
4. **Given** test reports significance, **When** interpretation is written, **Then** p-value format is consistent (no "p=0.0000")

---

### User Story 7 - Emphasis on Robust Summary Statistics (Priority: P3)

Researchers analyzing highly skewed data need reports that emphasize median and IQR rather than mean and SD to accurately represent central tendency and spread.

**Why this priority**: Moderate issue - improves interpretation accuracy for skewed distributions. Important for data quality communication.

**Independent Test**: Generate report for highly skewed metric and verify median/IQR are prominently featured in summary and interpretation. Delivers accurate data summaries.

**Acceptance Scenarios**:

1. **Given** metric has |skewness| > 1.0, **When** descriptive statistics table is created, **Then** median and IQR are highlighted (bold or flagged)
2. **Given** metric has |skewness| > 1.0, **When** text interpretation is written, **Then** median is referenced instead of mean
3. **Given** metric has |skewness| < 1.0, **When** text interpretation is written, **Then** mean ± SD is referenced
4. **Given** highly skewed metric (skewness > 2.0), **When** report is generated, **Then** warning note explains why median is more appropriate than mean

---

### User Story 8 - Neutral Statistical Language (Priority: P3)

Researchers need interpretations that describe distributional differences without implying causality, using terms like "differs from" rather than "outperforms."

**Why this priority**: Moderate issue - improves scientific accuracy. Kruskal-Wallis/Mann-Whitney are associative tests and cannot establish causality.

**Independent Test**: Generate report and verify all interpretations use neutral language without causal claims. Delivers scientifically precise wording.

**Acceptance Scenarios**:

1. **Given** significant difference found, **When** interpretation is written, **Then** language uses "shows higher/lower values" not "outperforms"
2. **Given** effect size is reported, **When** interpretation is written, **Then** language uses "differs from" or "exceeds" not "is better than"
3. **Given** 100% probability in Cliff's Delta, **When** interpretation is written, **Then** language uses "all observed values in group X exceed those in group Y" not "100% certain X is better"
4. **Given** power analysis warning, **When** recommendation is written, **Then** language avoids claiming "no effect exists" (uses "insufficient evidence")

---

### Edge Cases

- What happens when bootstrap resampling fails to converge (all samples identical)?
  - System should fall back to analytic CI methods or flag as unable to compute CI
- How does system handle when all three groups are identical (zero variance)?
  - System should detect perfect equality, report effect size = 0 with CI [0, 0], and flag as special case
- What happens when sample size is too small for meaningful power analysis (n < 5 per group)?
  - System should report power as "indeterminate" with warning about inadequate sample size
- How does system handle non-overlapping groups (Cliff's Delta = ±1.000 legitimately)?
  - System should verify this is true perfect separation, compute CI showing high certainty, and add note explaining the finding
- What happens when Levene's test indicates equal variances but sample sizes are very unbalanced (ratio > 4:1)?
  - System should prefer Welch's test even with equal variances due to unbalanced design
- How does system report when no pairwise comparisons are significant after correction?
  - System should clearly state correction reduced significance, explain implications, report both raw and adjusted p-values

## Requirements

### Functional Requirements

**Bootstrap Confidence Intervals**

- **FR-001**: System MUST resample each group independently when computing bootstrap confidence intervals for effect sizes
- **FR-002**: System MUST verify that every computed confidence interval contains its corresponding point estimate
- **FR-003**: System MUST use at least 10,000 bootstrap iterations for effect size CI calculations
- **FR-004**: System MUST handle bootstrap failures gracefully by falling back to analytic methods or reporting inability to compute CI

**Test Selection Logic**

- **FR-005**: System MUST check both normality (Shapiro-Wilk per group) and variance equality (Levene's test) before selecting statistical test
- **FR-006**: System MUST use standard ANOVA for multi-group comparisons when all groups are normal and variances are equal
- **FR-007**: System MUST use Welch's ANOVA for multi-group comparisons when all groups are normal but variances are unequal
- **FR-008**: System MUST use Kruskal-Wallis test for multi-group comparisons when at least one group is non-normal
- **FR-009**: System MUST use Student's t-test for two-group comparisons when both groups are normal and variances are equal
- **FR-010**: System MUST use Welch's t-test for two-group comparisons when both groups are normal but variances are unequal
- **FR-011**: System MUST use Mann-Whitney U test for two-group comparisons when at least one group is non-normal
- **FR-012**: System MUST document test selection rationale in the report explaining which assumptions were checked

**Effect Size Selection**

- **FR-013**: System MUST use Cohen's d for effect sizes when parametric tests (t-test, ANOVA, Welch's variants) are selected
- **FR-014**: System MUST use Cliff's Delta for effect sizes when non-parametric tests (Mann-Whitney, Kruskal-Wallis) are selected
- **FR-015**: System MUST ensure effect size measure matches the test type in all report sections

**Power Analysis**

- **FR-016**: System MUST calculate achieved power for every statistical comparison performed
- **FR-017**: System MUST generate a dedicated "Power Analysis" section in the full statistical report
- **FR-018**: System MUST provide sample size recommendations when achieved power is below target (default 0.80)
- **FR-019**: System MUST use appropriate power calculation method based on test type (t-test power, ANOVA power, non-parametric approximations)
- **FR-020**: System MUST report power analysis results in a table format with columns: comparison, effect size, achieved power, recommended n
- **FR-021**: System MUST include power-based warnings in interpretations when power is insufficient (<0.50)

**Multiple Comparison Corrections**

- **FR-022**: System MUST apply Holm-Bonferroni correction when more than one pairwise comparison is performed
- **FR-023**: System MUST report both raw and adjusted p-values in the results
- **FR-024**: System MUST use adjusted p-values for significance decisions (comparing to α)
- **FR-025**: System MUST document the correction method used in the Statistical Methodology section
- **FR-026**: System MUST NOT apply correction when only one comparison is made

**P-value Formatting**

- **FR-027**: System MUST format p-values < 0.001 as "p < 0.001" (not "p = 0.0000" or "p = 0.000")
- **FR-028**: System MUST format p-values ≥ 0.001 as "p = X.XXX" with exactly 3 decimal places
- **FR-029**: System MUST format p-values consistently throughout all report sections

**Data Summary Emphasis**

- **FR-030**: System MUST calculate skewness for all metrics in descriptive statistics
- **FR-031**: System MUST flag metrics with |skewness| > 1.0 as skewed in descriptive statistics table
- **FR-032**: System MUST emphasize median and IQR in text interpretations for metrics with |skewness| > 1.0
- **FR-033**: System MUST emphasize mean and SD in text interpretations for metrics with |skewness| ≤ 1.0
- **FR-034**: System MUST include explanatory note for highly skewed metrics (skewness > 2.0) explaining why median is more appropriate

**Language Precision**

- **FR-035**: System MUST use neutral descriptive language in interpretations (e.g., "shows higher values than" instead of "outperforms")
- **FR-036**: System MUST avoid causal language unless explicitly indicated as experimental study with controls
- **FR-037**: System MUST rephrase certainty claims from "100% probability" to "all observed values exceeded" for Cliff's Delta = ±1.000
- **FR-038**: System MUST use "insufficient evidence to detect difference" rather than "no difference exists" for non-significant results with low power

**Validation Requirements**

- **FR-039**: System MUST include automated validation that checks all CIs contain their point estimates before report finalization
- **FR-040**: System MUST log warnings when unusual patterns detected (all effects large, all CIs zero-width, all p-values < 0.001)
- **FR-041**: System MUST verify test selection matches stated methodology for each metric

### Success Criteria

**Accuracy & Correctness**

- 100% of confidence intervals mathematically contain their point estimates (validated across 1000+ bootstrap runs)
- Test selection matches data characteristics in 100% of cases (verified against synthetic datasets with known properties)
- Effect size measure aligns with test type in 100% of comparisons

**Completeness**

- Power Analysis section appears in all full statistical reports with metrics for all comparisons
- Multiple comparison corrections are applied when applicable (100% of reports with 2+ comparisons)
- Both raw and adjusted p-values are reported when corrections are applied

**Professional Quality**

- Zero instances of "p = 0.0000" formatting in generated reports
- Skewed metrics (|skewness| > 1.0) emphasize median/IQR in at least 80% of interpretive text
- Zero instances of causal language ("outperforms", "better than") in non-experimental reports

**Reproducibility**

- Reports generated from same data produce identical results (same test selections, effect sizes, CIs) on repeated runs
- Statistical methodology section documents all test selection criteria and correction methods applied

**User Satisfaction**

- Researchers can validate report accuracy against published statistical methods references
- Reports pass peer review without statistical methodology questions in 90% of academic submissions
- Generated reports require minimal manual editing for publication readiness

### Key Entities

**StatisticalTest** (enhanced):
- Test type (t-test, Welch's t-test, Mann-Whitney U, ANOVA, Welch's ANOVA, Kruskal-Wallis)
- Rationale for selection (which assumptions checked, which passed/failed)
- Raw p-value
- Adjusted p-value (if correction applied)
- Achieved power
- Recommended sample size (if underpowered)

**EffectSize** (enhanced):
- Measure type (Cohen's d or Cliff's Delta)
- Point estimate value
- Confidence interval (lower, upper) - must contain point estimate
- Bootstrap iteration count
- Interpretation aligned with measure type

**PowerAnalysis** (new):
- Comparison identifier
- Effect size used
- Sample sizes per group
- Achieved power (0.0 to 1.0)
- Target power (typically 0.80)
- Recommended sample size to reach target
- Power adequacy flag (sufficient/insufficient/indeterminate)

**DescriptiveStatistics** (enhanced):
- Mean, median, SD, IQR (all existing)
- Skewness value
- Skewness flag (normal, moderately skewed, highly skewed)
- Primary summary recommendation (mean±SD vs median[IQR])

**MultipleComparisonCorrection** (new):
- Correction method (Holm-Bonferroni, Bonferroni, FDR, or none)
- Number of comparisons
- Original alpha level
- Adjusted alpha levels per comparison
- Mapping of raw to adjusted p-values

### Assumptions

- Bootstrap resampling with 10,000 iterations provides sufficiently stable CI estimates (industry standard)
- Target power of 0.80 is appropriate default (conventional in research)
- Holm-Bonferroni provides good balance between Type I error control and power (less conservative than Bonferroni)
- Shapiro-Wilk test with α=0.05 is acceptable for normality assessment despite sensitivity at larger sample sizes
- Skewness threshold of |1.0| effectively separates approximately symmetric from clearly skewed distributions
- Users are conducting observational studies by default (no causality unless explicitly indicated)
- Three decimal places for p-values provides adequate precision while following conventions
- Welch's variants preferred over pooled variants when variances unequal (robust default)

### Dependencies

- SciPy ≥ 1.11.0 for Welch's ANOVA (`scipy.stats.f_oneway` with `equal_var=False` or custom implementation)
- statsmodels ≥ 0.14.0 for power analysis (`TTestIndPower`, `FTestAnovaPower`)
- statsmodels for multiple comparison corrections (`multipletests` with Holm method)
- NumPy ≥ 1.24.0 for bootstrap resampling and percentile calculations
- Existing statistical analysis infrastructure (normality tests, effect sizes, bootstrap framework)

### Out of Scope

- Bayesian statistical methods (beyond frequentist approach)
- Advanced power analysis for complex designs (factorial, mixed models)
- Automated data quality checks beyond skewness (outlier detection, measurement error)
- Graphical display of power curves
- Alternative multiple comparison methods (Tukey HSD, Scheffe, Dunnett)
- Post-hoc pairwise tests with corrections (Dunn's test for Kruskal-Wallis)
- Effect size measures beyond Cohen's d and Cliff's Delta (omega-squared, eta-squared, etc.)
- Customizable bootstrap parameters (iteration count fixed at 10,000)
- Language translation of statistical terms
- Integration with external statistical software (R, SPSS, SAS)

### Constraints

- Must maintain backward compatibility with existing report structure (sections 1-7)
- Power Analysis must be Section 5, shifting current sections 5-6 to 6-7
- Bootstrap CI calculation must not exceed 60 seconds per comparison on standard hardware
- Changes must not break existing unit tests for statistical functions
- Report file size must not increase by more than 50% due to power analysis additions
- Must work with Python 3.11+ only (no Python 2 compatibility needed)
- Statistical methods must follow published academic standards (APA, Nature, Science)

### Performance Requirements

- Bootstrap CI calculation completes within 5 seconds per comparison for n ≤ 100 per group
- Full statistical report generation (with power analysis) completes within 3 minutes for 10 metrics × 3 groups
- Power analysis adds no more than 20% to total report generation time
- Memory usage for bootstrap stays under 500MB even with 10,000 iterations

### Security & Privacy

Not applicable - statistical calculations are purely mathematical transformations of already-collected data with no authentication, authorization, or data privacy concerns.
