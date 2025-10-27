# Data Model: GHSpec-Kit Integration Enhancement

**Feature**: 007-integration-of-ghspec  
**Date**: October 27, 2025  
**Purpose**: Document key entities, their attributes, relationships, and validation rules

## Entity Definitions

### 1. Constitution

**Purpose**: Set of project-level principles, coding standards, testing requirements, and organizational constraints that guide all GHSpec-Kit development phases.

**Attributes**:
- `source_type`: String (enum: "project", "inline", "default") - Origin of constitution content
- `file_path`: Optional[Path] - Absolute path to constitution file if source_type is "project" or "default"
- `content`: String - Full markdown text of constitution principles (unbounded length)
- `size_bytes`: Integer - Size of constitution content in bytes
- `loaded_at`: Timestamp - When constitution was loaded into adapter instance
- `chunked`: Boolean - Whether content was chunked for prompt injection (True if size > 100KB)

**Relationships**:
- Referenced by PhaseExecutionContext during prompt building
- Loaded once during GHSpecAdapter.__init__() and cached for run lifetime

**Validation Rules**:
- content MUST NOT be empty string or whitespace-only
- If source_type is "project" or "default", file_path MUST exist
- If source_type is "inline", file_path MUST be None
- Markdown format validation: SHOULD contain headers (##) for section structure

**State Transitions**: Immutable after loading (no updates during experiment run)

---

### 2. Tech Stack Configuration

**Purpose**: Optional specification of preferred technologies, frameworks, cloud providers, and infrastructure choices for the Plan phase.

**Attributes**:
- `constraints_text`: Optional[String] - Natural language description of tech stack requirements
- `provided`: Boolean - Whether constraints were explicitly configured (vs. AI free choice)
- `source`: String (enum: "yaml", "none") - Configuration source
- `applied_in_phase`: Optional[String] - Which phase used these constraints ("plan" expected)

**Relationships**:
- Loaded from experiment.yaml `tech_stack_constraints` key
- Injected into Plan phase user prompt via _build_phase_prompt()
- Referenced in sprint context for consistency checking (sprint_num > 1)

**Validation Rules**:
- If provided is True, constraints_text MUST be non-empty string
- constraints_text MUST NOT contain only whitespace
- No format restrictions on content (natural language description)

**State Transitions**:
- Loaded during GHSpecAdapter.start() from config
- Remains constant throughout run

---

### 3. Clarification Guidelines

**Purpose**: Pre-defined responses or decision rules used to automatically resolve AI clarification requests without manual intervention (deterministic HITL).

**Attributes**:
- `file_path`: Path - Absolute path to HITL guidelines file (config/hitl/ghspec_clarification_guidelines.txt)
- `content`: String - Full text of clarification responses
- `iteration_sections`: Optional[List[String]] - Parsed iteration-specific guidance (for multi-iteration support)
- `loaded_at`: Timestamp - When guidelines were loaded

**Relationships**:
- Referenced by _handle_clarification() during phase execution
- Cached in self.hitl_text (inherited from BaseAdapter pattern)
- May be appended with iteration-specific text for clarification_count > 1

**Validation Rules**:
- file_path MUST exist before any phase execution
- content MUST NOT be empty
- If iteration_sections present, MUST have at least 1 section

**State Transitions**:
- Loaded once on first _handle_clarification() call
- Cached for subsequent clarifications in same run

---

### 4. Phase Execution Context

**Purpose**: Aggregated state tracking current phase, sprint number, previous artifacts, token counts, and HITL interactions across the 5-phase workflow.

**Attributes**:
- `current_phase`: String (enum: "specify", "plan", "tasks", "implement", "bugfix") - Active phase name
- `phase_number`: Integer (1-5) - Numeric phase identifier
- `step_num`: Integer - Scenario step number (from orchestrator)
- `sprint_num`: Integer - Sprint iteration (1-indexed)
- `run_id`: String - Unique run identifier
- `start_timestamp`: Integer - Unix timestamp when phase started
- `end_timestamp`: Optional[Integer] - Unix timestamp when phase completed
- `artifacts_generated`: List[Path] - Paths to spec.md, plan.md, tasks.md, code files
- `tokens_in`: Integer - Aggregate input tokens for all phases so far
- `tokens_out`: Integer - Aggregate output tokens for all phases so far
- `api_calls`: Integer - Total API call count
- `cached_tokens`: Integer - Tokens served from cache
- `hitl_count`: Integer - Number of clarification iterations in current phase
- `validation_errors`: Optional[List[String]] - Errors from previous validation run

**Relationships**:
- Maintained by GHSpecAdapter.execute_step() across phase sequence
- Passed to each _execute_phase() and _execute_task_implementation()
- Aggregated metrics returned to orchestrator at end of execute_step()

**Validation Rules**:
- current_phase MUST match phase_number mapping (1=specify, 2=plan, 3=tasks, 4=implement, 5=bugfix)
- tokens_in, tokens_out, api_calls MUST be non-negative integers
- start_timestamp MUST be <= end_timestamp (if end_timestamp set)
- sprint_num MUST be >= 1

**State Transitions**:
- Initialized at start of execute_step()
- Updated after each phase completes
- Finalized when execute_step() returns to orchestrator

---

### 5. Bugfix Task

**Purpose**: Derived repair instruction targeting a specific error, including file path, error message, and targeted fix scope.

**Attributes**:
- `task_id`: String - Unique identifier (e.g., "bugfix-001", "bugfix-002")
- `file_path`: Path - Relative path to file requiring fix (from src_dir)
- `error_type`: String (enum: "syntax", "import", "runtime", "validation") - Error category
- `error_message`: String - Full error text from validation output
- `line_number`: Optional[Integer] - Line where error occurred (if available from traceback)
- `error_excerpt`: Optional[String] - Relevant code snippet around error
- `spec_context`: String - Excerpt from spec.md relevant to this file/feature
- `fix_strategy`: String - Brief description of intended repair approach

**Relationships**:
- Derived from validation_errors list via _derive_bugfix_tasks()
- Up to 3 bugfix tasks created per iteration (FR-006)
- Each task corresponds to one file that needs fixing
- Used to build bugfix prompt via _build_bugfix_prompt()

**Validation Rules**:
- file_path MUST be relative path within workspace src_dir
- error_message MUST NOT be empty
- error_type MUST be one of defined enum values
- spec_context MUST NOT be empty (fail if cannot extract relevant section)

**State Transitions**:
- Created: Derived from validation output
- Processed: Fix generated and applied
- Resolved: File updated, pending re-validation
- (No explicit state field - lifecycle managed by bugfix loop logic)

---

### 6. Template Configuration

**Purpose**: Configuration controlling how prompt templates are loaded (static vs. dynamic) and which source is used.

**Attributes**:
- `source_mode`: String (enum: "static", "dynamic") - Template loading strategy
- `static_path`: Path - Directory for static templates (docs/ghspec/prompts/)
- `dynamic_path`: Path - Directory for dynamic templates (frameworks/ghspec/.specify/templates/commands/)
- `ghspec_commit_hash`: Optional[String] - Spec-Kit repository commit hash (if dynamic mode)
- `loaded_templates`: Dict[String, String] - Cached template content (phase → content)

**Relationships**:
- Loaded from experiment.yaml `template_source` key
- Referenced by _load_prompt_template() for all phases
- If dynamic, ghspec_commit_hash logged in experiment metadata

**Validation Rules**:
- source_mode MUST be "static" or "dynamic"
- If source_mode is "static", static_path directory MUST exist
- If source_mode is "dynamic", dynamic_path directory MUST exist
- Template files MUST contain "System Prompt" and "User Prompt Template" sections

**State Transitions**:
- Loaded during GHSpecAdapter.start()
- Templates cached on first load per phase (lazy evaluation)
- Immutable for run duration (consistent prompts across phases)

---

## Entity Relationships Diagram

```
┌──────────────────┐
│  Constitution    │◄──┐
└──────────────────┘   │
                       │
┌──────────────────┐   │  Referenced during
│ Tech Stack       │◄──┤  prompt building
│ Configuration    │   │
└──────────────────┘   │
                       │
┌──────────────────┐   │
│ Clarification    │◄──┤
│ Guidelines       │   │
└──────────────────┘   │
                       │
                       │
┌──────────────────────┴───────────┐
│  Phase Execution Context         │
│  (orchestrates workflow)          │
└──────────────────────┬───────────┘
                       │
                       │ Manages
                       │
                ┌──────▼──────┐
                │ Bugfix Task │ (0-3 instances)
                └─────────────┘

┌──────────────────┐
│ Template Config  │──► Determines template source
└──────────────────┘    for all phases
```

---

## Data Flow

### Constitution Loading Flow
1. GHSpecAdapter.__init__() called
2. _load_constitution() checks: project → inline → default
3. Constitution content cached in self.constitution_content
4. During each phase: Constitution excerpts injected into system prompts
5. Large constitutions (>100KB): Chunk into first 30KB + last 10KB for prompts

### Clarification Handling Flow
1. Phase executes, AI response checked via _needs_clarification()
2. If clarification detected: _handle_clarification() invoked
3. Load guidelines from config/hitl/ghspec_clarification_guidelines.txt
4. Append iteration-specific guidance if clarification_count > 1
5. Re-inject into prompt, retry API call
6. Increment hitl_count in PhaseExecutionContext
7. Max 3 iterations per phase (FR-004)

### Bugfix Derivation Flow
1. Phase 4 (Implement) completes, validation runs
2. Validation errors captured in PhaseExecutionContext.validation_errors
3. _derive_bugfix_tasks() parses errors, creates up to 3 Bugfix Tasks
4. For each task: Extract file_path, error_message, line_number from traceback
5. _build_bugfix_prompt() loads bugfix_template.md, injects task context
6. AI generates fix, _apply_fix() writes updated file
7. Re-run validation, iterate up to 3 times (FR-015)

---

## Validation Constraints Summary

| Entity | Key Constraint | Enforcement Point |
|--------|----------------|-------------------|
| Constitution | content must be non-empty | _load_constitution() |
| Tech Stack Config | constraints_text non-empty if provided=True | GHSpecAdapter.start() |
| Clarification Guidelines | file must exist before phase execution | _handle_clarification() |
| Phase Execution Context | current_phase matches phase_number | execute_step() |
| Bugfix Task | file_path must be within src_dir | _derive_bugfix_tasks() |
| Template Configuration | source_mode must be valid enum | _get_template_path() |

---

## Persistence Strategy

**All entities are transient (in-memory for run duration).** No database persistence required.

**File-based persistence**:
- Constitution: Read from config/ directory files
- Clarification Guidelines: Read from config/hitl/ file
- Templates: Read from docs/ or frameworks/ directories
- Phase artifacts: Written to workspace (spec.md, plan.md, tasks.md, code files)

**Logging persistence**:
- Phase Execution Context: Logged to runs/<framework>/<run-id>/orchestrator.log as JSON
- Bugfix attempts: Logged with before/after diffs for analysis
- Token metrics: Logged per phase and aggregated at run end

**No cross-run state**: Each experiment run is independent (Constitution Principle XII)
