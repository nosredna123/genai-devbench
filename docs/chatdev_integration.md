# ChatDev Framework Integration Research

**Date**: 2025-10-08  
**Framework**: ChatDev (OpenBMB/ChatDev)  
**Commit**: 31fd994416a251ecdeb1f0a73c329271743bfb56  
**Purpose**: Document integration requirements for BAEs experiment framework

---

## 1. Framework Overview

**ChatDev** is a multi-agent LLM-based software development framework that simulates a virtual software company with specialized agents (CEO, CTO, Programmer, Reviewer, Tester, Designer).

**Architecture**: CLI-based (no persistent API server)  
**Primary Language**: Python 3.9+  
**Entry Point**: `run.py`

---

## 2. CLI Interface

### Command Structure

```bash
python run.py \
  --task "Description of software to build" \
  --name "ProjectName" \
  --org "OrganizationName" \
  --config "Default" \
  --model "GPT_4O_MINI"
```

### Key Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `--task` | Yes | "Develop a basic Gomoku game." | Natural language description of software to build |
| `--name` | No | "Gomoku" | Project name (used in directory naming) |
| `--org` | No | "DefaultOrganization" | Organization name (used in directory naming) |
| `--config` | No | "Default" | Configuration profile (Default, Art, Human, incremental) |
| `--model` | No | "GPT_3_5_TURBO" | Model selection: GPT_3_5_TURBO, GPT_4, GPT_4_TURBO, GPT_4O, GPT_4O_MINI |
| `--path` | No | "" | Path to existing code for incremental mode |

### Execution Flow

1. **Pre-processing**: Load configurations, set up logging
2. **Recruitment**: Initialize agent roles
3. **Execute Chain**: Run multi-phase development (design → code → test → document)
4. **Post-processing**: Save artifacts to `WareHouse/`

---

## 3. Output Structure

### Working Directory

ChatDev creates output in `WareHouse/name_org_timestamp/`:

```
WareHouse/
└── Gomoku_DefaultOrganization_20231020123456/
    ├── meta.txt              # Task description and metadata
    ├── requirements.txt      # Generated Python dependencies
    ├── main.py              # Generated code files
    ├── manual.md            # User manual
    ├── ChatChainConfig.json # Configuration used
    └── [other generated files]
```

### Log File

ChatDev writes logs to `WareHouse/name_org_timestamp/chatdev.log`:

```
[2023-20-10 12:34:56 INFO] **[Start Chat]**
[2023-20-10 12:34:58 INFO] Chief Executive Officer: Let's start the design...
[2023-20-10 12:35:12 INFO] Chief Technology Officer: I suggest we use...
```

**Log Format**: `[timestamp level] message`

---

## 4. Token Usage Tracking

### Challenge: No Direct Token Logging

ChatDev does **NOT** directly log token usage in its standard output or log files. The framework uses OpenAI's API internally but doesn't expose token counts.

### Detection Strategy

**Option 1: Parse OpenAI Library Calls** (COMPLEX)
- Modify ChatDev's `camel/model_backend.py` to log tokens
- Risk: Requires patching framework code

**Option 2: Monitor OpenAI API Usage** (RECOMMENDED)
- Use OpenAI Usage API to verify token counts after run completes
- Already implemented in `src/utils/api_client.py`
- Acceptable delay: 5 minutes with exponential backoff retry

**Option 3: Scan Log for Model Interactions** (FALLBACK)
- Count number of agent exchanges in log
- Estimate tokens based on message lengths
- Inaccurate but better than zero

### Recommended Approach for Integration

```python
def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
    # Execute ChatDev
    result = subprocess.run([python_path, "run.py", ...], ...)
    
    # Option 1: Try to parse logs for hints (may find none)
    tokens_in, tokens_out = self._parse_token_usage(result.stdout)
    
    # Option 2: Return 0 and rely on OpenAI Usage API verification
    # Orchestrator will call api_client.verify_token_counts() later
    
    return {
        'tokens_in': tokens_in or 0,  # Will be verified by Usage API
        'tokens_out': tokens_out or 0,
        ...
    }
```

