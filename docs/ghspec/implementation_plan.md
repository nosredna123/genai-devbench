# GHSpec Adapter Implementation — Next Steps

**Decision Date**: October 15, 2025  
**Status**: ✅ **APPROVED — Enhanced Hybrid Approach**  
**Start Date**: Immediately  
**Estimated Completion**: November 5, 2025 (3 weeks)

---

## 🎯 What We're Building

**Enhanced Hybrid GHSpec Adapter** that:
- Uses Spec-Kit's bash scripts for project management
- Makes direct OpenAI API calls with our key/model
- Implements **task-by-task** with file-level context
- Includes **iteration loops** (HITL + bugfix) for fair comparison
- Achieves methodological parity with ChatDev/BAEs

---

## 🔑 Critical Improvements Over Original Plan

### What Changed (Based on External AI Analysis)

| Original Plan | Enhanced Plan | Why It Matters |
|---------------|---------------|----------------|
| 4 API calls per step (one per phase) | **Task-by-task API calls** | Matches Copilot's incremental nature |
| No file context | **Current file content in prompts** | Prevents conflicts/overwrites |
| No iteration | **Clarification + bugfix loops** | Fair comparison with ChatDev/BAEs |
| No HITL handling | **Fixed expanded spec responses** | Counts HITL like other frameworks |
| External validation only | **Validation-driven repair** | Agent-like self-correction |

**Bottom Line**: Enhanced version is **scientifically defensible**, original would likely be rejected in peer review.

---

## 📋 Implementation Phases

### Phase 1: Research & Design (4-5 hours)
**Goal**: Finalize prompt designs and workflow logic

**Tasks**:
- [ ] Study Spec-Kit CLI behavior (create-new-feature.sh, setup-plan.sh)
- [ ] Design prompt templates for each phase:
  - [ ] Specify: Business spec generation
  - [ ] Plan: Technical architecture
  - [ ] Tasks: Breakdown into implementable units
  - [ ] Implement: Per-task code generation
  - [ ] Bugfix: Error-driven correction
- [ ] Define HITL policy:
  - [ ] Write expanded specification text (`config/hitl/expanded_spec.txt`)
  - [ ] Define clarification detection patterns
- [ ] Document validation hooks (where adapter queries runner for results)

**Deliverables**:
- Prompt template designs (markdown documents)
- HITL expanded specification file
- Workflow diagram with API call points

---

### Phase 2: Environment Setup (3-4 hours)
**Goal**: Adapter can clone Spec-Kit and setup workspace

**Tasks**:
- [ ] Implement `start()` method:
  - [ ] Clone Spec-Kit from configured URL
  - [ ] Checkout specific commit hash
  - [ ] Verify commit matches config
  - [ ] Setup workspace directory structure
- [ ] Initialize logging with run_id tracking
- [ ] Create artifact storage directories:
  - [ ] `specs/NNN-feature-name/`
  - [ ] `specs/NNN-feature-name/spec.md`
  - [ ] `specs/NNN-feature-name/plan.md`
  - [ ] `specs/NNN-feature-name/tasks.md`
- [ ] Test: Verify repo clones and workspace is ready

**Deliverables**:
- Working `start()` implementation
- Workspace structure validation
- Unit tests for environment setup

---

### Phase 3: Spec/Plan/Tasks Generation (5-7 hours)
**Goal**: Generate first 3 phases via OpenAI API

**Tasks**:
- [ ] Implement `_execute_phase("specify")`:
  - [ ] Load specify template
  - [ ] Build prompt with user command
  - [ ] Call OpenAI API (track start timestamp)
  - [ ] Detect clarifications → HITL response
  - [ ] Save to `spec.md`
- [ ] Implement `_execute_phase("plan")`:
  - [ ] Load plan template
  - [ ] Build prompt with spec content
  - [ ] Call OpenAI API
  - [ ] Save to `plan.md`
- [ ] Implement `_execute_phase("tasks")`:
  - [ ] Load tasks template
  - [ ] Build prompt with spec + plan
  - [ ] Call OpenAI API
  - [ ] Parse response into structured task list
  - [ ] Save to `tasks.md`
- [ ] Implement `_needs_clarification()` detector
- [ ] Implement `_handle_clarification()` responder
- [ ] Track tokens via Usage API for all calls
- [ ] Test: Run single step, verify artifacts generated

**Deliverables**:
- Working spec/plan/tasks generation
- Clarification handling (HITL emulation)
- Token tracking validated
- Integration test with simple prompt

---

### Phase 4: Task-Level Implementation (10-14 hours)
**Goal**: Implement code task-by-task with file context

