# Feature Specification: Enhanced Statistical Report Generation

**Feature Branch**: `011-enhance-statistical-report`  
**Created**: 2025-10-29  
**Status**: Draft  
**Input**: Enhance statistical_report.md with comprehensive statistical analysis including effect sizes, normality tests, power analysis, and publication-ready visualizations

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Comprehensive Statistical Testing (Priority: P1)

Researchers running framework comparisons need rigorous statistical analysis that goes beyond basic descriptive statistics to determine if observed performance differences are statistically significant and practically meaningful.

**Why this priority**: This is the core scientific value - without proper statistical testing, the report cannot make valid claims about framework performance differences. This forms the foundation for all other improvements.

**Independent Test**: Can be fully tested by running an experiment with 2+ frameworks and verifying the report includes: Shapiro-Wilk normality tests, appropriate parametric/non-parametric tests (t-test/Mann-Whitney or ANOVA/Kruskal-Wallis), effect size calculations (Cohen's d/Cliff's delta), and proper p-value interpretation.

**Acceptance Scenarios**:

1. **Given** experiment data with 2 frameworks and normally distributed metrics, **When** report is generated, **Then** report includes Shapiro-Wilk test results, parametric tests (t-test/ANOVA), Cohen's d effect sizes, and interpretation guidance
2. **Given** experiment data with 3+ frameworks and non-normal distributions, **When** report is generated, **Then** report includes Shapiro-Wilk test results, Kruskal-Wallis H-test, pairwise Mann-Whitney U tests with Bonferroni correction, Cliff's delta effect sizes
3. **Given** experiment data with small sample sizes (n<30), **When** report is generated, **Then** report warns about statistical power limitations and provides bootstrap confidence intervals
4. **Given** metrics with zero variance (all values identical), **When** report is generated, **Then** report skips statistical tests for those metrics with clear explanation

---

### User Story 2 - Statistical Power Analysis (Priority: P2)

Researchers need to understand if their experiment has sufficient statistical power to detect meaningful differences, and guidance on how many additional runs are needed to reach adequate power.

**Why this priority**: Power analysis prevents researchers from drawing premature conclusions from underpowered experiments and provides actionable guidance for experimental design.

**Independent Test**: Can be tested by generating reports with varying sample sizes (n=2, 5, 10, 30) and verifying power calculations are present, interpreted correctly, and include recommendations for additional runs when power is insufficient.

**Acceptance Scenarios**:

1. **Given** experiment with n=5 runs per framework, **When** report is generated, **Then** report includes achieved power calculation for detected effect sizes and recommendation for target sample size to reach 80% power
2. **Given** experiment with large effect sizes but small n, **When** report is generated, **Then** report highlights that differences may be detectable with current power level
3. **Given** experiment with small effect sizes, **When** report is generated, **Then** report calculates required sample size to detect those effects with 80% power at α=0.05

---

### User Story 3 - Publication-Ready Statistical Visualizations Integrated in Paper (Priority: P2)

Researchers preparing papers need high-quality statistical visualizations with proper statistical context (box plots showing distributions, violin plots with kernel density, forest plots with effect sizes and CIs, Q-Q plots for normality) that are **automatically incorporated** into the generated paper's methodology and results sections, enhancing the scientific rigor and publication quality.

**Why this priority**: Statistical visualizations are essential for publication and make analysis results accessible. They must be generated during the statistical analysis phase AND actively used by the paper generation pipeline to create a complete, publication-ready manuscript with rigorous statistical reporting. This transforms the paper from basic comparative analysis to comprehensive statistical evaluation suitable for peer-reviewed journals.

**Independent Test**: Can be tested by running the full paper generation pipeline with `PaperGenerator.generate()` and verifying that:
1. Statistical figures are generated in `output_dir/figures/statistical/` during Step 1
2. The generated paper's Results section includes embedded statistical figures (box plots, forest plots)
3. The generated paper's Methodology section references statistical test information from enhanced reports
4. The final LaTeX/PDF paper includes both comparative charts AND statistical visualizations
5. Statistical report content is used to populate paper sections (e.g., effect sizes in results, power analysis in discussion)

**Acceptance Scenarios**:

1. **Given** paper generation runs with execution time data, **When** Results section is generated, **Then** section includes box plot showing distributions AND references effect sizes and p-values from statistical report
2. **Given** paper generation with multiple frameworks, **When** Results section is generated, **Then** forest plot of pairwise comparisons is embedded with interpretation text derived from statistical analysis
3. **Given** paper generation completes, **When** Methodology section is generated, **Then** section includes "Statistical Analysis" subsection describing normality tests, effect size measures, and power analysis performed
4. **Given** paper compilation to PDF, **When** figures are included, **Then** both comparative bar charts (from FigureExporter) AND statistical box/violin plots appear in Results section with proper captions
5. **Given** statistical power warnings exist, **When** Discussion section is generated, **Then** section includes limitations paragraph mentioning statistical power and sample size recommendations from enhanced report

---

### User Story 4 - Assumption Validation & Diagnostic Reporting (Priority: P3)

Researchers need transparent reporting of statistical assumptions (normality, homogeneity of variance, independence) with diagnostic tests and recommendations for remediation when assumptions are violated.

**Why this priority**: Ensures statistical integrity by making assumption violations explicit and guiding researchers to appropriate alternative analyses.

