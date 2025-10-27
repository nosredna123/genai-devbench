# Research & Technical Decisions: GHSpec-Kit Integration Enhancement

**Feature**: 007-integration-of-ghspec  
**Date**: October 27, 2025  
**Purpose**: Resolve technical unknowns and document architectural decisions for enhancement implementation

## Research Tasks Completed

### 1. Constitution File Loading Strategy

**Decision**: Implement hierarchical fallback pattern with no size limits

**Rationale**:
- Spec-Kit's constitution concept requires flexible loading from multiple sources
- Clarification confirmed unlimited size support (via chunking/summarization)
- Existing HITL pattern (config/hitl/) provides proven file-based configuration model
- Python's pathlib and open() handle arbitrarily large files efficiently

**Alternatives Considered**:
- Hard size limits (2KB, 10KB, 50KB): Rejected - too restrictive for complex organizational standards
- Database storage: Rejected - adds unnecessary dependency, violates Minimal Dependencies principle
- Inline YAML: Rejected - poor readability for multi-paragraph coding standards

**Implementation Approach**:
- Check for `config/constitution/project_constitution.md` first (explicit user-provided)
- Fall back to experiment.yaml `constitution_text` field (inline override)
- Fall back to `config/constitution/default_principles.md` (sensible defaults)
- Large file handling: Read in chunks if >100KB, summarize sections >50KB for prompt injection
- Cache loaded constitution in adapter instance to avoid repeated disk I/O

---

### 2. Prompt Template Management (Static vs. Dynamic)

**Decision**: Support both modes via configuration flag, default to static for reproducibility

**Rationale**:
- Reproducibility principle requires fixed prompt versions for published experiments
- Development/research flexibility benefits from tracking upstream Spec-Kit improvements
- Existing docs/ghspec/prompts/ contains curated static templates
- Cloned frameworks/ghspec/ repository may contain updated official templates

**Alternatives Considered**:
- Static only: Rejected - limits ability to test new Spec-Kit features
- Dynamic only: Rejected - breaks reproducibility when upstream changes
- Manual sync process: Rejected - error-prone, violates automation principle

**Implementation Approach**:
- Add `template_source` config key: `"static"` (default) or `"dynamic"`
- Static mode: Load from `docs/ghspec/prompts/{phase}_template.md`
- Dynamic mode: Load from `frameworks/ghspec/.specify/templates/commands/{phase}.md`
- Version pinning: When dynamic, document Spec-Kit commit hash in experiment metadata
- Template validation: Check for required sections (System Prompt, User Prompt Template)

---

### 3. Bugfix Phase Automation Architecture

**Decision**: Implement error-driven task derivation with targeted fix generation

**Rationale**:
- Existing _derive_bugfix_tasks() and _build_bugfix_prompt() methods provide foundation
- Spec-Kit's bugfix philosophy: minimal targeted fixes, preserve working code
- Validation errors (syntax, import, runtime) map naturally to file-specific fix tasks
- Existing bugfix_template.md prompt guides AI toward conservative repairs

**Alternatives Considered**:
- Full re-generation: Rejected - wasteful, high risk of breaking working code
- Manual HITL bugfix: Rejected - violates deterministic HITL principle
- Retry without changes: Rejected - infinite loop risk, low success rate

**Implementation Approach**:
- Parse validation output to extract: error type, file path, line number, error message
- Derive up to 3 bugfix tasks (limit per FR-006), prioritize by error severity
- For each task: Load bugfix_template.md, inject error context + spec excerpts
- Call OpenAI API with bugfix-specific system prompt (conservative, minimal changes)
- Apply fixes to affected files, re-run validation, track iteration count (max 3)
- Log all bugfix attempts with before/after diffs for experiment analysis

---

### 4. Multi-Iteration Clarification Handling

**Decision**: Extend existing _handle_clarification() to support up to 3 loops per phase

**Rationale**:
- Current implementation handles 1 clarification iteration
- Spec-Kit guidance allows up to 3 questions per phase
- Deterministic HITL requires pre-defined responses for all iterations
- Edge case: AI might re-ask if first clarification insufficient

**Alternatives Considered**:
- Single iteration only: Rejected - may fail on complex ambiguities
- Unlimited iterations: Rejected - infinite loop risk, violates constitution's fail-fast
- Progressive clarification expansion: Rejected - over-engineered for deterministic responses

