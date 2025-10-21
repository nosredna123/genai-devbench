# Implementation Plan: Workspace Refactor - Shared Framework & VEnv Architecture

**Branch**: `main` | **Date**: October 21, 2025 | **Spec**: [SHARED_FRAMEWORK_VENV_DESIGN.md](./SHARED_FRAMEWORK_VENV_DESIGN.md)

**Feature**: Eliminate wasteful framework copying and venv duplication by centralizing shared resources while isolating run-specific artifacts.

## Summary

**Problem**: Current implementation copies framework code (~3.6MB) and creates fresh virtual environments (~619MB) for every run, wasting ~622MB disk space and 5+ minutes per run. This violates DRY principles and creates unnecessary I/O overhead.

**Solution**: Centralize framework setup logic in `BaseAdapter`, create shared venvs once during `setup.sh`, and maintain only run-specific artifacts in workspace directories. This achieves 99.8% disk reduction per run and instant startup times.

**Technical Approach**: 
1. Add generic venv/framework management methods to `BaseAdapter`
2. Modify `setup.sh` template to create shared `.venv` directories
3. Refactor all adapters to use shared resources instead of copying
4. Separate read-only shared resources from writable run-specific data

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: PyYAML, subprocess, pathlib, shutil  
**Storage**: File system (frameworks/, runs/ directories)  
**Testing**: pytest with 68 existing adapter tests (must remain passing)  
**Target Platform**: Linux/macOS (bash scripts)  
**Project Type**: Single Python project with template generation  
**Performance Goals**: 
- Reduce per-run disk usage from ~622MB to ~1MB (99.8% reduction)
- Eliminate 5-minute venv creation time (instant startup)
- Maintain 83% total disk savings (7.5GB → 1.25GB per 6-run experiment)

**Constraints**: 
- Must maintain backward compatibility with existing experiments
- All 68 adapter tests must pass
- Framework reproducibility must be preserved (commit hash pinning)
- Scientific reproducibility requirements (identical runs)

**Scale/Scope**: 
- 3 framework adapters (BAEs, ChatDev, GHSpec)
- ~150 lines of duplicate code to be removed
- 13 implementation tasks across 5 files

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Verify compliance with BAEs Experiment Constitution v1.0.0:

- [x] **Scientific Reproducibility**: ✅ Framework versions remain pinned via commit hashes; shared venvs don't affect determinism
- [x] **Clarity & Transparency**: ✅ Centralized methods improve code clarity; DRY principle enhances maintainability
- [x] **Open Science**: ✅ No new proprietary dependencies; all code remains CC BY 4.0
- [x] **Minimal Dependencies**: ✅ Uses existing stdlib (pathlib, subprocess, shutil); no new dependencies
- [x] **Deterministic HITL**: ✅ No changes to HITL workflow; clarifications remain automated
- [x] **Reproducible Metrics**: ✅ No changes to metrics collection; OpenAI API tracking unchanged
- [x] **Version Control Integrity**: ✅ Commit hashes remain pinned; framework versions controlled
- [x] **Automation-First**: ✅ Enhanced automation via `setup.sh`; no manual steps added
- [x] **Failure Isolation**: ✅ Improved isolation - only artifacts in workspace; frameworks shared safely
- [x] **Educational Accessibility**: ✅ Clearer separation of concerns; better code organization

**Constitution Verdict**: ✅ **PASS** - All principles satisfied. This refactor actively improves principles II (Clarity) and IV (Minimal Dependencies) by eliminating code duplication.

## Project Structure

### Documentation (this feature)

```
docs/20251021-workspace-refactor/
├── SHARED_FRAMEWORK_VENV_DESIGN.md    # Design document (completed)
├── IMPLEMENTATION_PLAN.md             # This file (Phase 0-1 output)
├── research.md                        # Phase 0: Technical research
├── data-model.md                      # Phase 1: Directory structure contracts
├── contracts/                         # Phase 1: API contracts for BaseAdapter methods
│   ├── base_adapter_methods.yaml     # Method signatures and contracts
│   └── directory_structure.yaml      # Filesystem layout contracts
└── tasks.md                           # Phase 2: Detailed task breakdown
```

### Source Code (affected files)

