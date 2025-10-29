# Paper Generation Module

Automated generation of camera-ready research papers from experiment results with comprehensive statistical analysis.

## Quick Start

```bash
# Generate paper from experiment
python scripts/generate_paper.py <experiment_dir> --output-dir <output_dir>

# Example
python scripts/generate_paper.py ~/projects/my_experiment --output-dir papers/draft1
```

## What Gets Generated

### Core Outputs
- **`paper.md`** - Markdown paper with statistical analysis integrated
- **`paper.tex`** - LaTeX source (if not using `--skip-latex`)
- **`paper.pdf`** - Compiled PDF (if LaTeX compilation succeeds)

### Statistical Reports
- **`statistical_report_summary.md`** - Executive summary (<300 lines)
  - Key findings with effect sizes
  - Critical visualizations
  - Power recommendations
  
- **`statistical_report_full.md`** - Complete analysis (800-1200 lines)
  - Detailed methodology
  - All statistical tests (Shapiro-Wilk, t-test/Mann-Whitney, ANOVA/Kruskal-Wallis)
  - Effect sizes with bootstrap confidence intervals
  - Power analysis with sample size recommendations
  - Assumption validation (normality, variance homogeneity)
  - Educational explanations with plain-language interpretations

### Visualizations
- **`figures/comparative/`** - Traditional comparison charts (bar, line)
- **`figures/statistical/`** - Statistical visualizations (SVG format)
  - Box plots - Median, quartiles, outliers
  - Violin plots - Distribution shapes with KDE
  - Forest plots - Effect sizes with confidence intervals
  - Q-Q plots - Normality assessment per framework

### Metrics
- **`metrics.json`** - Aggregated experiment metrics
- **`statistical_report.md`** - Legacy basic statistical summary

## Command Options

```bash
python scripts/generate_paper.py <experiment_dir> [OPTIONS]

Required:
  experiment_dir              Path to experiment directory with runs/ folder

Optional:
  --output-dir DIR           Output directory (default: experiment_dir/paper)
  --skip-latex               Skip LaTeX/PDF compilation (Markdown only)
  --figures-only             Export only figures, skip paper generation
  --model MODEL              AI model for prose generation (default: gpt-4o-mini)
  --prose-level LEVEL        Prose detail: minimal|standard|detailed (default: standard)
  --verbose, -v              Enable debug logging
```

## Usage Examples

### Basic Paper Generation
```bash
# Generate complete paper with all artifacts
python scripts/generate_paper.py experiments/chatdev_vs_metagpt
```

### Quick Draft (No PDF)
```bash
# Skip LaTeX compilation for faster iterations
python scripts/generate_paper.py experiments/my_exp --skip-latex
```

### Custom Output Location
```bash
# Specify output directory
python scripts/generate_paper.py experiments/my_exp --output-dir papers/submission_v1
```

### Statistical Analysis Only
```bash
# Generate analysis artifacts, skip paper prose generation
python scripts/generate_paper.py experiments/my_exp --figures-only
```

### Minimal Prose
```bash
# Reduce AI-generated interpretation, focus on data
python scripts/generate_paper.py experiments/my_exp --prose-level minimal
```

## Paper Sections Generated

The generated paper includes:

1. **Abstract** - Auto-generated summary of experiment and key findings
2. **Introduction** - Context and motivation
3. **Methodology** - Experimental setup + **Statistical Analysis** subsection
4. **Results** - Comparative analysis + effect sizes + statistical visualizations
5. **Discussion** - Interpretation + power limitations + threats to validity
6. **Conclusion** - Summary and future work

### Statistical Integration

The paper automatically includes:
- ✅ **Methodology**: Statistical tests used, assumptions checked, effect size measures
- ✅ **Results**: Effect sizes (Cohen's d, Cliff's delta) alongside descriptive statistics
- ✅ **Results**: Embedded statistical visualizations (box plots, forest plots)
- ✅ **Discussion**: Power analysis limitations and sample size recommendations

## Architecture

### Pipeline Flow
```
ExperimentAnalyzer
  ├─> Load run data from runs/ directory
  ├─> Aggregate metrics (means, medians, counts)
  ├─> Perform statistical analysis (T001-T039)
  │    ├─> Normality tests (Shapiro-Wilk)
  │    ├─> Statistical tests (t-test/Mann-Whitney, ANOVA/Kruskal-Wallis)
  │    ├─> Effect sizes (Cohen's d, Cliff's delta) with bootstrap CIs
  │    ├─> Power analysis (achieved power, recommended n)
  │    └─> Generate visualizations (box, violin, forest, Q-Q plots)
  ├─> Generate statistical reports (summary + full)
  └─> Write metrics.json

PaperGenerator
  ├─> Load analyzed data (metrics.json + statistical reports)
  ├─> Parse statistical findings
  ├─> Generate prose for each section (via AI)
  ├─> Enhance sections with statistical content
  │    ├─> Methodology: Statistical Analysis subsection
  │    ├─> Results: Effect sizes + visualizations
  │    └─> Discussion: Power limitations
  ├─> Export figures (comparative + statistical)
  ├─> Write paper.md
  └─> Compile to paper.pdf (if LaTeX enabled)
```

### Key Modules

