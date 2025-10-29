# GenAI-DevBench - Experiment Generator

**Generate standalone experiment projects for evaluating GenAI software development frameworks**

GenAI-DevBench is a powerful generator that creates complete, self-contained experiment projects for rigorous benchmarking of AI-powered development frameworks (BAES, ChatDev, GitHub Copilot). Each generated experiment is a fully independent Git repository with everything needed to run sophisticated comparative evaluations.

---

## 🎯 What Does This Do?

This generator creates **standalone experiment projects** that:

- ✅ Are completely independent (no dependencies on this generator after creation)
- ✅ Include only the code and configurations needed for your specific setup
- ✅ Come with one-command setup and execution scripts
- ✅ Are initialized as Git repositories ready for version control
- ✅ Can be distributed, archived, or run on any machine with Python 3.9+

**Think of it as:** A project template generator specifically designed for AI framework evaluation experiments.

---

## ⚡ Quick Start

### Prerequisites

- **Python 3.11+** (required)
- **Git** (required)
- **API Keys**: OpenAI for BAEs/ChatDev, GitHub token for Spec-kit
- **System**: 8GB RAM, 10GB disk space (per multi-framework run)

### Installation

```bash
# Clone repository
git clone https://github.com/nosredna123/genai-devbench.git
cd genai-devbench

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys:
#   OPENAI_API_KEY_BAES=sk-your-openai-key
#   OPENAI_API_KEY_CHATDEV=sk-your-openai-key
#   OPENAI_API_KEY_GHSPEC=sk-your-openai-key
#
# IMPORTANT: Also add API Key IDs for usage tracking (find in OpenAI Dashboard > Usage):
#   OPENAI_API_KEY_BAES_ID=key_XXXXXXXXXXXX
#   OPENAI_API_KEY_CHATDEV_ID=key_XXXXXXXXXXXX
#   OPENAI_API_KEY_GHSPEC_ID=key_XXXXXXXXXXXX
```

### Your First Experiment (5 Minutes)

The framework supports **config sets** - curated templates for common scenarios:

```bash
# 1. List available config sets
python scripts/new_experiment.py --list-config-sets

# Output:
# 📦 Available Config Sets:
#   • default (6 steps): Traditional 6-step CRUD application
#   • minimal (1 step): Hello World API for testing

# 2. Generate experiment from config set
python scripts/new_experiment.py \
    --name my_first_experiment \
    --config-set default \
    --model gpt-4o-mini \
    --frameworks baes \
    --runs 10

# 3. Customize (optional)
vim my_first_experiment/config.yaml
# → Disable steps, reorder, adjust timeouts

# 4. Run the experiment
cd my_first_experiment
./run.sh

# 5. View results
cat runs/latest/summary.json
```

**What happened:**
- ✅ Generated experiment from `default` config set (6 CRUD steps)
- ✅ Copied all prompts, HITL files, and configurations
- ✅ Created self-contained, runnable experiment
- ✅ Ready to customize and execute

**See [Config Sets Quick Start](docs/configurable_steps/QUICKSTART_CONFIG_SETS.md) for detailed guide.**

---

## ⚠️ Breaking Changes - Metrics Configuration (v2.0+)

**If you have existing experiment configs**, you need to migrate your metrics configuration to the new unified format.

### What Changed?

The old 3-subsection metrics format has been replaced with a simpler unified format:

**OLD (deprecated):**
```yaml
metrics:
  reliable_metrics:
    TOK_IN: { name: "Input Tokens", ... }
  derived_metrics:
    COST_USD: { name: "Cost", ... }
  excluded_metrics:
    MC: { name: "Maintainability", ... }
```

**NEW (required):**
```yaml
metrics:
  TOK_IN: 
    name: "Input Tokens"
    status: measured  # or 'derived', 'unmeasured'
    reason: "Direct from OpenAI API"  # optional
    # ... other fields
  COST_USD:
    name: "Cost"
    status: derived
    reason: "Calculated from token counts"
  MC:
    name: "Maintainability"
    status: unmeasured
    reason: "Requires static analysis tool integration"
```

### Migration Required

If you see this error:
```
ConfigMigrationError: Old metrics format detected. Found subsections: reliable_metrics, derived_metrics
```

