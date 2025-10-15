# Research Prompt: GHSpec Adapter Implementation Strategy

## 🎯 CRITICAL TASK: Validate or Replace Proposed Solution

**You are being asked to CRITICALLY EVALUATE a proposed implementation approach and either VALIDATE it or PROPOSE A BETTER ALTERNATIVE.**

**Do NOT simply accept the proposed solution.** Your job is to:
1. **Challenge assumptions** - Question every claim made about the Hybrid Approach
2. **Find weaknesses** - Identify fatal flaws, hidden complexities, or invalid comparisons
3. **Explore alternatives** - Consider options we may have dismissed too quickly
4. **Recommend the BEST solution** - Not just workable, but optimal for scientific validity

**This is a research decision with publication implications.** Be thorough, be critical, be honest.

---

## Context

We're building an experimental framework to compare software development approaches:
- **ChatDev**: Autonomous multi-agent framework (makes its own OpenAI API calls)
- **BAEs**: Autonomous multi-agent framework (makes its own OpenAI API calls)
- **GHSpec (github/spec-kit)**: Template-based scaffolding system for AI agents (Copilot/Claude)

## Critical Discovery

GHSpec (spec-kit) **does NOT make OpenAI API calls directly**. It only:
1. Creates markdown templates with instructions
2. Provides slash commands (e.g., `/speckit.implement`) for AI agents to execute
3. Relies on external AI agents (Copilot/Claude) to read templates and call OpenAI

**Problem**: We cannot control which API key or model the external AI agents use.

## Our Requirements

1. **API Key Control**: Must use `OPENAI_API_KEY_GHSPEC` (not Copilot's key)
2. **Model Control**: Must use `gpt-4o-mini` (specified in config)
3. **Token Tracking**: Must track exact token usage for cost comparison
4. **Fair Comparison**: Results must be scientifically valid when compared to ChatDev/BAEs

## ⚠️ CRITICAL UPDATE: New Discovery

**After analyzing the spec-kit fork** (`/home/amg/projects/uece/baes/spec-kit`), we discovered:

### Spec-Kit Has Executable Bash Scripts!

The templates include `scripts:` sections with **actual bash scripts** that can be run programmatically:

```yaml
# templates/commands/specify.md
---
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
---
```

These scripts:
- ✅ Create feature directories (`specs/NNN-feature-name/`)
- ✅ Initialize files from templates
- ✅ Return JSON output for parsing
- ✅ Work without AI agents

### Revised Proposed Solution: HYBRID APPROACH

**Approach**: Combine spec-kit's bash scripts + direct OpenAI API calls.

**Multi-phase workflow per step** (4 API calls):
```
User Command 
  ↓
[Spec-Kit Script: create-new-feature.sh] → Creates feature directory
  ↓
[Phase 1: Specify - OpenAI API] → Uses template prompt as system prompt
  ↓
[Spec-Kit Script: setup-plan.sh] → Initializes plan structure
  ↓
[Phase 2: Plan - OpenAI API] → Uses template prompt as system prompt
  ↓
[Phase 3: Tasks - OpenAI API] → Uses template prompt as system prompt
  ↓
[Phase 4: Implement - OpenAI API] → Uses template prompt as system prompt
  ↓
Code Output
```

Each phase:
- **Project management**: Use spec-kit's bash scripts (high fidelity!)
- **AI generation**: Call OpenAI directly with template prompts as system prompts
- **API control**: Use OPENAI_API_KEY_GHSPEC and gpt-4o-mini
- **File structure**: Follow spec-kit's conventions exactly

## Critical Research Questions

### 1. Experimental Validity Threat
**Question**: Is it scientifically valid to compare:
- **ChatDev/BAEs**: Autonomous frameworks with multi-agent iteration, self-critique, replanning
- **Our GHSpec adapter**: Simplified prompt-based approach (4 sequential API calls, no iteration)

**Sub-questions**:
- Does this create an "apples-to-oranges" comparison?
- Are we measuring "framework capability" or "our implementation capability"?
- How should we frame results to maintain scientific integrity?

**Options**:
- A) Implement simplified version, document as "lower bound" for GHSpec
- B) Implement complex iteration logic to match ChatDev's autonomy
- C) Abandon GHSpec comparison as invalid

