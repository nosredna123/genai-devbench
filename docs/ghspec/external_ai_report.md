
# GHSpec Adapter Implementation Strategy — Critical Evaluation (Enhanced Hybrid)

## Executive Summary

The **Hybrid Approach (Option F)** proposes to integrate GitHub’s Spec‑Kit with an OpenAI API–driven backend to simulate GitHub Copilot’s role in our experiments. It solves **API control**, **model control**, and **token tracking** but, as originally framed, lacks **iterative refinement** and **context‑aware parity** with autonomous frameworks (ChatDev/BAEs).

**Verdict:** **APPROVE with enhancements** — adopt an **Enhanced Hybrid**: keep Spec‑Kit’s structure (spec → plan → tasks → implement), drive all AI calls via our OpenAI API (`OPENAI_API_KEY_GHSPEC`, `gpt-4o-mini`), and add **agent‑like loops** (clarification handling, validation‑driven bugfix, limited re‑planning). This preserves fidelity to Spec‑Kit while enforcing **methodological parity** and **scientific validity**.

**Why this wins**
- Full API/model control and exact token accounting
- High fidelity to spec‑driven workflow (Spec‑Kit artifacts, file structure)
- Iteration + self‑repair → parity with ChatDev/BAEs methodology
- Reproducible, deterministic runs (temperature≈0, pinned commits)
- Feasible (~35h), extensible, defensible in peer‑review

---

## 1) Systematic Critique of the Basic Hybrid (Option F)

### Fidelity to Copilot workflow
- **Strength:** Mirrors Spec‑Kit phases; uses same artifacts (spec.md, plan.md, tasks.md).
- **Gaps:** Real Copilot is **IDE‑interactive** (incremental, context from open files). A single‑pass API call per phase omits **interactive refinement** and **file‑scoped context**, risking quality drift.
- **Fix:** Use per‑task prompts with **file context** and **sequential application**, plus **post‑task checks**.

### Reproducibility
- **Strength:** Deterministic prompts, pinned model/version, controlled environment.
- **Caveat:** Must manage **stateful context** (spec/plan/tasks + evolving codebase) across steps; otherwise determinism ≠ correctness.
- **Fix:** Persist artifacts; pass **current file contents** into prompts; pin seeds/temperature.

### API/Model Control & Token Tracking
- **Strength:** 100% control; usage via **OpenAI Usage API** for exact tokens per step/run.
- **Action:** Wrap each step with timestamps and aggregate usage; log per‑call tokens if desired.

### Scientific Validity (parity)
- **Risk:** One‑shot generation vs. ChatDev/BAEs’ **iterative** nature → apples vs oranges.
- **Fix:** Add **iteration & repair loop**: HITL micro‑answers (fixed clarification text), validation‑triggered **bugfix** attempt, limited **re‑planning** if needed.

### Implementation Complexity
- **Realistic:** Medium; hidden work in task parsing, safe code application, error handling, context windows.
- **Mitigation:** Sequential, **file‑at‑a‑time** edits; deterministic prompts; conservative retries.

---

## 2) Parity With Autonomous Frameworks

To match ChatDev/BAEs methodology:
1. **Iteration**: After implement, run validations → on failure, generate **bugfix tasks** and re‑invoke model (bounded attempts).
2. **Context carryover**: Persist and inject **spec/plan/tasks + current code** into prompts for subsequent steps.
3. **HITL emulation**: Detect model clarifications → reply with **fixed expanded specification**; count as HITL.
4. **Comparable loops**: Limit clarifications and fix‑attempts similarly to ChatDev runner limits.

---

## 3) Alternatives (Why Not…)

- **Automate Copilot in VS Code (headless):** Max fidelity, but **no API/model control**, **no token counts**, brittle UI automation, ToS risks, poor reproducibility.
- **Intercept Copilot API traffic:** Legally/technically fragile; cannot enforce model parity; no token telemetry.
- **Use alternate agent CLIs (Claude/Cursor):** Better headless support but **breaks Copilot parity** and model control; adds third‑party variability.
- **Template‑only / mock execution:** Useful for harness tests, **not scientific** (no AI behavior).

**Conclusion:** Enhanced Hybrid is the optimal middle ground: fidelity to Spec‑Kit’s **process**, with agent‑like parity and full measurement.

---

## 4) Recommended Solution — **Enhanced Hybrid GHSpec Adapter**

**Core idea:** Use Spec‑Kit structure for **spec → plan → tasks**, then implement **task‑by‑task** via OpenAI API with **file context**, add **clarification** handling and **validation‑driven bugfix** loop. Persist artifacts, enforce deterministic settings, and track tokens via the Usage API.

