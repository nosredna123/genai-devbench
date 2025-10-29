# Paper Generation Architecture

## Overview

The paper generation system is now fully **self-contained** and requires only raw experiment run data as input. All analysis and paper generation happens internally within the generator repository.

## Design Principles

### Clean Separation
- **Experiment Repository**: Contains only raw run data (`runs/{framework}/{run_id}/metrics.json`)
- **Generator Repository**: Contains all analysis logic, paper generation code, and templates
- **Output Directory**: Contains all generated artifacts (analysis results + paper files)

### Self-Contained Pipeline
Paper generation now includes analysis as an internal step. No pre-generated analysis files are required in the experiment directory.

## Architecture

### Data Flow

```
Input:  experiment_dir/runs/{framework}/{run_id}/metrics.json (raw step-level data)
        ↓
Step 1: ExperimentAnalyzer reads runs/, computes statistics
        ↓
Output: output_dir/metrics.json (aggregated statistics)
        output_dir/statistical_report.md (summary report)
        ↓
Step 2: PaperGenerator loads analyzed data from output_dir
        ↓
Steps 3-9: Generate sections, figures, LaTeX, PDF, enhance README
        ↓
Output: output_dir/main.tex (paper source)
        output_dir/figures/*.{pdf,png} (visualizations)
        output_dir/*.{cls,bst,pdf} (LaTeX support files)
```

### Directory Structure

**Before (experiment_dir remains clean)**:
```
experiment_dir/
├── runs/
│   ├── ghspec/
│   │   ├── {run_id}/
│   │   │   └── metrics.json  ← Raw step-level data
│   ├── baes/
│   └── chatdev/
├── config/
├── src/
└── README.md
```

**After (all outputs in output_dir)**:
```
output_dir/
├── metrics.json              ← Step 1: Aggregated statistics
├── statistical_report.md     ← Step 1: Summary report
├── main.tex                  ← Step 7: Paper source
├── figures/                  ← Step 4: Visualizations
│   ├── execution_time_comparison.{pdf,png}
│   ├── total_cost_usd_comparison.{pdf,png}
│   ├── api_calls_comparison.{pdf,png}
│   └── tokens_total_comparison.{pdf,png}
└── ACM-Reference-Format.bst  ← LaTeX support files
```

## Implementation

### Key Components

#### 1. ExperimentAnalyzer (`src/paper_generation/experiment_analyzer.py`)

**Purpose**: Analyze raw experiment runs and generate aggregated statistics.

**Methods**:
- `__init__(experiment_dir, output_dir)`: Initialize with paths
- `analyze()`: Main entry point, returns frameworks_data dict
- `_aggregate_framework_metrics()`: Compute statistics per framework
- `_load_run_metrics()`: Load single run's metrics.json
- `_aggregate_metric()`: Compute mean/std/min/max for one metric
- `_write_metrics_json()`: Write aggregated data to output_dir
- `_write_statistical_report()`: Generate Markdown summary

**Input**: `experiment_dir/runs/{framework}/{run_id}/metrics.json`
**Output**: 
- `output_dir/metrics.json`
- `output_dir/statistical_report.md`

**Statistics Computed** (per framework):
- `num_runs`: Total valid runs
- `execution_time`: mean, std, min, max
- `total_cost_usd`: mean, std, min, max
- `api_calls`: mean, std, min, max
- `tokens_total`: mean, std, min, max

#### 2. PaperGenerator (`src/paper_generation/paper_generator.py`)

**Pipeline** (9 steps):

1. **Step 1: Analyze raw runs** (NEW)
   - Create ExperimentAnalyzer instance
   - Call `analyze()` to generate metrics.json and statistical_report.md
   - Write to output_dir

2. **Step 2: Load analyzed data** (modified)
   - Read frameworks_data from Step 1 (in-memory)
   - Load statistical_report.md from output_dir
   - Validate experiment metadata

3. **Step 3: Generate sections**
   - Abstract, Introduction, Related Work, Methodology, Results, Discussion, Conclusion
   - Use ProseEngine with GPT-3.5-turbo

4. **Step 4: Export figures**
   - Generate comparison visualizations (bar charts with error bars)
   - Export to PDF and PNG formats

5. **Step 5: Assemble paper structure**
   - Combine sections into full paper document

6. **Step 6: Insert citation placeholders**
   - Add `**[CITE: ...]**` markers for future bibliography

7. **Step 7: Convert to LaTeX**
   - Transform Markdown to LaTeX using custom converter
   - Write main.tex with ACM sigconf template

8. **Step 8: Compile PDF** (optional)
   - Run pdflatex if available and --skip-latex not set

9. **Step 9: Enhance experiment README**
   - Add reproduction guide section to experiment's README.md

### Usage

```bash
# Basic usage (output to default location)
python scripts/generate_paper.py /path/to/experiment

# Custom output directory
python scripts/generate_paper.py /path/to/experiment --output-dir /tmp/paper_output

# Skip LaTeX compilation (for faster iteration)
python scripts/generate_paper.py /path/to/experiment --skip-latex

# Generate only figures (no prose)
python scripts/generate_paper.py /path/to/experiment --figures-only

# Verbose logging
python scripts/generate_paper.py /path/to/experiment --verbose
```

## Migration from Old Architecture

### What Changed

**Old Approach** (INCORRECT):
- Required pre-generated `experiment_dir/analysis/metrics.json`
- PaperGenerator read from experiment_dir/analysis/
- Experiment directory was modified with analysis outputs

**New Approach** (CORRECT):
- Analysis happens automatically as Step 1
- All outputs written to output_dir
- Experiment directory stays clean (only raw data)

### Benefits

1. **Self-contained**: Single command generates everything
2. **Reproducible**: Same raw data → same outputs
3. **Clean separation**: Experiment repo stays pristine
4. **Flexible**: Can re-analyze with different parameters
5. **Maintainable**: All logic in generator repo

## Testing

### Test Case: Real Experiment

**Experiment**: `/home/amg/projects/uece/baes/test_29_0747/`

**Data**:
- ghspec: 29 runs (mean execution: 989.6s)
- baes: 34 runs (mean execution: 196.7s)
- chatdev: 33 runs (mean execution: 1256.6s)

**Command**:
```bash
python scripts/generate_paper.py /home/amg/projects/uece/baes/test_29_0747 \
  --output-dir /tmp/test_paper \
  --skip-latex \
  --verbose
```

**Results**:
- ✅ Step 1: Analysis completed (96 runs across 3 frameworks)
- ✅ Generated metrics.json in output_dir (1.7K)
- ✅ Generated statistical_report.md in output_dir (1.2K)
- ✅ Generated main.tex (23K, 2,931 words)
- ✅ Generated 8 figures (4 metrics × 2 formats)
- ✅ Experiment directory remains clean (no analysis/ created)
- ✅ Total time: 30.5 seconds

## Future Enhancements

1. **Parallel Analysis**: Process multiple frameworks concurrently
2. **Incremental Updates**: Only re-analyze new runs
3. **Custom Metrics**: Support user-defined aggregation functions
4. **Statistical Tests**: Add significance testing to analysis
5. **Caching**: Cache analysis results for faster iteration
6. **Validation**: Add schema validation for metrics.json format

## References

- Implementation: `src/paper_generation/experiment_analyzer.py`
- Integration: `src/paper_generation/paper_generator.py`
- Script: `scripts/generate_paper.py`
- Template: `templates/readme_reproduction_section.md`