**Implementation Approach**:
- Track clarification_count per phase (initialize to 0)
- After each _handle_clarification() call, increment counter
- If _needs_clarification() still true and count < 3: re-inject expanded guidelines, retry
- If count reaches 3 and still unclear: log warning, proceed with best-effort interpretation
- HITL file structure: Append iteration-specific guidance sections (e.g., "Iteration 2: ...'")

---

### 5. Tech Stack Constraint Injection

**Decision**: Add optional tech_stack_constraints field to experiment.yaml, inject into Plan phase prompts

**Rationale**:
- Controlled experiments require consistent tech stacks across framework comparisons
- Spec-Kit's /speckit.plan command accepts user input for tech preferences
- Existing prompt templates have {placeholders} for context injection
- Constitution's fail-fast principle: missing constraints should not default silently

**Alternatives Considered**:
- Hard-coded per experiment: Rejected - poor scalability, violates DRY
- Interactive prompt: Rejected - breaks automation-first principle
- Infer from previous sprint: Rejected - doesn't help first sprint, may propagate bad choices

**Implementation Approach**:
- Add `tech_stack_constraints` key to experiment.yaml (optional, default: None)
- If present: inject as "TECHNICAL CONSTRAINTS: {constraints}" in plan_template user prompt
- If absent: inject "TECHNICAL CONSTRAINTS: None specified - AI free choice based on spec"
- Validate format: Must be non-empty string if provided (fail-fast on empty/whitespace)
- Document in experiment metadata for cross-run comparisons

---

### 6. OpenAI API Failure Handling

**Decision**: Implement fail-fast with no retries, per clarification requirement

**Rationale**:
- Clarification confirmed: "Fail-fast: Any API failure aborts entire run, no retries"
- Retry logic masks intermittent issues and complicates experiment validity
- Clear failure attribution more valuable than partial results for research
- Existing BaseAdapter.call_openai_chat_completion() raises exceptions - preserve this

**Alternatives Considered**:
- Exponential backoff retries: Rejected - contradicts fail-fast clarification
- Phase-level checkpoints: Rejected - adds complexity, violates YAGNI for current scope
- Best-effort logging: Rejected - partial data harms reproducibility

**Implementation Approach**:
- Remove any retry logic from GHSpecAdapter methods
- Let OpenAI API exceptions propagate to orchestrator unchanged
- Orchestrator marks experiment as FAILED with clear error message
- Log API call timestamps, request/response metadata before call (for debugging)
- Document expected failure modes in quickstart.md (rate limits, network timeouts)

---

### 7. Concurrent Execution Safety

**Decision**: Enforce single-threaded execution via process-level locking (future enhancement) or documentation

**Rationale**:
- Clarification confirmed: "Single-threaded only: No concurrent execution support"
- Current architecture (isolated workspace_path per run) provides process isolation
- No shared mutable state in GHSpecAdapter (constitution cached per instance)
- Orchestrator already runs sequentially - no code changes needed immediately

**Alternatives Considered**:
- File-based locks: Rejected - YAGNI, adds complexity for hypothetical future need
- Shared resource coordination: Rejected - no shared resources in current design
- Thread-safe data structures: Rejected - not applicable to single-threaded requirement

**Implementation Approach**:
- Document single-threaded requirement in src/adapters/ghspec_adapter.py docstring
- Add assertion in __init__: Warn if called from non-main thread (development aid)
- Orchestrator responsibility: Ensure sequential execution (already implemented)
- Future enhancement: Add process lock file (runs/ghspec.lock) if parallelism needed

---

## Best Practices Research

### Python File Handling for Large Constitutions
- Use streaming reads with open(file, 'r', encoding='utf-8')
- Process in 10KB chunks if file > 100KB
- pathlib.Path.stat().st_size for size check before reading
- Summarization via first N lines + last N lines if context window exceeded

### OpenAI API Usage Patterns
- Existing fetch_usage_from_openai() in BaseAdapter handles token tracking
- Timestamp tracking: Use int(time.time()) for start/end around API calls
- Error handling: Catch requests.exceptions for network errors, OpenAIError for API failures
- Model selection: gpt-4o-mini already configured in existing adapter

### Prompt Template Parsing
- Markdown section splitting: Use re.split(r'\n##+ ', content) for headers
- Code block extraction: Match ```...``` with re.DOTALL for multi-line content
- Validation: Check for required sections ("System Prompt", "User Prompt Template")
- Placeholder substitution: str.replace() for simple {key} → value mapping