### 2. Architecture Fidelity
**Question**: How closely must our adapter replicate spec-kit's intended workflow?

**Spec-kit's intended workflow**:
1. Developer runs `specify init` → creates templates
2. Developer runs `specify task "build API"` → creates spec.md
3. AI agent (Copilot) reads spec.md
4. AI agent executes slash commands iteratively (`/speckit.plan`, `/speckit.implement`)
5. AI agent makes OpenAI calls with its own key/config
6. Human reviews, provides feedback, AI iterates

**Our workflow (proposed)**:
1. Adapter runs `specify init` → creates templates
2. Adapter reads templates → builds prompts
3. Adapter makes 4 sequential OpenAI API calls (specify→plan→tasks→implement)
4. Adapter saves outputs → returns metrics

**Is this acceptable or does it invalidate the comparison?**

### 3. Alternative Approaches
**Question**: Are there better implementation strategies we haven't considered?

**Option A**: Intercept AI Agent API Calls
- Use proxy/middleware to intercept Copilot's OpenAI calls
- Override API key/model in proxy
- **Issue**: Complex, brittle, may violate Copilot ToS

**Option B**: Template-Only Approach
- Use spec-kit templates as static prompts
- Single API call per step (not 4-phase)
- **Issue**: Loses spec-kit's structured workflow

**Option C**: Hybrid Approach
- Use spec-kit for planning phases (specify, plan, tasks)
- Only implement "implement" phase ourselves
- **Issue**: Still can't control API keys in planning phases

**Option D**: Fork spec-kit
- Modify spec-kit source to add OpenAI integration
- **Issue**: Becomes "our version" not actual GHSpec

**Option E**: VS Code Automation (Headless Copilot) - DEPRECATED
- Automate VS Code with Copilot extension in headless mode
- **Issues**: Too complex, can't control API keys, platform-specific
- **Status**: Superseded by Option G (Copilot CLI)

**Option E-2**: GitHub Copilot CLI ⭐ **NEW DISCOVERY**
- Use GitHub Copilot CLI in programmatic mode with spec-kit templates
- Copilot CLI can execute shell commands, modify files, interact with GitHub
- **Key Features** (from docs):
  - Programmatic mode: `copilot -p "prompt" --allow-all-tools`
  - Can pipe scripts: `echo ./script.sh | copilot`
  - Supports trusted directories (security)
  - Works with MCP servers (Model Context Protocol)
  - Interactive or headless operation
  - Can create PRs, commit code, run git commands
- **Pros**:
  - ✅ Official GitHub tool (not hacky)
  - ✅ Works from command line (scriptable)
  - ✅ Can execute bash scripts AND modify files
  - ✅ Could potentially work with spec-kit workflow directly
  - ✅ Supports both interactive and programmatic modes
- **Issues**:
  - ❌ **CRITICAL**: Still uses GitHub's Copilot API keys (not our OPENAI_API_KEY_GHSPEC)
  - ❌ **CRITICAL**: Still uses GitHub's model selection (not our gpt-4o-mini)
  - ❌ **CRITICAL**: No token tracking via OpenAI Usage API (uses Copilot premium requests)
  - ⚠️ Requires GitHub Copilot Pro/Business/Enterprise subscription
  - ⚠️ Model is Claude Sonnet 4 by default (can change via /model, but limited options)
  - ⚠️ Security: `--allow-all-tools` gives Copilot full system access
  - ⚠️ Quota: Each prompt counts against monthly premium request quota
- **Analysis Needed**:
  - Could this replace our Hybrid Approach?
  - Does programmatic mode enable better automation than VS Code?
  - Can we track usage somehow (even if not via OpenAI API)?
  - Would comparison still be scientifically valid?
  - **CRITICAL QUESTION**: Does this solve any of our core problems (API key control, token tracking)?

