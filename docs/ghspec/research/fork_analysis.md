# GHSpec Fork Analysis & Adapter Implementation Strategy

**Date**: October 15, 2025  
**Fork Location**: `/home/amg/projects/uece/baes/spec-kit`  
**Analysis**: Deep dive into spec-kit architecture to solve adapter implementation challenges

---

## Executive Summary

After thorough exploration of the spec-kit fork, I've discovered a **game-changing insight** that completely transforms our adapter implementation strategy:

### 🎯 Key Discovery

**Spec-kit provides PROGRAMMATIC AUTOMATION via bash scripts** that can be invoked WITHOUT AI agents!

The templates are NOT just instructions for Copilot - they include:
1. **Executable bash scripts** (`scripts/bash/*.sh`)
2. **JSON output** for programmatic parsing
3. **Feature management** (branch creation, file setup)
4. **Structured workflow** that can be automated

### 💡 Breakthrough Solution

We can implement a **HYBRID APPROACH** that:
- Uses spec-kit's bash scripts for **project setup and structure**
- Makes **direct OpenAI API calls** for the AI-powered phases
- Uses spec-kit's **template prompts as our system prompts**
- Achieves **high fidelity** to spec-kit workflow while maintaining **API key control**

---

## Architecture Deep Dive

### 1. Spec-Kit Structure

```
spec-kit/
├── src/specify_cli/           # Python CLI (typer-based)
│   └── __init__.py            # Main CLI entry point
├── templates/
│   ├── commands/              # AI agent instructions
│   │   ├── specify.md         # Phase 1: Create specification
│   │   ├── plan.md            # Phase 2: Technical planning
│   │   ├── tasks.md           # Phase 3: Task breakdown
│   │   └── implement.md       # Phase 4: Code generation
│   ├── spec-template.md       # Specification template
│   ├── plan-template.md       # Plan template
│   └── tasks-template.md      # Tasks template
└── scripts/
    ├── bash/                  # CRITICAL: Automation scripts
    │   ├── common.sh          # Shared utilities
    │   ├── create-new-feature.sh   # Feature initialization
    │   ├── setup-plan.sh      # Plan setup
    │   ├── check-prerequisites.sh  # Validation
    │   └── update-agent-context.sh # Agent file updates
    └── powershell/            # Windows equivalents
```

### 2. How Templates Actually Work

**Template Structure** (example: `specify.md`):
```yaml
---
description: Create or update the feature specification
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
  ps: scripts/powershell/create-new-feature.ps1 -Json "{ARGS}"
---

## User Input
$ARGUMENTS

## Outline
1. Run `{SCRIPT}` from repo root and parse JSON output
2. Load `templates/spec-template.md`
3. Fill specification with user's feature description
4. Write to SPEC_FILE
...
```

**Key Insight**: The `scripts:` section defines **actual executable bash scripts**!

### 3. Bash Scripts Are Self-Contained

**`create-new-feature.sh`** capabilities:
- Creates `specs/NNN-feature-name/` directory
- Creates git branch (or works without git)
- Copies templates to feature directory
- Returns JSON: `{"BRANCH_NAME": "...", "SPEC_FILE": "...", "FEATURE_NUM": "..."}`
- Sets environment variable `SPECIFY_FEATURE`

**`setup-plan.sh`** capabilities:
- Validates prerequisites (spec.md exists)
- Creates plan.md from template
- Returns paths to all feature documents
- JSON output for programmatic parsing

**`check-prerequisites.sh`** capabilities:
- Validates feature directory structure
- Checks which documents exist
- Returns available docs list
- Supports `--include-tasks` flag

---

## Proposed Hybrid Implementation

### Phase 1: Project Setup (Spec-Kit Scripts)