- **`experiment_analyzer.py`** - Data aggregation + statistical analysis entry point
- **`statistical_analyzer.py`** - Core statistical tests, effect sizes, power analysis
- **`statistical_visualizations.py`** - Box, violin, forest, Q-Q plot generation
- **`educational_content.py`** - Plain-language explanations ("What/Why/How")
- **`paper_generator.py`** - Paper prose generation + statistical integration
- **`figure_exporter.py`** - Traditional comparative chart generation
- **`prose_engine.py`** - AI-powered section prose generation

## Dependencies

### Required
- Python 3.11+
- scipy ≥1.11.0 - Statistical tests (Shapiro-Wilk, t-test, Mann-Whitney, ANOVA, Kruskal-Wallis, Levene)
- statsmodels ≥0.14.0 - Power analysis
- numpy ≥1.24.0 - Bootstrap resampling, numerical operations
- matplotlib ≥3.8.0 - Base plotting
- seaborn ≥0.12.0 - Statistical visualizations (KDE for violin plots)
- PyYAML ≥6.0 - Configuration parsing
- requests ≥2.31.0 - OpenAI API calls

### Optional (for PDF generation)
- LaTeX distribution (TeX Live, MikTeX) with pdflatex

## Configuration

Paper generation can be customized via experiment's `config/paper_config.yaml`:

```yaml
# Example paper configuration
paper:
  title: "Comparative Analysis of AI Coding Frameworks"
  authors:
    - "Researcher Name"
  sections:
    - abstract
    - introduction
    - methodology
    - results
    - discussion
    - conclusion
  
  prose_level: standard  # minimal | standard | detailed
  skip_latex: false
  
  # Statistical analysis settings (optional)
  statistical:
    alpha: 0.05           # Significance level
    power_target: 0.80    # Target statistical power
    bootstrap_n: 10000    # Bootstrap iterations
    random_seed: 42       # For reproducibility
```

## Troubleshooting

### LaTeX Compilation Fails
```bash
# Generate Markdown only
python scripts/generate_paper.py <experiment_dir> --skip-latex

# Then compile manually
cd <output_dir>
pdflatex paper.tex
```

### Missing Visualizations
Check that:
- Experiment has valid run data in `runs/` directory
- Each run has `metrics.json` with required fields
- At least 2 frameworks with 3+ runs each (for statistical analysis)

### Low Statistical Power Warnings
This is expected for small sample sizes. Recommendations:
- Run more iterations (target: 10-20 runs per framework)
- Check `statistical_report_summary.md` for recommended sample sizes
- Report power limitations in Discussion section

### API Key Issues
Set OpenAI API key for prose generation:
```bash
export OPENAI_API_KEY=your-key-here
# or
python scripts/generate_paper.py <experiment_dir> --api-key your-key-here
```

## Advanced Usage

### Programmatic API

```python
from pathlib import Path
from src.paper_generation.paper_generator import PaperGenerator
from src.paper_generation.models import PaperConfig

# Configure paper generation
config = PaperConfig(
    experiment_dir=Path("experiments/my_exp"),
    output_dir=Path("papers/draft1"),
    skip_latex=False,
    prose_level="standard"
)

# Generate paper
generator = PaperGenerator(config)
generator.generate()

print(f"Paper generated: {config.output_dir / 'paper.md'}")
```

### Custom Statistical Analysis

```python
from src.paper_generation.experiment_analyzer import ExperimentAnalyzer

# Analyze experiment with custom settings
analyzer = ExperimentAnalyzer(
    experiment_dir=Path("experiments/my_exp"),
    output_dir=Path("analysis")
)

# Run analysis
frameworks_data = analyzer.analyze()

# Access statistical findings
print(f"Frameworks: {list(frameworks_data.keys())}")
print(f"Metrics: {analyzer.available_metrics}")
```

## Performance

Expected performance on typical experiments:
- **Statistical Analysis**: <60 seconds (n=10 runs, 3 frameworks, 10 metrics)
- **Bootstrap Resampling**: <2 seconds per metric-framework pair (10,000 iterations)
- **Visualization Generation**: <5 seconds total (all plot types)
- **Paper Prose Generation**: 30-90 seconds (depends on AI model response time)
- **LaTeX Compilation**: 5-15 seconds (depends on system)

## Educational Features

All statistical reports include:
- 📚 **What/Why/How explanations** for each statistical test
- 💡 **Plain-language interpretations** (8th grade reading level)
- 📊 **Real-world analogies** for abstract concepts (e.g., "like height difference between age groups")
- ✅ **Practical recommendations** based on power analysis
- ⚠️ **Warnings** for violated assumptions with suggested alternatives
- 🎓 **Glossary** with definitions of all statistical terms
- 🚀 **Quick Start Guide** for non-statisticians

## References

For detailed specification and design decisions:
- Feature specification: `specs/011-enhance-statistical-report/spec.md`
- Implementation plan: `specs/011-enhance-statistical-report/plan.md`
- User guide: `specs/011-enhance-statistical-report/quickstart.md`
- API contracts: `specs/011-enhance-statistical-report/contracts/`

## Support

For issues or questions:
1. Check validation checklist in quickstart guide
2. Review logs with `--verbose` flag
3. Inspect statistical reports for warnings
4. Consult API contracts in `specs/011-enhance-statistical-report/contracts/`