**Option F**: Hybrid Approach (Spec-Kit Scripts + Direct API) ⭐ **RECOMMENDED**
- Use spec-kit's bash scripts for project management (create-new-feature.sh, etc.)
- Use spec-kit's template prompts as system prompts (not rewriting them)
- Call OpenAI API directly for AI-powered phases
- **Pros**:
  - ✅ Full API key/model control
  - ✅ Uses spec-kit's actual templates and scripts (high fidelity)
  - ✅ Exact token tracking
  - ✅ Reproducible (scripts + templates version-controlled)
  - ✅ Honest scientific framing ("automated spec-kit workflow")
  - ✅ Medium implementation complexity
- **Issues**:
  - Still not using actual Copilot (no chat interface, no human iteration)
  - Single-pass per phase (no iterative refinement)
  - Need to parse template structure to extract prompts

**Which approach best balances API control + experimental validity?**

### 4. Prompt Engineering Fidelity
**Question**: How should we construct prompts from spec-kit templates?

**Spec-kit template structure** (actual example from `specify.md`):
```markdown
---
description: Create or update the feature specification
scripts:
  sh: scripts/bash/create-new-feature.sh --json "{ARGS}"
---

## User Input
```text
$ARGUMENTS
```

## Outline
1. Run `{SCRIPT}` from repo root and parse its JSON output for BRANCH_NAME and SPEC_FILE
2. Load `templates/spec-template.md` to understand required sections
3. Follow this execution flow:
   1. Parse user description from Input
      If empty: ERROR "No feature description provided"
   2. Extract key concepts from description
   3. For unclear aspects: Make informed guesses, mark [NEEDS CLARIFICATION]
   4. Fill User Scenarios & Testing section
   5. Generate Functional Requirements (must be testable)
   6. Define Success Criteria (measurable, technology-agnostic)
   7. Identify Key Entities
4. Write specification to SPEC_FILE using template structure
5. Validate spec quality (completeness checklist)
6. Report completion with branch name, spec file path

## General Guidelines
- Focus on **WHAT** users need and **WHY**
- Avoid HOW to implement (no tech stack, APIs, code)
- Written for business stakeholders, not developers
```

**Critical Analysis Needed**:
- The template says "Run `{SCRIPT}`" - but we're making API calls, not running bash in the AI context
- Template assumes AI agent can execute bash commands - our approach separates bash execution from API calls
- Does this instruction mismatch invalidate using templates as prompts?

**Our options**:
- **A) Use templates verbatim**: Copy entire "Outline" section as system prompt
  - Pro: Maximum fidelity to spec-kit
  - Con: Contains bash execution instructions that don't apply to API calls
  
- **B) Extract intent, rephrase**: Parse template, remove bash-specific instructions, keep logic
  - Pro: Clean prompts suitable for Chat Completions API
  - Con: We're modifying spec-kit's prompts (lower fidelity)
  
- **C) Hybrid**: Run bash scripts separately, use template prompts with variable substitution
  - Pro: Bash scripts handle file management, prompts guide content generation
  - Con: Complex coordination, potential for context mismatch

**D) Pre-process templates**: Replace `{SCRIPT}` markers with actual data before API call
  - Example: Replace "Run `{SCRIPT}` and parse JSON" with "Use this data: {actual_json_output}"
  - Pro: Templates work as-is, we just inject the script results
  - Con: Need sophisticated template variable replacement

**Question for your analysis**: Which option maintains fidelity while being technically sound?

### 5. Token Usage Attribution
**Question**: How do we fairly attribute token costs when workflow differs?

**Scenario**:
- ChatDev: 50 API calls (iteration, refinement, critique) = 100k tokens
- Our GHSpec: 24 API calls (4 phases × 6 steps) = 50k tokens

**Issues**:
- Lower token count doesn't mean "better" - just different workflow
- ChatDev's iteration might produce higher quality
- Our approach is constrained, not optimized

**How should we report/compare costs fairly?**

## Research Deliverables Requested

1. **Recommendation**: Which implementation approach best balances requirements?
2. **Scientific Framing**: How to present results honestly (limitations, threats to validity)?
3. **Prompt Strategy**: Specific guidance on using spec-kit templates as prompts
4. **Metrics Strategy**: How to compare token usage across different paradigms?
5. **Risk Assessment**: What are the biggest threats to experimental validity?

