---
title: "BAEs Experiment Specification"
project: "baes_experiment"
version: "1.0"
authors: ["Anderson Martins Gomes"]
created: "2025-10-08"
license: "CC BY 4.0"
description: >
  Specification of the automated experimental framework designed to evaluate
  BAEs, ChatDev, and GitHub Spec-kit in a six-step academic-domain scenario.
---

# 🧠 BAEs Experiment Specification (`baes_experiment`)

## 1. Purpose

This project provides a **reproducible automation framework** for comparing three large-language-model–driven software generation systems:

- **BAEs (Business Autonomous Entities)**
- **ChatDev** ([OpenBMB/ChatDev](https://github.com/OpenBMB/ChatDev))
- **GitHub Spec-kit** ([github/spec-kit](https://github.com/github/spec-kit))

Each framework is tested under **identical natural-language instructions** to build and evolve a **complete full-stack web application** — backend CRUD API + web UI — across six evolution steps.

The goal is to measure:
- **Autonomy**
- **Token and latency efficiency**
- **Functional correctness**
- **Continuity and downtime**

using a **fully deterministic orchestration** process.

---

## 2. Repository Structure

```
baes_experiment/
├── specification.md
├── config/
│   ├── experiment.yaml
│   ├── prompts/
│   │   ├── step_1.txt … step_6.txt
│   └── hitl/
│       └── expanded_spec.txt
├── adapters/
│   ├── base_adapter.py
│   ├── baes_adapter.py
│   ├── chatdev_adapter.py
│   └── ghspec_adapter.py
├── orchestrator/
│   ├── run_controller.py
│   ├── single_run.py
│   ├── hitl_policy.py
│   ├── tests_api.py
│   ├── tests_ui.py
│   ├── zdi_probe.py
│   └── metrics/
│       ├── local_logger.py
│       ├── usage_api.py
│       ├── aggregate.py
│       └── summarize.py
├── runners/
│   ├── run_experiment.sh
│   └── docker/
│       ├── docker-compose.baes.yml
│       ├── docker-compose.chatdev.yml
│       └── docker-compose.ghspec.yml
└── runs/
    ├── baes/
    ├── chatdev/
    └── ghspec/
```

---

## 3. Six-Step Academic Scenario

| Step | Command | Deliverable |
|------|----------|-------------|
| **1** | “Create a new entity called **Student** with attributes *name* and *age*. Build a **complete web application** (backend CRUD API + web interface) allowing users to create, view, update, and delete students.” | Full module |
| **2** | “Add a new field called **email** to Student. Update the database, API, and **web interface** without data loss or downtime.” | Schema migration |
| **3** | “Create **Course** with *title* and *level*, and extend the app to manage courses through API and UI.” | Second module |
| **4** | “Relate **Student** and **Course** (many-to-many). Add API and UI for enrollment management.” | Cross-entity integration |
| **5** | “Create **Teacher** with *name* and *department* and extend the web app accordingly.” | Third module |
| **6** | “Relate **Teacher** and **Course** (many-to-many). Add assignment screens and endpoints.” | Full tri-entity graph |

Each command is executed identically for all frameworks.

---

## 4. Framework CLI Contract

All frameworks must satisfy the following **uniform contract** (directly or via adapter):

```bash
framework start --run-id <RID> --port-api <P1> --port-ui <P2>
framework command --run-id <RID> --step <N> --text "<command>"
framework health --api http://localhost:<P1> --ui http://localhost:<P2>
framework stop --run-id <RID>
```

### Ports
| Framework | API Port | UI Port |
|------------|-----------|---------|
| BAEs | 8001 | 3001 |
| ChatDev | 8002 | 3002 |
| GitHub Spec-kit | 8003 | 3003 |

Each run is isolated (fresh environment and database).

---

## 5. Deterministic HITL Policy

### Description
When a clarification is required, the orchestrator sends **one fixed clarification paragraph** (`config/hitl/expanded_spec.txt`).

```text
Use Python 3.11 and SQLite. Implement full CRUD APIs in FastAPI with JSON payloads.
Provide a functional web UI (Streamlit, React, or Flask templates) connected to these APIs.
Apply automatic schema migration without data loss. Keep routes stable.
Maintain continuous service. Model Student–Course and Teacher–Course as many-to-many.
Render minimal forms/tables. Evolve incrementally, not from scratch.
```

### Rules
- Maximum **k = 2 clarifications per step**  
- Each clarification has **HEU = 3**  
- Logged in `hitl_events.jsonl` with timestamp and SHA-1 hash  
- Ensures **zero randomness** and **identical feedback across frameworks**

### Implementation
See `orchestrator/hitl_policy.py`, class `ExpandedSpecHITLPolicy`.

---

## 6. Metrics

| Category | Metric | Description |
|-----------|---------|-------------|
| **Interaction** | `UTT` | Utterance count |
|  | `HIT` | Human interventions |
|  | `AUTR` | Autonomy rate = 1 − HIT/6 |
|  | `HEU` | Weighted effort |
| **Efficiency** | `TOK_IN`, `TOK_OUT` | Token usage |
|  | `T_WALL` | Wall-clock runtime |
| **Quality** | `CRUDe` | CRUD coverage |
|  | `ESR` | Endpoint success rate |
|  | `MC` | Migration continuity |
|  | `ZDI` | Zero-downtime incidents |
| **Composite** | `Q*` | 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC |
|  | `AEI` | AUTR / log(1 + TOK_IN) |

All metrics are stored per step and aggregated across runs.

---

## 7. Stopping Rule

The orchestrator repeats runs until **95% confidence intervals** for AUTR, TOK_IN, T_WALL, CRUDe, ESR, MC all have **≤10% half-width**.

- Minimum 5 runs  
- Maximum 25 runs  
- Stopping criterion ensures precision without excess cost.

---

## 8. Usage API Integration

Each framework uses a unique **OpenAI API key**:

| Framework | Key Name |
|------------|-----------|
| BAEs | `token-tracker-baes` |
| ChatDev | `token-tracker-chatdev` |
| GitHub Spec-kit | `token-tracker-github_spec` |

### Query Example
```bash
curl -X 'GET' "https://api.openai.com/v1/usage?date=YYYY-MM-DD&user_public_id=$ID"      -H "Authorization: Bearer $ADMIN_KEY"      -H "OpenAI-Organization: $ORG_ID"
```

- **Same project**, distinct keys → separation via `user_public_id`  
- Logged alongside local token data  
- All times recorded in **UTC**

---

## 9. Validation & Testing

### API Tests
Performed after every step:
```bash
POST /students
GET /students/{id}
PATCH /students/{id}
DELETE /students/{id}
...
POST /enroll, /assign
```

### UI Tests
- Expect HTTP 200 for main pages (`/students`, `/courses`, `/teachers`)
- HTML must contain key labels (“Create Student”, “Courses”, etc.)

### Downtime Probe
`zdi_probe.py` checks every 5 seconds → `ZDI` metric.

---

## 10. Artifacts per Run

| File | Description |
|------|--------------|
| `metrics.json` | All measured values |
| `hitl_events.jsonl` | HITL logs |
| `api_spec.json` | OpenAPI dump |
| `ui_snapshot.html` | UI capture |
| `db_snapshot.sqlite` | Database snapshot |
| `usage_api.json` | Raw OpenAI usage data |
| `stdout.log` | Framework logs |
| `commit.txt` | Repo SHA |
| `run.tar.gz` | Archived workspace |

**No artifacts reused between runs.**

---

## 11. Automation Flow

```bash
./runners/run_experiment.sh all
```

Each iteration:
1. Clone framework repo and checkout pinned commit.  
2. Create isolated Python 3.11 venv.  
3. Launch framework.  
4. Run six-step scenario.  
5. Collect metrics and logs.  
6. Query Usage API.  
7. Evaluate stopping rule.  
8. Repeat if required.

---

## 12. Statistical Analysis

- **Tests:** Kruskal–Wallis + Dunn–Šidák post-hoc  
- **Effect size:** Cliff’s δ  
- **CI:** 95% bootstrap  
- **Visuals:**  
  - Radar chart (AUTR, TOK_IN, CRUDe, ESR, MC, ZDI)  
  - Pareto plot (Q* vs TOK_IN)  
  - Timeline chart of CRUD and downtime

---

## 13. Determinism Summary

| Parameter | Value |
|------------|-------|
| Model | `gpt5-mini` |
| Temperature | 0 |
| top_p | 1.0 |
| max_output_tokens | 4096 |
| Retries | 3 |
| Auto-retry per step | r = 2 |
| HITL limit | k = 2 |
| HITL weight | HEU = 3 |
| Timezone | UTC |
| Replications | 5–25 |
| Reuse | None |
| Reproducibility | 100% deterministic |
| Publication | Open-science ready |

---

## 14. Citation (for paper)

> *“The experiment harness `baes_experiment` executes a six-step academic-domain scenario across BAEs, ChatDev, and GitHub Spec-kit. Each framework generates a full web application (API + UI) under identical instructions. Token, autonomy, and quality metrics are logged automatically, with OpenAI Usage API validation. Human clarifications are deterministic via a single expanded specification, ensuring perfect reproducibility.”*

---

## 15. License

This project is distributed under the **Creative Commons Attribution 4.0 International (CC BY 4.0)** license.  
You are free to use, modify, and publish it with attribution.

---

© 2025 Anderson Martins Gomes  
Universidade Estadual do Ceará (UECE)