**Meets requirements:**
- **API Key Control:** `OPENAI_API_KEY_GHSPEC`
- **Model Control:** `gpt-4o-mini` (config)
- **Token Tracking:** Usage API; aggregate per step
- **Fair Comparison:** Iteration, HITL, and repair for parity

---

## 5) Implementation Plan (≈35 hours)

### Phase 1 — Research & Design (3–5h)
- Map Spec‑Kit CLI/artifacts; identify prompt patterns for spec/plan/tasks.
- Define HITL policy and validation hooks.

### Phase 2 — Env Setup (3–4h)
- Adapter `start()`: clone/pin Spec‑Kit; (optional) venv and deps.
- Ensure workspace structure; logging scaffolding.

### Phase 3 — Spec & Plan (4–6h)
- **Step 1 only:** Generate `spec.md`, `plan.md`, and `tasks.md` via API using Spec‑Kit‑style prompts. Persist to workspace.

### Phase 4 — Implement Orchestration (8–12h)
- Parse tasks; for each task:
  - Build prompt with **spec/plan + target file current content**.
  - Generate code; **apply file‑level** updates (overwrite strategy).
  - Detect clarifications → respond with fixed expanded spec; count HITL.
- End of step: runner performs validations. On failures:
  - Create **bugfix tasks** from failure logs; one bounded fix round.

### Phase 5 — Health & Shutdown (1–2h)
- `health_check()`: trivial (workspace/ready flag).
- `stop()`: cleanup/logging.

### Phase 6 — Testing & Validation (4–6h)
- Smoke test (tiny project); token telemetry check; deterministic reruns.
- Failure‑injection test → bugfix loop executes once.

**Total:** ~35h (buffer included).

---

## 6) Prompt Strategy

### A. Spec / Plan / Tasks (Step 1)
- **Spec prompt (system):** “You are a **Spec‑Driven** analyst. Produce a business‑facing spec: user journeys, acceptance criteria, assumptions. Avoid implementation details.”
- **Plan prompt (system):** “You are a lead architect. Based on the spec, produce a technical plan (stack, modules, APIs, data model, tests).”
- **Tasks prompt (system):** “You are a project planner. Break plan into implementable tasks (small, file‑scoped). Order for MVP first.”

### B. Implement (Per Task)
**System:** “You are ‘Copilot‑style’ code assistant. You will modify exactly one file per task.”  
**User:** Include: spec excerpt, **relevant plan section**, **task text**, **current file content** (or blank), constraints (“keep style, tests must pass”). Ask for **full file content** output only.

### C. HITL & Bugfix
- **HITL:** If the model asks, respond with **fixed expanded spec**.
- **Bugfix prompt:** Provide failing test message + current file(s). Instruct to fix code and output updated file(s).

---

## 7) API Orchestration

- Use **Chat Completions** (`temperature=0`) for determinism.  
- Sequential calls: spec → plan → tasks → implement (per task).  
- **Token usage:** wrap step with timestamps → query **Usage API** for exact in/out tokens.  
- Error handling: retry (≤3) on transient API errors; clear logs for traceability.

---

## 8) Code Examples (pseudo‑Python)

```python
def build_task_prompt(task, spec_md, plan_md, file_path):
    content = Path(file_path).read_text() if Path(file_path).exists() else ""
    system = ("You are a Copilot-style assistant. Modify ONE file to satisfy the task. "
              "Output ONLY the full final content of that file.")
    user = (
        f"SPEC:\n{truncate(spec_md, 5000)}\n\n"
        f"PLAN:\n{truncate(plan_md, 3000)}\n\n"
        f"TASK:\n{task['description']}\n\n"
        f"FILE: {file_path}\nCURRENT CONTENT:\n```\n{content}\n```"
        "\nINSTRUCTIONS: Implement the task in this file. Keep style. "
        "If unclear, make reasonable assumptions. Output just the file content."
    )
    return [{"role": "system", "content": system},
            {"role": "user", "content": user}]
```

```python
def execute_step(self, step_num, command_text):
    start_ts = int(time.time()); hitl = 0
    if step_num == 1:
        spec_md = gen_spec(command_text); write("spec.md", spec_md)
        plan_md = gen_plan(spec_md); write("plan.md", plan_md)
        tasks = gen_tasks(spec_md, plan_md); write("tasks.md", fmt(tasks))
    else:
        append_to_spec(command_text)  # or keep spec fixed; prefer delta-tasks
        tasks = gen_delta_tasks(command_text, read("spec.md"), read("plan.md"))

    for t in tasks:
        msgs = build_task_prompt(t, read("spec.md"), read("plan.md"), t["file"])
        out = call_openai(msgs)
        if needs_clarification(out):
            hitl += 1
            msgs.append({"role":"assistant","content": out})
            msgs.append({"role":"user","content": read("expanded_spec.txt")})
            out = call_openai(msgs)
        write(t["file"], extract_file_content(out))

    # validator runs outside adapter; optionally perform one bugfix cycle:
    if not self.runner_validation_passed():
        fix_tasks = derive_bugfix_tasks(self.validation_report())
        for ft in fix_tasks:
            msgs = build_bugfix_prompt(ft, ...); out = call_openai(msgs)
            write(ft["file"], extract_file_content(out))

    tokens_in, tokens_out = self.fetch_usage_from_openai(
        api_key_env_var="OPENAI_API_KEY_GHSPEC",
        start_timestamp=start_ts,
        end_timestamp=int(time.time()),
        model=self.config.get("model")
    )
    return {"success": True, "hitl_count": hitl,
            "tokens_in": tokens_in, "tokens_out": tokens_out}
```