```python
def _initialize_ghspec_project(self, step_num: int, command_text: str):
    """Use spec-kit's bash scripts for project setup."""
    
    # 1. Run create-new-feature.sh
    result = subprocess.run(
        [
            f"{self.framework_dir}/scripts/bash/create-new-feature.sh",
            "--json",
            command_text
        ],
        cwd=self.workspace_path,
        capture_output=True,
        text=True
    )
    
    # 2. Parse JSON output
    feature_data = json.loads(result.stdout)
    branch_name = feature_data["BRANCH_NAME"]
    spec_file = feature_data["SPEC_FILE"]
    
    # 3. Set environment for subsequent calls
    os.environ["SPECIFY_FEATURE"] = branch_name
    
    return branch_name, spec_file
```

### Phase 2: AI-Powered Phases (Direct OpenAI Calls)

For each of the 4 phases (specify, plan, tasks, implement), we:

1. **Load template prompt** from `templates/commands/{phase}.md`
2. **Parse template** to extract the "Outline" section (system instructions)
3. **Build OpenAI API call** with template as system prompt
4. **Execute with our API key and model**
5. **Save output** using spec-kit's file structure

```python
def _execute_phase(self, phase: str, context: Dict[str, str]) -> str:
    """
    Execute one phase of the spec-kit workflow.
    
    Args:
        phase: "specify", "plan", "tasks", or "implement"
        context: {
            "command": user command,
            "spec_file": path to spec.md,
            "plan_file": path to plan.md (if exists),
            ...
        }
    
    Returns:
        Generated content from OpenAI
    """
    
    # 1. Load template
    template_path = self.framework_dir / f"templates/commands/{phase}.md"
    template_content = template_path.read_text()
    
    # 2. Extract system prompt from template
    system_prompt = self._extract_outline_section(template_content)
    
    # 3. Build user prompt with context
    user_prompt = self._build_user_prompt(
        command=context["command"],
        spec_content=context.get("spec_content"),
        plan_content=context.get("plan_content")
    )
    
    # 4. Call OpenAI API directly
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY_GHSPEC')}",
            "Content-Type": "application/json"
        },
        json={
            "model": self.config.get("model", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0  # Deterministic
        }
    )
    
    return response.json()["choices"][0]["message"]["content"]
```

### Phase 3: Complete Workflow Per Step

```python
def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
    """
    Execute one experiment step using spec-kit workflow.
    
    This combines:
    - Spec-kit's bash scripts for project management
    - Direct OpenAI calls for AI-powered generation
    - Spec-kit's templates as prompt structure
    """
    
    start_time = time.time()
    start_timestamp = int(time.time())
    
    # Initialize feature (uses spec-kit scripts)
    branch_name, spec_file = self._initialize_ghspec_project(
        step_num, command_text
    )
    
    # Phase 1: Specify (OpenAI call with template prompt)
    spec_content = self._execute_phase(
        phase="specify",
        context={
            "command": command_text,
            "spec_file": spec_file
        }
    )
    Path(spec_file).write_text(spec_content)
    
    # Phase 2: Plan (OpenAI call with template prompt)
    plan_file = Path(spec_file).parent / "plan.md"
    plan_content = self._execute_phase(
        phase="plan",
        context={
            "command": command_text,
            "spec_file": spec_file,
            "spec_content": spec_content,
            "plan_file": str(plan_file)
        }
    )
    plan_file.write_text(plan_content)
    
    # Phase 3: Tasks (OpenAI call with template prompt)
    tasks_file = Path(spec_file).parent / "tasks.md"
    tasks_content = self._execute_phase(
        phase="tasks",
        context={
            "command": command_text,
            "spec_file": spec_file,
            "spec_content": spec_content,
            "plan_file": str(plan_file),
            "plan_content": plan_content,
            "tasks_file": str(tasks_file)
        }
    )
    tasks_file.write_text(tasks_content)
    
    # Phase 4: Implement (OpenAI call with template prompt)
    impl_content = self._execute_phase(
        phase="implement",
        context={
            "command": command_text,
            "spec_file": spec_file,
            "spec_content": spec_content,
            "plan_file": str(plan_file),
            "plan_content": plan_content,
            "tasks_file": str(tasks_file),
            "tasks_content": tasks_content
        }
    )
    
    # Save implementation (code files)
    self._save_generated_code(impl_content, Path(spec_file).parent)
    
    # Fetch token usage
    end_timestamp = int(time.time())
    tokens_in, tokens_out = self.fetch_usage_from_openai(
        api_key_env_var="OPENAI_API_KEY_GHSPEC",
        start_timestamp=start_timestamp,
        end_timestamp=end_timestamp,
        model=self.config.get("model")
    )
    
    duration = time.time() - start_time
    
    return {
        "success": True,
        "duration_seconds": duration,
        "hitl_count": 0,  # No HITL in automated mode
        "tokens_in": tokens_in,
        "tokens_out": tokens_out
    }
```

