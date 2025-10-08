# Feature Specification: BAEs Experiment Framework

**Feature Branch**: `001-baes-experiment-framework`  
**Created**: 2025-10-08  
**Status**: Draft  
**Input**: User description: "BAEs experiment framework for comparing LLM-driven software generation systems (BAEs, ChatDev, GitHub Spec-kit) across a six-step academic scenario with deterministic orchestration, reproducible metrics, and automated validation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - [Brief Title] (Priority: P1)

[Describe this user journey in plain language]


**Independent Test**: [Describe how this can be tested independently - e.g., "Can be fully tested by [specific action] and delivers [specific value]"]

**Acceptance Scenarios**:

### User Story 1 - Execute Single Framework Run (Priority: P1)

A researcher executes a complete six-step experiment run for one framework (e.g., BAEs) to evaluate its ability to generate and evolve a full-stack web application from natural language commands. The system orchestrates the entire process automatically, collecting metrics and validating outputs at each step.

**Why this priority**: This is the core functionality that enables any experimental comparison. Without the ability to execute a single framework run reliably, no comparative analysis is possible.

**Independent Test**: Can be fully tested by running `./runners/run_experiment.sh baes` and verifying that all six steps complete with metrics collected, artifacts archived, and health checks passed.

**Acceptance Scenarios**:

1. **Given** the researcher has configured experiment.yaml with BAEs framework details, **When** they execute run_experiment.sh for BAEs, **Then** the system creates an isolated environment, executes all six steps sequentially, collects token/time/quality metrics, and archives all artifacts with a unique run ID.

2. **Given** a framework run is in progress at step 3, **When** the framework requests clarification, **Then** the system automatically responds with the fixed expanded specification text (max 2 clarifications per step), logs the HITL event with timestamp and hash, and continues execution.

3. **Given** a step completes successfully, **When** the orchestrator validates the generated application, **Then** API tests execute all CRUD operations, UI tests verify page accessibility and content, and downtime probes confirm zero-downtime transitions.

4. **Given** all six steps have completed, **When** the orchestrator finalizes the run, **Then** metrics.json contains all measured values, usage_api.json shows OpenAI token consumption, and run.tar.gz archives the complete workspace.

---

### User Story 2 - Compare Multiple Frameworks (Priority: P2)

A researcher compares all three frameworks (BAEs, ChatDev, GitHub Spec-kit) across identical scenarios to identify performance differences in autonomy, efficiency, and quality. The system executes multiple runs per framework until statistical confidence is achieved.

**Why this priority**: This enables the primary research question—comparative evaluation—but depends on the single-run capability (P1) being functional.

**Independent Test**: Can be fully tested by running `./runners/run_experiment.sh all` and verifying that confidence intervals for key metrics reach ≤10% half-width for all frameworks.

**Acceptance Scenarios**:

1. **Given** the researcher executes run_experiment.sh for all frameworks, **When** the stopping rule evaluates after each iteration, **Then** the system continues until 95% confidence intervals for AUTR, TOK_IN, T_WALL, CRUDe, ESR, and MC all have ≤10% half-width (minimum 5 runs, maximum 25 runs per framework).

2. **Given** multiple runs have completed for all frameworks, **When** the researcher requests statistical analysis, **Then** the system performs Kruskal-Wallis tests with Dunn-Šidák post-hoc corrections, calculates Cliff's δ effect sizes, and generates radar charts, Pareto plots, and timeline visualizations.

3. **Given** all frameworks use identical prompts and HITL responses, **When** any run is repeated, **Then** token counts, API responses, and generated code structures are bit-identical to previous runs with the same framework version.

---

### User Story 3 - Verify Reproducibility (Priority: P3)

A researcher validates that experimental results are perfectly reproducible by re-running experiments with identical configurations and verifying bit-identical outputs. This ensures scientific validity and enables peer verification.

**Why this priority**: Reproducibility is critical for academic credibility but can be validated after initial runs are functional.