**→ See [CONFIG_MIGRATION_GUIDE.md](docs/CONFIG_MIGRATION_GUIDE.md)** for step-by-step migration instructions.

### Benefits of New Format

- ✅ **Simpler**: One section instead of three
- ✅ **More flexible**: `status` field replaces rigid subsections
- ✅ **Better documentation**: `reason` field explains why metrics are unmeasured
- ✅ **Auto-generated limitations**: Reports automatically document unmeasured metrics

---

### Compare Multiple Experiments

```bash
# Create baseline
python scripts/new_experiment.py \
    --name baseline_gpt4o \
    --model gpt-4o \
    --frameworks baes \
    --runs 10

# Create variant
python scripts/new_experiment.py \
    --name variant_gpt4omini \
    --model gpt-4o-mini \
    --frameworks baes \
    --runs 10

# Run both
python scripts/run_experiment.py baseline_gpt4o
python scripts/run_experiment.py variant_gpt4omini

# Analyze both
./runners/analyze_results.sh baseline_gpt4o
./runners/analyze_results.sh variant_gpt4omini

# Compare
diff experiments/baseline_gpt4o/analysis/report.md \
     experiments/variant_gpt4omini/analysis/report.md
```

**See [Comparison Guide](docs/COMPARISON_GUIDE.md) for statistical comparison techniques.**

### Legacy Single-Run Mode

The framework still supports legacy single-run mode (deprecated):

```bash
# Legacy: Execute single framework run (15-30 minutes)
# DEPRECATED: Use new_experiment.py instead
./runners/run_experiment.sh baes

# Legacy: View metrics from a run
cat runs/baes/<run-id>/metrics.json

# Legacy: Analyze legacy runs
./runners/analyze_results.sh ./analysis_output
```

**Note:** Legacy mode is maintained for backward compatibility but new workflows should use the multi-experiment system.

## 📦 Config Sets

**Config Sets** are curated experiment templates that provide pre-configured prompts, steps, and HITL files for common scenarios. They enable rapid experiment creation and standardized testing across different domains.

### Available Config Sets

| Config Set | Steps | Description | Use Case |
|------------|-------|-------------|----------|
| **default** | 6 | Traditional CRUD application (Student/Course/Teacher) | Full-featured API testing, framework comparison |
| **minimal** | 1 | Hello World API | Quick testing, learning, debugging |
| *microservices* | - | Multi-service architecture | *(Coming in V2)* |
| *ml_pipeline* | - | ML model development | *(Coming in V2)* |

### Config Set Workflow

```bash
# 1. List available config sets
python scripts/new_experiment.py --list-config-sets

# 2. Generate experiment from config set
python scripts/new_experiment.py \
    --name my_test \
    --config-set default \
    --model gpt-4o-mini \
    --frameworks baes chatdev \
    --runs 10

# 3. Customize post-generation (optional)
vim my_test/config.yaml
# → Disable steps: set enabled: false
# → Reorder steps: move entries (executes in declaration order)
# → Adjust timeouts and metrics

# 4. Run experiment
cd my_test
./run.sh
```

### Features

- ✅ **Curated Templates**: Pre-configured prompts and steps for common scenarios
- ✅ **Self-Contained**: All files copied (prompts, HITL, configs)
- ✅ **Customizable**: Edit config.yaml post-generation
- ✅ **Declaration Order**: Steps execute in YAML order, not sorted by ID
- ✅ **Fail-Fast Validation**: Catches errors before wasting tokens

### Creating Custom Config Sets

Want to create your own config set? See the [Creating Config Sets Guide](docs/configurable_steps/CREATING_CONFIG_SETS.md).

---

## Documentation

### Getting Started
- **[Quick Start Guide](docs/QUICKSTART.md)** ⭐ **Start here!** - Create your first experiment in 5 minutes
- **[Config Sets Quick Start](docs/configurable_steps/QUICKSTART_CONFIG_SETS.md)** 🆕 **Config sets guide** - Use curated templates
- **[Workflows Guide](docs/WORKFLOWS.md)** - Common usage patterns and real-world scenarios
- **[Comparison Guide](docs/COMPARISON_GUIDE.md)** - Statistical comparison of experiments
- **[Best Practices Guide](docs/BEST_PRACTICES.md)** - Recommendations for effective experimentation