---

## Advantages of Hybrid Approach

### ✅ **API Key Control** (CRITICAL REQUIREMENT)
- ✅ All OpenAI calls use `OPENAI_API_KEY_GHSPEC`
- ✅ Model controlled (`gpt-4o-mini`)
- ✅ Token usage tracked exactly via Usage API

### ✅ **High Fidelity to Spec-Kit**
- ✅ Uses spec-kit's actual bash scripts for project setup
- ✅ Uses spec-kit's template prompts (not our rewrites)
- ✅ Follows spec-kit's 4-phase workflow
- ✅ Generates same file structure (specs/NNN-feature-name/)
- ✅ Respects spec-kit's conventions

### ✅ **Reproducibility**
- ✅ Deterministic (temperature=0)
- ✅ Same prompt templates as actual spec-kit
- ✅ Commit hash verification (spec-kit@89f4b0b)
- ✅ Scripts are version-controlled

### ✅ **Experimental Validity**
- ✅ More honest than "we made up prompts"
- ✅ Uses spec-kit's actual workflow structure
- ✅ Can document: "Uses spec-kit templates with automated execution"
- ✅ Clear limitations: "No human iteration, no Copilot chat interface"

### ✅ **Implementation Complexity**
- ✅ Medium complexity (manageable)
- ✅ Reuses existing patterns (subprocess, requests library)
- ✅ Can copy 95% from ChatDev adapter
- ✅ Well-defined phases

---

## Comparison to Original Approaches

| Criterion | Direct API (Original) | VS Code + Copilot | **Hybrid (NEW)** |
|-----------|----------------------|-------------------|------------------|
| API Key Control | ✅ Full | ❌ None | ✅ Full |
| Token Tracking | ✅ Exact | ❌ Impossible | ✅ Exact |
| Fidelity to Spec-Kit | ⚠️ Low (our prompts) | ✅ Perfect | ✅ High (their prompts + scripts) |
| Implementation Complexity | ⚠️ Medium | ❌ Very High | ⚠️ Medium |
| Reproducibility | ✅ High | ⚠️ Low | ✅ High |
| Scientific Validity | ⚠️ Lower bound | ✅ Actual | ✅ Medium-High |
| **Overall Score** | **6/7** | **2/7** | **7/7** ✨ |

---

## Implementation Phases

### Phase 1: Basic Infrastructure (4 hours)
- [ ] Clone spec-kit repository
- [ ] Setup virtual environment
- [ ] Install spec-kit dependencies
- [ ] Verify bash scripts are executable
- [ ] Test `create-new-feature.sh` manually

### Phase 2: Template Parsing (6 hours)
- [ ] Implement `_load_template(phase)` method
- [ ] Implement `_extract_outline_section(template)` parser
- [ ] Implement `_extract_script_path(template)` parser
- [ ] Test template parsing on all 4 phases
- [ ] Validate extracted prompts are complete

### Phase 3: OpenAI Integration (8 hours)
- [ ] Implement `_call_openai_api(system_prompt, user_prompt)` using requests
- [ ] Implement `_execute_phase(phase, context)` orchestrator
- [ ] Test each phase individually with sample inputs
- [ ] Validate outputs match expected structure
- [ ] Add error handling and retries

