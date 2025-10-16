# BAEs Adapter Implementation Plan

**Date**: October 16, 2025  
**Purpose**: Integrate BAEs framework into the experiment orchestrator  
**Target**: Implement `src/adapters/baes_adapter.py`

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

### 2.1 Core Architecture

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
        # Local copy for development
        shutil.copytree(repo_url[7:], self.framework_dir)
    else:
        # Git clone for production
        subprocess.run(['git', 'clone', repo_url, str(self.framework_dir)],
                      check=True, timeout=300)
    
    # 3. Verify commit hash
    commit_hash = self.config.get('commit_hash', 'HEAD')
    if commit_hash != 'HEAD':
        subprocess.run(['git', 'checkout', commit_hash],
                      cwd=self.framework_dir, check=True)
    
    self.verify_commit_hash(self.framework_dir, commit_hash)
    
    # 4. Setup Python environment
    # Add framework to Python path
    sys.path.insert(0, str(self.framework_dir))
    
    # 5. Set environment variables
    os.environ['BAE_CONTEXT_STORE_PATH'] = str(self.database_dir / "context_store.json")
    os.environ['MANAGED_SYSTEM_PATH'] = str(self.managed_system_dir)
    os.environ['API_PORT'] = str(self.config['api_port'])
    os.environ['UI_PORT'] = str(self.config['ui_port'])
    os.environ['BAE_MAX_RETRIES'] = str(self.config.get('max_retries', 3))
    
    # 6. Initialize kernel (lazy initialization)
    self._kernel = None  # Will be initialized on first use
    
    logger.info("BAEs framework ready",
               extra={'run_id': self.run_id,
                     'metadata': {
                         'framework_dir': str(self.framework_dir),
                         'managed_system_dir': str(self.managed_system_dir)
                     }})
```

#### Task 1.3: Kernel Initialization
```python
@property
def kernel(self):
    """Lazy initialization of EnhancedRuntimeKernel"""
    if self._kernel is None:
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
    """Check if BAEs framework is healthy."""
    try:
        # 1. Check if kernel is initialized
        if not hasattr(self, '_kernel') or not self._kernel:
            return False
        
        # 2. Check if context store is accessible
        context_store = self._kernel.context_store
        if not context_store:
            return False
        
        # 3. Check if BAE registry has entities
        supported_entities = self._kernel.bae_registry.get_supported_entities()
        if not supported_entities:
            return False
        
        # 4. Optionally check servers (only if they should be running)
        # We skip this for experiments as servers may not always be running
        
        logger.debug("Health check passed",
                    extra={'run_id': self.run_id,
                          'metadata': {'entities': len(supported_entities)}})
        
        return True
        
    except Exception as e:
        logger.error(f"Health check failed: {e}",
                    extra={'run_id': self.run_id})
        return False
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
        'repo_url': 'file:///home/amg/projects/uece/baes/baes_demo',
        'commit_hash': 'HEAD',
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

## 5. Required BAEs Framework Modifications

### 5.1 Token Tracking Enhancement

**File**: `baes/llm/openai_client.py` (or wherever OpenAI calls are made)

```python
class OpenAIClient:
    def __init__(self):
        self.token_usage_history = []
    
    def create_chat_completion(self, messages, **kwargs):
        response = openai.ChatCompletion.create(
            messages=messages,
            **kwargs
        )
        
        # Track token usage
        usage = response.get('usage', {})
        self.token_usage_history.append({
            'timestamp': time.time(),
            'prompt_tokens': usage.get('prompt_tokens', 0),
            'completion_tokens': usage.get('completion_tokens', 0),
            'total_tokens': usage.get('total_tokens', 0)
        })
        
        return response
    
    def get_total_tokens(self):
        """Get total tokens used"""
        return {
            'prompt_tokens': sum(u['prompt_tokens'] for u in self.token_usage_history),
            'completion_tokens': sum(u['completion_tokens'] for u in self.token_usage_history),
            'total_tokens': sum(u['total_tokens'] for u in self.token_usage_history)
        }
    
    def reset_token_tracking(self):
        """Reset token tracking"""
        self.token_usage_history = []
```

### 5.2 Kernel Enhancement for Token Access

**File**: `baes/core/enhanced_runtime_kernel.py`

```python
class EnhancedRuntimeKernel:
    def get_token_usage(self) -> Dict[str, int]:
        """Get total token usage from all SWEA agents"""
        total_prompt = 0
        total_completion = 0
        
        # Collect from all agents
        for agent in [self.backend_swea, self.frontend_swea, 
                     self.database_swea, self.test_swea, self.techlead_swea]:
            if agent and hasattr(agent, 'llm_client'):
                usage = agent.llm_client.get_total_tokens()
                total_prompt += usage.get('prompt_tokens', 0)
                total_completion += usage.get('completion_tokens', 0)
        
        # Also check BAEs
        for bae in self.bae_registry.get_all_baes().values():
            if hasattr(bae, 'llm_client'):
                usage = bae.llm_client.get_total_tokens()
                total_prompt += usage.get('prompt_tokens', 0)
                total_completion += usage.get('completion_tokens', 0)
        
        return {
            'prompt_tokens': total_prompt,
            'completion_tokens': total_completion,
            'total_tokens': total_prompt + total_completion
        }
    
    def reset_token_tracking(self):
        """Reset token tracking for all agents"""
        for agent in [self.backend_swea, self.frontend_swea,
                     self.database_swea, self.test_swea, self.techlead_swea]:
            if agent and hasattr(agent, 'llm_client'):
                agent.llm_client.reset_token_tracking()
        
        for bae in self.bae_registry.get_all_baes().values():
            if hasattr(bae, 'llm_client'):
                bae.llm_client.reset_token_tracking()
```

### 5.3 Result Structure Enhancement

**File**: `baes/core/enhanced_runtime_kernel.py`

Add token usage to result:

```python
def process_natural_language_request(self, request: str, start_servers=True):
    # ... existing code ...
    
    # Get token usage
    token_usage = self.get_token_usage()
    
    result = {
        "success": True,
        "entity": entity_name,
        "execution_results": execution_results,
        "coordination_plan": coordination_plan,
        "files_generated": files_generated,
        "token_usage": token_usage,  # ADD THIS
        "error": None
    }
    
    return result
```

---

## 6. Configuration Updates

### 6.1 Experiment Configuration

**File**: `config/experiment.yaml`

Add BAEs section:

```yaml
frameworks:
  baes:
    enabled: true
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

### 7.2 Shared Token Tracking Utilities

**File**: `src/utils/token_tracker.py`

```python
class TokenTracker:
    """Unified token tracking across frameworks"""
    
    def __init__(self):
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
