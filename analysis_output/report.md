# Statistical Analysis Report

**Generated:** 2025-10-16 14:01:13 UTC

**Frameworks:** ghspec, chatdev, baes

---

## Experimental Methodology

### 🔬 Research Design

This study compares three autonomous AI-powered software development frameworks under **controlled experimental conditions** to evaluate their performance, efficiency, and automation capabilities. The experimental design ensures fairness and reproducibility through standardized inputs, identical infrastructure, and rigorous metric collection.

### 🎯 Frameworks Under Test

**1. ChatDev** (OpenBMB/ChatDev)
- Multi-agent collaborative framework with role-based AI agents (CEO, CTO, Programmer, Reviewer)
- Waterfall-inspired workflow with distinct phases (design, coding, testing, documentation)
- Repository: `github.com/OpenBMB/ChatDev` (commit: `52edb89`)

**2. GHSpec** (GitHub Spec-Kit)
- Specification-driven development framework following structured phases
- Four-phase workflow: specification → planning → task breakdown → implementation
- Sequential task execution with full context awareness
- Repository: `github.com/github/spec-kit` (commit: `89f4b0b`)

**3. BAEs** (Business Autonomous Entities)
- API-based autonomous business entity framework
- Kernel-mediated request processing with specialized entities
- Repository: `github.com/gesad-lab/baes_demo` (commit: `1dd5736`)

### 📋 Experimental Protocol

#### **Standardized Task Sequence**

All frameworks execute the **identical six-step evolution scenario** in strict sequential order:

1. **Step 1**: Create CRUD application (Student/Course/Teacher with FastAPI + SQLite)
2. **Step 2**: Add enrollment relationship (many-to-many Student-Course)
3. **Step 3**: Add teacher assignment (many-to-one Course-Teacher)
4. **Step 4**: Implement validation and error handling
5. **Step 5**: Add pagination and filtering to all endpoints
6. **Step 6**: Create comprehensive web UI for all operations

*Natural language commands stored in version-controlled files (`config/prompts/step_1.txt` through `step_6.txt`) ensure perfect reproducibility across runs.*

#### **Controlled Variables**

To ensure fair comparison, the following variables are **held constant** across all frameworks:

**Generative AI Model**:
- Model: `gpt-4o-mini` (OpenAI GPT-4 Omni Mini)
- Temperature: Framework default (typically 0.7-1.0)
- All frameworks use the **same model version** for all steps

**API Infrastructure**:
- Each framework uses a **dedicated OpenAI API key** (prevents quota conflicts)
- API keys: `OPENAI_API_KEY_BAES`, `OPENAI_API_KEY_CHATDEV`, `OPENAI_API_KEY_GHSPEC`
- Token consumption measured via **OpenAI Usage API** (`/v1/organization/usage/completions`)
- Time-window queries (Unix timestamps) ensure accurate attribution to each execution step

**Execution Environment**:
- Python 3.11+ isolated virtual environments per framework
- Dependencies installed from framework-specific requirements at pinned commits
- Single-threaded sequential execution (no parallelism)
- 10-minute timeout per step (`step_timeout_seconds: 600`)

**Random Seed**:
- Fixed seed: `random_seed: 42` (for frameworks that support deterministic execution)

#### **Framework Adapter Implementation**

**Isolation Strategy**: Each framework runs through a custom **adapter** (wrapper) that:

1. **Clones repository** at exact commit hash (ensures version consistency)
2. **Creates isolated virtual environment** with framework-specific dependencies
3. **Translates standard commands** to framework-specific CLI/API invocations
4. **Executes steps sequentially** with proper environment variables and timeouts
5. **Captures stdout/stderr** for logging and debugging
6. **Queries OpenAI Usage API** with step-specific time windows for token counting
7. **Cleans up gracefully** after run completion

**Non-Invasive Design**: Adapters are **read-only wrappers** that:
- ✅ Do NOT modify framework source code
- ✅ Do NOT alter framework algorithms or decision-making
- ✅ Do NOT inject custom prompts beyond the standardized task descriptions
- ✅ Only handle infrastructure (environment setup, execution, metric collection)