**Independent Test**: Can be fully tested by executing the same run twice with identical config/experiment.yaml and comparing metrics.json, hitl_events.jsonl, and token counts byte-for-byte.

**Acceptance Scenarios**:

1. **Given** a previous run completed with specific framework commit hash and prompt set, **When** the researcher re-executes with identical configuration, **Then** all metrics (TOK_IN, TOK_OUT, HIT count, AUTR) match exactly, HITL events have identical timestamps (deterministic seeding), and OpenAI usage API data matches local logs.

2. **Given** the researcher inspects run artifacts, **When** they review commit.txt, **Then** the exact framework repository SHA is recorded, allowing precise version replication.

3. **Given** multiple researchers execute the same experiment independently, **When** they compare results, **Then** confidence intervals overlap and median values are within measurement precision (±1 token for API variance).

---

### User Story 4 - Analyze Metrics and Generate Reports (Priority: P3)

A researcher analyzes collected metrics to understand framework behavior patterns, identify failure modes, and generate publication-ready visualizations and statistical summaries.

**Why this priority**: Analysis is valuable for interpretation but depends on completed runs (P1, P2).

**Independent Test**: Can be fully tested by running analysis scripts on archived run data and verifying that reports include all required statistical tests and visualizations.

**Acceptance Scenarios**:

1. **Given** run artifacts exist in runs/{framework}/{run-id}/ directories, **When** the researcher executes aggregate analysis, **Then** the system computes mean/median/CI for all metrics, identifies outlier runs, and flags statistical significance in pairwise comparisons.

2. **Given** quality metrics (CRUDe, ESR, MC, ZDI) are available, **When** the researcher generates composite scores, **Then** Q* = 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC and AEI = AUTR / log(1 + TOK_IN) are calculated and ranked across frameworks.

3. **Given** all metrics are finalized, **When** the researcher exports for publication, **Then** radar charts, Pareto plots, and timeline charts are generated in vector format with consistent styling and labeled axes.

---

### Edge Cases

- What happens when a framework crashes during step execution?
  - System logs the failure, marks the run as "failed", archives partial artifacts (metrics up to failure point, logs, error trace), and continues with next scheduled run. Failed runs do not count toward the stopping rule minimum (5 successful runs required per framework).

- What happens when a step exceeds the 10-minute timeout?
  - System logs a warning at 9:30 mark. At 10:00, sends SIGTERM to framework process, waits 30 seconds for graceful shutdown, then sends SIGKILL if needed. The run is marked as "timeout failure", partial artifacts are archived, and the run terminates (next scheduled run begins).

- What happens when the OpenAI Usage API is temporarily unavailable?
  - System retries API queries up to 3 times with exponential backoff. If still unavailable, run completes with local token counts only, and usage_api.json is marked as incomplete for manual reconciliation.

- What happens when a framework exceeds the 2-clarification limit in a single step?
  - System logs the violation, stops accepting further clarifications for that step, and allows the framework to proceed without additional guidance (autonomy penalty recorded in HIT metric).

- What happens when health checks detect API downtime during a migration step?
  - ZDI probe increments the downtime counter, logs the timestamp and duration, and continues monitoring. The run is not interrupted, but MC (migration continuity) metric reflects the downtime.

- What happens when a framework generates code that fails CRUD validation?
  - System logs the specific failed endpoints (e.g., POST /students → 500 error), records the failure in ESR and CRUDe metrics, and continues to the next step (no automated fixes to preserve experimental integrity).

- What happens when disk space is exhausted during artifact archival?
  - System halts the current run, logs a critical error with disk usage stats, and skips archival for that run. Researcher must free space and manually restart experiments.

- What happens when the same run ID is accidentally reused?
  - System detects existing run directory, appends a UUID suffix to prevent collision, logs a warning, and proceeds with the unique ID.

## Requirements *(mandatory)*

### Functional Requirements

**Orchestration & Execution**