### Config Sets & Customization 🆕
- **[Creating Config Sets](docs/configurable_steps/CREATING_CONFIG_SETS.md)** - Build your own config sets
- **[Implementation Plan](docs/configurable_steps/FINAL-IMPLEMENTATION-PLAN.md)** - Technical design details
- **[Feature Specification](docs/configurable_steps/feature-spec.md)** - Complete requirements

### Multi-Experiment System
- **[Architecture Guide](docs/architecture.md)** - System design and multi-experiment components
- **[Configuration Reference](docs/configuration_reference.md)** - Complete config schema and examples
- **[Validation System](docs/validation_system.md)** - Configuration validation reference
- **[Troubleshooting Guide](docs/troubleshooting.md)** - Common issues and solutions

### Metrics and Analysis
- **[Metrics Guide](docs/metrics.md)** - Complete reference for all 16 metrics
- **[Statistical Power Analysis](docs/statistical_power_analysis.md)** - Sample size calculations
- **[API Usage Reconciliation](docs/reconcile_usage_guide.md)** - Accurate cost tracking

### Legacy Documentation
- [Original Quickstart](docs/quickstart.md) - Legacy single-run quickstart (deprecated)
- [Feature Specification](specs/001-baes-experiment-framework/spec.md) - Requirements and user stories
- [Implementation Plan](specs/001-baes-experiment-framework/plan.md) - Technical design
- [Research Decisions](specs/001-baes-experiment-framework/research.md) - Design rationale

### Testing
- **Test Suite:** Comprehensive unit tests with 100% pass rate
- **Run Tests:** `pytest tests/unit/test_report_generation.py -v`
- **Test Coverage:** 26 tests covering validation, dynamics, and edge cases
- **Execution Time:** < 2 seconds for full suite

## Architecture

```
genai-devbench/
├── experiments/                 # 🆕 Multi-experiment storage (isolated)
│   ├── <experiment_name>/       # Individual experiment directory
│   │   ├── config.yaml          # Experiment configuration (immutable)
│   │   ├── README.md            # Auto-generated documentation
│   │   ├── runs/                # Run outputs for this experiment
│   │   │   ├── manifest.json    # Run tracking and metadata
│   │   │   ├── baes/            # Framework-specific runs
│   │   │   ├── chatdev/
│   │   │   └── ghspec/
│   │   ├── analysis/            # Analysis outputs
│   │   │   ├── report.md        # Statistical report
│   │   │   └── visualizations/  # Charts and graphs
│   │   └── .meta/               # Metadata
│   │       └── config.hash      # Config integrity verification
│   └── .experiment_registry.json # 🆕 Global experiment registry
├── scripts/                     # 🆕 Experiment management
│   ├── new_experiment.py        # Create experiments (interactive/CLI)
│   └── run_experiment.py        # Run experiments (high-level wrapper)
├── config/                      # Experiment configuration
│   ├── experiment.yaml          # Framework configs, timeouts, seeds
│   ├── prompts/                 # 6-step CRUD evolution scenario
│   └── hitl/                    # HITL clarification templates
├── src/
│   ├── orchestrator/            # Execution coordination
│   │   ├── runner.py            # OrchestratorRunner (single/multi)
│   │   ├── metrics_collector.py # 16 metrics computation
│   │   ├── validator.py         # CRUD/UI/downtime validation
│   │   └── archiver.py          # tar.gz with SHA-256
│   ├── adapters/                # Framework integrations
│   │   ├── base_adapter.py      # Abstract BaseAdapter
│   │   ├── baes_adapter.py      # BAEs implementation
│   │   ├── chatdev_adapter.py   # ChatDev implementation
│   │   └── ghspec_adapter.py    # GitHub Spec-kit implementation
│   ├── analysis/                # Statistical analysis
│   │   ├── statistics.py        # Tests, effect sizes, reports
│   │   ├── stopping_rule.py     # Bootstrap CI convergence
│   │   └── visualizations.py    # Radar, Pareto, timeline charts
│   └── utils/                   # Utilities
│       ├── logger.py            # Structured JSON logging
│       ├── config_loader.py     # YAML validation
│       ├── isolation.py         # Workspace management
│       ├── api_client.py        # OpenAI Usage API verification
│       ├── experiment_paths.py  # 🆕 Path resolution for experiments
│       └── experiment_registry.py # 🆕 Global experiment tracking
├── runners/                     # Entry point scripts
│   ├── run_experiment.sh        # ⚠️ DEPRECATED (use scripts/run_experiment.py)
│   ├── analyze_results.sh       # Analysis pipeline (experiment-aware)
│   └── reconcile_usage.sh       # 🆕 API usage reconciliation
├── runs/                        # 🗄️ Legacy run outputs (gitignored, deprecated)
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── contract/                # Contract tests
└── docs/                        # Documentation
    ├── QUICKSTART.md            # 🆕 5-minute getting started guide
    ├── WORKFLOWS.md             # 🆕 Common usage patterns
    ├── COMPARISON_GUIDE.md      # 🆕 Statistical comparison guide
    ├── BEST_PRACTICES.md        # 🆕 Recommendations and tips
    └── ...                      # Other documentation
```