## Technical Constraints

- **Language**: Python 3.x
- **Library**: Must use `requests` (not `openai` SDK) for DRY consistency
- **Framework**: Existing adapter pattern (base_adapter.py, chatdev_adapter.py)
- **Token Tracking**: Already implemented via OpenAI Usage API
- **Reproducibility**: Must support deterministic execution (commit hash verification)

## Current Codebase References

### Our Framework
- `src/adapters/base_adapter.py`: Shared adapter functionality (requests library pattern)
- `src/adapters/chatdev_adapter.py`: Reference implementation (936 lines, autonomous framework)
- `src/adapters/ghspec_adapter.py`: Placeholder (needs implementation)

### Spec-Kit Fork (Analyzed)
- **Location**: `/home/amg/projects/uece/baes/spec-kit`
- **Commit**: `7b55522` (fork of `github/spec-kit@89f4b0b`)
- **Key Files Analyzed**:
  - `src/specify_cli/__init__.py`: Python CLI (typer-based, ~150 lines)
  - `scripts/bash/create-new-feature.sh`: Feature initialization (~90 lines)
  - `scripts/bash/setup-plan.sh`: Plan setup script
  - `scripts/bash/check-prerequisites.sh`: Prerequisite validation
  - `scripts/bash/common.sh`: Shared utilities (~100 lines)
  - `templates/commands/specify.md`: Specification phase prompt (~200 lines)
  - `templates/commands/plan.md`: Planning phase prompt (~100 lines)
  - `templates/commands/tasks.md`: Task breakdown prompt (~100 lines)
  - `templates/commands/implement.md`: Implementation phase prompt (~200 lines)

### Bash Script Capabilities (Verified)
- **create-new-feature.sh**:
  - Input: `--json "feature description"`
  - Output: `{"BRANCH_NAME": "001-feature-name", "SPEC_FILE": "/path/to/spec.md", "FEATURE_NUM": "001"}`
  - Side effects: Creates `specs/NNN-feature-name/` directory, creates git branch (optional), copies templates
  - Dependencies: bash, sed, grep (standard Unix tools), git (optional)

- **setup-plan.sh**:
  - Input: `--json`
  - Output: `{"FEATURE_SPEC": "...", "IMPL_PLAN": "...", "SPECS_DIR": "...", "BRANCH": "..."}`
  - Side effects: Creates plan.md from template
  - Dependencies: bash, template files

- **check-prerequisites.sh**:
  - Input: `--json [--require-tasks] [--include-tasks]`
  - Output: `{"FEATURE_DIR": "...", "AVAILABLE_DOCS": ["spec.md", "plan.md", ...]}`
  - Side effects: None (read-only validation)
  - Dependencies: bash, file system

### Template Structure (Analyzed)
Each template has:
```yaml
---
description: Human-readable description
scripts:
  sh: path/to/script.sh --json "{ARGS}"
  ps: path/to/script.ps1 -Json "{ARGS}"
---

## User Input
$ARGUMENTS

## Outline
1. Step-by-step instructions for AI agent
2. Load templates from X
3. Execute workflow Y
...

## General Guidelines
- Additional instructions
- Quality criteria
- Error handling
```

**Key Question**: Can we reliably extract "Outline" section as system prompt for API calls?

## Success Criteria

✅ **Must Have**:
- Control API key (OPENAI_API_KEY_GHSPEC)
- Control model (gpt-4o-mini)
- Track exact token usage
- Generate working code outputs

✅ **Should Have**:
- Scientifically valid comparison to ChatDev/BAEs
- Honest representation of spec-kit's capabilities
- Reproducible results

✅ **Nice to Have**:
- High fidelity to spec-kit's intended workflow
- Comparable quality outputs to ChatDev/BAEs

---

## Your Task: Critical Analysis & Solution Design

### Primary Objective