- **FR-001**: System MUST execute a six-step scenario where each step sends a natural language command to a framework and waits for completion before proceeding to the next step.

- **FR-002**: System MUST support three framework adapters (BAEs, ChatDev, GitHub Spec-kit) that translate standard CLI commands (start, command, health, stop) into framework-specific invocations.

- **FR-003**: System MUST isolate each run in a unique workspace directory with a generated run ID and clean environment (fresh database, no shared state between runs).

- **FR-004**: System MUST provide deterministic human-in-the-loop responses using a fixed expanded specification text from config/hitl/expanded_spec.txt, limited to 2 clarifications per step with weighted effort score HEU=3.

- **FR-005**: System MUST execute runs sequentially (no parallel framework executions) to ensure resource isolation and deterministic timing measurements.

**Metrics Collection**

- **FR-006**: System MUST collect interaction metrics: utterance count (UTT), human intervention count (HIT), autonomy rate (AUTR = 1 - HIT/6), and weighted effort (HEU).

- **FR-007**: System MUST collect efficiency metrics: input tokens (TOK_IN), output tokens (TOK_OUT), and wall-clock runtime (T_WALL) in UTC timestamps.

- **FR-008**: System MUST collect quality metrics: CRUD coverage (CRUDe, 0-12 scale), endpoint success rate (ESR, 0-1), migration continuity (MC, 0-1), and zero-downtime incidents (ZDI count).

- **FR-009**: System MUST verify local token counts against OpenAI Usage API using framework-specific API keys (token-tracker-baes, token-tracker-chatdev, token-tracker-github_spec) and log discrepancies.

- **FR-010**: System MUST compute composite scores: Q* = 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC and AEI = AUTR / log(1 + TOK_IN).

**Validation & Testing**

- **FR-011**: System MUST execute API validation tests after each step, testing all CRUD endpoints (POST, GET, PATCH, DELETE) for Student, Course, Teacher entities and relational endpoints (enroll, assign).

- **FR-012**: System MUST execute UI validation tests after each step, verifying HTTP 200 responses for main pages and checking for expected HTML content labels.

- **FR-013**: System MUST run downtime probes every 5 seconds during execution, checking API and UI health endpoints and incrementing ZDI counter for any non-200 responses.

- **FR-014**: System MUST validate that schema migrations preserve existing data (no data loss between steps 1-2, 3-4, 5-6).

**Artifact Management**

- **FR-015**: System MUST archive per-run artifacts in run.tar.gz including: complete workspace (framework-generated source code, database files, migrations, all intermediate artifacts), orchestrator logs (metrics.json, hitl_events.jsonl, api_spec.json, ui_snapshot.html, db_snapshot.sqlite, usage_api.json, stdout.log, stderr.log, orchestrator.log), commit.txt with framework SHA, and metadata.json with archive hash. API keys and virtual environments are excluded. Archive compressed with gzip.

- **FR-016**: System MUST store artifacts in isolated directories: runs/{framework}/{run-id}/ with no reuse or cross-contamination between runs. Original workspace deleted after successful archival to conserve space.

- **FR-017**: System MUST record framework repository commit SHA in commit.txt for exact version tracking, and compute SHA-256 hash of run.tar.gz stored in metadata.json for integrity verification.

**Statistical Analysis**

- **FR-018**: System MUST implement a stopping rule that continues runs until 95% confidence intervals for AUTR, TOK_IN, T_WALL, CRUDe, ESR, and MC all have ≤10% half-width (minimum 5 runs, maximum 25 runs per framework).

- **FR-019**: System MUST perform Kruskal-Wallis tests for multi-framework comparison and Dunn-Šidák post-hoc tests for pairwise comparisons.

- **FR-020**: System MUST calculate Cliff's δ effect sizes and 95% bootstrap confidence intervals for all pairwise comparisons.

- **FR-021**: System MUST generate visualizations: radar charts (6 metrics), Pareto plots (Q* vs TOK_IN), and timeline charts (CRUD coverage and downtime events over steps).