### Spec-Kit Phase Sequencing
- Each phase depends on previous artifacts: Plan needs Spec, Tasks need Spec+Plan, Implement needs all three
- Atomic writes: Save each artifact immediately after generation (fail-fast on disk errors)
- Artifact validation: Check file existence and minimum size before starting dependent phase
- Logging: Emit structured event for phase start/end with timestamps and artifact paths

---

## Technology Integration Patterns

### Constitution Loading Pattern
```python
def _load_constitution(self) -> str:
    """Load project constitution with hierarchical fallback."""
    # Priority 1: Explicit project constitution
    project_const = Path("config/constitution/project_constitution.md")
    if project_const.exists():
        return project_const.read_text(encoding='utf-8')
    
    # Priority 2: Inline YAML override
    if 'constitution_text' in self.config:
        return self.config['constitution_text']
    
    # Priority 3: Default principles
    default_const = Path("config/constitution/default_principles.md")
    if default_const.exists():
        return default_const.read_text(encoding='utf-8')
    
    # Fail-fast: No constitution available
    raise FileNotFoundError("No constitution found (checked project/inline/default)")
```

### Template Source Selection Pattern
```python
def _get_template_path(self, phase: str) -> Path:
    """Resolve template path based on configuration."""
    mode = self.config.get('template_source', 'static')
    
    if mode == 'static':
        return self.project_root / "docs" / "ghspec" / "prompts" / f"{phase}_template.md"
    elif mode == 'dynamic':
        return self.project_root / "frameworks" / "ghspec" / ".specify" / "templates" / "commands" / f"{phase}.md"
    else:
        raise ValueError(f"Invalid template_source: {mode} (must be 'static' or 'dynamic')")
```

### Bugfix Loop Pattern
```python
def _execute_bugfix_phase(self, validation_errors: list) -> Tuple[int, int, int]:
    """Automated bugfix with error-driven task derivation."""
    bugfix_tasks = self._derive_bugfix_tasks(validation_errors)[:3]  # FR-006: max 3
    
    iteration = 0
    max_iterations = 3  # FR-015: prevent infinite loops
    
    while iteration < max_iterations and bugfix_tasks:
        for task in bugfix_tasks:
            # Generate fix, apply, validate
            fix_code = self._generate_bugfix(task)
            self._apply_fix(task['file'], fix_code)
        
        # Re-validate
        new_errors = self._run_validation()
        if not new_errors:
            return (iteration + 1, tokens_in, tokens_out)  # Success
        
        bugfix_tasks = self._derive_bugfix_tasks(new_errors)[:3]
        iteration += 1
    
    # Failed to fix within iteration limit
    logger.warning(f"Bugfix phase exhausted {max_iterations} attempts")
    return (max_iterations, tokens_in, tokens_out)
```

---

## Risk Mitigation Strategies

| Risk | Mitigation Strategy |
|------|---------------------|
| Large constitution exceeds context window | Implement chunking: Use first 30KB + last 10KB for prompt injection |
| Dynamic templates break reproducibility | Default to static mode, document template_source in metadata |
| Bugfix loop fails to converge | Hard limit of 3 iterations (FR-015), log all attempts for analysis |
| Tech stack constraints ignored by AI | Explicit validation: Check plan.md for constraint keywords after generation |
| API failures mid-workflow | Fail-fast immediately, orchestrator logs phase progress for debugging |
| Concurrent execution attempts | Document single-threaded requirement, add development-time assertion |

---

## Dependencies & Prerequisites

**No new external dependencies required.** All enhancements use:
- Python 3.11+ standard library (pathlib, re, time, json)
- Existing dependencies (PyYAML for config, requests for OpenAI)
- Existing BaseAdapter infrastructure (logging, API calls, token tracking)

**Prerequisites for implementation**:
1. Existing GHSpecAdapter with Phases 1-4 partially implemented
2. BaseAdapter.fetch_usage_from_openai() method available
3. Prompt templates in docs/ghspec/prompts/
4. HITL guidelines in config/hitl/ghspec_clarification_guidelines.txt
5. Experiment configuration via config/experiment.yaml

---

## Next Steps (Phase 1)

1. Create data-model.md documenting key entities (Constitution, Template Config, Bugfix Task)
2. Update quickstart.md with setup instructions for constitution and template configuration
3. No API contracts needed (internal adapter enhancement, no new external interfaces)
4. Proceed to /speckit.tasks for detailed implementation task breakdown