**CRITICALLY EVALUATE** the proposed Hybrid Approach (Option F) and either:
1. **Validate it** with detailed justification, OR
2. **Propose a superior alternative** with implementation details

### Required Analysis

#### 1. Systematic Critique of Hybrid Approach (Option F)

**Analyze each aspect**:

**A) API Key Control Claim** ✅
- Verify: Can we truly control API key/model with this approach?
- Challenge: Are there hidden dependencies on Copilot's API?
- Question: Do bash scripts make any external API calls we're unaware of?

**B) Fidelity Claim** ✅ "High fidelity"
- Verify: How similar is automated execution vs. interactive Copilot usage?
- Challenge: Does single-pass execution fundamentally change the workflow?
- Question: Are we losing critical aspects like iterative refinement, context awareness, or chat-based clarification?

**C) Reproducibility Claim** ✅
- Verify: Are bash scripts truly deterministic?
- Challenge: Do scripts have environment dependencies (git, specific shell versions)?
- Question: Can we guarantee same output across different systems?

**D) Scientific Validity Claim** ✅ "Medium-High"
- Verify: Is this honest comparison or are we measuring "our automation" not "GHSpec capability"?
- Challenge: How different is this from Option B (Template-Only Approach)?
- Question: Would results generalize to actual GHSpec usage by developers?

**E) Implementation Complexity** ⚠️ "Medium"
- Verify: Is 34 hours estimate realistic?
- Challenge: What are the hidden complexities (template parsing, error handling, context management)?
- Question: Are we underestimating integration challenges?

**F) Template Parsing Assumption**
- Verify: Can we reliably extract system prompts from markdown templates?
- Challenge: Templates are written for AI agents (Copilot), not Chat Completions API - do they translate cleanly?
- Question: Will template instructions like "Run `{SCRIPT}`" work when we're making API calls, not executing bash?

**G) Missing Features Analysis**
- What does Copilot provide that direct API calls don't?
  - IDE context (open files, recent changes, project structure)
  - Incremental code generation (streaming, partial completions)
  - Multi-turn conversation (clarifications, refinements)
  - Codebase awareness (symbols, imports, dependencies)
- How significant are these missing features for spec-kit workflow?

**H) Threat to Validity Deep Dive**
- If ChatDev uses 50 API calls with iteration and we use 4 single-pass calls, are we comparing:
  - Framework intelligence? (what we claim)
  - Execution strategy? (actually what differs)
- Can we separate "spec-kit's prompt quality" from "Copilot's iterative execution"?

#### 2. Alternative Solutions Exploration

**Revisit Rejected Options** with new insights:

**Could Option A (Intercept API Calls) work better?**
- Use mitmproxy or HTTP proxy to intercept requests
- Inject API key/model in proxy layer
- Let Copilot run normally, just redirect backend
- New question: Is this technically feasible? More honest than hybrid?

**Could Option B (Template-Only) be equally valid?**
- If we're extracting templates anyway, why not simplify to single API call per step?
- Reduces complexity, same API control
- New question: What do we actually lose vs. Hybrid (Option F)?

**Could we enhance Option F?**
- Add iteration logic: make multiple API calls per phase until quality threshold met
- Add context awareness: parse existing files, include in prompts
- Add streaming: process partial responses like Copilot does
- New question: Would this better approximate Copilot's behavior?

**Are there unexplored options?**
- Use GitHub Copilot API (if available) with custom keys
- Use Claude Code or other spec-kit compatible agents we CAN control
- Create minimal PoC: test single phase implementation first, validate assumptions
- Fork and modify spec-kit to add API integration points

**NEW: GitHub Copilot CLI (Option E-2) Analysis**

**Official Documentation**: https://docs.github.com/en/copilot/concepts/agents/about-copilot-cli

**What it offers**:
```bash
# Programmatic mode example
copilot -p "Create a user model with authentication" --allow-all-tools

# Could potentially work with spec-kit:
cd workspace && copilot -p "Follow spec-kit workflow: /speckit.specify Create a CRUD API" --allow-all-tools
```

**Critical Questions to Answer**:

