<!--
SYNC IMPACT REPORT
==================
Version Change: [NEW] → 1.0.0
Modification Type: Initial constitution creation for BAEs experiment project

Principles Created:
- I. Scientific Reproducibility
- II. Clarity and Transparency
- III. Open Science
- IV. Minimal Dependencies
- V. Deterministic Human-in-the-Loop (HITL)
- VI. Reproducible Metrics
- VII. Version Control Integrity
- VIII. Automation-First Philosophy
- IX. Failure Isolation
- X. Educational Accessibility

Added Sections:
- Core Principles (10 principles)
- Technical Standards
- Quality Assurance
- Governance

Templates Requiring Updates:
✅ plan-template.md - Constitution Check section aligns with reproducibility principles
✅ spec-template.md - Requirements structure supports deterministic specification
✅ tasks-template.md - Task categorization supports automation and isolation requirements

Follow-up TODOs:
- None - all placeholders filled with concrete values
-->

# BAEs Experiment Constitution

## Core Principles

### I. Scientific Reproducibility

All experiments MUST yield identical results when rerun on the same framework versions and prompts.
Randomness MUST be eliminated or logged deterministically using fixed random seeds and timestamps.

**Non-negotiable requirements**:
- Fixed random seeds MUST be declared in `config/experiment.yaml`
- All framework versions MUST be pinned to specific commit hashes
- Prompt text MUST be version-controlled and immutable once a run begins
- Reruns on identical inputs MUST produce bit-identical outputs (token counts, API responses,
  generated code structures)

**Rationale**: Academic validity depends on independent researchers obtaining identical results.
Non-determinism undermines peer review and prevents meaningful comparison across frameworks.

### II. Clarity and Transparency

Every component—from adapters to orchestrator logs—MUST be easily understood and well-documented
for independent verification by other researchers.

**Non-negotiable requirements**:
- All Python modules MUST include docstrings for classes and public methods
- Configuration files MUST use self-documenting YAML with inline comments
- Adapter implementations MUST document their mapping from standard CLI to framework-specific
  commands
- Orchestrator logs MUST use structured JSON format with timestamp, run ID, step, and event type
- All metrics calculations MUST include inline comments explaining formulas

**Rationale**: Transparency enables peer review, error detection, and educational reuse.
Opaque implementations cannot be validated or improved by the research community.

### III. Open Science

All code, configurations, and run artifacts MUST be published under a permissive license.
No proprietary data or closed-source dependencies are permitted.

**Non-negotiable requirements**:
- Source code MUST be licensed under CC BY 4.0
- All run artifacts (logs, metrics, generated applications) MUST be published
- Documentation MUST be licensed under CC BY 4.0
- No API keys or proprietary credentials may be hard-coded
- Third-party frameworks MUST be open-source or publicly accessible

**Rationale**: Open science accelerates discovery, enables replication studies, and ensures
equitable access to research tools. Proprietary barriers prevent independent verification.

### IV. Minimal Dependencies

The system MUST use standard Python libraries and lightweight tools to ensure portability
and longevity across different computing environments.

**Non-negotiable requirements**:
- Core orchestrator MUST run on Python 3.11+ standard library where possible
- External dependencies MUST be limited to: PyYAML, requests, pytest
- No framework-specific SDKs or proprietary toolchains in the orchestrator
- Docker containers MUST use official Python base images
- All dependencies MUST be pinned with exact versions in `requirements.txt`

**Rationale**: Heavy dependency chains create fragility. Minimalism ensures the experiment
remains runnable in 5+ years and ports easily to new platforms.

### V. Deterministic Human-in-the-Loop (HITL)

Clarifications MUST be handled automatically through a fixed expanded specification paragraph
stored in `config/hitl/expanded_spec.txt`. No manual or random input is permitted.

**Non-negotiable requirements**:
- All HITL queries MUST receive the same pre-written clarification text
- The expanded specification MUST be version-controlled and timestamped
- HITL interactions MUST be logged with query text, response text, and timestamp
- No interactive prompts or runtime user input allowed during runs
- Adapter HITL methods MUST be deterministic and testable

**Rationale**: Manual intervention introduces irreproducible variance. A fixed clarification
ensures all frameworks receive identical guidance, preserving experimental control.

### VI. Reproducible Metrics

All measurements—token usage, runtime, CRUD accuracy, downtime—MUST be computed with
consistent formulas and verified against the OpenAI Usage API.

**Non-negotiable requirements**:
- Token counts MUST be fetched from OpenAI Usage API and logged locally
- Runtime MUST be measured in UTC timestamps (ISO 8601 format)
- CRUD accuracy MUST use a standardized test suite with deterministic inputs
- Downtime MUST be measured as seconds where health endpoints return non-200 status
- All metrics MUST be stored in JSON format with schema validation
- Aggregate calculations MUST document formulas in code comments

**Rationale**: Inconsistent measurement invalidates comparisons. API-verified metrics eliminate
disputes about token counts and ensure audit trails.

### VII. Version Control Integrity

Each framework (BAEs, ChatDev, Spec-kit) MUST be run from a pinned commit hash.
No mutable dependencies or local edits are permitted.