**Reproducibility & Determinism**

- **FR-022**: System MUST enforce deterministic execution: temperature=0, top_p=1.0, fixed random seeds in config, and identical prompts across runs.

- **FR-023**: System MUST version-control all prompts (step_1.txt through step_6.txt) and HITL responses (expanded_spec.txt) to ensure immutability during experiments.

- **FR-024**: System MUST pin framework versions to specific commit hashes in config/experiment.yaml and verify checksums before each run.

- **FR-025**: System MUST log all events in structured JSON format with UTC timestamps (ISO 8601), run ID, step number, and event type.

**Automation**

- **FR-026**: System MUST provide a single entry point (run_experiment.sh) that accepts framework names ("baes", "chatdev", "ghspec", or "all") and executes complete experiment cycles without manual intervention.

- **FR-027**: System MUST automatically provision isolated Python 3.11 virtual environments, install dependencies, clone framework repositories, and configure ports per framework.

- **FR-028**: System MUST handle retries and timeouts automatically: up to 3 API retries with exponential backoff, up to 2 step retries (r=2) before marking a step as failed, and enforce 10-minute timeout per step (configurable in config/experiment.yaml as step_timeout_seconds). On timeout, system sends SIGTERM, waits 30 seconds, then SIGKILL if needed.

### Key Entities

- **Framework**: Represents an LLM-driven software generation system (BAEs, ChatDev, or GitHub Spec-kit) with attributes: name, repository URL, commit hash, API port, UI port, API key name.

- **Run**: Represents a single experimental execution with attributes: run ID (UUID), framework name, start timestamp, end timestamp, status (in-progress/completed/failed), artifact directory path.

- **Step**: Represents one of six evolutionary commands with attributes: step number (1-6), command text, completion timestamp, success status, retry count.

- **Metric**: Represents a measured value with attributes: metric name (e.g., TOK_IN, AUTR, CRUDe), value (numeric), unit, step number, run ID.

- **HITL Event**: Represents a human-in-the-loop clarification with attributes: timestamp, step number, query text, response text (from expanded_spec.txt), response hash (SHA-1), run ID.

- **Artifact**: Represents a stored output file with attributes: filename, file path, file size, content hash (SHA-256), run ID.

- **Validation Result**: Represents test outcomes with attributes: test type (API/UI/downtime), endpoint/page tested, HTTP status, response time, success boolean, step number, run ID.

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Experimental Execution**

- **SC-001**: A researcher can execute a complete six-step run for a single framework in under 60 minutes of wall-clock time (10 minutes per step × 6 steps, excluding orchestrator overhead). Runs exceeding step timeouts are terminated as failures.

- **SC-002**: The system successfully completes at least 5 runs per framework without manual intervention, achieving the minimum sample size for statistical analysis.

- **SC-003**: All runs execute with zero manual steps—from environment setup through metric collection—using only run_experiment.sh invocation.

**Reproducibility**

- **SC-004**: Identical experiment configurations produce bit-identical metrics (±0 tokens) for token counts, HITL event counts, and autonomy rates across independent executions.

- **SC-005**: Independent researchers can replicate results within 5% relative error for mean values of all metrics when using the same framework commit hashes and prompts.

- **SC-006**: All run artifacts (logs, metrics, database snapshots) are archived and retrievable for verification, with 100% of completed runs having complete artifact sets.

**Metrics Accuracy**

- **SC-007**: Local token counts match OpenAI Usage API data within ±2% for 95% of runs (allowing for minor API reporting delays).

- **SC-008**: CRUD coverage metrics correctly identify all 12 possible CRUD operations across 3 entities (Student, Course, Teacher) with 100% accuracy in validation tests.

- **SC-009**: Downtime detection captures all service interruptions ≥5 seconds with timestamp precision of ±1 second.

**Statistical Power**