```
genai-devbench/
├── src/adapters/
│   ├── base_adapter.py               # [MODIFY] Add 4 new generic methods
│   ├── baes_adapter.py               # [MODIFY] Remove venv logic, use shared resources
│   ├── chatdev_adapter.py            # [MODIFY] Remove venv logic, use shared resources
│   └── ghspec_adapter.py             # [MODIFY] Remove framework copying
│
├── templates/
│   └── setup.sh                      # [MODIFY] Add shared venv creation
│
├── config/
│   └── experiment.yaml               # [MODIFY] Add use_venv flags
│
└── tests/
    └── unit/
        ├── test_baes_adapter*.py     # [VERIFY] All tests must pass
        ├── test_chatdev_adapter*.py  # [VERIFY] All tests must pass
        └── test_ghspec_adapter*.py   # [VERIFY] All tests must pass
```

**Structure Decision**: Single Python project (Option 1) - this is a refactoring effort within the existing monolithic structure. No new modules or services are introduced; only internal reorganization of responsibilities.

## Complexity Tracking

*No Constitution violations - this section documents design complexity justifications*

| Design Decision | Justification | Alternative Considered |
|-----------------|---------------|------------------------|
| Shared venv for all runs | Same commit hash = identical packages; read-only nature is safe | Per-run venvs with symlinks - adds complexity without benefits |
| BaseAdapter owns venv logic | DRY principle; consistent behavior across all adapters | Keep in adapters with shared utility module - partial duplication remains |
| setup.sh creates venvs | One-time cost; explicit setup phase | Lazy creation on first run - adds runtime complexity and first-run penalty |

---

## Phase 0: Research & Analysis

### Research Questions

Based on Technical Context and design document review, the following areas require investigation:

#### 1. Virtual Environment Sharing Safety
**Question**: Can multiple Python processes safely share a read-only venv simultaneously?

**Research Tasks**:
- Investigate Python venv architecture (pyvenv.cfg, site-packages)
- Confirm no write operations occur during package imports
- Test concurrent access patterns with pytest-xdist
- Document any edge cases (C extensions, __pycache__)

**Expected Outcome**: Confirmation that shared venvs are safe for concurrent read-only access

#### 2. Framework Patching Strategy
**Question**: Where should ChatDev compatibility patches be applied if framework is shared?

**Research Tasks**:
- Review current ChatDev patching logic (_patch_openai_compatibility, _patch_o1_model_support)
- Determine if patches modify source files or runtime state
- Decide: patch during setup.sh (once) vs. patch during adapter.start() (per-run)
- Document patch persistence requirements

**Expected Outcome**: Clear strategy for applying framework patches in shared environment

#### 3. Workspace Directory Contracts
**Question**: What directories does each adapter actually need in workspace?

**Research Tasks**:
- Analyze BAeSAdapter: managed_system/, database/ confirmed
- Analyze ChatDevAdapter: WareHouse/ for generated projects
- Analyze GHSpecAdapter: output directories for generated specs
- Document any framework-specific temporary directories

**Expected Outcome**: Complete list of required workspace subdirectories per adapter

#### 4. setup.sh Template Integration
**Question**: How does setup.sh determine which frameworks need venvs?

**Research Tasks**:
- Review current setup.sh structure and configuration loading
- Design conditional venv creation based on use_venv flag
- Plan error handling for failed venv creation
- Document timeout and retry strategies

**Expected Outcome**: Concrete setup.sh implementation approach

#### 5. Backward Compatibility
**Question**: Will existing experiments break with this change?

**Research Tasks**:
- Identify experiments relying on workspace/framework_dir structure
- Review metrics collection paths (do they reference workspace/framework?)
- Check if any tests hardcode workspace/baes_framework paths
- Plan migration strategy for in-flight experiments

**Expected Outcome**: Compatibility assessment and migration plan

### Research Deliverable: research.md

**Output Location**: `docs/20251021-workspace-refactor/research.md`

