# Implementation Plan: Camera-Ready Paper Generation from Experiment Results

**Branch**: `010-paper-generation` | **Date**: 2025-10-28 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-paper-generation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Generate camera-ready scientific papers in ACM SIGSOFT format from experiment results with AI-generated comprehensive prose (≥800 words per section for Introduction, Related Work, Methodology, Results, Discussion, Conclusion), statistical analysis, auto-generated publication-quality figures (PDF vector + PNG 300+ DPI), and enhanced reproducibility documentation. System must compile to valid PDF matching ACM conference requirements, mark all AI-generated content for manual review, use citation placeholders to avoid hallucinations, and complete generation in ≤3 minutes for typical experiments (50 runs, 3 frameworks).

**Scope**: AI model (gpt-5-mini) is used **only for paper prose generation**. Experiment execution and framework interactions remain unchanged.

## Technical Context

**Language/Version**: Python 3.11+ (matching existing genai-devbench codebase)  
**Primary Dependencies**: 
- PyYAML (existing - config loading)
- requests (existing - OpenAI API calls for paper prose generation only)
- pytest (existing - testing)
- Pandoc (external system tool - Markdown→LaTeX conversion, NEEDS CLARIFICATION: version requirements)
- LaTeX distribution (external system tool - PDF compilation, user-installed)
- Matplotlib (existing in requirements.txt - figure generation)

**Storage**: File-based (YAML configs, JSON run data, generated LaTeX/Markdown files, PDF/PNG figures)  
**Testing**: pytest (existing framework)  
**Target Platform**: Linux, macOS, Windows (cross-platform CLI tools)  
**Project Type**: Single project (extending existing genai-devbench codebase)  
**Performance Goals**: 
- Paper generation completes in ≤3 minutes for 50 runs across 3 frameworks
- AI prose generation: ≥800 words per section × 6 sections = ≥4800 words total
- Figure export: all visualizations in <30 seconds

**Constraints**: 
- Must integrate with Feature 009 (refactored MetricsConfig-driven report generator)
- Total output size <100MB (paper + figures + templates)
- No proprietary dependencies (Open Science principle)
- Fail-fast on missing tools (Pandoc, LaTeX) with clear installation instructions
- Must work in headless environments (no X11 display for figure generation)

**Scale/Scope**: 
- Generate 6 major paper sections (Abstract, Introduction, Related Work, Methodology, Results, Discussion, Conclusion)
- Support multiple figure types (metric comparisons, cost breakdowns, distributions)
- Handle experiments with 1-10 frameworks
- Support customization (section selection, metric filtering, prose detail levels)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with BAEs Experiment Constitution v1.2.0:

- [x] **Scientific Reproducibility**: Fixed random seeds not applicable (deterministic LaTeX generation). Framework versions: ACM template version bundled and pinned.
- [x] **Clarity & Transparency**: All modules will include docstrings. Paper generation logic documented. Citation placeholder system explained.
- [x] **Open Science**: Code licensed CC BY 4.0. Dependencies: Pandoc (GPLv2), LaTeX (free), Matplotlib (PSF), all open-source.
- [x] **Minimal Dependencies**: Using standard library + existing dependencies (PyYAML, requests, pytest, Matplotlib). Pandoc/LaTeX are external tools.
- [N/A] **Deterministic HITL**: Not applicable - paper generation is post-experiment, no HITL needed.
- [N/A] **Reproducible Metrics**: Not applicable - this feature generates papers from existing metrics, doesn't measure new ones.
- [x] **Version Control Integrity**: ACM template files bundled at specific version, documented in code.
- [x] **Automation-First**: Fully automated via CLI commands (generate_paper.py, export_figures.py). No manual steps.
- [x] **Failure Isolation**: Each paper generation uses experiment directory as input. No shared state between runs.
- [x] **Educational Accessibility**: Documentation includes LaTeX compilation guide, figure export examples, troubleshooting for missing dependencies.
- [x] **DRY Principle**: Shared base classes for section generators. Template loading utilities. No duplicate LaTeX formatting code.
- [x] **No Backward Compatibility Burden**: Each generated paper is standalone. Breaking changes to paper format allowed.
- [x] **Fail-Fast Philosophy**: Missing Pandoc/LaTeX causes immediate error with installation instructions. No fallback to degraded output.

## Project Structure

### Documentation (this feature)

```
specs/010-paper-generation/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── paper_generation/           # NEW: Paper generation module
│   ├── __init__.py
│   ├── paper_generator.py      # Main orchestrator (PaperGenerator)
│   ├── section_generator.py    # Base class for section generators
│   ├── sections/               # Individual section generators
│   │   ├── __init__.py
│   │   ├── abstract_generator.py
│   │   ├── introduction_generator.py
│   │   ├── related_work_generator.py
│   │   ├── methodology_generator.py
│   │   ├── results_generator.py
│   │   ├── discussion_generator.py
│   │   └── conclusion_generator.py
│   ├── prose_engine.py         # AI-powered text generation
│   ├── figure_exporter.py      # Figure generation and export
│   ├── document_formatter.py   # LaTeX/Markdown formatting
│   ├── pandoc_converter.py     # Pandoc wrapper
│   ├── citation_handler.py     # Citation placeholder insertion
│   └── template_bundle.py      # ACM template management
│
├── analysis/                   # EXISTING: Feature 009 refactored code
│   └── report_generator.py     # MetricsConfig-driven reports (dependency)
│
└── utils/                      # EXISTING: Shared utilities
    └── [existing utilities]

scripts/                        # NEW: CLI entry points
├── generate_paper.py           # Main paper generation CLI
└── export_figures.py           # Figure export CLI

templates/                      # NEW: ACM SIGSOFT templates
├── acm_sigsoft/
│   ├── sigconf.cls             # ACM class file
│   ├── ACM-Reference-Format.bst # Bibliography style
│   ├── acmart.pdf              # Template documentation
│   └── VERSION                 # Template version tracking

tests/
├── paper_generation/           # NEW: Tests for paper generation
│   ├── test_paper_generator.py
│   ├── test_section_generators.py
│   ├── test_prose_engine.py
│   ├── test_figure_exporter.py
│   ├── test_pandoc_converter.py
│   └── fixtures/               # Test experiment data
└── [existing test directories]
```

