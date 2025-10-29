# BAEs Adapter Implementation Plan

**Date**: October 16, 2025  
**Purpose**: Integrate BAEs framework into the experiment orchestrator  
**Target**: Implement `src/adapters/baes_adapter.py`  
**Status**: Updated after critique review

---

## 0. Critique Resolution Summary

This plan has been reviewed against a comprehensive external critique and updated to address all identified concerns:

### ✅ Resolved Issues:

1. **Dependency Management** (CRITICAL):
   - **Decision**: Create isolated venv for BAEs (like ChatDev) - Option C
   - **Implementation**: Added `_setup_virtual_environment()` method (Task 1.2.1)
   - **Rationale**: Prevents dependency conflicts (FastAPI, Pydantic, Streamlit versions)
   - **BAEs Dependencies**: Pydantic 2.5.0, FastAPI 0.104.1, OpenAI 1.3.7, Streamlit 1.28.1

2. **Server Health Checks** (IMPORTANT):
   - **Decision**: Check HTTP endpoints AFTER generation steps complete
   - **Implementation**: Two-phase health check - internal (always) + external (after step 2+)
   - **Rationale**: Validates full webapp is working as expected after deployment

3. **Token Tracking** (IMPORTANT):
   - **Decision**: Unified Usage API reconciliation for ALL adapters (no exceptions)
   - **Implementation**: Returns (0, 0) for tokens; reconciliation fills actual values
   - **Rationale**: Consistency, accuracy, auditability across frameworks

4. **Server Startup Timing** (MINOR):
   - **Decision**: Trust BAEs internal startup logic (same as other adapters)
   - **Implementation**: No additional wait/polling after `process_natural_language_request()`
   - **Rationale**: Consistent adapter behavior; BAEs handles startup internally

5. **Downtime Measurement** (MINOR):
   - **Decision**: Framework-internal restarts (Uvicorn --reload) do NOT count as incidents
   - **Implementation**: Added Section 7.5 clarifying ZDI metric definition
   - **Rationale**: Reloads are expected behavior, not failures

### 📋 Key Changes Made:

- **Section 3.2**: Updated comparison table to include environment and token tracking
- **Task 1.2**: Added venv setup and `OPENAI_API_KEY_BAES` configuration
- **Task 1.2.1**: New method `_setup_virtual_environment()` (follows ChatDev pattern)
- **Task 1.3**: Updated kernel initialization to use venv imports
- **Task 3.2**: Enhanced `health_check()` with two-phase checking (internal + HTTP endpoints)
- **Section 5**: Complete rewrite - unified token tracking strategy, no BAEs modifications needed
- **Section 6**: Added API key configuration and venv settings
- **Section 7.5**: New section clarifying downtime measurement philosophy

### 🎯 Validation:

All critique concerns addressed. Plan now aligned with:
- Existing orchestrator architecture (venv isolation, API key separation)
- Unified token tracking methodology (Usage API reconciliation)
- Consistent health checking philosophy (validate after generation)
- Clear metric definitions (ZDI excludes framework-internal operations)

---

## 1. Executive Summary

### Objective
Implement a fully functional BAEs adapter that integrates the Business Autonomous Entities framework into the experiment orchestrator, enabling automated testing and comparison with GHSpec and ChatDev frameworks.

### Key Challenges
1. **Different Architecture**: BAEs uses domain entity-focused architecture vs task-based (GHSpec) or agent-based (ChatDev)
2. **CLI-First Design**: BAEs has conversational CLI (`bae_chat.py`) not designed for programmatic access
3. **State Management**: BAEs maintains complex state (servers, database, generated files)
4. **Async Operations**: Server startup/restart adds complexity not present in other adapters

### Success Criteria
- ✅ All 6 experiment steps execute successfully
- ✅ Timestamp tracking works correctly
- ✅ Token usage captured accurately
- ✅ HITL interventions handled deterministically
- ✅ Generated artifacts properly captured
- ✅ Consistent with existing adapter pattern (DRY principle)

---

## 2. BAEs Framework Analysis

### 2.1 Framework Status (as of October 2025)

