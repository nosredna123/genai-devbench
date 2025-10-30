# Implementation Plan: Statistical Analysis Enhancements

**Feature ID**: 013  
**Branch**: `013-statistical-enhancements`  
**Priority**: High  
**Estimated Effort**: 5-7 days

## Overview

Implement core enhancements to statistical analysis system based on expert review validation.
Focus on warning summary system, effect size interpretation, visual indicators, and code refactoring.

**Excludes**: 
- A priori power calculator
- Automated tests (manual testing only)
- Detailed documentation

## Technical Stack

- **Language**: Python 3.11+
- **Libraries**: 
  - scipy ≥1.11.0 (statistical tests)
  - statsmodels ≥0.14.0 (multiple comparison)
  - numpy ≥1.24.0 (numerical operations)
  - matplotlib (visualizations)
- **Project Structure**: Existing `src/paper_generation/` module

## Architecture

### Components to Modify

1. **Data Models** (`src/paper_generation/models.py`)
   - Add warning tracking to `StatisticalFindings`
   - Add `add_warning()` method for categorized warnings

2. **Configuration** (`src/paper_generation/config.py`) - NEW FILE
   - Create `StatisticalConfig` dataclass
   - Centralize all thresholds and parameters

3. **Statistical Analyzer** (`src/paper_generation/statistical_analyzer.py`)
   - Extract variance checking to separate method
   - Integrate configuration system
   - Add warning collection hooks
   - Standardize logging levels

4. **Experiment Analyzer** (`src/paper_generation/experiment_analyzer.py`)
   - Add CLI warning summary output
   - Add Markdown warning section generation
   - Standardize logging levels

5. **Educational Content** (`src/paper_generation/educational_content.py`)
   - Add effect size interpretation tables to glossary

6. **Visualizations** (`src/paper_generation/statistical_visualizations.py`)
   - Add zero-variance indicators to box plots
   - Add deterministic CI indicators to forest plots

## File Structure

```
src/paper_generation/
├── config.py                      # NEW - Statistical configuration
├── models.py                      # MODIFY - Add warnings tracking
├── statistical_analyzer.py        # MODIFY - Warning hooks, config, refactoring
├── experiment_analyzer.py         # MODIFY - Warning summaries
├── educational_content.py         # MODIFY - Effect size tables
└── statistical_visualizations.py  # MODIFY - Visual indicators
```

## Dependencies

- Feature 012 (Statistical report fixes) - **MERGED to main**

## Non-Functional Requirements

- **Code Quality**: Extract methods >50 lines, consistent logging
- **Backward Compatibility**: No breaking API changes, sensible defaults
- **Manual Testing**: All features validated manually (no automated tests)

## Success Criteria

- ✅ Warning summary in CLI when warnings exist
- ✅ Warning section in Markdown reports when warnings exist
- ✅ Effect size interpretation table in glossary
- ✅ Visual indicators for zero-variance in plots
- ✅ Configuration system with defaults
- ✅ Variance checking extracted to method
- ✅ Consistent logging levels
- ✅ Manual testing passes (5 scenarios)
- ✅ No breaking changes