**Structure Decision**: Single project extending existing genai-devbench codebase. New `src/paper_generation/` module contains all paper generation logic, organized by component (section generators, prose engine, figure export, document formatting). CLI scripts in `scripts/` directory provide command-line interface. ACM templates bundled in `templates/acm_sigsoft/` for portability.

## Complexity Tracking

*No constitution violations detected. All principles satisfied.*

**Note on External Tools**: Pandoc and LaTeX are external system-level tools (not Python dependencies), consistent with the "Minimal Dependencies" principle which focuses on Python library dependencies. These tools are detected and fail-fast with installation instructions if missing (Principle XIII).

---

## Phase Completion Summary

### ✅ Phase 0: Research & Unknowns Resolution

**Completed**: 2025-10-28

**Artifacts Generated**:
- `research.md`: Comprehensive research on all NEEDS CLARIFICATION items

**Key Decisions**:
1. **Pandoc Version**: Require ≥2.0 for stable math rendering
2. **AI Prose Strategy**: gpt-5-mini default with --model flag for overrides (gpt-5, gpt-4o, gpt-4-turbo, etc.)
3. **Citation Placeholders**: Format `[CITE: description]` → `\textbf{[CITE: ...]}` in LaTeX
4. **ACM Template**: Bundle sigconf v1.90 with VERSION tracking
5. **Figure Quality**: Dual export (PDF vector + PNG 300 DPI) with headless Matplotlib
6. **README Enhancement**: 5-subsection Reproduction guide

**All unknowns from Technical Context resolved.**

---

### ✅ Phase 1: Design & Contracts

**Completed**: 2025-10-28

**Artifacts Generated**:
- `data-model.md`: Entity definitions (PaperConfig, PaperStructure, Figure, Table, SectionContext)
- `contracts/api.md`: Programmatic interfaces with fail-fast error handling
- `quickstart.md`: User guide with examples and troubleshooting

**Key Designs**:
1. **Data Model**: Fail-fast validation in all entities (\_\_post_init\_\_ methods)
2. **API Contract**: Clear interfaces for PaperGenerator, FigureExporter, ProseEngine, CitationHandler
3. **Error Handling**: Explicit exception types with remediation guidance
4. **CLI Contract**: Standard Unix tool pattern with exit codes and help text

**Agent Context Updated**: GitHub Copilot instructions updated with Python 3.11+ and File-based storage.

---

### ⏸️ Phase 2: Task Breakdown (NOT CREATED)

**Status**: Ready for `/speckit.tasks` command

**Next Steps**: Run `/speckit.tasks` to generate implementation task breakdown in `tasks.md`

---

## Constitution Check (Post-Design Re-evaluation)

All principles remain satisfied after Phase 1 design:

- [x] **Scientific Reproducibility**: ACM template version pinned (sigconf v1.90)
- [x] **Clarity & Transparency**: API contracts documented, all interfaces explicit
- [x] **Open Science**: All dependencies open-source (Pandoc GPLv2, LaTeX free, Matplotlib PSF)
- [x] **Minimal Dependencies**: No new Python dependencies added (using existing: PyYAML, requests, pytest, Matplotlib)
- [N/A] **Deterministic HITL**: Not applicable (paper generation is post-experiment)
- [N/A] **Reproducible Metrics**: Not applicable (uses existing metrics from Feature 009)
- [x] **Version Control Integrity**: Template VERSION file enforces version tracking
- [x] **Automation-First**: Full CLI automation, no manual steps required
- [x] **Failure Isolation**: Each paper generation is independent, uses experiment dir as input
- [x] **Educational Accessibility**: Quickstart guide with examples, troubleshooting section
- [x] **DRY Principle**: Base classes (SectionGenerator), shared utilities (CitationHandler, DocumentFormatter)
- [x] **No Backward Compatibility Burden**: Each paper is standalone git artifact, breaking changes allowed
- [x] **Fail-Fast Philosophy**: All error types defined, fail-fast on validation, no fallback mechanisms

**No violations introduced during design phase.**

---

## Implementation Readiness

**Status**: ✅ Ready for Phase 2 (Task Breakdown)

**Artifacts Complete**:
- [x] `plan.md` (this file)
- [x] `research.md` (Phase 0)
- [x] `data-model.md` (Phase 1)
- [x] `contracts/api.md` (Phase 1)
- [x] `quickstart.md` (Phase 1)
- [x] Agent context updated (.github/copilot-instructions.md)

**Next Command**: `/speckit.tasks` to generate task breakdown for implementation

**Estimated Implementation Time**: 4-5 weeks (per spec.md)
- Core Implementation: 3-4 weeks
- Testing & Validation: 1 week
- Documentation: 3 days

---

## Branch & Paths

**Feature Branch**: `010-paper-generation` (currently checked out)  
**Spec File**: `/home/amg/projects/uece/baes/genai-devbench/specs/010-paper-generation/spec.md`  
**Plan File**: `/home/amg/projects/uece/baes/genai-devbench/specs/010-paper-generation/plan.md`  
**Specs Directory**: `/home/amg/projects/uece/baes/genai-devbench/specs/010-paper-generation/`

**Status**: Phase 0 & 1 Complete, ready for Phase 2 task breakdown via `/speckit.tasks` command.