**Key Changes:**
- 🆕 **experiments/** directory: All experiments organized by name
- 🆕 **Experiment Registry**: Global tracking of all experiments
- 🆕 **Config Hash**: Immutable configuration with integrity verification
- 🆕 **Isolated Runs**: Each experiment has its own runs and analysis
- ⚠️ **Deprecated**: Legacy `runners/run_experiment.sh` (use `scripts/run_experiment.py`)
- 🗄️ **Legacy**: Old `runs/` directory maintained for backward compatibility

---

## 📄 Camera-Ready Paper Generation

**NEW**: Generate publication-ready papers from experiment results with AI-assisted prose, statistical analysis, and ACM formatting.

### Quick Start

```bash
# After running an experiment with statistical analysis
cd my_first_experiment

# Generate camera-ready paper (requires OpenAI API key)
python ../../scripts/generate_paper.py . --output-dir paper

# Output:
#   paper/main.pdf         # ACM SIGSOFT formatted PDF
#   paper/main.tex         # LaTeX source with AI-generated prose
#   paper/figures/         # Publication-quality figures (PDF + PNG)
#   README.md              # Enhanced with reproduction instructions
```

### Features

**Automated Content Generation:**
- ✅ **AI-Generated Prose**: All sections (Introduction, Related Work, Methodology, Results, Discussion, Conclusion) with ≥800 words each
- ✅ **Statistical Tables**: Descriptive statistics, hypothesis tests, effect sizes automatically formatted
- ✅ **Publication Figures**: Vector PDFs (scalable) + PNG (300 DPI) for all metrics
- ✅ **Citation Placeholders**: Bold markers like **[CITE: framework_name]** for manual citation filling
- ✅ **ACM SIGSOFT Format**: Ready for conference submission (sigconf template)

**Customization Options:**
```bash
# Generate only specific sections
python ../../scripts/generate_paper.py . \
    --sections=methodology,results,discussion

# Filter metrics in results section
python ../../scripts/generate_paper.py . \
    --metrics-filter=execution_time,total_cost_usd,quality_score

# Control prose detail level
python ../../scripts/generate_paper.py . \
    --prose-level=minimal  # minimal | standard | comprehensive

# Export only figures (fast, no prose generation)
python ../../scripts/generate_paper.py . --figures-only
# or use dedicated script:
python ../../scripts/export_figures.py . --formats=pdf,png --dpi=300
```

**Reproduction Enhancement:**
- 📝 Automatically enhances experiment README.md with comprehensive reproduction instructions
- ⏱️ Enables independent researchers to reproduce experiments in ≤30 minutes
- 🔍 Includes environment setup, dependencies, execution steps, and expected outputs

### Output Structure

```
my_experiment/
├── paper/
│   ├── main.pdf              # Compiled PDF (if pdflatex available)
│   ├── main.tex              # LaTeX source
│   ├── main.md               # Markdown intermediate
│   ├── figures/
│   │   ├── metric_comparison_execution_time.pdf
│   │   ├── metric_comparison_execution_time.png
│   │   ├── metric_comparison_cost.pdf
│   │   ├── metric_comparison_cost.png
│   │   └── statistical_significance.pdf
│   └── acm_sigsoft/          # ACM template files
└── README.md                 # Enhanced with Reproduction Guide
```

### Requirements

**System:**
- Python 3.11+ with matplotlib, numpy, pandas
- Pandoc ≥2.0 (for Markdown→LaTeX conversion)
- pdflatex (optional, for PDF compilation)

**API:**
- OpenAI API key (set `OPENAI_API_KEY` environment variable)
- Note: Separate from experiment API keys; used only for prose generation

**Installation:**
```bash
# Install Pandoc (Ubuntu/Debian)
sudo apt-get install pandoc texlive-latex-base texlive-latex-extra

# Install Pandoc (macOS)
brew install pandoc
brew install --cask mactex-no-gui  # optional, for PDF

# Verify
pandoc --version  # Should be ≥2.0
```

### Best Practices

⚠️ **Important**: AI-generated prose requires manual review:
1. ✅ Verify all claims match experimental data
2. ✅ Fill citation placeholders with proper references
3. ✅ Review interpretations for accuracy (AI may overclaim)
4. ✅ Check statistical reporting (p-values, effect sizes)
5. ✅ Validate figure captions and descriptions

**See [Paper Generation Guide](docs/paper_generation_guide.md) for detailed usage and troubleshooting.**

---

## Metrics Reference

### Quality Metrics (5)
- **AUTR** (Automated User Testing Rate): Autonomy rate = 1 - (HIT/UTT), measuring independence from human intervention [0-1]
- **Q\*** (Quality Star): Composite score = 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC [0-1]
- **ESR** (Emerging State Rate): Successful incremental evolution steps [0-1]
- **CRUDe** (CRUD Evolution): CRUD operation coverage [0-12]
- **MC** (Model Call Efficiency): Inverse normalized API calls [0-1]

### Efficiency Metrics (6)
- **TOK_IN** (Input Tokens): Total tokens sent to LLM APIs
- **TOK_OUT** (Output Tokens): Total tokens received from LLM APIs
- **T_WALL** (Wall-Clock Time): Total elapsed time (seconds)
- **T_USER** (User Time): CPU time in user mode (seconds)
- **T_CPU** (System Time): CPU time in kernel mode (seconds)
- **AEI** (API Efficiency Index): AUTR / log(1 + TOK_IN)

### Reliability Metrics (3)
- **ZDI** (Zero-Downtime Incidents): Count of availability failures
- **RTE** (Runtime Errors): Proportion of steps with crashes [0-1]
- **MCI** (Model Call Interruptions): Count of API retry events

### Process Metrics (2)
- **ITR** (Iterations): Number of framework invocations
- **DPL** (Deployment Success): Binary deployment outcome {0, 1}

See [Metrics Guide](docs/metrics.md) for detailed definitions, formulas, and interpretation.

## Statistical Analysis

The framework automatically performs:

1. **Aggregate Statistics**: Mean, median, std, 95% bootstrap CI for each metric
2. **Hypothesis Testing**: Kruskal-Wallis H-test for group differences (p < 0.05)
3. **Pairwise Comparisons**: Dunn-Šidák corrected Mann-Whitney U tests
4. **Effect Sizes**: Cliff's delta (non-parametric effect magnitude)
5. **Outlier Detection**: Values >3σ from median
6. **Convergence Detection**: Stop when CI half-width < 10% of mean

Results output as markdown report with publication-ready SVG visualizations.

## Reproducibility

The framework ensures deterministic execution through:

- **Fixed Seeds**: Python random, NumPy seeds set per run
- **Commit Verification**: SHA verification of framework repository state
- **HITL Logging**: SHA-1 hashing of human-in-the-loop responses
- **Byte-for-Byte Validation**: Reproducibility test script for output comparison
- **Temperature Zero**: LLM sampling with temperature=0.0, top_p=1.0

See [Architecture Guide](docs/architecture.md#reproducibility) for details.

## License

This project is licensed under CC BY 4.0 - see [LICENSE](LICENSE) file for details.

## Citation

If you use this framework in your research, please cite:

```bibtex
@software{genai-devbench_2025,
  title={GenAI-DevBench},
  author={GESAD Lab},
  year={2025},
  url={https://github.com/nosredna123/genai-devbench}
}
```

## Contributing

This is a research artifact. For questions or issues, please open a GitHub issue.
