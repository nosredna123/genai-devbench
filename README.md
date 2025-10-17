# BAEs Experiment Framework

**Automated experiment orchestrator for comparing LLM-driven software generation systems**

This framework executes reproducible experiments to compare three LLM-driven frameworks (BAEs, ChatDev, GitHub Spec-kit) across a six-step academic CRUD evolution scenario. It provides deterministic orchestration, reproducible metrics collection, and automated statistical analysis.

## Features

- **Automated Execution**: Single-command orchestration of complete experiment runs
- **Deterministic HITL**: Fixed clarification responses with SHA-1 verification for reproducible results
- **Comprehensive Metrics**: 16 metrics including autonomy (AUTR), quality (Q*, ESR, CRUDe, MC), efficiency (tokens, time, AEI), and reliability (ZDI, RTE, MCI)
- **Statistical Analysis**: Bootstrap confidence intervals, Kruskal-Wallis tests, Dunn-Šidák pairwise comparisons, Cliff's δ effect sizes
- **Convergence Detection**: Automatic stopping when 95% CI half-width < 10% of mean (min 5, max 25 runs)
- **Publication-Quality Visualizations**: Radar charts, Pareto plots, timeline charts (SVG export)
- **Complete Archival**: Full workspace preservation with SHA-256 verification
- **Isolation**: Per-run UUID workspaces with deterministic seeding

## Quick Start

### Prerequisites

- **Python 3.11+** (required)
- **Git** (required)
- **API Keys**: OpenAI for BAEs/ChatDev, GitHub token for Spec-kit
- **System**: 8GB RAM, 10GB disk space (per multi-framework run)

### Installation

```bash
# Clone repository
git clone https://github.com/gesad-lab/baes_experiment.git
cd baes_experiment

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your API keys:
#   BAES_API_KEY=sk-your-openai-key
#   CHATDEV_API_KEY=sk-your-openai-key
#   GHSPEC_API_KEY=ghp_your-github-token
```

### Running Experiments

```bash
# Execute single framework run (15-30 minutes)
./runners/run_experiment.sh baes

# Execute multi-framework comparison until convergence (1-3 hours)
./runners/run_experiment.sh --multi baes chatdev ghspec

# Analyze results and generate visualizations
./runners/analyze_results.sh ./analysis_output
```

### Viewing Results

```bash
# View metrics from a run
cat runs/baes/<run-id>/metrics.json

# View statistical report
cat analysis_output/report.md

# Open visualizations in browser
firefox analysis_output/radar_chart.svg
firefox analysis_output/pareto_plot.svg
firefox analysis_output/timeline_chart.svg
```

## Documentation

### Getting Started
- **[Quickstart Guide](docs/quickstart.md)** - Get up and running in minutes
- **[Architecture Guide](docs/architecture.md)** - System design and components
- **[Metrics Guide](docs/metrics.md)** - Complete reference for all 16 metrics
- **[Configuration Reference](docs/configuration_reference.md)** - Complete config schema and examples
- **[Validation System](docs/validation_system.md)** - Configuration validation reference
- **[Troubleshooting Guide](docs/troubleshooting.md)** - Common issues and solutions

### Specification
- [Feature Specification](specs/001-baes-experiment-framework/spec.md) - Requirements and user stories
- [Implementation Plan](specs/001-baes-experiment-framework/plan.md) - Technical design
- [Research Decisions](specs/001-baes-experiment-framework/research.md) - Design rationale
- [Task Breakdown](specs/001-baes-experiment-framework/tasks.md) - Implementation tasks

### Testing
- **Test Suite:** Comprehensive unit tests with 100% pass rate
- **Run Tests:** `pytest tests/unit/test_report_generation.py -v`
- **Test Coverage:** 26 tests covering validation, dynamics, and edge cases
- **Execution Time:** < 2 seconds for full suite

## Architecture

```
baes_experiment/
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
│       └── api_client.py        # OpenAI Usage API verification
├── runners/                     # Entry point scripts
│   ├── run_experiment.sh        # Main experiment orchestrator
│   └── analyze_results.sh       # Analysis pipeline
├── runs/                        # Experiment outputs (gitignored)
├── tests/                       # Test suite
│   ├── unit/                    # Unit tests
│   ├── integration/             # Integration tests
│   └── contract/                # Contract tests
└── docs/                        # Documentation
```

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
@software{baes_experiment_2025,
  title={BAEs Experiment Framework},
  author={GESAD Lab},
  year={2025},
  url={https://github.com/gesad-lab/baes_experiment}
}
```

## Contributing

This is a research artifact. For questions or issues, please open a GitHub issue.