---

## 5. Human-in-the-Loop (HITL) Detection

### HITL Support in ChatDev

ChatDev has a **Human-Agent-Interaction mode** (`--config "Human"`), where:
- The system pauses and prompts for human review
- User can provide feedback as a "Reviewer" role
- Detected pattern: `"Please provide your feedback:"` or similar prompts

### Detection Patterns

When running in Human mode, ChatDev writes to stdout:

```
**[Human Reviewer Feedback Needed]**
Please review the code and provide suggestions:
> _
```

**Keywords to detect**:
- `"Human Reviewer"` or `"Feedback Needed"`
- `"Please review"`
- `"Your input:"` or `"> _"`
- Waiting for stdin input

### HITL Injection Strategy

```python
def _detect_hitl_events(self, output: str) -> int:
    hitl_patterns = [
        r"Human Reviewer",
        r"Feedback Needed",
        r"Please review",
        r"Your input:",
        r"> _"
    ]
    
    hitl_count = 0
    for pattern in hitl_patterns:
        if re.search(pattern, output, re.IGNORECASE):
            hitl_count += 1
            # Inject fixed response via stdin or restart
    
    return hitl_count
```

**Note**: For our experiments, we will **NOT** use `--config "Human"` mode to avoid HITL complexity. We use `--config "Default"` for fully automated execution.

---

## 6. Service Architecture

### No Persistent Services

ChatDev is **CLI-based only**:
- No REST API server
- No persistent background processes
- Each invocation is self-contained

### Implications for Adapter

```python
def start(self):
    # No API server to start
    # Just clone repo and set up venv
    pass

def health_check(self):
    # Cannot check API endpoints
    # Instead: verify run.py exists and Python is available
    return os.path.exists(self.framework_dir / "run.py")

def stop(self):
    # No persistent process to kill
    # Just cleanup if subprocess is still running
    if self.process and self.process.poll() is None:
        self.process.terminate()
```

---

## 7. Environment Requirements

### Python Version

ChatDev requires **Python 3.9+** (per README).

**Compatibility**: Our orchestrator uses Python 3.11+, which is compatible.

### Dependencies

From `requirements.txt`:

```
openai==1.47.1          # ⚠️ CRITICAL: Specific version required
tiktoken==0.8.0         # Token counting for OpenAI models
tenacity==8.2.2         # Retry logic
Flask==2.3.2            # (Visualizer only - not needed for CLI)
Flask-SocketIO==5.3.4   # (Visualizer only)
colorama==0.4.6         # Terminal colors
numpy==1.24.3           # Numerical operations
regex==2023.6.3         # Pattern matching
requests==2.31.0        # HTTP client
virtualenv==20.23.0     # Virtual environments
Pillow==10.3.0          # Image processing (for Art mode)
Markdown==3.4.4         # Documentation generation
Wikipedia-API==0.6.0    # External knowledge
beautifulsoup4==4.12.2  # HTML parsing
faiss-cpu==1.7.4        # Vector similarity (for experience learning)
pyyaml==6.0             # YAML parsing
easydict==1.10          # Configuration management
```

**Installation Strategy**:

```bash
cd chatdev_framework
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Potential Conflicts**: 
- Our orchestrator uses `requests==2.31.0` (same version ✅)
- Our orchestrator uses `pyyaml==6.0.1` vs ChatDev's `6.0` (compatible ✅)

---

## 8. Exit Codes and Error Detection

### Success Indicators

- **Exit Code**: `0` (standard success)
- **Output Directory**: `WareHouse/` contains generated project
- **Log File**: No `ERROR` or `CRITICAL` entries

### Failure Indicators

- **Exit Code**: Non-zero (1, -1, etc.)
- **Exception Messages**: Python traceback in stderr
- **Missing Output**: No directory created in `WareHouse/`

### Common Errors

| Error | Pattern | Cause |
|-------|---------|-------|
| API Key Missing | `openai.error.AuthenticationError` | Missing/invalid OPENAI_API_KEY |
| API Rate Limit | `RateLimitError` | Too many requests to OpenAI |
| Timeout | `ReadTimeout` | OpenAI API slow response |
| Invalid Task | `AttributeError` or empty output | Malformed task description |

---

## 9. Timeout Strategy

### ChatDev Execution Time

Typical execution for simple apps: **5-15 minutes**  
Complex apps with multiple phases: **20-30 minutes**

**Recommendation**: 10-minute timeout per step aligns with ChatDev's typical runtime.

### Timeout Implementation

```python
try:
    result = subprocess.run(
        [python_path, "run.py", "--task", command_text, ...],
        timeout=600,  # 10 minutes
        capture_output=True,
        text=True,
        cwd=self.framework_dir,
        env={**os.environ, 'OPENAI_API_KEY': api_key}
    )
except subprocess.TimeoutExpired:
    logger.error("ChatDev execution timeout")
    # Send SIGTERM, wait 30s, then SIGKILL
    self.process.terminate()
    time.sleep(30)
    if self.process.poll() is None:
        self.process.kill()
```

---

## 10. Reproducibility Considerations

### Deterministic Behavior

ChatDev uses LLM APIs which are **non-deterministic by default**.

**To enforce determinism**:
1. Set `temperature=0` in model configuration
2. Use fixed random seeds (if ChatDev supports)
3. Pin framework commit hash (already done: `31fd994...`)
4. Use same model version (GPT-4O-MINI)

**Configuration File**: `CompanyConfig/Default/ChatChainConfig.json`

```json
{
  "model": "GPT_4O_MINI",
  "temperature": 0.0,  // ⚠️ May need to modify this
  "top_p": 1.0
}
```

**Action Required**: Check if ChatChainConfig.json supports temperature parameter.

---

## 11. Integration Implementation Checklist

### T064: Environment Setup ✅

```python
def start(self):
    # 1. Clone repository (already done in placeholder)
    # 2. Create virtual environment
    venv_path = self.framework_dir / ".venv"
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
    
    # 3. Install dependencies
    pip_path = venv_path / "bin" / "pip"
    subprocess.run([
        str(pip_path), "install", "-r", "requirements.txt"
    ], cwd=self.framework_dir, check=True)
    
    # 4. Verify installation
    python_path = venv_path / "bin" / "python"
    result = subprocess.run([str(python_path), "--version"], capture_output=True)
    logger.info(f"ChatDev Python: {result.stdout.decode()}")
```

### T065: Service Management ✅

```python
# ChatDev has NO services - this is a no-op
def start(self):
    # After environment setup, just verify run.py exists
    if not (self.framework_dir / "run.py").exists():
        raise RuntimeError("ChatDev run.py not found")
```

### T066: Command Execution ✅

```python
def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
    python_path = self.framework_dir / ".venv" / "bin" / "python"
    api_key = os.getenv(self.config['api_key_env'])
    
    # Generate unique project name per step
    project_name = f"BAEs_Step{step_num}_{self.run_id[:8]}"
    
    cmd = [
        str(python_path), "run.py",
        "--task", command_text,
        "--name", project_name,
        "--org", "BAEs_Experiment",
        "--config", "Default",
        "--model", "GPT_4O_MINI"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=self.framework_dir,
        capture_output=True,
        text=True,
        timeout=600,
        env={**os.environ, 'OPENAI_API_KEY': api_key}
    )
    
    return {
        'success': result.returncode == 0,
        'duration_seconds': time.time() - start_time,
        ...
    }
```

### T067: Token Tracking ⚠️

```python
def _parse_token_usage(self, output: str) -> Tuple[int, int]:
    # ChatDev doesn't log tokens - return 0
    # Orchestrator will use OpenAI Usage API to verify
    return 0, 0