1. **API Key Control** (CRITICAL REQUIREMENT):
   - Can we configure Copilot CLI to use our OPENAI_API_KEY_GHSPEC?
   - Or does it always use GitHub's Copilot backend with their keys?
   - **Documentation says**: Uses Copilot Pro/Business/Enterprise (GitHub's keys)
   - **Verdict**: ❌ Cannot control API key

2. **Model Control** (CRITICAL REQUIREMENT):
   - Can we force Copilot CLI to use gpt-4o-mini?
   - **Documentation says**: Default is Claude Sonnet 4, can change via /model command
   - Available models likely limited to GitHub's Copilot options
   - **Verdict**: ❌ Cannot control to use specific OpenAI model (gpt-4o-mini)

3. **Token Tracking** (CRITICAL REQUIREMENT):
   - Can we track exact token usage via OpenAI Usage API?
   - **Documentation says**: Uses "Copilot premium requests" quota (not OpenAI tokens)
   - No access to underlying OpenAI API calls
   - **Verdict**: ❌ Cannot track OpenAI tokens (different billing model)

4. **Spec-Kit Integration**:
   - Could Copilot CLI execute spec-kit's slash commands?
   - Slash commands like `/speckit.specify` are markdown instructions, not CLI commands
   - Copilot CLI has its own slash commands (/model, /feedback, /mcp)
   - **Verdict**: ⚠️ Would need adaptation, not direct compatibility

5. **Workflow Automation**:
   - Can we automate the 4-phase spec-kit workflow programmatically?
   - Yes, via programmatic mode: `copilot -p "prompt" --allow-all-tools`
   - **Verdict**: ✅ Technically possible

6. **Scientific Validity**:
   - Would this comparison be defensible?
   - We'd be comparing: ChatDev (OpenAI) vs BAEs (OpenAI) vs GHSpec (Copilot CLI with GitHub's keys/models)
   - Different backends, different token economics, different models
   - **Verdict**: ⚠️ Still problematic for fair comparison

**Comparative Analysis**:

