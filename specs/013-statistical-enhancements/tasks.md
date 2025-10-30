# Implementation Tasks: Statistical Analysis Enhancements

**Feature**: 013-statistical-enhancements  
**Total Tasks**: 11 tasks across 3 phases

---

## Phase 1: Warning System Infrastructure (1-2 days)

### TASK-013-01: Add warnings field to StatisticalFindings model
- **File**: `src/paper_generation/models.py`
- **Dependencies**: None
- **Description**: Add warning tracking capability to StatisticalFindings dataclass
- **Steps**:
  1. Import `List` and `field` from dataclasses
  2. Add `warnings: List[str] = field(default_factory=list)` to StatisticalFindings
  3. Add method: `add_warning(self, category: str, message: str)`
  4. Method implementation: `self.warnings.append(f'**{category}**: {message}')`
- **Status**: [X] Complete

---

### TASK-013-02: Integrate warning collection in analyzer
- **File**: `src/paper_generation/statistical_analyzer.py`
- **Dependencies**: TASK-013-01
- **Description**: Add warning collection calls throughout statistical analysis
- **Steps**:
  1. Update method signatures to pass `findings` object where needed
  2. Add `findings.add_warning('Zero Variance', ...)` when zero variance detected
  3. Add `findings.add_warning('Deterministic CI', ...)` for deterministic CIs
  4. Add `findings.add_warning('Assumption Violation', ...)` for normality/variance violations
  5. Add `findings.add_warning('Outliers Detected', ...)` for outlier detection
  6. Keep existing `logger.warning()` calls for CLI output (don't remove)
- **Status**: [X] Complete

---

### TASK-013-03: Add CLI warning summary
- **File**: `src/paper_generation/experiment_analyzer.py`
- **Dependencies**: TASK-013-02
- **Description**: Display warning summary at end of analysis in CLI
- **Steps**:
  1. Locate `analyze_experiment()` method
  2. After analysis completes, check `if findings.warnings:`
  3. Print separator: `logger.warning("=" * 60)`
  4. Print header: `logger.warning("ANALYSIS WARNINGS SUMMARY (%d issues)", len(findings.warnings))`
  5. Print separator again
  6. Enumerate warnings: `for i, warning in enumerate(findings.warnings, 1):`
  7. Print each: `logger.warning(f"{i}. {warning}")`
  8. Print closing separator
- **Status**: [X] Complete

---

### TASK-013-04: Add Markdown warning section
- **File**: `src/paper_generation/experiment_analyzer.py`
- **Dependencies**: TASK-013-02
- **Description**: Add warning section to generated Markdown reports
- **Steps**:
  1. Locate `_generate_statistical_report()` method
  2. Find where methodology section is added
  3. After methodology section, before glossary, add:
     ```python
     if findings.warnings:
         sections.append("## ⚠️ Notes and Warnings\n\n")
         sections.append(
             "The following conditions were detected during analysis "
             "and may affect interpretation:\n\n"
         )
         for i, warning in enumerate(findings.warnings, 1):
             sections.append(f"{i}. {warning}\n")
         sections.append("\n")
     ```
  4. Update section numbering after this insertion (Methodology 6→5, Glossary 7→6 if needed)
- **Status**: [X] Complete

---

## Phase 2: Effect Size Interpretation & Visuals (2 days)

### TASK-013-05: Add effect size interpretation to glossary
- **File**: `src/paper_generation/educational_content.py`
- **Dependencies**: None
- **Description**: Add interpretation tables for Cohen's d and Cliff's Delta
- **Steps**:
  1. Locate `get_statistical_glossary()` method
  2. Add new subsection: "### Effect Size Interpretation Guide"
  3. Add Cohen's d table with ranges:
     - |d| < 0.2: Negligible - Minimal practical difference
     - 0.2 ≤ |d| < 0.5: Small - Detectable but modest difference
     - 0.5 ≤ |d| < 0.8: Medium - Moderate, meaningful difference
     - |d| ≥ 0.8: Large - Substantial difference
  4. Add Cliff's Delta table with ranges:
     - |δ| < 0.147: Negligible - Groups largely overlap
     - 0.147 ≤ |δ| < 0.33: Small - One group tends higher
     - 0.33 ≤ |δ| < 0.474: Medium - Clear tendency difference
     - |δ| ≥ 0.474: Large - Strong separation
     - |δ| = 1.0: Complete - No overlap (all A > all B)
  5. Add context note: "Effect size interpretation should consider domain context. Small effects may be practically important in performance benchmarking."
- **Status**: [X] Complete

---

### TASK-013-06: Add zero-variance indicators to box plots
- **File**: `src/paper_generation/statistical_visualizations.py`
- **Dependencies**: None
- **Description**: Visual indicators for zero-variance distributions in box plots
- **Steps**:
  1. Locate box plot creation method (likely `_create_box_plot` or similar)
  2. Before plotting each distribution, check: `std_dev == 0 or IQR < 0.01`
  3. If zero-variance detected:
     - Draw horizontal line: `ax.axhline(y=mean, xmin=x_pos-0.2, xmax=x_pos+0.2, color='red', linewidth=3)`
     - Add annotation: `ax.annotate('No variation', xy=(x_pos, mean), ...)`
     - Skip normal box plot for this distribution
  4. Else: plot normally with standard box plot
  5. Track if any zero-variance detected, add legend entry: "Zero Variance" if any found
- **Status**: [ ] Not Started

---

### TASK-013-07: Add deterministic CI indicators to forest plots
- **File**: `src/paper_generation/statistical_visualizations.py`
- **Dependencies**: None
- **Description**: Visual indicators for deterministic CIs in forest plots (Cliff's Delta)
- **Steps**:
  1. Locate forest plot creation method (Cliff's Delta effect size plot)
  2. When plotting each effect size point, check: `abs(value) == 1.0 AND ci_lower == ci_upper`
  3. If deterministic CI:
     - Use open marker: `marker='o', facecolors='none'`
     - Use red edge: `edgecolors='red', linewidths=2`
     - Larger size: `s=150`
  4. Else: use normal filled marker
  5. Track if any deterministic found, add legend entry: "Complete Separation" if any found
- **Status**: [ ] Not Started

---

## Phase 3: Code Refactoring (2-3 days)

### TASK-013-08: Create statistical configuration module
- **File**: `src/paper_generation/config.py` (NEW FILE)
- **Dependencies**: None
- **Description**: Create centralized configuration for statistical analysis
- **Steps**:
  1. Create new file `src/paper_generation/config.py`
  2. Import: `from dataclasses import dataclass`
  3. Define StatisticalConfig dataclass with fields:
     ```python
     @dataclass
     class StatisticalConfig:
         """Configuration for statistical analysis parameters."""
         # Significance testing
         alpha: float = 0.05
         random_seed: int = 42
         bootstrap_iterations: int = 10000
         target_power: float = 0.80
         
         # Zero-variance detection
         variance_threshold_sd: float = 0.01
         variance_threshold_iqr: float = 0.01
         
         # Effect size interpretation thresholds
         cohens_d_small: float = 0.2
         cohens_d_medium: float = 0.5
         cohens_d_large: float = 0.8
         
         cliffs_delta_small: float = 0.147
         cliffs_delta_medium: float = 0.33
         cliffs_delta_large: float = 0.474
         
         # Reporting preferences
         decimal_places_effect: int = 3
         decimal_places_pvalue: int = 3
         
         # Multiple comparison correction
         correction_method: str = 'holm'  # Options: 'holm', 'bonferroni', 'fdr_bh'
     ```
  4. Add docstrings explaining each field
- **Status**: [ ] Not Started

---

### TASK-013-09: Extract variance checking method
- **File**: `src/paper_generation/statistical_analyzer.py`
- **Dependencies**: TASK-013-08
- **Description**: Extract variance checking logic into separate method
- **Steps**:
  1. Create new method: `_check_variance_quality(self, vals1, vals2, metric_name, group1, group2)`
  2. Move variance checking logic from `_calculate_effect_sizes()`:
     - Calculate: `std1 = np.std(vals1)`, `std2 = np.std(vals2)`
     - Calculate: `iqr1 = np.percentile(vals1, 75) - np.percentile(vals1, 25)`
     - Calculate: `iqr2 = np.percentile(vals2, 75) - np.percentile(vals2, 25)`
     - Detect: `zero_variance = (std1 < 0.01 or std2 < 0.01 or iqr1 < 0.01 or iqr2 < 0.01)`
  3. Return dict:
     ```python
     {
         'zero_variance': zero_variance,
         'skip_cohens_d': zero_variance,
         'std1': std1, 'std2': std2,
         'iqr1': iqr1, 'iqr2': iqr2,
         'metric_name': metric_name,
         'group1': group1, 'group2': group2
     }
     ```
  4. Update `_calculate_effect_sizes()` to call this method
- **Status**: [ ] Not Started

---

### TASK-013-10: Integrate config into analyzer initialization
- **File**: `src/paper_generation/statistical_analyzer.py`
- **Dependencies**: TASK-013-08, TASK-013-09
- **Description**: Use StatisticalConfig throughout analyzer
- **Steps**:
  1. Import: `from .config import StatisticalConfig`
  2. Update `__init__` signature: add `config: StatisticalConfig = None`
  3. In `__init__`: `if config is None: config = StatisticalConfig()`
  4. Store: `self.config = config`
  5. Replace hardcoded values with config references:
     - `0.01` → `self.config.variance_threshold_sd` (in variance checks)
     - `0.01` → `self.config.variance_threshold_iqr` (in IQR checks)
     - `10000` → `self.config.bootstrap_iterations` (in bootstrap)
     - `'holm'` → `self.config.correction_method` (in multiple comparison)
     - Effect size thresholds (small/medium/large) → config values
  6. Update `_check_variance_quality()` to use config thresholds
- **Status**: [ ] Not Started

---

### TASK-013-11: Standardize logging levels
- **Files**: 
  - `src/paper_generation/statistical_analyzer.py`
  - `src/paper_generation/experiment_analyzer.py`
- **Dependencies**: None (can be done in parallel)
- **Description**: Ensure consistent logging level usage
- **Steps**:
  1. Review all `logger.debug()`, `logger.info()`, `logger.warning()`, `logger.error()` calls
  2. Apply standard:
     - `logger.info()` for milestones: "Analysis started", "Analysis complete"
     - `logger.warning()` for data quality issues: "Zero variance detected", "Outliers found"
     - `logger.debug()` for detailed diagnostics: "Skipping effect size", "Using test X"
     - `logger.error()` for failures: "Analysis failed", "File not found"
  3. Use format strings instead of concatenation:
     - Before: `logger.warning("Zero variance for " + metric)`
     - After: `logger.warning("Zero variance for %s", metric)`
  4. Example standardization:
     - Data quality: `logger.warning("Zero variance in %s for %s", metric, framework)`
     - Progress: `logger.info("Analyzing %d metrics: %s", len(metrics), metrics)`
     - Debugging: `logger.debug("Skipping effect size for %s vs %s: zero variance", g1, g2)`
- **Status**: [ ] Not Started

---

## Execution Order

### Sequential Tasks (must complete in order):
1. **Phase 1**: TASK-013-01 → TASK-013-02 → TASK-013-03/04
   - Task 01 creates the data model
   - Task 02 depends on Task 01 (needs warnings field)
   - Tasks 03 and 04 depend on Task 02 (need populated warnings)

2. **Phase 3**: TASK-013-08 → TASK-013-09 → TASK-013-10
   - Task 08 creates the config
   - Task 09 can use config (depends on 08)
   - Task 10 integrates config everywhere (depends on 08, 09)

### Parallel Tasks (can be done independently):
- **Phase 2**: TASK-013-05, TASK-013-06, TASK-013-07 (all independent)
- **Phase 1/3**: TASK-013-11 (independent, can be done anytime)

### Recommended Execution Flow:
```
Phase 1: Tasks 01 → 02 → 03, 04 (parallel)
Phase 2: Tasks 05, 06, 07 (all parallel)
Phase 3: Tasks 08 → 09 → 10, and Task 11 (parallel with others)
```

---

## Notes

- **No automated tests**: Manual validation only
- **Backward compatibility**: All changes must not break existing code
- **Configuration defaults**: StatisticalConfig provides sensible defaults
- **Logging preservation**: Keep existing logger.warning() calls in CLI, add findings.add_warning() alongside