**Tasks**:
- [ ] Implement `_parse_tasks()`:
  - [ ] Extract task list from tasks.md
  - [ ] Parse file paths, descriptions, acceptance criteria
  - [ ] Return structured list of task dictionaries
- [ ] Implement `_build_task_prompt()`:
  - [ ] Extract relevant spec sections for this task
  - [ ] Extract relevant plan sections for this task
  - [ ] Read current file content (if exists)
  - [ ] Build context-rich prompt
  - [ ] Truncate if needed (context window management)
- [ ] Implement `_extract_relevant_section()`:
  - [ ] Use semantic matching or keywords
  - [ ] Return excerpt (not full document)
- [ ] Implement `_read_file_if_exists()`:
  - [ ] Check if file exists in workspace
  - [ ] Return content or empty string
- [ ] Implement `_save_file()`:
  - [ ] Extract code from API response
  - [ ] Write to workspace (create dirs if needed)
  - [ ] Log file modification
- [ ] Implement task iteration loop in `execute_step()`:
  - [ ] For each task in task list
  - [ ] Build prompt → call API → save file
  - [ ] Handle clarifications per task
- [ ] Test: Run with multi-file project, verify all files created

**Deliverables**:
- Working task-by-task implementation
- File context passing validated
- Multi-file project test passing

---

### Phase 5: HITL & Bugfix (6-8 hours)
**Goal**: Add iteration loops for parity

**Tasks**:
- [ ] Implement `_get_validation_report()`:
  - [ ] Interface to query runner for validation results
  - [ ] Parse test failures, compilation errors, etc.
- [ ] Implement `_derive_bugfix_tasks()`:
  - [ ] Take validation errors
  - [ ] Create task list for fixes (max 3)
  - [ ] Prioritize by severity
- [ ] Implement `_build_bugfix_prompt()`:
  - [ ] Include error message
  - [ ] Include current file content
  - [ ] Include spec context
  - [ ] Request specific fix
- [ ] Implement `_attempt_bugfix_cycle()`:
  - [ ] Get validation failures
  - [ ] Derive bugfix tasks
  - [ ] For each task: prompt → API → save
  - [ ] Bounded to 1 cycle (no infinite loops)
- [ ] Update `execute_step()` to call bugfix after validation
- [ ] Test: Inject failure → verify bugfix attempt → verify logs

**Deliverables**:
- Working bugfix loop
- Validation integration
- Failure injection test passing

---

### Phase 6: Testing & Validation (5-7 hours)
**Goal**: Ensure quality and reproducibility

**Tasks**:
- [ ] Create smoke test:
  - [ ] Minimal project (e.g., "Build a calculator")
  - [ ] Run through adapter
  - [ ] Verify artifacts created
  - [ ] Verify code files present
- [ ] Test token telemetry:
  - [ ] Verify Usage API returns data
  - [ ] Verify aggregation across steps
  - [ ] Verify per-step tracking
- [ ] Test determinism:
  - [ ] Run same prompt 3 times with same seed
  - [ ] Compare outputs for consistency
  - [ ] Document any variance
- [ ] Test clarification handling:
  - [ ] Craft prompt that triggers clarification
  - [ ] Verify HITL count increments
  - [ ] Verify expanded spec is used
- [ ] Test bugfix loop:
  - [ ] Inject validation failure
  - [ ] Verify bugfix tasks created
  - [ ] Verify fix attempt logged
- [ ] Validate artifact format:
  - [ ] spec.md matches Spec-Kit structure
  - [ ] plan.md matches Spec-Kit structure
  - [ ] tasks.md matches Spec-Kit structure
  - [ ] Code follows expected patterns

**Deliverables**:
- Test suite passing (unit + integration)
- Determinism report
- Token tracking validation
- Artifact format validation

---

## 🎯 Success Criteria

### Must Have
- [ ] All 3 critical requirements met:
  - [ ] ✅ Uses OPENAI_API_KEY_GHSPEC
  - [ ] ✅ Uses gpt-4o-mini from config
  - [ ] ✅ Tracks tokens via Usage API
- [ ] Task-by-task implementation (not single-pass)
- [ ] File context in every task prompt
- [ ] HITL emulation working
- [ ] Bugfix loop working (bounded)
- [ ] Artifacts match Spec-Kit format
- [ ] Deterministic with seed parameter
- [ ] Integration tests pass

### Should Have
- [ ] Smart truncation for context management
- [ ] Relevant section extraction (not full docs)
- [ ] Comprehensive logging
- [ ] Error handling and retries
- [ ] Unit test coverage >80%