*Example: ChatDev adapter constructs command:*
```
python run.py --task "<step_text>" --name "BAEs_Step1_<run_id>" \
             --config Default --model GPT_4O_MINI
```

#### **Metric Collection**

**Token Counting (TOK_IN, TOK_OUT)**:
- Primary source: **OpenAI Usage API** (authoritative, billing-grade accuracy)
- Query parameters: `start_time` (step start Unix timestamp), `end_time` (step end timestamp)
- Model filter: `models=["gpt-4o-mini"]` (isolates framework's usage)
- Aggregates all API calls within time window (handles multi-request steps)

**Timing (T_WALL_seconds, ZDI)**:
- Wall-clock time: `time.time()` before/after each step (Python `time` module)
- Zero-Downtime Intervals (ZDI): Idle time between consecutive steps

**Automation Metrics (AUTR, HIT, HEU)**:
- AUTR: Automated testing rate (test files generated / total steps)
- HIT: Human-in-the-loop count (clarification requests detected in logs)
- HEU: Human effort units (manual interventions required)

**Quality Metrics (CRUDe, ESR, MC, Q\*)**:
- CRUDe: CRUD operations implemented (validated via API endpoint inspection)
- ESR: Emerging state rate (successful evolution steps / total steps)
- MC: Model call efficiency (successful calls / total calls)
- Q\*: Composite quality score (0.4·ESR + 0.3·CRUDe/12 + 0.3·MC)

**Composite Scores (AEI)**:
- AEI: Automation Efficiency Index = AUTR / log(1 + TOK_IN)
- Balances automation quality against token consumption

### ⚠️ Threats to Validity (Ameaças à Validade)

#### **Internal Validity**

**✅ Controlled Threats:**
- **Model Consistency**: All frameworks use identical `gpt-4o-mini` model
- **Command Consistency**: Same 6 natural language prompts in identical order
- **Timing Isolation**: Dedicated API keys prevent cross-framework interference
- **Environment Isolation**: Separate virtual environments prevent dependency conflicts
- **Version Pinning**: Exact commit hashes ensure reproducible framework behavior

**⚠️ Uncontrolled Threats:**
- **Framework-Specific Behavior**: Each framework has unique internal prompts, agent coordination, and retry logic
  - *Mitigation*: Documented in adapter implementations; accepted as inherent framework characteristics
- **Non-Deterministic LLM Responses**: `gpt-4o-mini` may produce different outputs for identical inputs
  - *Mitigation*: Fixed random seed (42) helps but doesn't guarantee full determinism
  - *Statistical Control*: Multiple runs (5-25 per framework) with bootstrap CI to capture variance
- **HITL Detection Accuracy**: Human-in-the-loop counts rely on keyword matching in logs
  - *Limitation*: May miss implicit clarifications or false-positive on debug messages

#### **External Validity**

**Generalization Concerns:**
- **Single Task Domain**: CRUD application (Student/Course/Teacher) may not represent all software types
  - *Scope*: Results apply to data-driven web API development; may differ for other domains (ML, systems, mobile)
- **Single Model**: Results specific to `gpt-4o-mini`; other models (GPT-4, Claude, Gemini) may alter rankings
  - *Trade-off*: Chose `gpt-4o-mini` for cost and speed; representative of practical usage
- **Framework Versions**: Pinned commits may not reflect latest improvements
  - *Justification*: Ensures reproducibility; future studies can test newer versions

#### **Construct Validity**

**Metric Interpretation:**
- **Token Usage (TOK_IN/TOK_OUT)**: Measures cost, not necessarily code quality
  - *Caveat*: Lower tokens ≠ better software; high-quality output may justify higher consumption
- **Quality Metrics (Q\*, ESR, CRUDe)**: May show zero values due to:
  - Missing validation logic in current implementation
  - Framework output formats not matching expected patterns
  - *Action Required*: Verify metric calculation before quality-based decisions (see Data Quality Alerts)
- **AUTR (Automated Testing Rate)**: All frameworks achieve 100% but test quality not measured
  - *Limitation*: Presence of test files ≠ comprehensive test coverage

#### **Conclusion Validity**

**Statistical Rigor:**
- **Non-Parametric Tests**: Kruskal-Wallis and Dunn-Šidák avoid normality assumptions
- **Effect Sizes**: Cliff's delta quantifies practical significance beyond p-values
- **Bootstrap CI**: 95% confidence intervals with 10,000 resamples for stable estimates
- **Small Sample Awareness**: Current results (5 runs) show large CI widths; p-values > 0.05 expected
  - *Stopping Rule*: Experiment continues until CI half-width ≤ 10% of mean (25 runs max)

**Interpretation Caveats:**
- **Non-Significant Results**: p > 0.05 does NOT prove frameworks are equivalent, only insufficient evidence of difference
- **Large Effect Sizes Without Significance**: May reflect true differences masked by small sample (see pairwise interpretations)
- **Relative Performance**: "baes uses 9.4x fewer tokens" is observational; not statistically confirmed yet

### 📊 Data Availability

**Reproducibility Artifacts:**
- Configuration: `config/experiment.yaml` (framework commits, timeouts, seed)
- Prompts: `config/prompts/step_1.txt` through `step_6.txt` (version-controlled)
- Source Code: Adapter implementations in `src/adapters/` (BaseAdapter, ChatDevAdapter, GHSpecAdapter, BAeSAdapter)
- Results Archive: Each run saved as `<run_id>.tar.gz` with metrics.json, step_metrics.json, logs, workspace
- Analysis Scripts: `src/analysis/statistics.py` (this report generator), `src/analysis/visualizations.py`

**Commit Hashes**:
- ChatDev: `52edb89997b4312ad27d8c54584d0a6c59940135`
- GHSpec: `89f4b0b38a42996376c0f083d47281a4c9196761`
- BAEs: `1dd573633a98b8baa636c200bc1684cec7a8179f`

---

## Metric Definitions

| Metric | Full Name | Description | Range | Ideal Value |
|--------|-----------|-------------|-------|-------------|
| **AUTR** | Automated User Testing Rate | % of tests auto-generated | 0-1 | Higher ↑ |
| **AEI** | Automation Efficiency Index | Quality per token consumed | 0-∞ | Higher ↑ |
| **Q\*** | Quality Star | Composite quality score | 0-1 | Higher ↑ |
| **ESR** | Emerging State Rate | % steps with successful evolution | 0-1 | Higher ↑ |
| **CRUDe** | CRUD Evolution Coverage | CRUD operations implemented | 0-12 | Higher ↑ |
| **MC** | Model Call Efficiency | Efficiency of LLM calls | 0-1 | Higher ↑ |
| **TOK_IN** | Input Tokens | Total tokens sent to LLM | 0-∞ | Lower ↓ |
| **TOK_OUT** | Output Tokens | Total tokens received from LLM | 0-∞ | Lower ↓ |
| **T_WALL_seconds** | Wall Clock Time | Total elapsed time (seconds) | 0-∞ | Lower ↓ |
| **ZDI** | Zero-Downtime Intervals | Idle time between steps (seconds) | 0-∞ | Lower ↓ |
| **HIT** | Human-in-the-Loop Count | Manual interventions needed | 0-∞ | Lower ↓ |
| **HEU** | Human Effort Units | Total manual effort required | 0-∞ | Lower ↓ |
| **UTT** | User Task Total | Number of evolution steps | Fixed | 6 |

---

## Statistical Methods Guide

This report uses non-parametric statistics to compare frameworks robustly.

### 📖 Key Concepts

**Bootstrap Confidence Intervals (CI)**
- Estimates the range where true mean likely falls (95% confidence)
- Example: `30,772 [2,503, 59,040]` means we're 95% confident the true mean is between 2,503 and 59,040
- Wider intervals = more uncertainty; narrower intervals = more precise estimates

**Kruskal-Wallis H-Test**
- Non-parametric test comparing multiple groups (doesn't assume normal distribution)
- Tests: "Are there significant differences across frameworks?"
- **H statistic**: Higher values = larger differences between groups
- **p-value**: Probability results occurred by chance
  - p < 0.05: Statistically significant (likely real difference) ✓
  - p ≥ 0.05: Not significant (could be random variation) ✗

**Pairwise Comparisons (Dunn-Šidák)**
- Compares specific framework pairs after significant Kruskal-Wallis result
- Dunn-Šidák correction prevents false positives from multiple comparisons
- Each comparison tests: "Is framework A different from framework B?"

**Cliff's Delta (δ) - Effect Size**
- Measures practical significance (how large is the difference?)
- Range: -1 to +1
  - **δ = 0**: No difference (distributions completely overlap)
  - **δ = ±1**: Complete separation (no overlap)
- Interpretation:
  - |δ| < 0.147: **Negligible** (tiny difference)
  - 0.147 ≤ |δ| < 0.330: **Small** (noticeable)
  - 0.330 ≤ |δ| < 0.474: **Medium** (substantial)
  - |δ| ≥ 0.474: **Large** (major difference)

### 💡 How to Read Results

1. **Check p-value**: Is the difference statistically significant (p < 0.05)?
2. **Check effect size**: Is the difference practically meaningful (|δ| ≥ 0.147)?
3. **Both matter**: Statistical significance without large effect = real but trivial difference

**Example Interpretation:**
- `p = 0.012 (✓), δ = 0.850 (large)` → Strong evidence of major practical difference
- `p = 0.048 (✓), δ = 0.095 (negligible)` → Statistically significant but practically trivial
- `p = 0.234 (✗), δ = 0.650 (large)` → Large observed difference but may be random variation

---

## Executive Summary

### 🏆 Best Performers

- **Most Efficient (AEI)**: ghspec (0.109) - best quality-per-token ratio
- **Fastest (T_WALL)**: baes (238.5s / 4.0 min)
- **Lowest Token Usage**: baes (25,607 input tokens)

### 📊 Key Insights

- ✅ All frameworks achieved perfect test automation (AUTR = 1.0)
- ⚠️ Quality metrics show zero values: Q_star, ESR, CRUDe, MC - may need verification
- Wall time varies 7.5x between fastest and slowest frameworks
- Token consumption varies 9.4x across frameworks

### ⚠️ Data Quality Alerts

- All frameworks show zero for `CRUDe` - verify metric calculation
- All frameworks show zero for `ESR` - verify metric calculation
- All frameworks show zero for `MC` - verify metric calculation
- All frameworks show zero for `Q_star` - verify metric calculation

---

## 1. Aggregate Statistics

### Mean Values with 95% Bootstrap CI

*Note: Token values shown with thousands separator; time in seconds (minutes if >60s)*

**Performance Indicators:** 🟢 Best | 🟡 Middle | 🔴 Worst

| Framework | AEI | AUTR | CRUDe | ESR | HEU | HIT | MC | Q_star | TOK_IN | TOK_OUT | T_WALL_seconds | UTT | ZDI |
|-----------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|
| ghspec | 0.109 [0.091, 0.128] 🟢 | 1.000 [1.000, 1.000] 🟢 | 0 [0, 0] 🟢 | 0.000 [0.000, 0.000] 🟢 | 0 [0, 0] 🟢 | 0 [0, 0] 🟢 | 0.000 [0.000, 0.000] 🟢 | 0.000 [0.000, 0.000] 🟢 | 30,772 [2,503, 59,040] 🟡 | 12,234 [925, 23,542] 🟡 | 399.5 [80.3, 718.7] 🟡 | 6 [6, 6] 🟢 | 80 [17, 144] 🟡 |
| chatdev | 0.081 [0.080, 0.081] 🔴 | 1.000 [1.000, 1.000] 🟢 | 0 [0, 0] 🟢 | 0.000 [0.000, 0.000] 🟢 | 0 [0, 0] 🟢 | 0 [0, 0] 🟢 | 0.000 [0.000, 0.000] 🟢 | 0.000 [0.000, 0.000] 🟢 | 240,714 [217,055, 264,373] 🔴 | 75,653 [74,482, 76,824] 🔴 | 1781.5 [1748.3, 1814.7] 🔴 | 6 [6, 6] 🟢 | 356 [350, 363] 🔴 |
| baes | 0.099 [0.099, 0.099] 🟡 | 1.000 [1.000, 1.000] 🟢 | 0 [0, 0] 🟢 | 0.000 [0.000, 0.000] 🟢 | 0 [0, 0] 🟢 | 0 [0, 0] 🟢 | 0.000 [0.000, 0.000] 🟢 | 0.000 [0.000, 0.000] 🟢 | 25,607 [25,607, 25,607] 🟢 | 6,694 [6,694, 6,694] 🟢 | 238.5 [238.5, 238.5] 🟢 | 6 [6, 6] 🟢 | 48 [48, 48] 🟢 |


## 2. Relative Performance

Performance normalized to best framework (100% = best performer).

*Lower percentages are better for cost metrics (tokens, time); higher percentages are better for quality metrics.*

| Framework | Tokens (↓) | Time (↓) | Test Auto (↑) | Efficiency (↑) | Quality (↑) |
|-----------|---------------|---------------|---------------|---------------|---------------|
| ghspec | 120% 🔴 | 168% 🔴 | 100% 🟢 | 100% 🟢 | 100% 🟢 |
| chatdev | 940% 🔴 | 747% 🔴 | 100% 🟢 | 74% 🔴 | 100% 🟢 |
| baes | 100% 🟢 | 100% 🟢 | 100% 🟢 | 90% 🟡 | 100% 🟢 |


## 3. Kruskal-Wallis H-Tests

Testing for significant differences across all frameworks.

| Metric | H | p-value | Significant | Groups | N |
|--------|---|---------|-------------|--------|---|
| AEI | 3.000 | 0.2231 | ✗ No | 3 | 5 |

💬 *Differences appear modest - may reflect random variation rather than true performance gaps.*

| AUTR | 0.000 | 1.0000 | ✗ No | 3 | 5 |

💬 *No evidence of differences - frameworks perform similarly on AUTR.*

| CRUDe | 0.000 | 1.0000 | ✗ No | 3 | 5 |

💬 *No evidence of differences - frameworks perform similarly on CRUDe.*

| ESR | 0.000 | 1.0000 | ✗ No | 3 | 5 |

💬 *No evidence of differences - frameworks perform similarly on ESR.*

| HEU | 0.000 | 1.0000 | ✗ No | 3 | 5 |

💬 *No evidence of differences - frameworks perform similarly on HEU.*

| HIT | 0.000 | 1.0000 | ✗ No | 3 | 5 |

💬 *No evidence of differences - frameworks perform similarly on HIT.*

| MC | 0.000 | 1.0000 | ✗ No | 3 | 5 |

💬 *No evidence of differences - frameworks perform similarly on MC.*

| Q_star | 0.000 | 1.0000 | ✗ No | 3 | 5 |

💬 *No evidence of differences - frameworks perform similarly on Q_star.*

| TOK_IN | 3.000 | 0.2231 | ✗ No | 3 | 5 |

💬 *Differences appear modest - may reflect random variation rather than true performance gaps.*

| TOK_OUT | 3.000 | 0.2231 | ✗ No | 3 | 5 |

💬 *Differences appear modest - may reflect random variation rather than true performance gaps.*

| T_WALL_seconds | 3.000 | 0.2231 | ✗ No | 3 | 5 |

💬 *Differences appear modest - may reflect random variation rather than true performance gaps.*

| UTT | 0.000 | 1.0000 | ✗ No | 3 | 5 |

💬 *No evidence of differences - frameworks perform similarly on UTT.*

| ZDI | 3.000 | 0.2231 | ✗ No | 3 | 5 |

💬 *Differences appear modest - may reflect random variation rather than true performance gaps.*



## 4. Pairwise Comparisons

Dunn-Šidák corrected pairwise tests with Cliff's delta effect sizes.

### AEI

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | 1.000 | large |
| ghspec vs baes | 1.0000 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | -1.000 | large |

  *→ Large observed difference (δ=1.000) but not statistically significant - may be random variation*
  *→ Large observed difference (δ=-1.000) but not statistically significant - may be random variation*


### AUTR

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | 0.000 | negligible |
| ghspec vs baes | 0.2207 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 0.000 | negligible |


### CRUDe

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | 0.000 | negligible |
| ghspec vs baes | 0.2207 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 0.000 | negligible |


### ESR

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | 0.000 | negligible |
| ghspec vs baes | 0.2207 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 0.000 | negligible |


### HEU

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | 0.000 | negligible |
| ghspec vs baes | 0.2207 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 0.000 | negligible |


### HIT

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | 0.000 | negligible |
| ghspec vs baes | 0.2207 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 0.000 | negligible |


### MC

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | 0.000 | negligible |
| ghspec vs baes | 0.2207 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 0.000 | negligible |


### Q_star

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | 0.000 | negligible |
| ghspec vs baes | 0.2207 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 0.000 | negligible |


### TOK_IN

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | -1.000 | large |
| ghspec vs baes | 1.0000 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 1.000 | large |

  *→ Large observed difference (δ=-1.000) but not statistically significant - may be random variation*
  *→ Large observed difference (δ=1.000) but not statistically significant - may be random variation*


### TOK_OUT

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | -1.000 | large |
| ghspec vs baes | 1.0000 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 1.000 | large |

  *→ Large observed difference (δ=-1.000) but not statistically significant - may be random variation*
  *→ Large observed difference (δ=1.000) but not statistically significant - may be random variation*


### T_WALL_seconds

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | -1.000 | large |
| ghspec vs baes | 1.0000 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 1.000 | large |

  *→ Large observed difference (δ=-1.000) but not statistically significant - may be random variation*
  *→ Large observed difference (δ=1.000) but not statistically significant - may be random variation*


### UTT

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | 0.000 | negligible |
| ghspec vs baes | 0.2207 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 0.000 | negligible |


### ZDI

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | -1.000 | large |
| ghspec vs baes | 1.0000 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 1.000 | large |

  *→ Large observed difference (δ=-1.000) but not statistically significant - may be random variation*
  *→ Large observed difference (δ=1.000) but not statistically significant - may be random variation*


## 5. Outlier Detection

Values > 3σ from median (per framework, per metric).

No outliers detected.

## 5. Composite Scores

**Q*** = 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC

**AEI** = AUTR / log(1 + TOK_IN)

| Framework | Q* Mean | Q* CI | AEI Mean | AEI CI |
|-----------|---------|-------|----------|--------|
| ghspec | 0.000 | [0.000, 0.000] | 0.109 | [0.091, 0.128] |
| chatdev | 0.000 | [0.000, 0.000] | 0.081 | [0.080, 0.081] |
| baes | 0.000 | [0.000, 0.000] | 0.099 | [0.099, 0.099] |


## 6. Visual Summary

### Key Visualizations

The following charts provide visual insights into framework performance:

**Radar Chart** - Multi-dimensional comparison across 6 key metrics

![Radar Chart](radar_chart.svg)

**Pareto Plot** - Quality vs Cost trade-off analysis

![Pareto Plot](pareto_plot.svg)

**Timeline Chart** - CRUD evolution over execution steps

![Timeline Chart](timeline_chart.svg)

---

## 7. Recommendations

### 🎯 Framework Selection Guidance

- **💰 Cost Optimization**: Choose **baes** if minimizing LLM token costs is priority. It uses 9.4x fewer tokens than chatdev.

- **⚡ Speed Priority**: Choose **baes** for fastest execution. It completes tasks 7.5x faster than chatdev (saves ~25.7 minutes per task).

- **⚙️ Efficiency Leader**: **ghspec** delivers the best quality-per-token ratio (AEI = 0.109), making it ideal for balancing quality and cost.

- **🤖 Automation**: All frameworks achieve perfect test automation (AUTR = 1.0) - automation quality is not a differentiating factor.

- **⚠️ Data Quality Alert**: Metrics Q_star, ESR, CRUDe, MC show zero values across all frameworks. Verify metric calculation before making quality-based decisions.

### 📋 Decision Matrix

| Use Case | Recommended Framework | Rationale |
|----------|----------------------|-----------|
| Cost-sensitive projects | baes | Lowest token consumption |
| Time-critical tasks | baes | Fastest execution time |
| Balanced quality/cost | ghspec | Best efficiency index (AEI) |