---

## 9) Scientific Framing (Paper‑Ready Text)

**Method.** We evaluate a **Spec‑Driven AI coding approach (GHSpec)** against autonomous frameworks (ChatDev, BAEs) on a six‑step software evolution task. Our GHSpec adapter executes the official Spec‑Kit workflow (spec → plan → tasks → implement) fully automatically. All AI calls use the same model (`gpt‑4o‑mini`) and our key (`OPENAI_API_KEY_GHSPEC`). The adapter generates a project specification and technical plan from the step description, derives tasks, and implements tasks **file‑by‑file** with access to the evolving codebase. When the model poses clarification questions, we supply a fixed, comprehensive clarification (no human input). After implementation, validations run; if failures occur, the adapter attempts a **single bug‑fix round** informed by failure logs. We record **time** and **token usage** via the OpenAI Usage API for each step.

**What we measure.** Correctness, completeness, CRUDe/ESR scores, time, token usage, and autonomy (HITL count, internal fix attempts).

**Limitations.** We emulate Copilot with direct API calls to ensure control and telemetry; thus, our GHSpec results reflect an **idealized Copilot‑style process** rather than the proprietary Copilot service. Interactive micro‑edits and model differences may cause deviations from real Copilot usage. We mitigate by preserving Spec‑Kit’s structure, providing full code/spec context, and using a strong general model.

**Threats to validity.** Internal: prompt/adapter errors could bias outcomes; mitigated via tests and deterministic settings. External: results may vary on different domains; mitigated by public release of artifacts and seeds. Construct: autonomy metric interpretation differs across paradigms; we count only explicit clarifications and controlled repair loops.

---

## 10) Decision Matrix

| Criterion | Weight | Basic Hybrid | **Enhanced Hybrid (Rec.)** | Copilot IDE Automation |
|---|---:|:---:|:---:|:---:|
| API Key Control | Critical | 10 | **10** | 0 |
| Token Tracking | Critical | 10 | **10** | 1 |
| Scientific Validity (parity) | High | 6 | **9** | 5 |
| Implementation Feasibility | High | 8 | **8** | 2 |
| Fidelity to Spec‑Kit | Medium | 6 | **7** | **10** |
| Reproducibility | Medium | 9 | **9** | 3 |
| Code Quality (expected) | Low | 7 | **8** | 6 |

**Recommendation:** **Adopt Enhanced Hybrid** — best aggregate score with parity and control.

---

## 11) Implementation Checklist

- [ ] Phase 1: Research & Design (3–5h)  
- [ ] Phase 2: Env Setup (3–4h)  
- [ ] Phase 3: Spec/Plan/Tasks (4–6h)  
- [ ] Phase 4: Implement Orchestration + HITL + Bugfix (8–12h)  
- [ ] Phase 5: Health/Shutdown (1–2h)  
- [ ] Phase 6: Testing/Validation (4–6h)  
- [ ] Total ≈ **35h**

---

## 12) Risks & Mitigations

- **Template/Context mismatch →** Use file‑scoped prompts; include spec/plan excerpts; add truncation safeguards.  
- **Large context windows →** Task granularity; summarize spec/plan per task.  
- **Flaky outputs →** Deterministic settings; bounded retries; one bugfix cycle.  
- **Fairness concerns →** Align clarification/fix limits with ChatDev/BAEs; same model across frameworks; identical validation harness.

---

## 13) What This Is *Not*

- Not the proprietary Copilot service; not UI‑driven; not a human‑in‑the‑loop study.  
- Not measuring prompt‑engineering prowess; we use **Spec‑Kit’s structure** to avoid cherry‑picked prompts.

---

## 14) Conclusion

**Approve with enhancements.** The Enhanced Hybrid GHSpec adapter preserves Spec‑Kit’s structured methodology while adding agent‑like iteration for **methodological parity** with ChatDev/BAEs. It ensures **API/model control**, precise **token telemetry**, **reproducibility**, and a defensible basis for peer‑reviewed comparison.