**Independent Test**: Can be tested by creating datasets that violate assumptions (e.g., highly skewed data, unequal variances) and verifying the report detects violations, reports diagnostic test results (Levene's test, Shapiro-Wilk), and recommends alternatives (e.g., log transformation, non-parametric tests).

**Acceptance Scenarios**:

1. **Given** metrics with significantly different variances across frameworks, **When** report is generated, **Then** report includes Levene's test results and recommends Welch's t-test or non-parametric alternatives
2. **Given** highly skewed metric distributions, **When** report is generated, **Then** report identifies skewness in descriptive statistics, shows Q-Q plot deviation, and suggests log transformation or non-parametric tests
3. **Given** outliers detected in data, **When** report is generated, **Then** report identifies outliers using IQR method, displays them in box plots, and recommends robust statistical methods

---

### User Story 5 - Reproducible Statistical Methodology Documentation (Priority: P3)

Researchers need complete documentation of statistical methods used, including test selection rationale, significance levels, correction methods, and software versions for reproducibility.

**Why this priority**: Essential for peer review and reproducibility of scientific findings. Allows readers to validate analytical approach and replicate analysis.

**Independent Test**: Can be tested by reviewing the generated report's methodology section for completeness: lists all statistical tests used, explains why each test was chosen, documents significance level and corrections applied, and includes software/library versions.

**Acceptance Scenarios**:

1. **Given** any experiment, **When** report is generated, **Then** report includes dedicated "Statistical Methodology" section documenting test selection criteria, significance levels (α), correction methods, and Python library versions
2. **Given** multiple comparison corrections are applied, **When** report is generated, **Then** report clearly states which correction was used (Bonferroni, Holm, FDR) and the adjusted α threshold
3. **Given** effect size calculations, **When** report is generated, **Then** report documents which effect size measure was used (Cohen's d, Cliff's delta) and interpretation thresholds (small/medium/large)

---

### User Story 6 - Educational and User-Friendly Statistical Explanations (Priority: P1)

Researchers with varying levels of statistical expertise need clear, didactic explanations of what each statistical test/plot means, why it was used, and how to interpret the results, enabling them to confidently understand and communicate their findings.

**Why this priority**: Statistical literacy varies widely among researchers. Without accessible explanations, even rigorous statistical analysis becomes a "black box" that researchers cannot confidently interpret or explain in papers. This is foundational for making the entire feature valuable to non-statistician users.

**Independent Test**: Can be tested by having researchers with basic statistics knowledge (undergraduate level) read the report and answer: (1) What does each test measure? (2) Why was it chosen? (3) What do the results mean for their experiment? Success = 90%+ correct answers without external resources.

**Acceptance Scenarios**:

1. **Given** any statistical test result in report, **When** researcher reads the section, **Then** they find a "What is this?" box explaining the test's purpose in 1-2 simple sentences (8th grade reading level)
2. **Given** any statistical test result, **When** researcher reads the section, **Then** they find a "Why use it?" explanation specific to their data characteristics (e.g., "Your data is not normally distributed, so we use Mann-Whitney U instead of t-test")
3. **Given** any statistical test result, **When** researcher reads the section, **Then** they find a "How to interpret?" guide with decision rules (e.g., "p < 0.05 means the difference is statistically significant - unlikely due to chance")
4. **Given** any visualization in report, **When** researcher views it, **Then** caption explains in plain language what each visual element represents and how to read it (e.g., "Box shows where middle 50% of data falls")
5. **Given** effect size reported, **When** researcher reads interpretation, **Then** they see practical analogy making magnitude concrete (e.g., "Cohen's d = 0.8 is like comparing average height of 8th graders vs college students - clearly noticeable")
6. **Given** technical statistical term used, **When** term appears for first time, **Then** it's followed by plain-language definition in parentheses (e.g., "heteroscedasticity (unequal variance across groups)")

---

### Edge Cases

- What happens when a framework has only 1 run (no variance)? → Report skips statistical tests, shows only descriptive statistics, and warns about insufficient data
- How does system handle metrics with all identical values? → Report detects zero variance, skips tests, and explains why testing is impossible
- What if all values are missing for a metric? → Report lists metric as "not measured" and excludes from analysis
- How to handle extreme outliers that distort visualizations? → Box plots show outliers explicitly; report includes outlier detection results; visualizations use appropriate scaling
- What if sample sizes differ across frameworks (unbalanced design)? → Report notes sample size imbalance, uses appropriate tests (e.g., Welch's ANOVA), and calculates power separately for each comparison
- How to handle tied ranks in non-parametric tests? → Use scipy's handling of ties (midrank method) and document this in methodology
- What if distributions are multimodal? → Report identifies multimodality in descriptive statistics, shows in violin plots, and warns about potential subpopulations

## Requirements *(mandatory)*

### Functional Requirements

**Core Statistical Testing**

- **FR-001**: System MUST perform Shapiro-Wilk normality tests on all metrics for each framework with n≥3
- **FR-002**: System MUST select appropriate statistical tests based on normality results: parametric (t-test, ANOVA) for normal distributions, non-parametric (Mann-Whitney U, Kruskal-Wallis H) for non-normal distributions
- **FR-003**: System MUST calculate effect sizes: Cohen's d for parametric tests, Cliff's delta for non-parametric tests
- **FR-004**: System MUST apply multiple comparison corrections (Bonferroni or Holm-Bonferroni) when performing pairwise tests across 3+ frameworks
- **FR-005**: System MUST calculate 95% bootstrap confidence intervals for all effect size estimates using 10,000 resamples
- **FR-006**: System MUST skip statistical tests for metrics with zero variance and document reason in report

**Statistical Power Analysis**

- **FR-007**: System MUST calculate achieved statistical power for each comparison given observed effect sizes and sample sizes
- **FR-008**: System MUST recommend target sample size to achieve 80% power when current power is below 70%
- **FR-009**: System MUST warn when sample size is insufficient (n<5 per group) for reliable statistical inference
- **FR-010**: System MUST provide power curves showing relationship between sample size and power for detected effect sizes

**Assumption Validation**

- **FR-011**: System MUST test homogeneity of variance using Levene's test for parametric comparisons
- **FR-012**: System MUST detect and report outliers using IQR method (values beyond 1.5×IQR from quartiles)
- **FR-013**: System MUST calculate and report skewness and kurtosis for all distributions
- **FR-014**: System MUST recommend alternative analyses when assumptions are violated (e.g., Welch's t-test for unequal variances)

**Visualization Generation**

- **FR-015**: System MUST generate box plots for each metric showing median, quartiles, range, and outliers by framework
- **FR-016**: System MUST generate violin plots showing full distribution shapes (kernel density estimation) for each metric by framework
- **FR-017**: System MUST generate forest plots showing effect sizes and 95% CIs for all pairwise comparisons
- **FR-018**: System MUST generate Q-Q plots for normality assessment of each metric-framework combination
- **FR-019**: System MUST save all statistical visualizations as publication-quality SVG files (300 DPI equivalent) in `output_dir/figures/statistical/` (separate from existing `output_dir/figures/` used by paper generation pipeline)
- **FR-020**: System MUST embed statistical visualizations in both markdown reports using relative paths to `figures/statistical/`
- **FR-021**: Statistical visualizations MUST use colorblind-friendly palette (e.g., matplotlib 'tab10' or seaborn 'colorblind')
- **FR-022**: Statistical visualizations MUST include clear axis labels, titles, legends, and figure numbers for publication readiness
- **FR-023**: System MUST generate visualizations during `ExperimentAnalyzer.analyze()` execution (same phase as report generation) to ensure data consistency

**Report Structure & Documentation**

- **FR-024**: System MUST generate TWO report versions: `statistical_report_summary.md` and `statistical_report_full.md` on every analysis run
- **FR-025**: System MUST include "Statistical Methodology" section documenting all tests used, selection rationale, significance levels, and corrections applied
- **FR-026**: System MUST include "Descriptive Statistics" section with enhanced tables showing mean, median, SD, min, max, Q1, Q3, skewness, kurtosis
- **FR-027**: System MUST include "Normality Assessment" section with Shapiro-Wilk results and Q-Q plots
- **FR-028**: System MUST include "Assumption Validation" section with Levene's test results and outlier detection
- **FR-029**: System MUST include "Statistical Comparisons" section with test results, effect sizes, and interpretations
- **FR-030**: System MUST include "Statistical Power Analysis" section with achieved power and sample size recommendations
- **FR-031**: System MUST provide interpretation guidance for each test result in plain language
- **FR-032**: System MUST document Python library versions (scipy, numpy, statsmodels, matplotlib, seaborn) in methodology section
- **FR-033**: Summary report MUST include links/references to full report for complete details
- **FR-034**: Summary report MUST embed only critical visualizations (3-5 plots): primary metric box plot, effect size forest plot, power summary
- **FR-035**: Full report MUST embed all generated visualizations inline where contextually relevant

**Educational Content & User-Friendliness**

- **FR-050**: Every statistical test result MUST include a didactic "What is this?" explanation describing the test's purpose in simple terms (e.g., "Shapiro-Wilk test checks if your data follows a bell curve (normal distribution)")
- **FR-051**: Every statistical test result MUST include a "Why use it?" explanation describing why this specific test was chosen for the data (e.g., "We use this because we need to know if we can trust parametric tests like t-tests")
- **FR-052**: Every statistical test result MUST include a "How to interpret?" explanation with practical interpretation guidelines (e.g., "If p > 0.05, your data is approximately normal; if p < 0.05, consider non-parametric tests")
- **FR-053**: Every visualization MUST include a plain-language caption explaining what the plot shows and how to read it (e.g., "This box plot shows the middle 50% of your data in the box, with the line showing the median. Dots beyond whiskers are outliers")
- **FR-054**: Effect size results MUST include context for magnitude interpretation using analogies (e.g., "Cohen's d of 0.8 is a 'large' effect - like the height difference between 13 and 18 year-olds")
- **FR-055**: Statistical power warnings MUST explain practical implications in researcher-friendly language (e.g., "Your experiment is like trying to hear a whisper in a noisy room - you need more samples to confidently detect differences")
- **FR-056**: Technical terms MUST be accompanied by plain-language equivalents on first use (e.g., "p-value (probability of seeing this result by chance)", "95% CI (range where true value likely falls)")
- **FR-057**: Each report section MUST start with a 1-2 sentence summary explaining what the section tells you and why it matters
- **FR-058**: Reports MUST include a "Quick Start Guide" section with decision tree showing how to use the report (e.g., "Start here → Check normality → Look at effect sizes → Read power recommendations")

**Data Quality & Error Handling**

- **FR-036**: System MUST validate that all runs are verified before including in analysis
- **FR-037**: System MUST handle missing metric values gracefully (skip that metric for that framework)
- **FR-038**: System MUST handle sample size differences across frameworks (unbalanced design)
- **FR-039**: System MUST report number of runs analyzed vs. available for transparency

**Pipeline Integration & Paper Enhancement**

- **FR-040**: Statistical visualization generation MUST occur within `ExperimentAnalyzer.analyze()` method (called by `PaperGenerator` in Step 1)
- **FR-041**: Statistical figures directory (`output_dir/figures/statistical/`) MUST be created alongside existing figures directory (`output_dir/figures/`)
- **FR-042**: Statistical reports MUST reference statistical figures using relative paths that work when reports are in `output_dir/`
- **FR-043**: System MUST NOT interfere with existing `FigureExporter` functionality (existing comparative charts in `output_dir/figures/` remain unchanged)
- **FR-044**: `PaperGenerator` Results section MUST embed at least 2 statistical visualizations (box plot for primary metric + effect size forest plot)
- **FR-045**: `PaperGenerator` Methodology section MUST include "Statistical Analysis" subsection with test information from enhanced statistical report
- **FR-046**: `PaperGenerator` MUST read and parse `statistical_report_summary.md` to extract key findings for paper sections
- **FR-047**: `PaperGenerator` MUST include effect sizes and p-values in Results section text when describing metric comparisons
- **FR-048**: `PaperGenerator` Discussion section MUST include statistical power limitations paragraph when power warnings exist in statistical report
- **FR-049**: LaTeX/PDF compilation MUST successfully include both comparative charts AND statistical visualizations with proper figure numbering and captions

### Key Entities

- **MetricDistribution**: Represents the statistical properties of a metric for one framework (values, mean, median, SD, skewness, kurtosis, normality test results)
- **StatisticalTest**: Represents a hypothesis test result (test type, statistic value, p-value, degrees of freedom, interpretation)
- **EffectSize**: Represents an effect size estimate (measure type, point estimate, 95% CI, magnitude interpretation)
- **PowerAnalysis**: Represents statistical power calculation (achieved power, required sample size for 80% power, power curve data)
- **Visualization**: Represents a generated plot (type, file path, metric name, frameworks included)
- **AssumptionCheck**: Represents validation of a statistical assumption (assumption type, test used, result, recommendation)
- **StatisticalFindings** (NEW): Structured data returned by `ExperimentAnalyzer.analyze()` for use by `PaperGenerator`:
  - `comparisons`: List of pairwise comparisons with effect sizes, CIs, p-values, test types
  - `primary_metric`: Name of most important metric (e.g., "execution_time")
  - `visualization_paths`: Dict mapping viz types to file paths (e.g., `{"box_plot": "figures/statistical/execution_time_boxplot.svg"}`)
  - `power_warnings`: List of warnings for underpowered comparisons
  - `methodology_summary`: Plain text description of statistical methods used (for paper methodology section)
  - `key_findings`: List of interpretable statements (e.g., "Framework A significantly outperformed B with large effect")

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Statistical Rigor**

- **SC-001**: Reports include normality tests for 100% of metrics with n≥3 per framework
- **SC-002**: Reports select statistically appropriate tests (parametric vs. non-parametric) based on normality assessment in 100% of cases
- **SC-003**: Reports include effect size calculations with 95% CIs for all comparisons
- **SC-004**: Reports apply multiple comparison corrections when comparing 3+ frameworks with documented adjusted α threshold

**Power & Sample Size Guidance**

- **SC-005**: Reports calculate achieved statistical power for all comparisons
- **SC-006**: Reports provide sample size recommendations when power is below 70%
- **SC-007**: Reports warn users when sample sizes are too small (n<5) for reliable inference

**Visualization Quality**

- **SC-008**: Reports include at least 4 visualization types (box plot, violin plot, forest plot, Q-Q plot) embedded as SVG images
- **SC-009**: All visualizations are publication-quality (300 DPI equivalent, clear labels, appropriate scaling)
- **SC-010**: Summary report embeds 3-5 critical visualizations; full report embeds all visualizations
- **SC-011**: Visualizations are embedded in markdown with descriptive captions and figure numbers

**Documentation Completeness**

- **SC-012**: Both report versions include complete "Statistical Methodology" section documenting test selection, significance levels, corrections, and software versions
- **SC-013**: Reports provide plain-language interpretation for 100% of statistical tests (not just p-values)
- **SC-014**: Reports document all assumption violations detected and recommend alternative analyses
- **SC-015**: Summary report includes clear links to full report for additional details

**Reproducibility**

- **SC-016**: Another researcher can reproduce the exact analysis given the raw data and documented methodology
- **SC-017**: Reports include sufficient detail for peer review (test selection rationale, correction methods, effect size interpretations)
- **SC-018**: Both summary and full reports are generated on every analysis run (100% consistency)

**Educational Content & Accessibility**

- **SC-025**: Every statistical test includes "What is this?", "Why use it?", and "How to interpret?" explanations in simple language (8th grade reading level)
- **SC-026**: Every visualization includes a plain-language caption explaining what it shows and how to read it
- **SC-027**: Effect size interpretations include practical analogies or examples (not just numerical thresholds)
- **SC-028**: Technical terms have plain-language equivalents on first use (100% of jargon explained)
- **SC-029**: Each major report section begins with a 1-2 sentence summary of what it tells you and why it matters
- **SC-030**: Reports include "Quick Start Guide" helping readers navigate and use the statistical information efficiently

**Paper Quality Enhancement**

- **SC-019**: Generated paper's Results section includes at least 2 embedded statistical visualizations with descriptive captions
- **SC-020**: Generated paper's Methodology section includes "Statistical Analysis" subsection documenting tests performed
- **SC-021**: Generated paper's Results text mentions effect sizes and p-values when comparing frameworks (not just mean differences)
- **SC-022**: Generated paper's Discussion section includes statistical limitations paragraph when power is below 70%
- **SC-023**: Final PDF includes both comparative charts and statistical plots with consistent formatting and figure numbering
- **SC-024**: Paper's figure captions for statistical plots include interpretation guidance (e.g., "Box plot shows median execution time with quartiles and outliers")

## Assumptions *(optional)*

- Python environment includes scipy (≥1.9.0), statsmodels (≥0.14.0), matplotlib (≥3.5.0), seaborn (≥0.12.0) for statistical analysis and visualization
- Experiment data follows the existing structure (verified runs in metrics.json with aggregate_metrics)
- Sample sizes are typically between 2-50 runs per framework (handles both small and moderate samples)
- **Users have varying levels of statistical expertise** - from basic undergraduate statistics to expert level - and all need accessible explanations
- **Educational content should target 8th grade reading level** for core explanations while maintaining scientific accuracy
- Generated visualizations will be viewed in markdown-compatible renderers (GitHub, VS Code, Jupyter) that support embedded SVG/PNG with emoji icons (📚, 💡, ⚠️, ✅, 🎓)
- Statistical significance threshold defaults to α=0.05 (configurable in experiment.yaml if needed)
- Effect size thresholds follow Cohen's conventions: small (0.2/0.147), medium (0.5/0.33), large (0.8/0.474) for d/delta respectively
- Bootstrap resampling uses 10,000 iterations for stable CI estimates (matches existing practice in codebase)
- Independence assumption: runs are truly independent (no cross-contamination between runs)
- **Plain-language analogies and examples** are valuable for making abstract statistical concepts concrete (e.g., comparing effect sizes to height differences between age groups)

## Dependencies *(optional)*

- Existing `ExperimentAnalyzer` class provides the framework for data loading and aggregation
- Existing `PaperGenerator` class provides paper section generation methods to be enhanced
- Existing verified run filtering logic ensures data quality
- matplotlib/seaborn for visualization generation
- scipy.stats for statistical tests (shapiro, mannwhitneyu, kruskal, ttest_ind, f_oneway, levene)
- statsmodels for power analysis (statsmodels.stats.power)
- numpy for bootstrap resampling and numerical operations
- PaperGenerator's section generation methods (_generate_methodology_section, _generate_results_section, _generate_discussion_section) will be enhanced to incorporate statistical content

## Out of Scope

- Bayesian statistical approaches (use frequentist methods)
- Machine learning model comparisons or predictions
- Time series analysis of metrics over sequential steps
- Multivariate analysis (e.g., MANOVA, PCA) - focus on univariate comparisons
- Interactive visualizations (use static publication-ready plots)
- Automatic outlier removal (detect and report, but don't remove)
- Custom statistical test implementations (use established scipy/statsmodels implementations)
- Real-time streaming analysis (works with completed experiment data)
- Integration with external statistical software (R, SPSS) - pure Python implementation
- Modifying the paper's Abstract or Introduction sections (statistical content goes in Methodology/Results/Discussion only)
- Creating entirely new paper sections (enhance existing sections with statistical content)
- Replacing existing comparative bar charts (statistical plots are additive, not replacements)

## Technical Notes *(optional)*

**Implementation Strategy**:

1. **Enhance `ExperimentAnalyzer` (Step 1)**:
   - Extend `_write_statistical_report()` method with comprehensive analysis
   - Create helper methods: `_test_normality()`, `_perform_statistical_tests()`, `_calculate_effect_sizes()`, `_calculate_power()`, `_validate_assumptions()`, `_generate_statistical_visualizations()`
   - **NEW**: Create `_format_didactic_explanation()` helper to generate "What/Why/How" sections for each test
   - **NEW**: Create `_generate_analogy()` helper to produce appropriate analogies for effect sizes and concepts
   - **NEW**: Create `_format_plain_language()` helper to simplify technical terms with parenthetical definitions
   - Generate TWO report versions: summary and full, both with educational content
   - Return structured statistical data for paper generation

2. **Enhance `PaperGenerator._load_analyzed_data()` (Step 2)**:
   - Load and parse `statistical_report_summary.md`
   - Extract key statistical findings:
     - Effect sizes and confidence intervals for each comparison
     - P-values for statistical significance
     - Power warnings (if any)
     - Primary statistical visualizations paths
   - Store in `self.statistical_data` for use in paper sections

3. **Enhance `PaperGenerator._generate_methodology_section()` (Step 3a)**:
   - Add "Statistical Analysis" subsection after experimental setup
   - Include: normality testing approach, test selection criteria, effect size measures, significance level, multiple comparison correction method
   - **Use simplified explanations** from statistical report for readability
   - Source content from parsed statistical report

4. **Enhance `PaperGenerator._generate_results_section()` (Step 3b)**:
   - Embed statistical box plot for primary metric (e.g., execution time)
   - Embed effect size forest plot showing all pairwise comparisons
   - Modify results text to include effect sizes and p-values when describing differences
   - Example: "Framework A was significantly faster than Framework B (t(18)=3.45, p=0.003, d=1.23, 95% CI [0.45, 2.01])"

5. **Enhance `PaperGenerator._generate_discussion_section()` (Step 3c)**:
   - If statistical power warnings exist, add "Statistical Limitations" paragraph
   - Include recommended sample sizes for future work
   - Mention achieved power levels and implications

6. **Enhance `PaperGenerator._convert_to_latex()` (Step 6)**:
   - Include both `figures/` and `figures/statistical/` directories in LaTeX compilation
   - Ensure proper figure numbering across both directories
   - Generate appropriate LaTeX figure captions from markdown

7. **Ensure backward compatibility**: If statistical analysis fails, fall back to basic descriptive statistics and continue paper generation

**Pipeline Integration Architecture**:

```
PaperGenerator.generate()
  └─> Step 1: analyzer = ExperimentAnalyzer(experiment_dir, output_dir)
      └─> analyzer.analyze()
          ├─> _aggregate_framework_metrics()      # Existing
          ├─> _write_metrics_json()                # Existing
          ├─> _write_statistical_report()          # ENHANCED
          │   ├─> _test_normality()                # NEW
          │   ├─> _perform_statistical_tests()     # NEW
          │   ├─> _calculate_effect_sizes()        # NEW
          │   ├─> _calculate_power()               # NEW
          │   ├─> _validate_assumptions()          # NEW
          │   ├─> _generate_statistical_visualizations()  # NEW
          │   │   └─> Creates figures/statistical/*.svg
          │   ├─> _write_statistical_report_summary()     # NEW
          │   │   └─> statistical_report_summary.md (with 3-5 plots)
          │   └─> _write_statistical_report_full()        # NEW
          │       └─> statistical_report_full.md (with all plots)
          └─> Returns frameworks_data
  
  └─> Step 2: _load_analyzed_data()                # ENHANCED
      ├─> Load metrics.json                        # Existing
      └─> Load statistical_report_summary.md       # NEW
          └─> Parse effect sizes, p-values, power warnings
  
  └─> Step 3: _generate_all_sections()             # ENHANCED
      ├─> _generate_methodology_section()          # ENHANCED
      │   └─> Add "Statistical Analysis" subsection with test info
      ├─> _generate_results_section()              # ENHANCED
      │   ├─> Embed statistical box plots          # NEW
      │   ├─> Embed effect size forest plot        # NEW
      │   └─> Include effect sizes + p-values in text  # NEW
      ├─> _generate_discussion_section()           # ENHANCED
      │   └─> Add power/limitations paragraph if warnings exist  # NEW
      └─> Other sections...                        # Existing
  
  └─> Step 4: FigureExporter.export_figures()      # Existing (UNCHANGED)
      └─> Creates figures/*.pdf and figures/*.png   # Comparative charts
  
  └─> Step 5: _combine_sections_to_markdown()      # Existing
  └─> Step 6: _convert_to_latex()                  # ENHANCED
      └─> Include both figures/ and figures/statistical/ in LaTeX
  └─> Step 7: _compile_latex_to_pdf()              # Existing
  └─> Step 8: _generate_metadata_yaml()            # Existing
  └─> Step 9: Logging and cleanup                  # Existing
```

**Directory Structure After Enhancement**:
```
output_dir/
├── metrics.json                          # Existing: aggregated metrics
├── statistical_report_summary.md         # NEW: concise report
├── statistical_report_full.md            # NEW: comprehensive report
└── figures/
    ├── execution_time_comparison.pdf     # Existing: from FigureExporter
    ├── execution_time_comparison.png     # Existing: from FigureExporter
    ├── total_cost_usd_comparison.pdf     # Existing: from FigureExporter
    ├── total_cost_usd_comparison.png     # Existing: from FigureExporter
    └── statistical/                      # NEW: statistical visualizations
        ├── execution_time_boxplot.svg
        ├── execution_time_violinplot.svg
        ├── total_cost_usd_boxplot.svg
        ├── total_cost_usd_violinplot.svg
        ├── effect_sizes_forestplot.svg
        ├── power_analysis.svg
        ├── execution_time_baes_qqplot.svg
        ├── execution_time_chatdev_qqplot.svg
        └── ... (Q-Q plots for each metric-framework)
```

**Key Integration Points**:

1. **Non-Interference**: Statistical visualizations use separate subdirectory (`figures/statistical/`) to avoid conflicts with existing `FigureExporter` outputs
2. **Timing**: Statistical analysis and visualization occur in Step 1 (before paper prose generation), ensuring figures are available if needed in paper sections
3. **Format Consistency**: Use SVG (like existing pipeline preference) for scalability and small file size
4. **Reusability**: Statistical reports can be read by paper generation pipeline if needed (e.g., for methodology section content)

**Dual Report Structure**:

**Summary Report (`statistical_report_summary.md`):**
```
1. Table of Contents
2. Quick Start Guide (NEW - see below)
3. Executive Summary (1-2 paragraphs)
4. Statistical Methodology (condensed with educational explanations)
5. Key Findings Summary Table
6. Critical Visualizations (3-5 plots with didactic captions):
   - Primary metric box plot (e.g., execution_time)
   - Effect size forest plot (all pairwise comparisons)
   - Power analysis summary
7. Statistical Power Warnings (if applicable, with plain-language explanations)
8. Quick Recommendations
9. Link to Full Report
```

**Full Report (`statistical_report_full.md`):**
```
1. Table of Contents
2. Quick Start Guide (NEW - navigation helper)
3. Statistical Methodology (complete with "What/Why/How" sections)
4. Descriptive Statistics (all metrics, enhanced tables with explanations)
5. Normality Assessment (Shapiro-Wilk + Q-Q plots with educational content)
6. Assumption Validation (Levene's test + outliers with interpretations)
7. Statistical Comparisons (all tests + didactic interpretations)
8. Effect Size Analysis (all pairwise + forest plots with analogies)
9. Statistical Power Analysis (detailed per comparison with practical implications)
10. Visualizations Gallery:
    - Box plots (all metrics) with "how to read" guides
    - Violin plots (all metrics) with distribution explanations
    - Q-Q plots (all metric-framework combinations) with normality context
11. Detailed Recommendations (actionable, plain language)
12. Reproducibility Information
13. Glossary of Statistical Terms (plain-language definitions)
```

**Quick Start Guide Structure** (appears at top of both reports):
```markdown
## 🚀 Quick Start Guide

**New to statistics? Start here:**

1. **Check the Summary** (Section 3) - Get the big picture in 2 minutes
   - Are my results statistically significant?
   - Which framework performed better?
   - Should I collect more data?

2. **Understand Your Data Distribution** (Section 4-5)
   - Look at box plots to see spread and outliers
   - Check if data is normally distributed (affects which tests we use)
   - 🎓 Don't know what "normal distribution" means? See the explanation boxes!

3. **Evaluate Practical Significance** (Section 8)
   - Statistical significance ≠ practical importance
   - Check effect sizes to see if differences are large enough to matter
   - Look for "small/medium/large" interpretations

4. **Assess Confidence in Results** (Section 9)
   - Check statistical power
   - If power is low (<70%), you may need more runs
   - See recommendations for target sample sizes

5. **Use in Your Paper**
   - Copy methodology descriptions for your Methods section
   - Use effect sizes and p-values in Results section
   - Include power limitations in Discussion section

**Navigation Tips:**
- 📚 = Educational explanation (what it means, why it matters)
- 💡 = Interpretation guide (how to understand the numbers)
- ⚠️ = Warning (important limitation or consideration)
- ✅ = Good result (assumptions met, adequate power, etc.)
- 🎓 = New to this concept? Read this section first
```

**Statistical Test Selection Logic**:
```
IF n < 3 per group:
    → Skip tests, show descriptive stats only, warn about insufficient data
ELSE IF zero variance detected:
    → Skip tests for that metric, explain why
ELSE:
    → Run Shapiro-Wilk normality test
    IF all groups normal (p > 0.05) AND Levene's test passes:
        IF 2 groups: → Independent t-test, Cohen's d
        IF 3+ groups: → One-way ANOVA + post-hoc t-tests with Bonferroni, Cohen's d
    ELSE:
        IF 2 groups: → Mann-Whitney U test, Cliff's delta
        IF 3+ groups: → Kruskal-Wallis H + post-hoc Mann-Whitney with Bonferroni, Cliff's delta
```

**Educational Explanation Templates**:

Each statistical test/visualization in the report MUST follow this template structure:

**Template Structure**:
```markdown
### [Test/Visualization Name]

**📚 What is this?**
[1-2 sentence explanation in simple terms, 8th grade reading level]

**🎯 Why use it?**
[1-2 sentences explaining why this specific test/plot was chosen for THIS data]

**📊 Results**
[Actual test results with values]

**💡 How to interpret?**
[Plain-language interpretation with decision rules and practical meaning]

**Example:**
[Optional concrete example or analogy making the concept relatable]
```

**Concrete Didactic Explanation Examples**:

**Example 1: Shapiro-Wilk Normality Test**
```markdown
### Normality Test (Shapiro-Wilk)

**📚 What is this?**
The Shapiro-Wilk test checks if your data follows a "bell curve" pattern (normal distribution) - 
like heights in a population where most people are average and fewer are very short or very tall.

**🎯 Why use it?**
We need to know if your data is normally distributed because it determines which statistical 
tests are appropriate. Normal data lets us use more powerful tests (t-test, ANOVA), while 
non-normal data requires different approaches (Mann-Whitney, Kruskal-Wallis).

**📊 Results**
- BAES execution_time: W = 0.94, p = 0.234
- ChatDev execution_time: W = 0.88, p = 0.045

**💡 How to interpret?**
- **p > 0.05**: Data IS approximately normal ✅ → Can use parametric tests
- **p < 0.05**: Data is NOT normal ⚠️ → Should use non-parametric tests

For your data: BAES is normal (p=0.234), but ChatDev is not (p=0.045). We'll use 
non-parametric tests (Mann-Whitney U) to be safe.

**Example:**
Think of it like checking if test scores in a class follow the typical pattern: most students 
get B/C grades (middle), fewer get A's or F's (extremes). If all students got A's, that wouldn't 
be a normal distribution!
```

**Example 2: Cohen's d Effect Size**
```markdown
### Effect Size (Cohen's d)

**📚 What is this?**
Cohen's d measures HOW MUCH two groups differ, not just WHETHER they differ. It's the difference 
between group averages expressed in standard deviations - a universal measuring stick.

**🎯 Why use it?**
Statistical significance (p-values) tells you if a difference is real, but not if it's large 
enough to care about. Effect size tells you if the difference matters in practice. With large 
samples, even tiny meaningless differences can be "statistically significant."

**📊 Results**
- BAES vs ChatDev execution_time: d = 1.23, 95% CI [0.65, 1.81]

**💡 How to interpret?**
- **d = 0.2**: Small effect (noticeable only with careful measurement)
- **d = 0.5**: Medium effect (noticeable to careful observer)
- **d = 0.8+**: Large effect (obvious to casual observer)

Your result (d = 1.23) is a **VERY LARGE** effect - BAES is substantially faster than ChatDev 
in a practically meaningful way, not just statistically.

**Example:**
d = 0.8 is like the height difference between 13-year-olds and 18-year-olds - clearly noticeable.
Your d = 1.23 is even larger - more like comparing 10-year-olds to adults. The speed difference 
between frameworks is obvious and substantial.
```

**Example 3: Box Plot Visualization**
```markdown
![Execution Time Distribution](figures/statistical/execution_time_boxplot.svg)

**Figure 1: Execution Time Distribution by Framework**

**📚 What does this show?**
A box plot displays the spread and central tendency of your data. It shows you where most values 
fall and identifies outliers (unusual values).

**📊 How to read this plot:**
- **Box**: Contains the middle 50% of your data (from 25th to 75th percentile)
- **Line in box**: The median (middle value) - half your runs were faster, half slower
- **Whiskers**: Extend to show the range of "typical" values (within 1.5× the box height)
- **Dots beyond whiskers**: Outliers - runs that were unusually fast or slow
- **Notch** (if present): Confidence interval around median - non-overlapping notches suggest 
  significantly different medians

**💡 What this tells you:**
Looking at BAES vs ChatDev, you can see:
1. BAES box is lower (faster median execution time)
2. BAES box is narrower (more consistent performance)
3. ChatDev has outliers (some runs were unusually slow)

This suggests BAES is both faster AND more reliable than ChatDev.
```

**Example 4: Statistical Power Warning**
```markdown
### ⚠️ Statistical Power Warning

**📚 What is statistical power?**
Statistical power is your experiment's ability to detect a real difference if one exists. 
Think of it like the sensitivity of a measuring scale - a bathroom scale can't detect the 
weight of a feather, even though the feather has weight.

**🎯 Why does this matter?**
Your current sample size (n=5 runs per framework) gives you only **58% power** to detect 
medium-sized differences. This means:
- If there IS a real difference, you only have 58% chance of detecting it
- 42% of the time, you'd miss real differences and incorrectly conclude "no difference"

**💡 What should you do?**
To reach adequate power (80% - standard in research), you need **15 additional runs per framework** 
(total n=20).

**Example:**
It's like trying to hear someone whisper in a noisy room. With 5 trials, you might catch some 
words but miss others. With 20 trials, you're confident about what was said. More runs = clearer 
signal = stronger conclusions.

**Can I still use these results?**
Yes, but with caution:
- ✅ Large differences you found are likely real (hard to miss)
- ⚠️ "No difference" conclusions are uncertain (might be due to low power)
- 📝 Mention power limitations in your paper's limitations section
```

**Visualization Standards**:
- SVG format for vector graphics (scalable, small file size, publication-ready)
- Figure size: 10×6 inches (standard publication size)
- Font sizes: Title 14pt, axes labels 12pt, tick labels 10pt
- Color palette: Colorblind-friendly (seaborn 'colorblind' or matplotlib 'tab10')
- File naming: `{metric_name}_{plot_type}.svg` (e.g., `execution_time_boxplot.svg`)
- Save to: `output_dir/figures/statistical/`

**Statistical Visualization Requirements**:

1. **Box Plots** (`{metric}_boxplot.svg`):
   - Show median (center line), Q1/Q3 (box boundaries), whiskers (1.5×IQR or min/max)
   - Plot outliers as individual points beyond whiskers
   - X-axis: Framework names, Y-axis: Metric value with units
   - Include grid lines for readability
   - Example: `matplotlib.pyplot.boxplot()` with `showfliers=True`

2. **Violin Plots** (`{metric}_violinplot.svg`):
   - Kernel density estimation (KDE) overlaid on box plot elements
   - Show median marker and quartile lines
   - Symmetric distributions (mirror KDE on both sides)
   - X-axis: Framework names, Y-axis: Metric value with units
   - Use `seaborn.violinplot()` with `inner='quartile'`

3. **Forest Plots** (`effect_sizes_forestplot.svg`):
   - Horizontal layout: Y-axis lists framework pairs, X-axis shows effect size
   - Point estimate as marker (diamond or circle)
   - 95% CI as horizontal error bar
   - Vertical line at 0 (no effect) for reference
   - Include interpretation thresholds (small/medium/large) as shaded regions
   - Label each row with comparison (e.g., "baes vs chatdev")

4. **Q-Q Plots** (`{metric}_{framework}_qqplot.svg`):
   - Theoretical quantiles (normal distribution) on X-axis
   - Sample quantiles on Y-axis
   - Reference line (y=x) showing perfect normal distribution
   - Actual data points plotted
   - Title includes Shapiro-Wilk p-value for quantitative assessment
   - Example: `scipy.stats.probplot()` with `plot=plt`

**Integration with Existing FigureExporter**:

The existing `FigureExporter` (in `src/paper_generation/figure_exporter.py`) generates comparative bar charts during Step 4 of the paper generation pipeline. The enhanced statistical visualizations complement this by:

- **Separation**: Statistical plots in `figures/statistical/`, comparative charts in `figures/`
- **Purpose**: Statistical plots show distributions/assumptions, comparative charts show means
- **Usage**: Statistical plots embedded in statistical reports AND paper Results/Methodology sections, comparative charts in paper Results section
- **No Conflicts**: Both can coexist; paper includes both types of visualizations
- **Shared Standards**: Both use ≥300 DPI, publication-quality output

**Example Enhanced Paper Sections**:

**Methodology Section (NEW "Statistical Analysis" subsection)**:
```markdown
### Statistical Analysis

To assess the statistical significance of performance differences between frameworks, 
we performed the following analyses:

1. **Normality Testing**: Shapiro-Wilk tests were applied to each metric for each 
   framework to assess distributional assumptions (α=0.05).

2. **Hypothesis Testing**: For metrics meeting normality assumptions, independent-samples 
   t-tests (2 frameworks) or one-way ANOVA (3+ frameworks) were used. For non-normal 
   distributions, Mann-Whitney U tests (2 frameworks) or Kruskal-Wallis H tests (3+ frameworks) 
   were employed.

3. **Effect Sizes**: We calculated Cohen's d for parametric comparisons and Cliff's delta 
   for non-parametric comparisons, with 95% bootstrap confidence intervals (10,000 resamples). 
   Effect sizes were interpreted using Cohen's conventions: small (d=0.2, δ=0.147), 
   medium (d=0.5, δ=0.33), large (d=0.8, δ=0.474).

4. **Multiple Comparisons**: When comparing 3+ frameworks, Bonferroni correction was 
   applied to control family-wise error rate.

5. **Power Analysis**: Post-hoc statistical power was calculated using statsmodels to 
   assess the adequacy of sample sizes for detecting medium effect sizes (α=0.05, power=0.80).

All analyses were performed using Python 3.11 with scipy (v1.11.0), statsmodels (v0.14.0), 
and numpy (v1.24.0).
```

**Results Section (ENHANCED with statistical content)**:
```markdown
### Results

#### Execution Time Performance

Figure 1 shows the execution time distributions for each framework across all experimental runs.

![Execution Time Distribution](figures/statistical/execution_time_boxplot.svg)
*Figure 1: Box plot showing execution time distributions. Boxes indicate median and quartiles, 
whiskers extend to 1.5×IQR, and individual outliers are plotted.*

The mean execution time was 45.2s (SD=5.3) for BAES and 62.8s (SD=8.1) for ChatDev. 
An independent-samples t-test revealed a statistically significant difference favoring 
BAES (t(18)=5.23, p<0.001, Cohen's d=2.34, 95% CI [1.45, 3.18]). This represents a 
very large effect size, indicating substantial practical significance.

Figure 2 summarizes effect sizes for all pairwise framework comparisons across key metrics.

![Effect Size Comparison](figures/statistical/effect_sizes_forestplot.svg)
*Figure 2: Forest plot showing effect sizes with 95% confidence intervals for all pairwise 
framework comparisons. Points to the right of zero favor the first framework in each pair.*

#### Cost Analysis

[Comparative bar chart from existing FigureExporter]
*Figure 3: Mean total cost (USD) by framework with error bars showing standard error.*

...
```

**Discussion Section (ENHANCED with power/limitations)**:
```markdown
### Discussion

...existing content...

#### Statistical Limitations

While our findings show statistically significant and practically meaningful differences, 
we note some limitations in statistical power for secondary metrics. ⚠️ **WARNING**: 
The comparison of total API calls achieved only 58% power for detecting medium effect sizes. 
We recommend collecting at least 15 additional runs per framework (target n=25) to achieve 
adequate power (80%) for comprehensive evaluation of all metrics. Future work should 
consider larger sample sizes, especially when evaluating metrics with high variance or 
smaller expected effect sizes.
```

**Performance Considerations**:
- Bootstrap resampling (10,000 iterations) may take 1-2 seconds per metric-framework combination
- For experiments with many metrics (>20) and frameworks (>3), total analysis time may be 30-60 seconds
- Generate visualizations in parallel if possible to reduce total time
- Cache normality test results to avoid recalculation

## Design Decisions *(resolved)*

### Decision 1: Report Format Preference ✅

**Context**: The current `statistical_report.md` is relatively simple (basic tables). The enhanced version will be substantially longer with multiple sections, visualizations, and detailed interpretations.

**Decision**: **Single comprehensive well-structured markdown file**

**Rationale**: Easier to reference in papers, all information in one place. The report will be organized with clear hierarchical sections and a table of contents for easy navigation despite the length (500-1000 lines expected).

**Implementation**:
- Single `statistical_report.md` file with clear section hierarchy
- Table of contents at the top with anchor links to major sections
- Clear visual separators between sections using markdown headers and horizontal rules
- Logical flow: Methodology → Descriptive Stats → Normality → Tests → Power → Visualizations → Summary

---

### Decision 2: Visualization Embedding Strategy ✅

**Context**: The report will generate many plots (box plots, violin plots, forest plots, Q-Q plots for each metric). For 10 metrics × 4 plot types = 40 images.

**Decision**: **Create TWO versions - summary report + full report**

**Rationale**: Maximum flexibility for different use cases. Summary report for quick insights and presentations, full report for comprehensive peer review and detailed analysis.

**Implementation**:
- **`statistical_report_summary.md`**: Includes key visualizations only (3-5 plots):
  - 1 box plot for most important metric (e.g., execution_time)
  - 1 forest plot showing all pairwise effect sizes
  - 1 power analysis summary plot
  - Critical tables and interpretations only
  - Links to full report for complete details
  
- **`statistical_report_full.md`**: Includes ALL visualizations inline:
  - Box plots for all metrics
  - Violin plots for all metrics
  - Forest plots for all comparisons
  - Q-Q plots for all metric-framework combinations
  - All statistical tables and detailed interpretations
  - Complete methodology documentation

**Both reports MUST be generated every time** to ensure consistency and availability of both formats.

---

### Decision 3: Statistical Power Recommendations ✅

**Context**: Power analysis will recommend target sample sizes (e.g., "Need 20 runs for 80% power to detect medium effect"). This could be very conservative for exploratory studies or when resources are limited.

**Decision**: **Prescriptive with warnings when power is low**

**Rationale**: Encourages statistical rigor and prevents premature conclusions from underpowered experiments. While this may be impractical for expensive experiments, it maintains scientific standards and makes underpowered conclusions explicit.

**Implementation**:
- Calculate achieved power for each comparison
- When power < 70%: Display **WARNING** badge and explicit recommendation
- Prescriptive language: "⚠️ WARNING: Current power is X%. **You need N additional runs to achieve 80% power** for detecting medium effects at α=0.05."
- When power ≥ 70%: Display **ADEQUATE** badge with achieved power
- When power ≥ 90%: Display **EXCELLENT** badge
- Always show: current n, achieved power, required n for 80% power, effect size used for calculation
- Include disclaimer: "These recommendations assume medium effect sizes. Adjust based on your minimum detectable difference requirements."