| Criterion | Hybrid (F) | Copilot CLI (E-2) | Verdict |
|-----------|------------|-------------------|---------|
| API Key Control | ✅ Full (our key) | ❌ None (GitHub's keys) | Hybrid wins |
| Model Control | ✅ gpt-4o-mini | ❌ Claude Sonnet 4 or GitHub's options | Hybrid wins |
| Token Tracking | ✅ OpenAI Usage API | ❌ Premium requests quota | Hybrid wins |
| Ease of Use | ⚠️ Need to build adapter | ✅ Ready-made CLI | CLI wins |
| Spec-Kit Fidelity | ⚠️ Medium (automation) | ⚠️ Medium (different tool) | Tie |
| Scientific Validity | ⚠️ Lower bound | ❌ Different backends | Hybrid wins |

**Conclusion on Copilot CLI**:
While GitHub Copilot CLI is an excellent tool for development, it **does NOT solve our core requirements**:
- ❌ Cannot control API key (uses GitHub's Copilot backend)
- ❌ Cannot force gpt-4o-mini (uses Claude Sonnet 4 or GitHub's model options)
- ❌ Cannot track OpenAI tokens (different billing/quota model)

**Recommendation**: Copilot CLI is not suitable for our experiment. Stick with Hybrid Approach (Option F) or propose alternative that maintains API/model/token control.

#### 3. Experimental Design Critique

**Question the core comparison**:
- Are we comparing "frameworks" or "execution paradigms"?
  - ChatDev/BAEs: Multi-agent systems with emergent behavior
  - GHSpec: Template-guided single-agent with human iteration
- Should we instead compare:
  - All frameworks in "automated mode" (no human, deterministic)
  - All frameworks in "interactive mode" (allow human feedback)
- Is GHSpec even comparable to autonomous frameworks?

**Alternative framing**:
- What if we DON'T compare GHSpec directly to ChatDev/BAEs?
- What if we evaluate it separately as "template-based approach"?
- What if we acknowledge it's a different category and report results separately?

#### 4. Implementation Risk Assessment

**For Hybrid Approach, identify**:
- **Blockers**: Issues that could make implementation impossible
  - Template parsing might fail (format incompatibility)
  - Bash scripts might have undocumented dependencies
  - Generated code might be incomplete (missing Copilot context)
- **Challenges**: Issues that increase complexity/time
  - Error handling for 4 sequential API calls
  - Context management between phases
  - File I/O and workspace coordination
- **Unknowns**: Questions we can't answer without implementation
  - Will template prompts work as system prompts?
  - Will bash script JSON output be parseable?
  - Will generated artifacts match spec-kit's expected structure?

### Deliverables Required

#### 1. Verdict on Hybrid Approach
- [ ] **APPROVE**: Hybrid Approach is best solution → Provide detailed justification
- [ ] **REJECT**: Hybrid Approach has fatal flaws → Provide specific reasons
- [ ] **ENHANCE**: Hybrid Approach needs modifications → Provide specific improvements

#### 2. Recommended Solution
If rejecting or enhancing, provide:
- **Approach name**: Clear, descriptive label
- **Implementation strategy**: Step-by-step with code examples
- **Advantages**: Why this is better than Hybrid
- **Disadvantages**: Honest assessment of limitations
- **Estimated effort**: Hours breakdown by phase
- **Risk mitigation**: How to handle identified risks

#### 3. Scientific Framing Guidance
Provide exact wording for paper's methodology section:
- **What we're measuring**: Precise definition
- **What we're NOT measuring**: Clear exclusions
- **Limitations**: Honest threats to validity
- **Generalizability**: When do results apply vs. not apply

#### 4. Prompt Strategy (if using templates)
- **Template extraction**: Regex/parser to get system prompts from markdown
- **Context injection**: How to add spec/plan/task context to prompts
- **Format conversion**: Transform template instructions to API calls
- **Example**: Show actual template → actual API call mapping

#### 5. Validation Strategy
How to verify our implementation works:
- **Smoke test**: Single step execution, check outputs
- **Comparison test**: Run same command with Copilot vs. our adapter, compare results
- **Quality test**: Evaluate generated code quality metrics

### Critical Questions to Answer

1. **Is automated spec-kit still "spec-kit"?** Or are we creating a different system?
2. **Can we defend the comparison scientifically?** What journal reviewers will ask?
3. **What's the MINIMUM viable implementation?** Can we start simpler and iterate?
4. **Should we pilot test first?** Implement one phase, validate, before committing to full approach?
5. **Are there spec-kit variants?** Other forks, different AI agents, that might be easier to control?

### Decision Framework

Use this matrix to evaluate options:

| Criterion | Weight | Hybrid (F) | Your Alternative | Reasoning |
|-----------|--------|------------|------------------|-----------|
| API Key Control | CRITICAL | ? | ? | Must be 100% |
| Token Tracking | CRITICAL | ? | ? | Must be exact |
| Scientific Validity | HIGH | ? | ? | Must be defensible |
| Implementation Feasibility | HIGH | ? | ? | Must be completable |
| Fidelity to Spec-Kit | MEDIUM | ? | ? | Higher is better |
| Reproducibility | MEDIUM | ? | ? | Must be high |
| Code Quality | LOW | ? | ? | Should be reasonable |

Fill in ratings (1-10) with justification.

---

## Output Format

### Executive Summary (150 words)
- Your recommendation in one paragraph
- Key reasoning in bullet points

### Detailed Analysis (2000+ words)
- Systematic critique of Hybrid Approach
- Alternative solutions explored with pros/cons
- Recommended solution with full implementation plan
- Scientific framing guidance
- Risk assessment and mitigation

### Implementation Checklist
- [ ] Phase 1: X (N hours)
- [ ] Phase 2: Y (N hours)
- ...
- [ ] Total: N hours

### Code Examples
Provide actual Python code snippets for:
- Template parsing
- API call construction
- Context management
- Error handling

**Example of what we need you to validate/improve**:

```python
# Proposed template parsing approach
def _extract_outline_section(template_content: str) -> str:
    """Extract the Outline section from template to use as system prompt."""
    # Does this work? Is there a better way?
    lines = template_content.split('\n')
    in_outline = False
    outline_lines = []
    
    for line in lines:
        if line.startswith('## Outline'):
            in_outline = True
            continue
        elif in_outline and line.startswith('## '):
            break
        elif in_outline:
            outline_lines.append(line)
    
    return '\n'.join(outline_lines)

# Proposed API call approach  
def _execute_phase(self, phase: str, command: str, context: Dict) -> str:
    """Execute one phase with OpenAI API."""
    template = self._load_template(f"templates/commands/{phase}.md")
    system_prompt = self._extract_outline_section(template)
    
    # Question: Should we pre-process {SCRIPT} references?
    # Question: How do we inject context (spec content, plan content)?
    
    response = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {os.getenv('OPENAI_API_KEY_GHSPEC')}"},
        json={
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": command}
            ],
            "temperature": 0
        }
    )
    
    return response.json()["choices"][0]["message"]["content"]

# Proposed workflow approach
def execute_step(self, step_num: int, command_text: str) -> Dict:
    """Execute one experiment step."""
    # 1. Run bash script for setup
    result = subprocess.run(
        [f"{self.framework_dir}/scripts/bash/create-new-feature.sh", "--json", command_text],
        cwd=self.workspace_path,
        capture_output=True,
        text=True
    )
    feature_data = json.loads(result.stdout)
    
    # 2. Phase 1: Specify
    spec_content = self._execute_phase("specify", command_text, {})
    Path(feature_data["SPEC_FILE"]).write_text(spec_content)
    
    # 3. Phase 2: Plan
    plan_content = self._execute_phase("plan", command_text, {"spec": spec_content})
    # ... and so on
    
    # Question: Is this the right level of abstraction?
    # Question: Are we missing critical error handling?
    # Question: How do we handle template-script coordination?
```

**Your task**: Critique this code, propose improvements, or suggest entirely different approach.

### Scientific Framing Template
Exact text we can use in the paper's methodology section.

---

**IMPORTANT**: Be ruthlessly critical. If Hybrid Approach has flaws, expose them. If there's a better solution, propose it with full details. We need the BEST solution, not just a workable one. The experiment's scientific validity depends on getting this right.

---

## Key Resources for Your Analysis

### Spec-Kit Fork Repository
- **Path**: `/home/amg/projects/uece/baes/spec-kit` (analyzed in detail)
- **Key findings documented in**: `docs/ghspec_fork_analysis.md` (3,500 words)

### Template Examples (Real Content)
- **Specify template**: 200 lines, includes validation checklist generation
- **Plan template**: 100 lines, includes research phase and design artifacts
- **Tasks template**: 100 lines, includes user story organization and parallel execution
- **Implement template**: 200 lines, includes TDD approach and project setup

### Bash Script Outputs (Verified)
- All scripts support `--json` flag for programmatic parsing
- Scripts work with or without git (fallback to directory-based feature tracking)
- JSON outputs include absolute paths to all relevant files

### Open Questions That Need Your Expert Analysis
1. **Template Compatibility**: Can markdown templates designed for interactive AI agents work as Chat Completions system prompts?
2. **Context Preservation**: How do we pass state between phases without Copilot's IDE context?
3. **Quality Equivalence**: Will single-pass API calls produce comparable quality to iterative Copilot refinement?
4. **Experimental Validity**: Are we measuring "spec-kit framework capability" or "our automation capability"?
5. **Better Alternatives**: Is there a fundamentally different approach we haven't considered?

### Your Decision Criteria
- **CRITICAL**: Must maintain API key/model control and exact token tracking
- **HIGH**: Must be scientifically defensible in peer-reviewed publication
- **HIGH**: Must be implementable within reasonable timeframe (< 50 hours)
- **MEDIUM**: Should maintain fidelity to spec-kit's intended workflow
- **LOW**: Code quality of generated outputs (measured separately)

### Success = Finding the Truth
Your success is measured by finding the RIGHT answer, not by validating our proposed solution. If the Hybrid Approach is flawed, say so clearly. If there's a better approach, propose it with full implementation details. We value critical thinking over consensus.