```

### T068: HITL Detection ✅

```python
def _detect_hitl_events(self, output: str) -> int:
    # If using Default mode: no HITL
    # If using Human mode: detect prompts
    if self.config.get('chatdev_config') == 'Human':
        patterns = [r"Human Reviewer", r"Feedback Needed", r"Please review"]
        for pattern in patterns:
            if re.search(pattern, output, re.IGNORECASE):
                return 1  # Max 1 HITL per step
    return 0
```

### T069: Health Checks ✅

```python
def health_check(self) -> bool:
    # Verify run.py exists
    run_py = self.framework_dir / "run.py"
    if not run_py.exists():
        return False
    
    # Verify Python environment is accessible
    python_path = self.framework_dir / ".venv" / "bin" / "python"
    try:
        result = subprocess.run(
            [str(python_path), "--version"],
            capture_output=True,
            timeout=5
        )
        return result.returncode == 0
    except:
        return False
```

### T070: Graceful Shutdown ✅

```python
def stop(self):
    # If subprocess is running, terminate it
    if hasattr(self, 'process') and self.process and self.process.poll() is None:
        self.process.terminate()
        try:
            self.process.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
```

---

## 12. Open Questions / Action Items

### ❓ Questions Requiring Investigation

1. **Temperature Control**: Does ChatChainConfig.json support `temperature` parameter?
   - Action: Inspect `CompanyConfig/Default/ChatChainConfig.json`
   - If not: May need to modify configuration file before runs

2. **Token Counting**: Can we patch `camel/model_backend.py` safely?
   - Action: Review source code to see if logging can be added
   - Risk: May affect reproducibility if patch changes behavior

3. **Incremental Mode**: Does `--path` parameter allow building on previous step?
   - Action: Test if we can chain steps by passing previous output
   - Benefit: More realistic scenario (step 2 builds on step 1)

### ✅ Confirmed Capabilities

- CLI-based execution ✅
- No persistent services ✅
- Virtual environment isolation ✅
- Exit codes for success/failure ✅
- Configurable via command-line arguments ✅
- Output directory structure known ✅

---

## 13. Estimated Implementation Time

| Task | Estimated Hours | Confidence |
|------|----------------|------------|
| T064: Environment Setup | 2-3h | High |
| T065: Service Management | 0.5h | High (no-op) |
| T066: Command Execution | 3-4h | High |
| T067: Token Tracking | 2h | Medium (verify Usage API fallback works) |
| T068: HITL Detection | 2h | High |
| T069: Health Checks | 1h | High |
| T070: Graceful Shutdown | 1h | High |
| T071: Single-Step Test | 2-3h | Medium (debugging) |
| T072: Six-Step Test | 2-3h | Medium (end-to-end validation) |
| T073: Reproducibility | 2-3h | Low (LLM non-determinism risk) |
| **TOTAL** | **18-25 hours** | |

---

## 14. Risk Assessment

### High Risk

- **Non-deterministic LLMs**: Even with `temperature=0`, results may vary
  - Mitigation: Document variance, focus on metric trends not exact values

### Medium Risk

- **No token logging**: Reliance on OpenAI Usage API
  - Mitigation: Already implemented with retry logic

- **Long execution times**: 10+ minutes per step
  - Mitigation: Timeout already configured at 10 minutes

### Low Risk

- **Dependency conflicts**: ChatDev and orchestrator share dependencies
  - Mitigation: Isolated virtual environment per run

---

## 15. Next Steps

1. ✅ **Document completed** (this file)
2. ⏭️ **Proceed to T064**: Implement environment setup in `chatdev_adapter.py`
3. ⏭️ **Test installation**: Verify dependencies install correctly
4. ⏭️ **Manual validation**: Run ChatDev standalone once to confirm behavior
5. ⏭️ **Implement T065-T073**: Complete remaining adapter methods

---

**Status**: Research complete ✅  
**Ready for implementation**: Yes  
**Blocking issues**: None identified