### Nice to Have
- [ ] Parallel task execution (if safe)
- [ ] Caching of spec/plan to reduce redundancy
- [ ] Detailed token breakdown per task
- [ ] Performance metrics (time per task)

---

## 📊 Progress Tracking

**Overall Progress**: 0% (Not Started)

| Phase | Hours | Status | Completion |
|-------|-------|--------|------------|
| Phase 1: Research & Design | 4-5h | ⏳ Not Started | 0% |
| Phase 2: Environment Setup | 3-4h | ⏳ Not Started | 0% |
| Phase 3: Spec/Plan/Tasks | 5-7h | ⏳ Not Started | 0% |
| Phase 4: Task Implementation | 10-14h | ⏳ Not Started | 0% |
| Phase 5: HITL & Bugfix | 6-8h | ⏳ Not Started | 0% |
| Phase 6: Testing | 5-7h | ⏳ Not Started | 0% |

**Total**: 33-45 hours (mean: 39h) → ~1 week full-time or 3 weeks part-time

---

## 🚨 Critical Risks (From External AI Analysis)

### Risk 1: Context Window Limits
**Mitigation**: Extract relevant sections only, implement smart truncation

### Risk 2: Bugfix Loop Ineffectiveness  
**Mitigation**: Allow up to 3 bugfix tasks, prioritize by severity, accept limitation

### Risk 3: Template Fidelity Loss
**Mitigation**: Base prompts on template structure, validate artifact formats

### Risk 4: Determinism Challenges
**Mitigation**: Use seed parameter, pin model version, test variance

---

## 📖 Reference Documents

- **Decision Analysis**: `docs/final_ghspec_decision.md` (This analysis)
- **External AI Report**: `docs/GHSpec_Enhanced_Hybrid_Report.md`
- **Original Analysis**: `docs/ghspec_fork_analysis.md`
- **Research Prompt**: `docs/ghspec_research_prompt.md`
- **Spec-Kit Location**: `/home/amg/projects/uece/baes/spec-kit`

---

## 🎬 Getting Started

### Today (Phase 1 Start)

1. **Read Spec-Kit documentation**:
   ```bash
   cd /home/amg/projects/uece/baes/spec-kit
   cat README.md
   cat templates/commands/specify.md
   cat templates/commands/plan.md
   cat templates/commands/tasks.md
   cat templates/commands/implement.md
   ```

2. **Test bash scripts manually**:
   ```bash
   cd /tmp/test-workspace
   /home/amg/projects/uece/baes/spec-kit/scripts/bash/create-new-feature.sh \
     --json "Build a calculator app"
   ```

3. **Design first prompt** (specify phase):
   - Create `docs/prompts/ghspec_specify_template.md`
   - Include: role definition, output format, constraints
   - Test with manual API call

4. **Write expanded specification**:
   - Create `config/hitl/ghspec_expanded_spec.txt`
   - Comprehensive feature requirements
   - Used for all HITL responses

### This Week (Phases 2-3)

- Implement `start()` method
- Implement spec/plan/tasks generation
- Validate token tracking works
- Run first end-to-end test

### Next Week (Phases 4-6)

- Implement task-by-task code generation
- Add HITL and bugfix loops
- Complete testing suite
- Integration with experiment framework

---

## ✅ What Makes Enhanced Hybrid the Best Option

### Comparison Summary

| Approach | API Control | Scientific Parity | Feasibility | **Score** |
|----------|-------------|-------------------|-------------|-----------|
| **Enhanced Hybrid** | ✅ Perfect | ✅ High | ✅ Feasible | **9.1/10** 🏆 |
| Basic Hybrid (Original) | ✅ Perfect | ⚠️ Medium | ✅ Feasible | 7.8/10 |
| Copilot IDE Automation | ❌ None | ✅ Perfect | ❌ Brittle | 3.4/10 |
| Copilot CLI | ❌ None | ⚠️ Medium | ⚠️ Partial | 4.2/10 |

**Why Enhanced Hybrid Wins**:
1. ✅ Solves all 3 critical requirements (API key, model, tokens)
2. ✅ Achieves methodological parity (iteration, HITL, repair)
3. ✅ Maintains Spec-Kit fidelity (structure, workflow, artifacts)
4. ✅ Feasible in reasonable time (~39 hours)
5. ✅ Independently validated by external AI
6. ✅ Defensible in peer review with honest framing

---

**Status**: ✅ **READY TO START IMPLEMENTATION**  
**Next Action**: Begin Phase 1 (Research & Design)  
**Questions?**: Review `docs/final_ghspec_decision.md` for full analysis