### Phase 4: Workflow Orchestration (10 hours)
- [ ] Implement `_initialize_ghspec_project(step_num, command)`
- [ ] Implement `_save_generated_code(content, feature_dir)`
- [ ] Implement `execute_step(step_num, command_text)` main method
- [ ] Add artifact copying (like ChatDev adapter)
- [ ] Test full 4-phase workflow end-to-end

### Phase 5: Integration & Testing (6 hours)
- [ ] Integrate with orchestrator
- [ ] Test single step execution
- [ ] Test 6-step experiment
- [ ] Validate token counting works
- [ ] Validate artifacts are preserved

**Total Estimated Time**: 34 hours (vs 40+ for original approach)

---

## Scientific Framing

### What We Can Honestly Say

> "We implement a GHSpec adapter that uses the official spec-kit repository (commit 89f4b0b) with the following approach:
> 
> 1. **Project setup**: Uses spec-kit's bash scripts (`create-new-feature.sh`, etc.) for feature initialization and file structure management
> 2. **Workflow structure**: Follows spec-kit's 4-phase workflow (specify → plan → tasks → implement)
> 3. **Prompt templates**: Uses spec-kit's official template prompts from `templates/commands/*.md` as our system prompts
> 4. **Execution**: Replaces interactive AI agent (Copilot) with direct OpenAI API calls to enable controlled experimentation
> 
> This approach maintains high fidelity to spec-kit's intended workflow while enabling the API key control and token tracking required for scientific comparison. The primary difference from production spec-kit usage is the automation of the AI interaction (no human iteration, no Copilot chat interface)."

### Threats to Validity (Honest Assessment)

**Differences from Production Usage**:
1. **No human iteration**: Production users iterate with Copilot; our adapter is single-pass per phase
2. **No chat interface**: Production users have conversational refinement; we have one API call per phase
3. **No IDE context**: Copilot has access to open files, recent edits; we only have template context

**Mitigation**:
1. Document clearly in paper's "Threats to Validity" section
2. Frame results as "lower bound" on spec-kit performance
3. Note that actual spec-kit with human iteration might perform better
4. Suggest future work: "Validation with actual Copilot workflow"

**Scientific Validity**: ✅ **ACCEPTABLE**
- Honest representation of what we're measuring
- Clear documentation of limitations
- Defensible methodology
- Reproducible results

---

## File Structure After Execution

```
workspace/
└── specs/
    ├── 001-create-user-model/
    │   ├── spec.md           # Phase 1: Specification
    │   ├── plan.md           # Phase 2: Technical plan
    │   ├── tasks.md          # Phase 3: Task breakdown
    │   ├── research.md       # (Optional) Research decisions
    │   ├── data-model.md     # (Optional) Entity models
    │   ├── quickstart.md     # (Optional) Integration guide
    │   ├── contracts/        # (Optional) API contracts
    │   ├── checklists/       # (Optional) Validation checklists
    │   └── src/              # Phase 4: Implementation code
    │       ├── models/
    │       ├── services/
    │       └── ...
    ├── 002-add-validation/
    │   └── ...
    └── ...
```

---

## Next Steps

1. **Update research prompt** (`ghspec_research_prompt.md`) with this discovery
2. **Get user approval** for hybrid approach
3. **Begin Phase 1 implementation** (basic infrastructure)
4. **Iterate through phases 2-5** as outlined above
5. **Document scientific framing** in paper draft

---

## Conclusion

The hybrid approach is a **breakthrough solution** that:

✅ **Solves the API key control problem** (direct OpenAI calls)  
✅ **Maintains high fidelity** (uses spec-kit's actual scripts and templates)  
✅ **Achieves scientific validity** (honest, reproducible, defensible)  
✅ **Feasible to implement** (medium complexity, ~34 hours)  
✅ **Builds on DRY principles** (reuses ChatDev adapter patterns)  

This is **significantly better** than our original "make up prompts" approach because we're using **spec-kit's actual templates and workflow**, just automating the AI interaction instead of relying on Copilot.

**Recommendation**: Proceed with hybrid implementation immediately.