**Non-negotiable requirements**:
- All framework repositories MUST be cloned at specific commit SHAs
- Commit hashes MUST be recorded in `config/experiment.yaml`
- No manual patches or uncommitted changes allowed in framework codebases
- Docker images MUST tag framework versions with commit hashes
- Orchestrator MUST verify commit hashes before each run

**Rationale**: Mutable dependencies break reproducibility. Commit pinning ensures exact
version replication and guards against upstream changes.

### VIII. Automation-First Philosophy

Every run—from environment setup to validation and logging—MUST be executable through
a single command (`run_experiment.sh`). No manual steps are permitted.

**Non-negotiable requirements**:
- `run_experiment.sh` MUST provision environments, run all steps, and collect metrics
- All configuration MUST be read from `config/experiment.yaml`
- No interactive confirmations or manual file edits during execution
- CI/CD pipelines MUST be able to execute full runs unattended
- Error recovery MUST be automated with retry policies or fail-fast behavior

**Rationale**: Manual steps introduce human error and limit scalability. Full automation
enables batch runs, CI integration, and reduces time-to-replication for other researchers.

### IX. Failure Isolation

Each run MUST occur in a clean, sandboxed environment. Artifacts MUST never leak between runs.

**Non-negotiable requirements**:
- Each run MUST use a unique run ID and isolated workspace directory
- Docker containers MUST be removed after each run (no persistent state)
- Temporary files MUST be stored in `runs/<framework>/<run-id>/` and cleaned up
- Database state MUST be reset between runs
- Log files MUST be isolated per run ID

**Rationale**: Shared state contaminates results. Isolation ensures each run is independent
and prevents cascading failures across experiments.

### X. Educational Accessibility

The artifact MUST serve as a model for PhD-level experimental reproducibility—readable,
teachable, and replicable by others.

**Non-negotiable requirements**:
- Documentation MUST include step-by-step setup instructions for beginners
- Code MUST follow PEP 8 style guidelines with descriptive variable names
- Complex algorithms MUST include explanatory comments and citations
- Example runs MUST be provided with expected outputs
- Troubleshooting guides MUST address common failure modes

**Rationale**: Research artifacts have pedagogical value beyond immediate results. Clear
educational materials amplify impact by enabling curriculum integration and training new
researchers.

## Technical Standards

### Programming Language
- Python 3.11+ for all orchestrator and adapter code
- Type hints MUST be used for public function signatures
- No legacy Python 2 idioms permitted

### Configuration Management
- YAML for all configuration files (`config/experiment.yaml`)
- JSON for structured logs and metrics output
- Environment variables via `.env` files (not hard-coded)

### Testing Requirements
- Unit tests MUST cover all adapter methods
- Integration tests MUST validate end-to-end run flows
- Test coverage MUST exceed 80% for orchestrator modules
- Tests MUST be deterministic (no time-dependent assertions)

### Logging Standards
- All logs MUST use JSON format with: `timestamp`, `level`, `run_id`, `step`, `message`
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- No sensitive data (API keys, tokens) in logs
- Logs MUST be written to `runs/<framework>/<run-id>/orchestrator.log`

### Documentation Standards
- README MUST include: purpose, setup, usage, troubleshooting
- Inline code documentation for all non-trivial functions
- Architecture diagrams for system components
- Citation of external frameworks and tools

## Quality Assurance

### Pre-Run Validation
Before each experiment run, the orchestrator MUST verify:
- All framework commit hashes match `config/experiment.yaml`
- Required ports are available
- Expanded HITL specification file exists
- Docker daemon is running
- OpenAI API key is configured

### Post-Run Validation
After each run, the orchestrator MUST:
- Verify metrics JSON schema validity
- Compare local token counts against OpenAI Usage API
- Archive all logs and artifacts with run ID
- Generate summary report with pass/fail status
- Clean up temporary files and containers

### Continuous Integration
- All commits MUST pass `pytest` suite
- Linting with `ruff` MUST show zero errors
- Type checking with `mypy` MUST pass
- Integration tests MUST complete in <10 minutes

## Governance

This constitution is the authoritative source for all experimental design and implementation
decisions in the BAEs experiment project. All code, documentation, and processes MUST comply
with the principles outlined above.

**Amendment Process**:
- Amendments require documented rationale and version bump
- Breaking changes require MAJOR version increment
- New principles or sections require MINOR version increment
- Clarifications and typo fixes require PATCH version increment
- All amendments MUST update dependent templates (plan, spec, tasks)

**Compliance Review**:
- All pull requests MUST include a constitution compliance checklist
- Code reviews MUST verify adherence to reproducibility and transparency principles
- Quarterly audits MUST validate metric calculation accuracy
- Any principle violations MUST be documented and justified in `docs/exceptions.md`

**Versioning Policy**:
- Constitution uses semantic versioning: MAJOR.MINOR.PATCH
- Version changes MUST be recorded in this file's Sync Impact Report
- All dependent templates MUST reference constitution version in frontmatter

**Version**: 1.0.0 | **Ratified**: 2025-10-08 | **Last Amended**: 2025-10-08