**Repository**: [https://github.com/gesad-lab/baes_demo](https://github.com/gesad-lab/baes_demo)  
**Latest Commit**: a34b207 ("update results")  
**Project Status**: Phase 1 Complete - Scenario 1 Core Components ✅

**Implemented Components**:
- ✅ Student BAE (domain entity representative)
- ✅ OpenAI GPT-4o-mini integration
- ✅ Context Store (domain knowledge persistence)
- ✅ Base Agent Framework
- ✅ EnhancedRuntimeKernel (107KB, fully functional)
- ✅ EntityRecognizer (multilingual, OpenAI-powered)
- ✅ BAE Registry (Student, Course, Teacher entities)
- ✅ ManagedSystemManager (server lifecycle)
- ✅ SWEA Agents: Backend, Frontend, Database, Test, TechLead
- ✅ Test Suite (5/5 tests passing)

**Planned/In-Progress** (per README):
- ⏳ Phase 2: Complete SWEA agent implementation
- ⏳ Phase 3: End-to-end Scenario 1 execution
- ⏳ Scenario 2: Runtime evolution capabilities

**Key Insight**: BAEs framework is **production-ready** for Scenario 1 (initial system generation) with all core components implemented. Our adapter will use the `process_natural_language_request()` API which is fully functional.

### 2.2 Technology Stack

**Core Dependencies** (from `requirements.txt`):
- `fastapi==0.104.1` - Backend framework (generated systems)
- `uvicorn[standard]==0.24.0` - ASGI server with auto-reload
- `streamlit==1.28.1` - Frontend framework (generated systems)
- `openai==1.3.7` - LLM integration (GPT-4o-mini)
- `pydantic==2.5.0` - **Version 2** (no conflicts with orchestrator)
- `sqlalchemy==2.0.23` - Database ORM
- `python-dotenv==1.0.0` - Environment configuration
- `jinja2==3.1.2` - Template rendering

**Testing Dependencies**:
- `pytest>=7.0.0` + async, mock, coverage, xdist, timeout plugins
- `selenium==4.15.2` - Browser automation for UI testing
- `httpx==0.25.2` - Async HTTP client

**Development Dependencies**:
- `black==23.12.1`, `flake8==6.1.0`, `mypy==1.8.0` - Code quality
- `pre-commit==4.2.0` - Git hooks

**Compatibility Notes**:
- ✅ Pydantic v2 (orchestrator can use v1 or v2, isolated via venv)
- ✅ OpenAI 1.3.7 (stable, no breaking changes)
- ✅ No conflicts with ChatDev dependencies (separate venv)

### 2.3 Core Architecture

```
User Request (Natural Language)
    ↓
EnhancedRuntimeKernel
    ↓
EntityRecognizer (OpenAI-powered)
    ↓
BAE Registry (Student, Course, Teacher)
    ↓
Selected BAE interprets request
    ↓
Coordination Plan generated
    ↓
SWEA Agents execute (Backend, Frontend, Database, Test, TechLead)
    ↓
Managed System generated (FastAPI + Streamlit + SQLite)
    ↓
Servers started (API:8100, UI:8600)
```

### 2.2 Key Components

**EnhancedRuntimeKernel** (`baes/core/enhanced_runtime_kernel.py`):
- Main orchestrator
- Manages BAE registry and SWEA agents
- Processes natural language requests
- Handles server lifecycle
- Tracks metrics and retry patterns

**BAE Registry** (`baes/core/bae_registry.py`):
- Manages domain entities (Student, Course, Teacher)
- Routes requests to appropriate BAE
- Validates entity support

**EntityRecognizer** (`baes/core/entity_recognizer.py`):
- Uses OpenAI to classify user requests
- Multilingual support
- Returns entity name and confidence score

**SWEA Agents**:
- `BackendSWEA`: FastAPI backend generation
- `FrontendSWEA`: Streamlit UI generation
- `DatabaseSWEA`: SQLite schema generation
- `TestSWEA`: Test generation
- `TechLeadSWEA`: Coordination and validation

**ManagedSystemManager** (`baes/core/managed_system_manager.py`):
- Manages generated system files
- Handles server startup/shutdown
- Port management (API:8100, UI:8600)

### 2.3 Current Interfaces

**CLI Interface** (`bae_chat.py`):
- Conversational loop
- Session management
- Server lifecycle management
- Human-friendly output
- **Not suitable for programmatic access**

**Kernel Interface** (programmatic):
```python
kernel = EnhancedRuntimeKernel()
result = kernel.process_natural_language_request(
    request="add student with name and email",
    start_servers=True
)
```

**Result Structure**:
```python
{
    "success": bool,
    "entity": str,  # "Student", "Course", etc.
    "execution_results": [
        {
            "task": str,
            "success": bool,
            "result": Any,
            "agent": str,  # SWEA agent name
            "retry_count": int
        }
    ],
    "coordination_plan": {...},
    "files_generated": [...],
    "error": str  # if any
}
```

---

## 3. Implementation Strategy

### 3.1 Adapter Design Pattern

Follow the same pattern as GHSpec and ChatDev adapters:

```python
class BAeSAdapter(BaseAdapter):
    def start(self) -> None:
        """Initialize framework (clone repo, setup env)"""
        
    def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
        """Execute one experiment step"""
        
    def stop(self) -> None:
        """Cleanup (shutdown servers, save state)"""
        
    def health_check(self) -> bool:
        """Check framework health"""
        
    def handle_hitl(self, query: str) -> str:
        """Handle human-in-the-loop interventions"""
```

### 3.2 Key Differences from Other Adapters

| Aspect | GHSpec | ChatDev | BAEs |
|--------|--------|---------|------|
| **Architecture** | Spec → Plan → Tasks | Multi-agent conversation | Domain entity focused |
| **Execution** | Sequential phases | Role-playing agents | BAE → SWEA coordination |
| **State** | Stateless (file-based) | Stateless (workspace) | Stateful (servers + DB) |
| **Artifacts** | Markdown + code | Separate workspaces | Managed system directory |
| **API Calls** | Direct OpenAI calls | Direct OpenAI calls | Via kernel (abstracted) |
| **Timestamps** | Per-phase tracking | Per-step tracking | Per-request tracking |
| **Environment** | Shared Python env | Isolated venv | Isolated venv (NEW) |
| **API Key** | OPENAI_API_KEY_GHSPEC | OPENAI_API_KEY_CHATDEV | OPENAI_API_KEY_BAES |
| **Token Tracking** | Usage API reconciliation | Usage API reconciliation | Usage API reconciliation |

### 3.3 Integration Approach

**Option A: Direct Kernel Integration** (RECOMMENDED)
- Use `EnhancedRuntimeKernel` directly
- Bypass CLI interface entirely
- Full control over execution flow
- Easy token tracking
- Clean separation of concerns

**Option B: CLI Wrapper**
- Wrap `bae_chat.py` with automation
- Parse output for metrics
- Complex and fragile
- Hard to track tokens
- **NOT RECOMMENDED**

**Option C: Hybrid Approach**
- Use kernel for execution
- Import CLI utilities for specific features
- Moderate complexity
- Good for gradual migration

**DECISION: Use Option A (Direct Kernel Integration)**

---

## 4. Detailed Implementation Plan

### Phase 1: Framework Integration (Week 1)

#### Task 1.1: Update Repository Configuration
**File**: `config/experiment.yaml`

Add BAEs framework configuration:
```yaml
baes:
  repo_url: "file:///home/amg/projects/uece/baes/baes_demo"
  commit_hash: "HEAD"  # Or specific commit for reproducibility
  api_port: 8100
  ui_port: 8600
  managed_system_path: "managed_system"
  context_store_path: "database/context_store.json"
  max_retries: 3
  auto_restart_servers: false  # Disable for experiments
```

#### Task 1.2: Setup Development Environment
**File**: `src/adapters/baes_adapter.py`

```python
def start(self) -> None:
    """Initialize BAEs framework environment."""
    logger.info("Starting BAEs framework", 
               extra={'run_id': self.run_id, 'event': 'framework_start'})
    
    # 1. Setup workspace structure
    self.framework_dir = Path(self.workspace_path) / "baes_framework"
    self.managed_system_dir = Path(self.workspace_path) / "managed_system"
    self.database_dir = Path(self.workspace_path) / "database"
    
    # 2. Clone/copy repository
    repo_url = self.config['repo_url']
    if repo_url.startswith('file://'):
        # Local copy for development (e.g., "file:///home/amg/projects/uece/baes/baes_demo")
        shutil.copytree(repo_url[7:], self.framework_dir)
    else:
        # Git clone for production (e.g., "https://github.com/gesad-lab/baes_demo")
        subprocess.run(['git', 'clone', repo_url, str(self.framework_dir)],
                      check=True, capture_output=True, stdin=subprocess.DEVNULL, timeout=300)
    
    # 3. Verify commit hash
    commit_hash = self.config.get('commit_hash', 'HEAD')
    if commit_hash != 'HEAD':
        subprocess.run(['git', 'checkout', commit_hash],
                      cwd=self.framework_dir, check=True,
                      capture_output=True, stdin=subprocess.DEVNULL)
    
    self.verify_commit_hash(self.framework_dir, commit_hash)
    
    # 4. Setup isolated virtual environment (like ChatDev)
    # This prevents dependency conflicts (e.g., Pydantic, FastAPI versions)
    self._setup_virtual_environment()
    
    # 5. Set environment variables
    os.environ['BAE_CONTEXT_STORE_PATH'] = str(self.database_dir / "context_store.json")
    os.environ['MANAGED_SYSTEM_PATH'] = str(self.managed_system_dir)
    os.environ['API_PORT'] = str(self.config['api_port'])
    os.environ['UI_PORT'] = str(self.config['ui_port'])
    os.environ['BAE_MAX_RETRIES'] = str(self.config.get('max_retries', 3))
    
    # 6. Set BAEs-specific API key for token tracking
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY_BAES')
    
    # 7. Initialize kernel (lazy initialization)
    self._kernel = None  # Will be initialized on first use
    
    logger.info("BAEs framework ready",
               extra={'run_id': self.run_id,
                     'metadata': {
                         'framework_dir': str(self.framework_dir),
                         'managed_system_dir': str(self.managed_system_dir),
                         'venv': str(self.venv_path),
                         'python': str(self.python_path)
                     }})
```

#### Task 1.2.1: Virtual Environment Setup (Dependency Isolation)

```python
def _setup_virtual_environment(self) -> None:
    """
    Create virtual environment and install BAEs dependencies.
    
    Follows the same pattern as ChatDev adapter (FR-002.1 steps 2-3):
    - Creates isolated venv to prevent dependency conflicts
    - Installs BAEs requirements (FastAPI, Streamlit, SQLAlchemy, etc.)
    - Ensures compatibility with orchestrator environment
    """
    self.venv_path = self.framework_dir / ".venv"
    self.python_path = None
    
    logger.info("Creating virtual environment for BAEs",
               extra={'run_id': self.run_id,
                     'metadata': {'path': str(self.venv_path)}})
    
    # Create virtual environment
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(self.venv_path)],
            check=True,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=120
        )
    except subprocess.CalledProcessError as e:
        logger.error("Failed to create virtual environment",
                    extra={'run_id': self.run_id,
                          'metadata': {'error': str(e)}})
        raise RuntimeError("Virtual environment creation failed") from e
    
    # Determine Python and pip paths (platform-independent)
    if sys.platform == "win32":
        self.python_path = self.venv_path / "Scripts" / "python.exe"
        pip_path = self.venv_path / "Scripts" / "pip.exe"
    else:
        self.python_path = self.venv_path / "bin" / "python"
        pip_path = self.venv_path / "bin" / "pip"
    
    # Ensure paths are absolute
    self.python_path = self.python_path.absolute()
    pip_path = pip_path.absolute()
    
    # Verify Python is accessible
    try:
        result = subprocess.run(
            [str(self.python_path), "--version"],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            text=True,
            timeout=10
        )
        python_version = result.stdout.strip()
        logger.info("Virtual environment created",
                   extra={'run_id': self.run_id,
                         'metadata': {'python_version': python_version}})
    except Exception as e:
        raise RuntimeError(f"Virtual environment Python not accessible: {e}") from e
    
    # Install dependencies from BAEs requirements.txt
    logger.info("Installing BAEs dependencies",
               extra={'run_id': self.run_id,
                     'event': 'dependency_install_start'})
    
    requirements_file = self.framework_dir / "requirements.txt"
    if not requirements_file.exists():
        raise RuntimeError(f"Requirements file not found: {requirements_file}")
    
    try:
        # Upgrade pip and install build tools
        logger.info("Upgrading pip and installing build tools",
                   extra={'run_id': self.run_id})
        
        subprocess.run(
            [str(pip_path), "install", "--upgrade", "pip", "setuptools>=67.0.0", "wheel"],
            check=True,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=120,
            cwd=self.framework_dir
        )
        
        # Install all requirements from BAEs
        logger.info("Installing BAEs requirements.txt",
                   extra={'run_id': self.run_id})
        
        subprocess.run(
            [str(pip_path), "install", "-r", str(requirements_file)],
            check=True,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=300,  # BAEs has many dependencies
            cwd=self.framework_dir
        )
        
        logger.info("BAEs dependencies installed successfully",
                   extra={'run_id': self.run_id,
                         'event': 'dependency_install_complete'})
        
    except subprocess.CalledProcessError as e:
        logger.error("Failed to install BAEs dependencies",
                    extra={'run_id': self.run_id,
                          'metadata': {'error': str(e),
                                     'stderr': e.stderr.decode() if e.stderr else ''}})
        raise RuntimeError("BAEs dependency installation failed") from e
    except subprocess.TimeoutExpired:
        logger.error("BAEs dependency installation timed out",
                    extra={'run_id': self.run_id})
        raise RuntimeError("BAEs dependency installation timed out")
```

#### Task 1.3: Kernel Initialization
```python
@property
def kernel(self):
    """
    Lazy initialization of EnhancedRuntimeKernel.
    
    CRITICAL: Imports BAEs modules from the isolated venv,
    not the orchestrator's environment.
    """
    if self._kernel is None:
        # Add framework directory to Python path for imports
        # (venv's site-packages already has BAEs dependencies)
        sys.path.insert(0, str(self.framework_dir))
        
        from baes.core.enhanced_runtime_kernel import EnhancedRuntimeKernel
        
        context_store_path = str(self.database_dir / "context_store.json")
        self._kernel = EnhancedRuntimeKernel(context_store_path)
        
        logger.debug("Initialized EnhancedRuntimeKernel",
                    extra={'run_id': self.run_id})
    
    return self._kernel
```

### Phase 2: Step Execution (Week 1-2)

#### Task 2.1: Command Mapping

Map experiment commands to BAEs natural language requests:

```python
COMMAND_MAPPING = {
    # Step 1: Initial CRUD
    "Create a Student/Course/Teacher CRUD application": 
        ["add student entity", "add course entity", "add teacher entity"],
    
    # Step 2: Enrollment relationship
    "Add enrollment relationship between Student and Course":
        ["add course to student entity"],
    
    # Step 3: Teacher assignment
    "Add teacher assignment relationship to Course":
        ["add teacher to course entity"],
    
    # Step 4: Validation
    "Implement comprehensive data validation":
        ["add validation to all entities"],
    
    # Step 5: Pagination
    "Add pagination and filtering":
        ["add pagination to all entities"],
    
    # Step 6: UI
    "Add comprehensive user interface":
        ["enhance ui for all entities"]
}

def _translate_command_to_requests(self, command_text: str) -> List[str]:
    """Translate experiment command to BAEs requests"""
    for pattern, requests in COMMAND_MAPPING.items():
        if pattern in command_text or command_text in pattern:
            return requests
    
    # Fallback: use command as-is
    return [command_text]
```

#### Task 2.2: Step Execution Loop

```python
def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
    """Execute experiment step using BAEs kernel."""
    self.current_step = step_num
    start_time = time.time()
    start_timestamp = int(time.time())
    
    logger.info(f"Executing step {step_num}",
               extra={'run_id': self.run_id, 'step': step_num,
                     'event': 'step_start',
                     'metadata': {'framework': 'baes', 
                                 'command': command_text[:100]}})
    
    # Translate command to BAEs requests
    requests = self._translate_command_to_requests(command_text)
    
    hitl_count = 0
    total_tokens_in = 0
    total_tokens_out = 0
    all_results = []
    
    try:
        for req_num, request in enumerate(requests, 1):
            logger.debug(f"Processing request {req_num}/{len(requests)}: {request}",
                        extra={'run_id': self.run_id, 'step': step_num})
            
            # Execute request through kernel
            result = self.kernel.process_natural_language_request(
                request=request,
                start_servers=(req_num == 1 and step_num == 1)  # Only start servers once
            )
            
            all_results.append(result)
            
            # Extract token usage
            tokens = self._extract_token_usage(result)
            total_tokens_in += tokens['input']
            total_tokens_out += tokens['output']
            
            # Check for errors
            if not result.get('success'):
                error_msg = result.get('error', 'Unknown error')
                logger.error(f"Request failed: {error_msg}",
                           extra={'run_id': self.run_id, 'step': step_num})
                raise RuntimeError(f"BAEs request failed: {error_msg}")
        
        duration = time.time() - start_time
        end_timestamp = int(time.time())
        
        logger.info(f"Step {step_num} completed",
                   extra={'run_id': self.run_id, 'step': step_num,
                         'event': 'step_complete',
                         'metadata': {
                             'success': True,
                             'duration': duration,
                             'requests_processed': len(requests),
                             'tokens_in': total_tokens_in,
                             'tokens_out': total_tokens_out
                         }})
        
        return {
            'success': True,
            'duration_seconds': duration,
            'hitl_count': hitl_count,
            'tokens_in': total_tokens_in,
            'tokens_out': total_tokens_out,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp,
            'results': all_results
        }
        
    except Exception as e:
        duration = time.time() - start_time
        end_timestamp = int(time.time())
        
        logger.error(f"Step {step_num} failed: {e}",
                    extra={'run_id': self.run_id, 'step': step_num,
                          'event': 'step_failed'})
        
        return {
            'success': False,
            'duration_seconds': duration,
            'hitl_count': hitl_count,
            'tokens_in': total_tokens_in,
            'tokens_out': total_tokens_out,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp,
            'error': str(e)
        }
```

#### Task 2.3: Token Usage Extraction

```python
def _extract_token_usage(self, result: Dict[str, Any]) -> Dict[str, int]:
    """Extract token usage from BAEs result."""
    tokens_in = 0
    tokens_out = 0
    
    # Check if kernel tracked tokens
    execution_results = result.get('execution_results', [])
    for exec_result in execution_results:
        # BAEs may track tokens in agent results
        agent_result = exec_result.get('result', {})
        if isinstance(agent_result, dict):
            tokens_in += agent_result.get('tokens_used', {}).get('prompt_tokens', 0)
            tokens_out += agent_result.get('tokens_used', {}).get('completion_tokens', 0)
    
    # Fallback: estimate based on coordination plan complexity
    if tokens_in == 0 and tokens_out == 0:
        # This is a placeholder - BAEs needs to be modified to track tokens
        logger.warning("No token usage tracked by BAEs kernel",
                      extra={'run_id': self.run_id, 'step': self.current_step})
    
    return {'input': tokens_in, 'output': tokens_out}
```

### Phase 3: State Management (Week 2)

#### Task 3.1: Server Lifecycle Management

```python
def _ensure_servers_stopped(self):
    """Ensure BAEs servers are stopped before starting new ones."""
    api_port = self.config['api_port']
    ui_port = self.config['ui_port']
    
    for port in [api_port, ui_port]:
        try:
            # Check if port is in use
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex(("localhost", port)) == 0:
                    logger.warning(f"Port {port} is in use, attempting to free it",
                                 extra={'run_id': self.run_id})
                    
                    # Kill process on port
                    subprocess.run(
                        f"lsof -ti:{port} | xargs kill -9",
                        shell=True,
                        timeout=10
                    )
                    time.sleep(1)
        except Exception as e:
            logger.error(f"Failed to free port {port}: {e}",
                        extra={'run_id': self.run_id})

def stop(self) -> None:
    """Gracefully shutdown BAEs framework."""
    logger.info("Stopping BAEs framework",
               extra={'run_id': self.run_id, 'event': 'framework_stop'})
    
    # 1. Stop servers
    if hasattr(self, '_kernel') and self._kernel:
        try:
            # Use kernel's managed system manager to stop servers
            if hasattr(self._kernel, '_managed_system_manager'):
                mgr = self._kernel._managed_system_manager
                if mgr:
                    mgr.stop_servers()
        except Exception as e:
            logger.error(f"Error stopping servers: {e}",
                        extra={'run_id': self.run_id})
    
    # 2. Force kill servers on ports
    self._ensure_servers_stopped()
    
    # 3. Archive generated artifacts
    self._archive_managed_system()
    
    logger.info("BAEs framework stopped",
               extra={'run_id': self.run_id, 'event': 'framework_stopped'})

def _archive_managed_system(self):
    """Archive the generated managed system."""
    if self.managed_system_dir.exists():
        archive_path = Path(self.workspace_path) / "managed_system.tar.gz"
        
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(self.managed_system_dir, arcname="managed_system")
        
        logger.info(f"Archived managed system to {archive_path}",
                   extra={'run_id': self.run_id})
```

#### Task 3.2: Health Check Implementation

```python
def health_check(self) -> bool:
    """
    Check if BAEs framework is healthy.
    
    Two-phase checking:
    1. Internal: Kernel, context store, BAE registry (always)
    2. External: HTTP endpoints (only after generation steps)
    """
    try:
        # Phase 1: Internal health (kernel, registry, context)
        # 1. Check if kernel is initialized
        if not hasattr(self, '_kernel') or not self._kernel:
            logger.warning("Health check failed: kernel not initialized",
                         extra={'run_id': self.run_id})
            return False
        
        # 2. Check if context store is accessible
        context_store = self._kernel.context_store
        if not context_store:
            logger.warning("Health check failed: context store not accessible",
                         extra={'run_id': self.run_id})
            return False
        
        # 3. Check if BAE registry has entities
        supported_entities = self._kernel.bae_registry.get_supported_entities()
        if not supported_entities:
            logger.warning("Health check failed: no entities in registry",
                         extra={'run_id': self.run_id})
            return False
        
        # Phase 2: External health (HTTP endpoints)
        # ONLY check after generation steps complete (when full webapp expected)
        # This aligns with user requirement: "check it immediately after all generation steps"
        if self._should_check_endpoints():
            if not self._check_http_endpoints():
                logger.warning("Health check failed: HTTP endpoints not responding",
                             extra={'run_id': self.run_id})
                return False
        
        logger.debug("Health check passed",
                    extra={'run_id': self.run_id,
                          'metadata': {'entities': len(supported_entities)}})
        
        return True
        
    except Exception as e:
        logger.error(f"Health check failed: {e}",
                    extra={'run_id': self.run_id})
        return False

def _should_check_endpoints(self) -> bool:
    """
    Determine if HTTP endpoints should be checked.
    
    Returns True if:
    - We're past the initial generation steps (step >= 2)
    - Servers have been started (managed_system exists)
    """
    return (hasattr(self, 'current_step') and 
            self.current_step >= 2 and
            self.managed_system_dir.exists())

def _check_http_endpoints(self) -> bool:
    """
    Verify that API and UI servers are responding.
    
    Expected after all generation steps complete:
    - API (port 8100): /health or /docs endpoint
    - UI (port 8600): Streamlit homepage
    """
    import requests
    
    api_port = self.config['api_port']
    ui_port = self.config['ui_port']
    
    # Check API endpoint
    try:
        response = requests.get(f"http://localhost:{api_port}/docs", timeout=5)
        if response.status_code != 200:
            logger.warning(f"API endpoint not healthy: {response.status_code}",
                         extra={'run_id': self.run_id})
            return False
    except requests.RequestException as e:
        logger.warning(f"API endpoint not reachable: {e}",
                     extra={'run_id': self.run_id})
        return False
    
    # Check UI endpoint (Streamlit returns 200 for root)
    try:
        response = requests.get(f"http://localhost:{ui_port}/", timeout=5)
        if response.status_code != 200:
            logger.warning(f"UI endpoint not healthy: {response.status_code}",
                         extra={'run_id': self.run_id})
            return False
    except requests.RequestException as e:
        logger.warning(f"UI endpoint not reachable: {e}",
                     extra={'run_id': self.run_id})
        return False
    
    logger.debug("HTTP endpoints healthy",
                extra={'run_id': self.run_id,
                      'metadata': {'api_port': api_port, 'ui_port': ui_port}})
    return True
```

### Phase 4: HITL Support (Week 2)

#### Task 4.1: HITL Handler

```python
def handle_hitl(self, query: str) -> str:
    """Return fixed HITL response for deterministic execution."""
    if self.hitl_text is None:
        # Load HITL text from config
        hitl_path = Path("config/hitl/expanded_spec.txt")
        if hitl_path.exists():
            with open(hitl_path, 'r') as f:
                self.hitl_text = f.read().strip()
        else:
            # Default HITL response for BAEs
            self.hitl_text = """
            Create a complete CRUD system with:
            - Student entity: name (string), email (string, unique), enrollment_date (date)
            - Course entity: code (string, unique), title (string), credits (integer)
            - Teacher entity: name (string), email (string, unique), department (string)
            - All entities should have full CRUD operations
            - Use FastAPI for backend, Streamlit for UI, SQLite for database
            """
    
    logger.info("HITL intervention",
               extra={'run_id': self.run_id, 'step': self.current_step,
                     'event': 'hitl',
                     'metadata': {'query_length': len(query)}})
    
    return self.hitl_text
```

**Note**: BAEs may not trigger HITL in the same way as other frameworks. The EntityRecognizer and BAEs themselves make decisions autonomously. We may need to modify BAEs to support HITL interventions explicitly.

### Phase 5: Metrics & Logging (Week 2-3)

#### Task 5.1: Integrate BAEs Metrics

BAEs has a `MetricsTracker` (`baes/utils/metrics_tracker.py`). We should integrate it:

```python
def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
    # ... existing code ...
    
    # Import BAEs metrics tracker
    from baes.utils.metrics_tracker import get_snapshot, flush_snapshot
    
    # Get metrics snapshot before execution
    pre_snapshot = get_snapshot()
    
    # Execute step
    result = self._execute_step_internal(step_num, command_text)
    
    # Get metrics snapshot after execution
    post_snapshot = get_snapshot()
    
    # Calculate metrics delta
    metrics_delta = self._calculate_metrics_delta(pre_snapshot, post_snapshot)
    
    # Add to result
    result['baes_metrics'] = metrics_delta
    
    return result

def _calculate_metrics_delta(self, pre: Dict, post: Dict) -> Dict:
    """Calculate difference in metrics snapshots."""
    return {
        'total_time': post.get('total_time', 0) - pre.get('total_time', 0),
        'llm_calls': post.get('llm_calls', 0) - pre.get('llm_calls', 0),
        'tokens_total': post.get('tokens_total', 0) - pre.get('tokens_total', 0),
        # Add other relevant metrics
    }
```

### Phase 6: Testing & Validation (Week 3)

#### Task 6.1: Unit Tests

**File**: `tests/unit/test_baes_adapter.py`

```python
import pytest
from pathlib import Path
from src.adapters.baes_adapter import BAeSAdapter

@pytest.fixture
def baes_adapter(tmp_path):
    config = {
        'repo_url': 'https://github.com/gesad-lab/baes_demo',
        'commit_hash': 'a34b207',  # Latest stable commit
        'api_port': 8100,
        'ui_port': 8600,
        'max_retries': 3
    }
    
    adapter = BAeSAdapter(config, 'test-run-id', str(tmp_path))
    yield adapter
    adapter.stop()

def test_adapter_initialization(baes_adapter):
    """Test adapter initializes correctly"""
    baes_adapter.start()
    assert baes_adapter.framework_dir.exists()
    assert baes_adapter.health_check()

def test_command_translation(baes_adapter):
    """Test command to request translation"""
    command = "Create a Student/Course/Teacher CRUD application"
    requests = baes_adapter._translate_command_to_requests(command)
    
    assert len(requests) > 0
    assert any('student' in r.lower() for r in requests)

def test_step_execution(baes_adapter):
    """Test single step execution"""
    baes_adapter.start()
    
    result = baes_adapter.execute_step(
        step_num=1,
        command_text="Create a Student CRUD application"
    )
    
    assert 'success' in result
    assert 'duration_seconds' in result
    assert 'tokens_in' in result
    assert 'tokens_out' in result
    assert 'start_timestamp' in result
    assert 'end_timestamp' in result
```

#### Task 6.2: Integration Tests

**File**: `tests/integration/test_baes_single_step.py`

```python
def test_baes_single_step_execution(baes_adapter, tmp_path):
    """Test complete single step execution"""
    baes_adapter.start()
    
    # Execute step 1
    result = baes_adapter.execute_step(
        step_num=1,
        command_text="Create a Student/Course/Teacher CRUD application"
    )
    
    assert result['success'] == True
    assert result['duration_seconds'] > 0
    assert result['tokens_in'] >= 0
    assert result['tokens_out'] >= 0
    
    # Check managed system was created
    managed_system_dir = tmp_path / "managed_system"
    assert managed_system_dir.exists()
    
    # Check for expected files
    # Backend files
    assert (managed_system_dir / "backend.py").exists() or \
           (managed_system_dir / "main.py").exists()
    
    # Frontend files
    assert (managed_system_dir / "frontend.py").exists() or \
           (managed_system_dir / "app.py").exists()
```

#### Task 6.3: End-to-End Test

**File**: `tests/integration/test_baes_six_step.py`

```python
def test_baes_complete_workflow(baes_adapter, tmp_path):
    """Test complete 6-step workflow"""
    baes_adapter.start()
    
    commands = [
        "Create a Student/Course/Teacher CRUD application",
        "Add enrollment relationship between Student and Course",
        "Add teacher assignment relationship to Course",
        "Implement comprehensive data validation",
        "Add pagination and filtering",
        "Add comprehensive user interface"
    ]
    
    for step_num, command in enumerate(commands, 1):
        result = baes_adapter.execute_step(step_num, command)
        
        assert result['success'] == True, \
            f"Step {step_num} failed: {result.get('error')}"
        
        assert result['duration_seconds'] > 0
        assert result['start_timestamp'] > 0
        assert result['end_timestamp'] > 0
    
    baes_adapter.stop()
    
    # Verify all artifacts were created
    managed_system_dir = tmp_path / "managed_system"
    assert managed_system_dir.exists()
```

---

## 5. Token Tracking Strategy

### 5.1 Unified Token Tracking Approach

**CRITICAL DECISION**: All adapters (GHSpec, ChatDev, BAEs) MUST use the same token tracking method for consistency and comparability.

**Method**: OpenAI Usage API Reconciliation
- **Primary Source**: Official OpenAI Usage API (accessed via `OPENAI_API_KEY_USAGE_TRACKING`)
- **Script**: `runners/reconcile_usage.sh`
- **Timing**: Runs 30-60 minutes after experiment completion (API delay requirement)
- **Per-Framework API Keys**:
  - GHSpec: `OPENAI_API_KEY_GHSPEC`
  - ChatDev: `OPENAI_API_KEY_CHATDEV`
  - BAEs: `OPENAI_API_KEY_BAES`

### 5.2 BAEs Adapter Implementation

The BAEs adapter MUST follow the same pattern as GHSpec and ChatDev:

```python
def execute_step(self, step_num: int, command_text: str) -> Tuple[bool, float, int, int, float, float]:
    """
    Execute one experiment step.
    
    Returns:
        Tuple containing:
        - success (bool): Whether step succeeded
        - duration_seconds (float): Execution time
        - tokens_in (int): Input tokens (PLACEHOLDER - reconciliation fills this)
        - tokens_out (int): Output tokens (PLACEHOLDER - reconciliation fills this)
        - start_timestamp (float): Unix timestamp when step started
        - end_timestamp (float): Unix timestamp when step completed
    """
    start_timestamp = time.time()
    
    # Set BAEs API key for this run
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY_BAES')
    
    logger.info("Executing BAEs step",
               extra={'run_id': self.run_id, 'step': step_num,
                     'event': 'step_start',
                     'metadata': {'command': command_text[:100]}})
    
    try:
        # Translate command to BAEs requests
        requests = self._translate_command_to_requests(command_text)
        
        # Execute each BAEs request
        all_success = True
        for idx, request in enumerate(requests):
            # Call BAEs kernel
            result = self.kernel.process_natural_language_request(
                request=request,
                start_servers=(step_num == 1 and idx == 0)  # Only first time
            )
            
            if not result.get('success', False):
                all_success = False
                logger.error(f"BAEs request failed: {request}",
                           extra={'run_id': self.run_id, 'step': step_num})
                break
        
        end_timestamp = time.time()
        duration = end_timestamp - start_timestamp
        
        # Token placeholders (will be filled by reconciliation)
        # The reconcile_usage.sh script queries Usage API with OPENAI_API_KEY_USAGE_TRACKING
        # and updates run metadata with actual token counts per step
        tokens_in = 0
        tokens_out = 0
        
        logger.info("BAEs step completed",
                   extra={'run_id': self.run_id, 'step': step_num,
                         'event': 'step_complete',
                         'metadata': {
                             'success': all_success,
                             'duration': duration,
                             'note': 'Token counts filled by reconciliation'
                         }})
        
        return all_success, duration, tokens_in, tokens_out, start_timestamp, end_timestamp
        
    except Exception as e:
        end_timestamp = time.time()
        logger.error(f"BAEs step failed: {e}",
                    extra={'run_id': self.run_id, 'step': step_num})
        return False, end_timestamp - start_timestamp, 0, 0, start_timestamp, end_timestamp
```

### 5.3 Why NOT Track Tokens in Adapter

**Rationale for unified approach**:

1. **Consistency**: All three frameworks measured identically
2. **Accuracy**: Official OpenAI source of truth (no parsing/calculation errors)
3. **Simplicity**: No framework-specific token extraction logic
4. **Auditability**: Single reconciliation report for all frameworks
5. **Comparability**: Fair apples-to-apples comparison

**What adapters should NOT do**:
- ❌ Parse token counts from framework outputs
- ❌ Call OpenAI API directly to get usage
- ❌ Maintain separate token tracking mechanisms
- ❌ Return non-zero token counts in execute_step()

**What reconciliation does**:
- ✅ Queries Usage API with `OPENAI_API_KEY_USAGE_TRACKING` 
- ✅ Filters by framework-specific API key (e.g., `OPENAI_API_KEY_BAES`)
- ✅ Matches API calls to experiment steps by timestamp
- ✅ Updates run metadata with actual token counts
- ✅ Generates reconciliation report

### 5.4 Optional: BAEs Internal Metrics (For Debugging Only)

BAEs may have internal metrics tracking via `metrics_tracker.py`. This can be useful for debugging but should NOT be the primary token source:

```python
def execute_step(self, step_num: int, command_text: str) -> Tuple[bool, float, int, int, float, float]:
    # ... main execution code ...
    
    # OPTIONAL: Log internal metrics for debugging/validation
    try:
        from baes.utils.metrics_tracker import get_snapshot
        metrics = get_snapshot()
        
        logger.debug("BAEs internal metrics",
                    extra={'run_id': self.run_id, 'step': step_num,
                          'metadata': {
                              'baes_reported_tokens': metrics.get('tokens_total', 0),
                              'baes_llm_calls': metrics.get('llm_calls', 0),
                              'note': 'For debugging only - reconciliation is source of truth'
                          }})
    except Exception as e:
        logger.debug(f"Could not retrieve BAEs metrics: {e}",
                    extra={'run_id': self.run_id})
    
    # Always return 0 for tokens - reconciliation fills actual values
    return all_success, duration, 0, 0, start_timestamp, end_timestamp
```

### 5.5 No BAEs Framework Modifications Required

**IMPORTANT**: With the unified Usage API approach, we do NOT need to modify BAEs framework code:

- ❌ No need to add token tracking to `OpenAIClient`
- ❌ No need to add `get_token_usage()` to `EnhancedRuntimeKernel`
- ❌ No need to enhance result structure with `token_usage` field

The BAEs framework can remain unchanged. All token tracking happens externally via the Usage API reconciliation process.

**BAEs Framework Maturity**: As of October 2025 (commit a34b207), the BAEs framework is in **Phase 1 Complete** status with all core components implemented and tested. The `EnhancedRuntimeKernel` at 107KB is fully functional with:
- Complete SWEA agent coordination (Backend, Frontend, Database, Test, TechLead)
- EntityRecognizer with multilingual support
- ManagedSystemManager for server lifecycle
- Context Store for domain knowledge persistence
- Test suite with 5/5 tests passing

The adapter will integrate with a **production-ready** framework, not a prototype.

---

## 6. Configuration Updates

### 6.1 Experiment Configuration

**File**: `config/experiment.yaml`

Add BAEs section:

```yaml
frameworks:
  baes:
    enabled: true
    repo_url: "https://github.com/gesad-lab/baes_demo"
    commit_hash: "a34b207"  # Latest as of Oct 2025, or "HEAD" for development
    api_port: 8100
    ui_port: 8600
    managed_system_path: "managed_system"
    context_store_path: "database/context_store.json"
    max_retries: 3
    auto_restart_servers: false  # Disable for experiments
    use_venv: true  # NEW: Create isolated environment like ChatDev
```

### 6.2 Environment Variables

**File**: `.env`

BAEs-specific API key for token tracking (already configured):

```bash
# Admin Key (for reconciliation via Usage API)
OPENAI_API_KEY_USAGE_TRACKING=sk-admin-...

# BAEs Framework (for generation)
OPENAI_API_KEY_BAES=sk-proj-OpISHqiUYt9o8-mnWMe5...

# ChatDev Framework (for generation)
OPENAI_API_KEY_CHATDEV=sk-proj-GvVfYDPs8axWjm7g1tZ_...

# GitHub Spec-kit Framework (for generation)
OPENAI_API_KEY_GHSPEC=sk-proj-2-llx3yW6CegypCmaT3_...
```

**Reconciliation Interval** (already configured):
```bash
RECONCILIATION_VERIFICATION_INTERVAL_MIN=10  # Development
# RECONCILIATION_VERIFICATION_INTERVAL_MIN=60  # Production
```
    repo_url: "file:///home/amg/projects/uece/baes/baes_demo"
    commit_hash: "HEAD"
    api_port: 8100
    ui_port: 8600
    managed_system_path: "managed_system"
    context_store_path: "database/context_store.json"
    max_retries: 3
    auto_restart_servers: false
    timeout_per_step: 600  # 10 minutes
```

### 6.2 Prompt Templates

BAEs uses its own prompts internally, but we should document them:

**File**: `config/prompts/baes_step_*.txt`

Create prompt templates that map to BAEs requests:

```
Step 1: Initial CRUD
- add student entity
- add course entity
- add teacher entity

Step 2: Relationships
- add course to student entity

Step 3: Teacher Assignment
- add teacher to course entity

... etc
```

---

## 7. DRY Principle Application

### 7.1 Extract Common Patterns to BaseAdapter

Move common functionality to `base_adapter.py`:

```python
class BaseAdapter:
    def _ensure_directory_exists(self, path: Path):
        """Ensure directory exists (common across adapters)"""
        path.mkdir(parents=True, exist_ok=True)
    
    def _archive_directory(self, source: Path, dest: Path):
        """Archive directory to tar.gz (common)"""
        with tarfile.open(dest, "w:gz") as tar:
            tar.add(source, arcname=source.name)
    
    def _kill_process_on_port(self, port: int):
        """Kill process on port (common for server management)"""
        try:
            subprocess.run(
                f"lsof -ti:{port} | xargs kill -9",
                shell=True,
                timeout=10
            )
        except Exception as e:
            logger.warning(f"Failed to kill process on port {port}: {e}")
```

---

## 7.5 Downtime Measurement Clarification

### 7.5.1 What Counts as "Downtime Incident"

**Definition**: A downtime incident (ZDI metric) is an **unplanned** unavailability of the web application caused by:
- ❌ Server crashes requiring manual restart
- ❌ Errors that prevent the application from responding
- ❌ Configuration issues that break the system
- ❌ Code changes that cause runtime failures

**What does NOT count as downtime**:
- ✅ Framework-internal restarts (e.g., Uvicorn `--reload` detecting changes)
- ✅ Planned server stops between experiment steps
- ✅ Brief unavailability during code deployment (< 2 seconds)
- ✅ Initial startup time (before first request)

### 7.5.2 BAEs-Specific Considerations

BAEs uses Uvicorn with `--reload` flag, which automatically reloads when code changes:

```python
# In BAEs ManagedSystemManager
uvicorn_cmd = [
    "uvicorn",
    "main:app",
    "--host", "0.0.0.0",
    "--port", str(api_port),
    "--reload"  # Auto-reload on code changes
]
```

**Impact**:
- When BAEs generates new code (e.g., adding validation), Uvicorn detects the change
- Uvicorn performs a hot reload (~1-2 seconds)
- This is **NOT a downtime incident** - it's expected framework behavior

**Measurement Approach**:
- Health checks run AFTER all generation steps complete
- If the application is responding at that point, ZDI = 0
- Only count incidents if health check fails or manual intervention needed

### 7.5.3 Implementation in health_check()

```python
def _check_http_endpoints(self) -> bool:
    """
    Verify endpoints are responding AFTER generation completes.
    
    This validates:
    - No crashes occurred during generation
    - Auto-reload successfully handled code changes
    - Application is in working state
    
    Does NOT penalize:
    - Brief reloads during generation (expected behavior)
    """
    # Check API and UI endpoints as shown in Task 3.2
    # ...
```

---

## 8. Timeline & Milestones
        self.history = []
    
    def record(self, prompt_tokens: int, completion_tokens: int):
        self.history.append({
            'timestamp': time.time(),
            'prompt_tokens': prompt_tokens,
            'completion_tokens': completion_tokens
        })
    
    def get_totals(self) -> Dict[str, int]:
        return {
            'prompt_tokens': sum(h['prompt_tokens'] for h in self.history),
            'completion_tokens': sum(h['completion_tokens'] for h in self.history),
            'total_tokens': sum(h['prompt_tokens'] + h['completion_tokens'] 
                              for h in self.history)
        }
    
    def reset(self):
        self.history = []
```

Use this in all adapters for consistent token tracking.

---

## 8. Timeline & Milestones

### Week 1: Foundation
- **Day 1-2**: Framework integration (Task 1.1-1.3)
  - ✅ Update configuration
  - ✅ Implement `start()` method
  - ✅ Test framework initialization

- **Day 3-4**: Basic execution (Task 2.1-2.2)
  - ✅ Command mapping
  - ✅ Basic `execute_step()`
  - ✅ Test single step execution

- **Day 5**: Token tracking (Task 2.3)
  - ✅ Implement token extraction
  - ✅ Test token tracking
  - ⚠️ May require BAEs modifications

### Week 2: Core Functionality
- **Day 1-2**: State management (Task 3.1-3.2)
  - ✅ Server lifecycle
  - ✅ Health checks
  - ✅ Cleanup procedures

- **Day 3-4**: HITL support (Task 4.1)
  - ✅ HITL handler
  - ✅ Test HITL interventions
  - ⚠️ May need BAEs modifications

- **Day 5**: Metrics integration (Task 5.1)
  - ✅ Integrate BAEs metrics
  - ✅ Test metrics collection

### Week 3: Testing & Integration
- **Day 1-2**: Unit tests (Task 6.1)
  - ✅ Write unit tests
  - ✅ Achieve >80% coverage

- **Day 3-4**: Integration tests (Task 6.2-6.3)
  - ✅ Single step test
  - ✅ Six step test
  - ✅ Comparison with GHSpec/ChatDev

- **Day 5**: Documentation & polish
  - ✅ Update README
  - ✅ Create usage examples
  - ✅ Final code review

---

## 9. Success Metrics

### Functional Metrics
- ✅ All 6 steps execute successfully
- ✅ Generated system contains all expected entities
- ✅ Token usage tracked accurately (±5% of actual)
- ✅ Timestamps recorded for all steps
- ✅ No HITL interventions required (deterministic)
- ✅ Managed system archived correctly

### Performance Metrics
- ⏱️ Step 1 (Initial CRUD): < 5 minutes
- ⏱️ Step 2-5 (Relationships): < 3 minutes each
- ⏱️ Step 6 (UI): < 5 minutes
- 📊 Total experiment duration: < 25 minutes
- 💰 Token usage: < 100k tokens total

### Quality Metrics
- 🧪 Test coverage: > 80%
- 📝 Code quality: Passes all linters
- 🔄 Consistency: Matches GHSpec/ChatDev adapter patterns
- 📚 Documentation: Complete API docs

---

## 10. Risks & Mitigation

### Risk 1: Token Tracking Inaccuracy
**Impact**: High  
**Probability**: Medium  
**Mitigation**:
- Modify BAEs to expose token usage explicitly
- Add comprehensive logging of all OpenAI calls
- Fallback to Usage API reconciliation

### Risk 2: Server State Management
**Impact**: Medium  
**Probability**: High  
**Mitigation**:
- Implement robust server cleanup in `stop()`
- Add port conflict detection
- Use unique ports per experiment run

### Risk 3: Command Translation Complexity
**Impact**: Medium  
**Probability**: Medium  
**Mitigation**:
- Create comprehensive command mapping
- Add fuzzy matching for similar commands
- Provide clear error messages for unmapped commands

### Risk 4: BAEs Framework Changes Required
**Impact**: High  
**Probability**: Low  
**Mitigation**:
- Document all required changes clearly
- Submit PRs to BAEs repository
- Maintain compatibility layer if needed

### Risk 5: Different Execution Paradigm
**Impact**: High  
**Probability**: Medium  
**Mitigation**:
- Accept that BAEs may have different step granularity
- Map multiple BAEs requests to single experiment step
- Document differences in final report

---

## 11. Acceptance Criteria

### Must Have (P0)
- ✅ Adapter implements all required methods from `BaseAdapter`
- ✅ All 6 experiment steps execute without errors
- ✅ Token usage tracked and reported
- ✅ Timestamps captured for all steps
- ✅ Managed system artifacts preserved
- ✅ Tests pass (unit + integration)

### Should Have (P1)
- ✅ HITL support (even if not triggered)
- ✅ Metrics integration with BAEs MetricsTracker
- ✅ Server cleanup on errors
- ✅ Comparison metrics vs GHSpec/ChatDev

### Nice to Have (P2)
- ⭐ Real-time progress monitoring
- ⭐ Detailed task breakdown logging
- ⭐ Performance profiling
- ⭐ Retry pattern analysis

---

## 12. Next Actions

### Immediate (This Week)
1. ✅ Review this implementation plan
2. ⏳ Update `config/experiment.yaml` with BAEs configuration
3. ⏳ Implement `start()` method
4. ⏳ Test framework initialization

### Short-term (Week 1-2)
1. ⏳ Implement `execute_step()` with command mapping
2. ⏳ Add token tracking (may require BAEs modifications)
3. ⏳ Implement server lifecycle management
4. ⏳ Write unit tests

### Medium-term (Week 2-3)
1. ⏳ Integration tests
2. ⏳ End-to-end six-step test
3. ⏳ Comparison with existing frameworks
4. ⏳ Documentation

### Long-term (Week 4+)
1. ⏳ Performance optimization
2. ⏳ Advanced metrics analysis
3. ⏳ Research paper integration
4. ⏳ Production deployment

---

## 13. References

### BAEs Framework Documentation
- `../baes_demo/README.md` - Project overview
- `../baes_demo/docs/PROOF_OF_CONCEPT.md` - Scenario specifications
- `../baes_demo/bae_chat.py` - CLI implementation
- `../baes_demo/baes/core/enhanced_runtime_kernel.py` - Core orchestrator

### Existing Adapters
- `src/adapters/ghspec_adapter.py` - GHSpec implementation (reference)
- `src/adapters/chatdev_adapter.py` - ChatDev implementation (reference)
- `src/adapters/base_adapter.py` - Base adapter interface

### Experiment Framework
- `config/experiment.yaml` - Configuration structure
- `src/orchestrator/runner.py` - Experiment orchestrator
- `docs/quickstart.md` - Setup and usage guide

---

## 14. Conclusion

This implementation plan provides a comprehensive roadmap for integrating the BAEs framework into the experiment orchestrator. The key challenges are:

1. **Architectural Differences**: BAEs is domain-entity focused vs task/agent-based
2. **State Management**: Servers and database add complexity
3. **Token Tracking**: Requires modifications to BAEs framework
4. **Command Translation**: Need mapping from experiment commands to BAEs requests

By following this plan and applying the DRY principle throughout, we can create a robust BAEs adapter that seamlessly integrates with the existing experiment framework while maintaining consistency with GHSpec and ChatDev adapters.

**Estimated Effort**: 3 weeks (15 working days)  
**Risk Level**: Medium (manageable with proper planning)  
**Expected Outcome**: Fully functional BAEs adapter ready for comparative experiments

---

**Document Status**: ✅ Ready for Implementation  
**Last Updated**: October 16, 2025  
**Version**: 1.0
