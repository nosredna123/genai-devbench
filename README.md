# BAEs Experiment Framework

**Automated experiment orchestrator for comparing LLM-driven software generation systems**

This framework executes reproducible experiments to compare three LLM-driven frameworks (BAEs, ChatDev, GitHub Spec-kit) across a six-step academic CRUD evolution scenario. It provides deterministic orchestration, reproducible metrics collection, and automated statistical analysis.

## Features

- **Automated Execution**: Single-command orchestration of complete experiment runs
- **Deterministic HITL**: Fixed clarification responses for reproducible results
- **Comprehensive Metrics**: 16 metrics including autonomy (AUTR), efficiency (tokens, time), quality (CRUDe, ESR, MC)
- **Statistical Analysis**: Confidence-based stopping rules, Kruskal-Wallis tests, Cliff's δ effect sizes
- **Complete Archival**: Full workspace preservation with SHA-256 verification
- **Isolation**: Per-run UUID workspaces with Docker containerization

## Quick Start

### Prerequisites

- Python 3.11+
- Docker
- Git
- 16GB RAM, 50GB disk space

### Installation

```bash
# Clone repository
git clone https://github.com/gesad-lab/baes_experiment.git
cd baes_experiment

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp .env.example .env
# Edit .env with your OpenAI API keys

# Configure experiment
# Edit config/experiment.yaml with framework repo URLs and commit hashes
```

### Running Experiments

```bash
# Execute single framework run
./runners/run_experiment.sh baes

# Execute all frameworks with stopping rule
./runners/run_experiment.sh all

# Analyze results
./runners/analyze_results.sh
```

## Architecture

```
baes_experiment/
├── config/              # Experiment configuration and prompts
├── src/
│   ├── orchestrator/    # Main run orchestration
│   ├── adapters/        # Framework-specific adapters
│   ├── analysis/        # Statistical analysis and visualization
│   └── utils/           # Logging, isolation, API clients
├── runners/             # Entry point scripts
├── runs/                # Archived experiment results
└── tests/               # Unit, integration, and contract tests
```

## Documentation

- [Specification](specs/001-baes-experiment-framework/spec.md) - Feature requirements and user stories
- [Implementation Plan](specs/001-baes-experiment-framework/plan.md) - Technical design and architecture
- [Research Decisions](specs/001-baes-experiment-framework/research.md) - Design rationale
- [Tasks](specs/001-baes-experiment-framework/tasks.md) - Implementation breakdown

## Metrics

- **AUTR** (Autonomy Rate): 1 - HIT/6
- **TOK_IN/OUT**: Input/output tokens from OpenAI Usage API
- **T_WALL**: Wall-clock runtime (UTC)
- **CRUDe**: CRUD coverage (0-12 scale)
- **ESR**: Endpoint success rate (0-1)
- **MC**: Migration continuity (0-1)
- **Q\***: Composite quality score
- **AEI**: Autonomy efficiency index

## License

This project is licensed under CC BY 4.0 - see [LICENSE](LICENSE) file for details.

## Citation

If you use this framework in your research, please cite:

```bibtex
@software{baes_experiment_2025,
  title={BAEs Experiment Framework},
  author={GeSAD Lab},
  year={2025},
  url={https://github.com/gesad-lab/baes_experiment}
}
```

## Contributing

This is a research artifact. For questions or issues, please open a GitHub issue.