- **SC-010**: The stopping rule successfully terminates experiments when 95% confidence intervals reach ≤10% half-width for all key metrics, avoiding both underpowered (too few runs) and wasteful (too many runs) scenarios.

- **SC-011**: Pairwise framework comparisons achieve statistical power ≥0.8 for detecting medium effect sizes (Cliff's δ ≥ 0.33) with the collected sample sizes.

**Quality & Robustness**

- **SC-012**: The system detects and logs all framework failures (crashes, timeouts, validation errors) without corrupting other runs or halting the experiment cycle.

- **SC-013**: Validation tests identify functional defects (missing endpoints, broken UI pages, data loss during migrations) with 100% recall (no false negatives).

- **SC-014**: All generated visualizations (radar charts, Pareto plots, timelines) render correctly with labeled axes, legends, and consistent color schemes suitable for publication.

**Educational Value**

- **SC-015**: A PhD student with basic Python knowledge can set up and execute the full experiment following documentation alone, completing setup in under 2 hours.

- **SC-016**: Code readability scores (PEP 8 compliance, docstring coverage) exceed 90% across all orchestrator and adapter modules.

## Assumptions

- **Assumption 1**: All frameworks (BAEs, ChatDev, GitHub Spec-kit) can generate Python-based web applications, as the prompts specify Python 3.11, FastAPI, and SQLite.

- **Assumption 2**: OpenAI Usage API data is available within 24 hours of API calls for reconciliation with local logs.

- **Assumption 3**: Researchers have valid OpenAI API keys with sufficient quota for generating three separate tracking keys.

- **Assumption 4**: The host system has sufficient resources (16GB RAM, 50GB disk space) to run isolated framework environments and store artifacts for 25 runs × 3 frameworks.

- **Assumption 5**: Framework repositories remain accessible at their public GitHub URLs for cloning at specified commit hashes.

- **Assumption 6**: The six-step scenario adequately represents realistic software evolution patterns for academic domain applications.

- **Assumption 7**: Failed steps result in run termination and a fresh run attempt. After r=2 automatic step retries fail, the system marks the run as "failed", archives partial artifacts for debugging, and continues with the next scheduled run. Failed runs do not count toward the stopping rule minimum. See [decisions.md](decisions.md#decision-1-failed-step-retry-policy) for detailed rationale.

- **Assumption 8**: Each step has a maximum timeout of 10 minutes (600 seconds). If a framework does not complete a step within this time, the system sends SIGTERM (graceful shutdown), waits 30 seconds, then sends SIGKILL if needed. The run is marked as "timeout failure" and terminated per Assumption 7. Timeout values are configurable in config/experiment.yaml. See [decisions.md](decisions.md#decision-2-step-timeout-policy) for detailed rationale.

- **Assumption 9**: Artifact archival includes the complete workspace: framework-generated source code, database files, all intermediate artifacts, orchestrator logs, and metrics. Archives are compressed with gzip and stored as run.tar.gz (~10GB per run). API keys and virtual environments are excluded. See [decisions.md](decisions.md#decision-3-artifact-archival-scope) for detailed contents and rationale.

## Constraints

- **Performance**: Each run must complete within 60 minutes of wall-clock time (10 minutes per step × 6 steps) to enable realistic experimental schedules. Runs exceeding step timeouts are terminated as failures.

- **Storage**: Artifact storage must not exceed 10GB per run to keep total experiment footprint under 1TB (75 runs × 10GB + margin). Full workspace archival includes generated code, database, and all logs.

- **Licensing**: All code, configurations, and artifacts must be CC BY 4.0 compatible with no proprietary dependencies.

- **Compatibility**: System must run on Ubuntu 22.04 LTS or equivalent Linux distributions with Python 3.11+ and Docker installed.

- **Network**: System requires stable internet access for OpenAI API calls and framework repository cloning but should gracefully handle transient network failures with retries.

- **Determinism**: No use of system time for random seeds; all randomness sources must be explicitly seeded from config/experiment.yaml.