**Required Sections**:
1. **Venv Safety Analysis**
   - Decision: [shared venv is/isn't safe]
   - Rationale: [Python package architecture evidence]
   - Testing approach: [concurrent access test plan]

2. **Patching Strategy**
   - Decision: [where patches are applied]
   - Rationale: [why this approach chosen]
   - Implementation notes: [specific changes needed]

3. **Workspace Directory Requirements**
   - BAEs: [list of directories]
   - ChatDev: [list of directories]
   - GHSpec: [list of directories]
   - Rationale: [why each is needed]

4. **setup.sh Implementation**
   - Approach: [conditional venv creation logic]
   - Error handling: [timeout, disk space checks]
   - Configuration reading: [how use_venv flag is accessed]

5. **Backward Compatibility**
   - Breaking changes: [list any]
   - Migration path: [how to upgrade existing experiments]
   - Deprecation warnings: [what to add]

---

## Phase 1: Design & Contracts

**Prerequisites**: research.md complete with all decisions finalized

### 1.1 Data Model: Directory Structure

**Output**: `docs/20251021-workspace-refactor/data-model.md`

**Content**:

#### Entity: SharedFramework
- **Location**: `<experiment>/frameworks/<name>/`
- **Attributes**:
  - Source code (cloned from repo)
  - .venv/ (virtual environment)
  - requirements.txt
  - Framework-specific files
- **Lifecycle**: Created once by setup.sh, read-only thereafter
- **Ownership**: BaseAdapter (via get_shared_framework_path)

#### Entity: RunWorkspace
- **Location**: `<experiment>/runs/<framework>/<run_id>/workspace/`
- **Attributes**:
  - managed_system/ (generated artifacts)
  - database/ (run-specific state)
  - outputs/ (framework-specific results)
- **Lifecycle**: Created per-run by adapter.start(), writable throughout run
- **Ownership**: Adapter-specific (created via create_workspace_structure)

#### Relationship: Workspace → Framework
- **Type**: References (read-only)
- **Cardinality**: Many workspaces : One framework
- **Implementation**: Path reference, no copying

#### State Transitions
1. **Setup Phase**: frameworks/ populated via git clone + venv creation
2. **Run Start**: workspace/ created with subdirectories only
3. **Run Execute**: Adapter reads from frameworks/, writes to workspace/
4. **Run Complete**: workspace/ contains all artifacts, frameworks/ unchanged

### 1.2 API Contracts: BaseAdapter Methods

**Output**: `docs/20251021-workspace-refactor/contracts/base_adapter_methods.yaml`

```yaml
openapi: 3.0.0
info:
  title: BaseAdapter Shared Resource Management API
  version: 1.0.0
  description: Internal API contracts for framework and venv management

components:
  schemas:
    FrameworkPath:
      type: object
      properties:
        framework_name:
          type: string
          enum: [baes, chatdev, ghspec]
        path:
          type: string
          format: path
          description: Absolute path to frameworks/<name>/
        exists:
          type: boolean
        
    VenvPath:
      type: object
      properties:
        venv_dir:
          type: string
          format: path
          description: Absolute path to frameworks/<name>/.venv/
        python_executable:
          type: string
          format: path
          description: Absolute path to Python interpreter
        is_valid:
          type: boolean
          
    WorkspaceStructure:
      type: object
      properties:
        subdirs:
          type: array
          items:
            type: string
          description: Directory names to create in workspace
        created_paths:
          type: object
          additionalProperties:
            type: string
            format: path
          description: Map of subdir name to absolute path

methods:
  setup_shared_venv:
    description: Set up or verify shared virtual environment for framework
    parameters:
      - name: framework_name
        type: string
        required: true
        description: Name of framework (baes, chatdev, ghspec)
      - name: requirements_file
        type: string
        format: path
        required: false
        default: frameworks/<name>/requirements.txt
      - name: python_version
        type: string
        required: false
        default: python3
      - name: timeout_install
        type: integer
        required: false
        default: 300
        description: Timeout in seconds for pip install
    returns:
      type: string
      format: path
      description: Absolute path to shared venv directory
    raises:
      - RuntimeError: If venv creation fails
      - TimeoutError: If pip install exceeds timeout
      - FileNotFoundError: If requirements.txt missing
    side_effects:
      - Creates frameworks/<name>/.venv/ if not exists
      - Installs packages from requirements.txt
      - Logs to structured logger
      
  get_framework_python:
    description: Get path to Python interpreter in shared venv
    parameters:
      - name: framework_name
        type: string
        required: true
    returns:
      type: string
      format: path
      description: Absolute path to venv Python executable
    raises:
      - RuntimeError: If venv doesn't exist or Python not executable
    side_effects: None (read-only)
    
  create_workspace_structure:
    description: Create run-specific directories in workspace
    parameters:
      - name: subdirs
        type: array
        items:
          type: string
        required: true
        description: List of directory names to create
    returns:
      type: object
      description: Map of subdir name to created Path object
    raises:
      - OSError: If directory creation fails
      - PermissionError: If insufficient permissions
    side_effects:
      - Creates directories in self.workspace_path
      - Creates parent directories as needed
      
  get_shared_framework_path:
    description: Get path to shared framework directory
    parameters:
      - name: framework_name
        type: string
        required: true
    returns:
      type: string
      format: path
      description: Absolute path to frameworks/<name>/
    raises:
      - RuntimeError: If framework directory doesn't exist
    side_effects: None (read-only)
```

### 1.3 Filesystem Contracts

**Output**: `docs/20251021-workspace-refactor/contracts/directory_structure.yaml`

```yaml
filesystem_layout:
  experiment_root:
    path_pattern: "<experiment_dir>/"
    description: Root directory for standalone experiment
    
    frameworks:
      path: "frameworks/"
      purpose: "Shared, read-only framework resources"
      lifecycle: "Created by setup.sh, never modified by runs"
      
      framework_dirs:
        baes:
          path: "frameworks/baes/"
          contents:
            - ".venv/"               # Shared Python virtual environment
            - "baes/"                # Framework source code
            - "requirements.txt"
            - "README.md"
          size: "~622MB (619MB .venv + 3MB source)"
          created_by: "setup.sh"
          
        chatdev:
          path: "frameworks/chatdev/"
          contents:
            - ".venv/"
            - "ChatDev/"
            - "requirements.txt"
          size: "~650MB estimated"
          created_by: "setup.sh"
          
        ghspec:
          path: "frameworks/ghspec/"
          contents:
            - "spec-kit/"            # Node.js project (no venv)
            - "package.json"
          size: "~50MB estimated"
          created_by: "setup.sh"
          
    runs:
      path: "runs/"
      purpose: "Per-run isolated workspaces with generated artifacts"
      
      run_structure:
        path_pattern: "runs/<framework>/<run_id>/"
        
        workspace:
          path: "workspace/"
          purpose: "Run-specific writable data"
          contents_baes:
            - "managed_system/"      # Generated application code
            - "database/"            # Context store and state
          contents_chatdev:
            - "WareHouse/"           # Generated project artifacts
          contents_ghspec:
            - "outputs/"             # Generated specifications
          size: "<1MB per run (only artifacts)"
          
        logs:
          - "run.log"                # Structured JSON logs
          - "metrics.json"           # Computed metrics
          
constraints:
  - name: "No framework copying to workspace"
    rule: "workspace/ MUST NOT contain framework source code"
    enforcement: "create_workspace_structure validates subdirs"
    
  - name: "Shared venv isolation"
    rule: "frameworks/<name>/.venv/ MUST be read-only during runs"
    enforcement: "File permissions, adapters only read"
    
  - name: "Run artifact isolation"
    rule: "Each run writes only to its own workspace/<run_id>/"
    enforcement: "workspace_path contains unique run_id"
```

### 1.4 Quickstart Guide

**Output**: `docs/20251021-workspace-refactor/quickstart.md`

**Content**: Step-by-step guide for developers using the new architecture:

```markdown
# Workspace Refactor Quickstart

## For Experiment Users

### Creating a New Experiment
```bash
# Generate experiment with new architecture
python scripts/new_experiment.py --name my-test --frameworks baes --runs 2

# Setup creates shared frameworks + venvs (one-time cost)
cd experiments/my-test
bash setup.sh

# Run experiments (instant startup, no venv creation)
bash run.sh
```

### Verifying Shared Resources
```bash
# Check shared venv exists (created once)
ls -lh frameworks/baes/.venv

# Check workspace has only artifacts (no framework copy)
ls -lh runs/baes/<run-id>/workspace/
# Should see: managed_system/, database/ only
```

## For Adapter Developers

### Using Shared Framework Resources

**Old Pattern** (❌ Deprecated):
```python
def start(self):
    self.framework_dir = Path(self.workspace_path) / "baes_framework"
    self.setup_framework_from_repo(...)  # Copies framework
    self._setup_virtual_environment()     # Creates venv
```

**New Pattern** (✅ Recommended):
```python
def start(self):
    # Reference shared framework (no copying)
    self.framework_dir = self.get_shared_framework_path('baes')
    
    # Use shared venv (already created)
    self.python_path = self.get_framework_python('baes')
    
    # Create only run-specific directories
    workspace_dirs = self.create_workspace_structure([
        'managed_system',
        'database'
    ])
    self.managed_system_dir = workspace_dirs['managed_system']
```

### Adding a New Framework Adapter

1. **Configure framework in experiment.yaml**:
```yaml
frameworks:
  myframework:
    repo_url: "https://github.com/org/repo"
    commit_hash: "abc123..."
    use_venv: true  # or false for Node.js/system deps
```

2. **Implement adapter.start()**:
```python
def start(self):
    # Get shared resources
    self.framework_dir = self.get_shared_framework_path('myframework')
    
    # Only if use_venv=true
    if self.config.get('use_venv'):
        self.python_path = self.get_framework_python('myframework')
    
    # Create workspace structure
    workspace_dirs = self.create_workspace_structure(['outputs'])
    self.outputs_dir = workspace_dirs['outputs']
```

3. **Update setup.sh** (automatic via template)
   - If `use_venv: true`, setup.sh will create .venv in frameworks/myframework/

## Troubleshooting

### Venv creation failed during setup
```bash
# Check Python version
python3 --version  # Must be 3.11+

# Check requirements.txt exists
cat frameworks/baes/requirements.txt

# Manually retry venv creation
python3 -m venv frameworks/baes/.venv
frameworks/baes/.venv/bin/pip install -r frameworks/baes/requirements.txt
```

### Framework not found error
```bash
# Ensure setup.sh was run
ls frameworks/  # Should list: baes, chatdev, ghspec

# Re-run setup if needed
bash setup.sh
```

### Workspace missing directories
- Check adapter's `create_workspace_structure()` call
- Ensure subdirs list matches framework requirements
- Verify workspace_path permissions
```
```

---

## Phase 2: Task Planning (OUT OF SCOPE)

**Note**: Phase 2 (detailed task breakdown) is handled by a separate command (`/speckit.tasks`) and is documented in `tasks.md`. This plan document covers Phase 0-1 only as per spec-kit workflow.

The task list has been captured in the project's todo list system and includes:
1. BaseAdapter method implementations (4 methods)
2. Adapter refactoring (3 adapters)
3. Template updates (setup.sh)
4. Configuration updates (experiment.yaml)
5. Testing and verification (2 validation tasks)

**Total**: 13 tasks across 5 source files

---

## Success Criteria

### Functional Requirements
- ✅ All 68 existing adapter tests pass
- ✅ New experiments use shared frameworks (no workspace copying)
- ✅ Venvs created once during setup.sh, reused by all runs
- ✅ Workspace contains only run-specific artifacts

### Performance Requirements
- ✅ Per-run disk usage: <1MB (down from 622MB)
- ✅ Run startup time: <1s (down from ~5min)
- ✅ Total experiment disk: ~1.25GB (down from ~7.5GB for 6-run experiment)

### Code Quality Requirements
- ✅ Remove ~150 lines of duplicate venv creation logic
- ✅ Centralize framework management in BaseAdapter
- ✅ Maintain backward compatibility (existing experiments work)
- ✅ Preserve scientific reproducibility (commit hash pinning)

---

## Risk Analysis

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Concurrent venv access causes corruption | Low | High | Research confirms read-only safety; add tests |
| ChatDev patches break with shared framework | Medium | Medium | Test patching during setup.sh; document strategy |
| Existing experiments fail with new structure | Low | High | Maintain backward compat; add deprecation path |
| Test suite requires path updates | Medium | Low | Run tests frequently; update fixtures as needed |
| setup.sh venv creation times out | Low | Medium | Implement progress indicators; allow retry |

---

## Next Steps

1. **Complete Phase 0**: Research all identified questions (venv safety, patching, directories)
   - Create `research.md` with findings
   - Make definitive decisions on open questions

2. **Complete Phase 1**: Finalize contracts and data model
   - Create `data-model.md` with directory structure entities
   - Create `contracts/` with method signatures
   - Create `quickstart.md` for developers

3. **Transition to Phase 2**: Generate detailed task breakdown
   - Run `/speckit.tasks` command (or manual creation)
   - Create `tasks.md` with implementation steps
   - Begin implementation following task order

4. **Implementation**: Execute the 13 tasks in dependency order
   - Start with BaseAdapter methods (foundation)
   - Update setup.sh template (infrastructure)
   - Refactor adapters (integration)
   - Verify tests and disk usage (validation)

---

## References

- **Design Document**: [SHARED_FRAMEWORK_VENV_DESIGN.md](./SHARED_FRAMEWORK_VENV_DESIGN.md)
- **Constitution**: `.specify/memory/constitution.md`
- **Current Implementation**: 
  - `src/adapters/base_adapter.py` (lines 164-277: setup_framework_from_repo)
  - `src/adapters/baes_adapter.py` (lines 101-162: _setup_virtual_environment)
  - `src/adapters/chatdev_adapter.py` (similar venv logic)
- **Test Suite**: `tests/unit/test_*_adapter*.py` (68 tests total)
- **Template**: `templates/setup.sh` (framework cloning logic)
- **Configuration**: `config/experiment.yaml` (framework definitions)
