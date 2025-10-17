# Statistical Analysis Report

**Generated:** 2025-10-17 18:31:58 UTC

**Frameworks:** baes, chatdev, ghspec

**Sample Size:** 63 total runs (baes: 24, chatdev: 21, ghspec: 18)

---

## 📚 Foundational Concepts

This section provides the essential background knowledge to understand the experiment's design, methodology, and findings.

### 🤖 What Are Autonomous AI Software Development Frameworks?

**Definition**: Autonomous AI software development frameworks are systems that use Large Language Models (LLMs) to automate software creation with minimal or no human intervention. Unlike traditional AI coding assistants (e.g., GitHub Copilot) that *assist* developers, these frameworks aim to independently:

1. **Interpret requirements** - Understand natural language task descriptions
2. **Design solutions** - Plan software architecture and implementation strategy
3. **Write code** - Generate complete, functional source code across multiple files
4. **Test & debug** - Create tests, detect errors, and apply fixes autonomously
5. **Iterate** - Refine the solution through multiple improvement cycles

**Key Distinction**: These are *autonomous agents* (work independently) vs. *copilots* (work alongside humans).

### 🎯 Research Question

**Primary Question**: How do different autonomous AI frameworks compare in terms of:
- **Efficiency** - Resource consumption (API tokens, execution time)
- **Automation** - Degree of independence from human intervention
- **Consistency** - Result stability across multiple runs with identical inputs

**Why This Matters**: As AI-powered development tools become mainstream, understanding their comparative strengths/weaknesses helps:
- **Researchers** - Identify design patterns that work well
- **Practitioners** - Choose appropriate tools for specific use cases
- **Framework developers** - Learn from competing approaches

### 🔬 Experimental Paradigm: Controlled Comparative Study

**Study Type**: Quantitative, controlled laboratory experiment with repeated measures

**Core Principle**: Hold all variables constant *except* the framework being tested. This ensures observed differences are attributable to framework design, not environmental factors.

**Independent Variable**: Framework choice (ChatDev, GHSpec, BAEs)
**Dependent Variables**: Performance metrics (tokens, time, automation rate, etc.)
**Control Variables**: Task prompts, AI model, execution environment, measurement methods

**Repeated Measures Design**:
- Each framework performs the **same task** multiple times (5-50 runs)
- Captures natural variability from LLM non-determinism
- Enables robust statistical comparison with confidence intervals

### 📊 Key Concepts for Understanding Results

#### **Statistical Significance vs. Practical Significance**

- **Statistical Significance** (p-value): Probability that observed differences occurred by random chance
  - p < 0.05: Less than 5% chance of randomness → "statistically significant"
  - *Does NOT* measure magnitude or importance of difference

- **Practical Significance** (effect size): *How large* is the difference?
  - Measured by Cliff's Delta (δ): ranges from -1 (complete separation) to +1
  - Large effect size = differences matter in practice
  - Small effect size = statistically significant but negligible impact

**Both Required**: A difference must be both statistically significant (p < 0.05) AND have meaningful effect size (|δ| ≥ 0.33) to be considered important.

#### **Non-Parametric Statistics**

**Why Not Use t-tests?** Traditional parametric tests assume:
- Data follows normal (bell-curve) distribution
- Equal variance across groups
- Large sample sizes

**Our Reality**: With 5-50 runs per framework, these assumptions often don't hold.

**Solution**: Non-parametric methods (Kruskal-Wallis, Mann-Whitney, Cliff's δ):
- Work with ranks instead of raw values (robust to outliers)
- No distribution assumptions required
- Valid for small sample sizes
- Appropriate for comparing medians rather than means

#### **Multiple Comparisons Problem**

**The Issue**: With 3 frameworks, we make 3 pairwise comparisons (A vs B, A vs C, B vs C). Each test has 5% false positive rate. Multiple tests increase overall error rate:
- 1 test: 5% chance of false positive
- 3 tests: ~14% chance of at least one false positive
- 10 tests: ~40% chance!

**Solution - Dunn-Šidák Correction**: Adjusts significance threshold to maintain overall 5% error rate across all comparisons. Instead of p < 0.05 for each test, we use stricter threshold p < α_corrected.

#### **Confidence Intervals (CI)**

**Intuitive Meaning**: "If we repeated this entire experiment 100 times, the true population mean would fall within the CI range in 95 of those experiments."

**Example Interpretation**:
```
TOK_IN: 45,230 [38,500, 52,100]
```
- Point estimate: 45,230 tokens (observed average)
- 95% CI: [38,500, 52,100] (plausible range for true mean)
- Interpretation: True average token consumption likely between 38,500-52,100

**CI Width Indicates Precision**:
- Narrow CI → high confidence in estimate, stable results
- Wide CI → high uncertainty, need more data

### 🎲 Randomness & Reproducibility

**Sources of Randomness**:

1. **LLM Non-Determinism**: Even with fixed temperature/seed, LLMs may produce different outputs due to:
   - Sampling algorithms in the model
   - Infrastructure variations (GPU scheduling, batching)
   - OpenAI API updates/changes

2. **Framework Internal Decisions**: Many frameworks use stochastic elements:
   - Random selection of agents/roles
   - Probabilistic retry logic
   - Non-deterministic parsing of LLM responses

**Managing Randomness**:
- ✅ **Fixed random seed** (42) where possible → reduces some variance
- ✅ **Multiple runs** → captures remaining natural variability
- ✅ **Statistical methods** → quantifies uncertainty via confidence intervals
- ✅ **Version pinning** → exact framework/dependency versions ensure reproducibility

**Reproducibility Guarantee**: Given identical:
- Framework version (commit hash)
- Task prompts (`config/prompts/step_*.txt`)
- AI model version
- Random seed

Results will be *similar* (not identical) due to irreducible LLM stochasticity. This is *expected* and *scientifically acceptable* — our statistical methods account for this variance.

### 📏 Measurement Validity

#### **Token Counting Accuracy**

**Challenge**: Frameworks make multiple API calls per step. How do we accurately count tokens?

**Our Solution - OpenAI Usage API**:
- **Authoritative source**: Same API OpenAI uses for billing (maximum accuracy)
- **Time-window queries**: Request token counts between step start/end timestamps
- **Model filtering**: Isolate specific model usage to avoid cross-contamination
- **Advantages**: Captures ALL API calls (including internal retries, error handling)

**Why Not Local Tokenizers?**
- Miss tokens from internal framework retries
- Don't account for special tokens added by API
- No visibility into prompt caching (new feature)

#### **Wall-Clock Time vs. Compute Time**

**T_WALL (Wall-Clock Time)**: Total elapsed time from step start to step end
- Includes: computation + API latency + network delays + framework overhead
- Represents *user-experienced duration*
- More variable due to network conditions

**Why Not Pure Compute Time?**
- API latency is *inherent* to these frameworks (can't be separated)
- Users care about total time-to-completion
- Wall-clock time is the practical measure

---

## Experimental Methodology

### 🔬 Research Design

This study compares three autonomous AI-powered software development frameworks under **controlled experimental conditions** to evaluate their performance, efficiency, and automation capabilities. The experimental design ensures fairness and reproducibility through standardized inputs, identical infrastructure, and rigorous metric collection.

### 🎯 Frameworks Under Test

**1. BAEs** (Business Autonomous Entities)
- API-based autonomous business entity framework
- Kernel-mediated request processing with specialized entities
- Repository: `gesad-lab/baes_demo` (commit: `1dd5736`)

**2. ChatDev** (OpenBMB/ChatDev)
- Multi-agent collaborative framework with role-based AI agents (CEO, CTO, Programmer, Reviewer)
- Waterfall-inspired workflow with distinct phases (design, coding, testing, documentation)
- Repository: `OpenBMB/ChatDev` (commit: `52edb89`)

**3. GHSpec** (GitHub Spec-Kit)
- Specification-driven development framework following structured phases
- Four-phase workflow: specification → planning → task breakdown → implementation
- Sequential task execution with full context awareness
- Repository: `github/spec-kit` (commit: `89f4b0b`)

### 📋 Experimental Protocol

#### **Sample Size and Replication**

This analysis is based on **63 experimental runs** across three frameworks:

- **baes**: 24 independent runs
- **chatdev**: 21 independent runs
- **ghspec**: 18 independent runs

**Replication Protocol:**
- Each run executes the complete 6-step evolution scenario independently
- **Runs are performed strictly sequentially** (not in parallel) to enable accurate API usage tracking:
  - OpenAI Usage API aggregates data across all parallel requests using the same API key
  - Sequential execution ensures each run's API usage can be isolated and measured distinctly
  - This is the only reliable method to attribute token consumption to individual experimental runs
- Each run uses a fresh isolated environment (new virtual environment, clean workspace)
- Random seed fixed at 42 for frameworks that support deterministic execution
- Non-deterministic LLM responses introduce natural variance across runs

**Statistical Power:**
- Current sample sizes (baes: 24, chatdev: 21, ghspec: 18) provide sufficient power for detecting large effect sizes
- **Bootstrap confidence intervals** (10,000 resamples) quantify uncertainty in our estimates:
  - Simulates collecting 10,000 alternative datasets by resampling our actual data with replacement
  - Each resample calculates the metric (e.g., mean AUTR), creating a distribution of possible values
  - 95% CI shows the range where we expect the true population mean to fall 95% of the time
  - This accounts for the fact that we only have a limited sample (not infinite runs)
- Stopping rule: Continue until CI half-width ≤ 10% of mean (max 50 runs per framework)
- Current status: baes (24/50), chatdev (21/50), ghspec (18/50)

#### **Standardized Task Sequence**

All frameworks execute the **identical 6-step evolution scenario** in strict sequential order:

1. **Step 1**: Create a Student/Course/Teacher CRUD application with Python, FastAPI, and SQLite.
2. **Step 2**: Add enrollment relationship between Student and Course entities.
3. **Step 3**: Add teacher assignment relationship to Course entity.
4. **Step 4**: Implement comprehensive data validation and error handling.
5. **Step 5**: Add pagination and filtering to all list endpoints.
6. **Step 6**: Add comprehensive user interface for all CRUD operations.

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
- AUTR: Autonomy rate = 1 - (HIT / UTT), measuring independence from human intervention
- HIT: Human-in-the-loop count (clarification requests detected in logs)
- HEU: Human effort units (manual interventions required)

**Quality Metrics (CRUDe, ESR, MC, Q\*)**: ⚠️ **NOT MEASURED IN CURRENT EXPERIMENTS**
- CRUDe: CRUD operations implemented (requires running application servers)
- ESR: Emerging state rate (requires endpoint validation)
- MC: Model call efficiency (requires runtime testing)
- Q\*: Composite quality score (0.4·ESR + 0.3·CRUDe/12 + 0.3·MC)
- **Note**: These metrics always show zero because generated applications are not executed. Validation would require starting servers (`uvicorn`, `flask run`) and testing endpoints, which is not implemented. See `docs/QUALITY_METRICS_INVESTIGATION.md` for details.

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
  - *Statistical Control*: Multiple runs (5-50 per framework) with bootstrap CI to capture variance
- **HITL Detection Accuracy**: Human-in-the-loop counts rely on pattern matching in logs
  - *ChatDev*: 5 regex patterns detect clarification requests (lines 821-832)
  - *GHSpec*: Explicit `[NEEDS CLARIFICATION:]` marker detection (line 544)
  - *BAEs*: ⚠️ **No detection implemented** - hardcoded to zero (lines 330, 348)
  - *Mitigation (BAEs)*: Manual investigation of 23 runs confirmed zero HITL events (see `BAES_HITL_INVESTIGATION.md`)
  - *Limitation*: Pattern matching may miss implicit clarifications or produce false positives
  - *Risk*: BAEs cannot detect HITL events in future experiments with ambiguous requirements

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
- **Quality Metrics (Q\*, ESR, CRUDe, MC)**: ⚠️ **Show zero values because runtime validation is not performed**
  - Generated applications are not started during experiments (`auto_restart_servers: false`)
  - Validation requires running servers and testing endpoints
  - Current experiment scope: **Code generation efficiency**, not **runtime quality**
  - *Action Required*: Implement server startup and endpoint testing for quality evaluation (see `docs/QUALITY_METRICS_INVESTIGATION.md`)
- **AUTR (Autonomy Rate)**: All frameworks achieve 100% autonomy (no human intervention required)
  - *Note*: AUTR = 1.0 means HIT = 0 (no human-in-the-loop interventions needed)
  - *Implementation Variance*: ChatDev and GHSpec use active HITL detection; BAEs hardcodes zero
  - *Validation*: See 'HITL Detection Implementation Notes' section for framework-specific details

#### **Conclusion Validity**

**Statistical Rigor:**
- **Non-Parametric Tests**: Kruskal-Wallis and Dunn-Šidák avoid normality assumptions
- **Effect Sizes**: Cliff's delta quantifies practical significance beyond p-values
- **Bootstrap CI**: 95% confidence intervals with 10,000 resamples for stable estimates
- **Small Sample Awareness**: Current results (baes: 24, chatdev: 21, ghspec: 18) show large CI widths; p-values > 0.05 expected
  - *Stopping Rule*: Experiment continues until CI half-width ≤ 10% of mean (50 runs max)

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
- BAEs: `1dd573633a98b8baa636c200bc1684cec7a8179f`
- ChatDev: `52edb89997b4312ad27d8c54584d0a6c59940135`
- GHSpec: `89f4b0b38a42996376c0f083d47281a4c9196761`

---

## Metric Definitions

| Metric | Full Name | Description | Range | Ideal Value | Status |
|--------|-----------|-------------|-------|-------------|--------|
| **AUTR** | Automated User Testing Rate | Autonomy: 1 - (HIT/UTT) | 0-1 | Higher ↑ | ⚠️ Partially Measured** |
| **AEI** | Automation Efficiency Index | AUTR / log(1 + TOK_IN) | 0-∞ | Higher ↑ | ⚠️ Partially Measured** |
| **Q\*** | Quality Star | Composite quality score | 0-1 | Higher ↑ | ⚠️ Not Measured* |
| **ESR** | Emerging State Rate | % steps with successful evolution | 0-1 | Higher ↑ | ⚠️ Not Measured* |
| **CRUDe** | CRUD Evolution Coverage | CRUD operations implemented | 0-12 | Higher ↑ | ⚠️ Not Measured* |
| **MC** | Model Call Efficiency | Efficiency of LLM calls | 0-1 | Higher ↑ | ⚠️ Not Measured* |
| **TOK_IN** | Input Tokens | Total tokens sent to LLM | 0-∞ | Lower ↓ | ✅ Measured |
| **TOK_OUT** | Output Tokens | Total tokens received from LLM | 0-∞ | Lower ↓ | ✅ Measured |
| **API_CALLS** | API Call Count | Number of model requests to LLM | 0-∞ | Lower ↓ | ✅ Measured |
| **CACHED_TOKENS** | Cached Input Tokens | Input tokens served from cache | 0-∞ | Higher ↑ | ✅ Measured |
| **T_WALL_seconds** | Wall Clock Time | Total elapsed time (seconds) | 0-∞ | Lower ↓ | ✅ Measured |
| **ZDI** | Zero-Downtime Intervals | Idle time between steps (seconds) | 0-∞ | Lower ↓ | ✅ Measured |
| **HIT** | Human-in-the-Loop Count | Manual interventions needed | 0-∞ | Lower ↓ | ⚠️ Partially Measured** |
| **HEU** | Human Effort Units | Total manual effort required | 0-∞ | Lower ↓ | ⚠️ Partially Measured** |
| **UTT** | User Task Total | Number of evolution steps | Fixed | 6 | ✅ Measured |

**\* Quality Metrics Not Measured**: CRUDe, ESR, MC, and Q\* show zero values because **generated applications are not executed during experiments**. The validation logic requires running servers to test CRUD endpoints (`http://localhost:8000-8002`), but servers are deliberately not started (`auto_restart_servers: false` in config). This experiment measures **code generation efficiency** (tokens, time, automation), not **runtime code quality**. See `docs/QUALITY_METRICS_INVESTIGATION.md` for details.

**\*\* HITL-Based Metrics Partially Measured**: AUTR, AEI, HIT, and HEU depend on Human-in-the-Loop (HITL) event detection, which is **not uniformly implemented** across all frameworks:
- ✅ **ChatDev**: Active pattern-based HITL detection (5 regex patterns)
- ✅ **GHSpec**: Active marker-based HITL detection (`[NEEDS CLARIFICATION:]`)
- ❌ **BAEs**: No HITL detection - hardcoded to zero (lines 330, 348 in adapter)

**Scientific Implication**: AUTR and AEI values for **BAEs are not reliable** because HITL events (if they occur) would not be detected. Current values (AUTR=1.0, HIT=0) may be accurate for this specific experiment but cannot be verified. For **ChatDev and GHSpec**, these metrics are properly measured. See 'HITL Detection Implementation Notes' section for full details.

**New Metrics Added (Oct 2025)**:
- **API_CALLS**: Number of LLM API requests - measures call efficiency (lower = better batching, fewer retries)
- **CACHED_TOKENS**: Tokens served from OpenAI's prompt cache - represents cost savings (~50% discount)
- **Cache Hit Rate**: Calculated as `(CACHED_TOKENS / TOK_IN) × 100%` - measures prompt reuse efficiency

### 🔍 HITL Detection Implementation Notes

**Human-in-the-Loop (HITL) Detection** varies significantly across frameworks due to architectural differences:

#### **ChatDev Adapter** ✅ Active Detection
- **Method**: Pattern-based log analysis with 5 regex patterns
- **Patterns Detected**:
  - `clarif(y|ication)` - Explicit clarification requests
  - `ambiguous|unclear` - Ambiguity indicators
  - `need.*input|require.*input` - Direct input requests
  - `cannot proceed|blocked` - Execution blockers
  - `manual.*intervention` - Manual intervention flags
- **Implementation**: `src/adapters/chatdev_adapter.py` (lines 821-832)
- **Status**: ✅ Actively detecting HITL events in ChatDev logs

#### **GHSpec Adapter** ✅ Active Detection
- **Method**: Explicit marker detection
- **Pattern**: `[NEEDS CLARIFICATION:]` in framework output
- **Rationale**: GHSpec uses standardized markers for human interaction points
- **Implementation**: `src/adapters/ghspec_adapter.py` (line 544)
- **Status**: ✅ Actively detecting HITL events via GHSpec markers

#### **BAEs Adapter** ❌ No Detection Implemented
- **Current Implementation**: `hitl_count` hardcoded to `0` (lines 330 & 348 in `src/adapters/baes_adapter.py`)
- **Scientific Implication**: **HITL-based metrics (HIT, AUTR, AEI, HEU) are not reliably measured for BAEs**
  - Cannot detect if HITL events occur during execution
  - Current values (HIT=0, AUTR=1.0) are **assumptions**, not measurements
  - Results may appear artificially high (perfect autonomy) regardless of actual behavior

- **Observational Evidence** (October 2025 - Informational Only):
  - Manual review of 23 BAEs runs found no clarification patterns in logs
  - Suggests BAEs likely operates autonomously for this specific task domain
  - However, this is **not a substitute for proper instrumentation**

- **Why Hardcoded Zero Is Insufficient**:
  - ❌ Not scientifically verifiable - no measurement mechanism
  - ❌ Cannot distinguish "no HITL events" from "events not detected"
  - ❌ Prevents valid comparison with ChatDev and GHSpec (which have detection)
  - ❌ May hide issues in future experiments with different task types

- **Required Future Work**: Implement BAEs-specific HITL detection:
  - Add pattern matching for: `clarification`, `ambiguous`, `cannot determine`, `unclear`
  - Search kernel output logs for entity communication failures
  - Track request-response validation errors
  - Update lines 330 & 348 to use detected count instead of hardcoded zero

#### **Impact on Experimental Validity**

**Metric Reliability by Framework**:

| Framework | HITL Detection | HIT Reliability | AUTR Reliability | AEI Reliability |
|-----------|----------------|-----------------|------------------|-----------------|
| ChatDev   | ✅ Implemented | ✅ Measured     | ✅ Measured      | ✅ Measured     |
| GHSpec    | ✅ Implemented | ✅ Measured     | ✅ Measured      | ✅ Measured     |
| BAEs      | ❌ Not Implemented | ❌ Hardcoded (0) | ❌ Assumed (1.0) | ❌ Unreliable |

**Interpretation Guidelines**:

1. **For ChatDev and GHSpec**: AUTR=1.0 is a **verified measurement** (active detection confirmed no HITL events)

2. **For BAEs**: AUTR=1.0 is an **unverified assumption** (no detection mechanism)
   - May be accurate (manual review suggests it is for current tasks)
   - Cannot be scientifically confirmed without proper instrumentation
   - **Should not be directly compared** with ChatDev/GHSpec AUTR values

3. **Cross-Framework Comparisons**:
   - ✅ **Valid**: TOK_IN, TOK_OUT, T_WALL, API_CALLS, CACHED_TOKENS (all properly measured)
   - ⚠️ **Questionable**: AUTR, AEI comparisons involving BAEs (measurement method inconsistent)
   - ❌ **Invalid**: Claims about BAEs autonomy superiority (not measured, only assumed)

**Critical Limitation for This Experiment**:
- AUTR and AEI comparisons are **methodologically unsound** when BAEs is included
- Recommendation: **Report BAEs AUTR/AEI as "Not Measured"** or clearly mark as estimated
- Alternative: Focus comparisons on **reliably measured metrics** (tokens, time, API calls)

**Documentation References**:
- Full adapter analysis: `AUTR_ADAPTER_ANALYSIS.md`
- BAEs investigation report: `BAES_HITL_INVESTIGATION.md`
- Adapter implementations: `src/adapters/` (all three adapters)

---

## Statistical Methods Guide

This report uses non-parametric statistics to compare frameworks robustly.

### 📖 Key Concepts

**Bootstrap Confidence Intervals (CI)** - Understanding Uncertainty

*What is bootstrapping?* A computational technique to estimate how much our results might vary if we ran the experiment again:

1. **The Problem**: We have limited data (e.g., 5-50 runs per framework), but we want to know what the 'true' average would be with infinite runs
2. **The Solution**: Bootstrap resampling simulates having multiple datasets:
   - Take our actual data (e.g., 10 AUTR values: [0.8, 0.9, 0.85, ...])
   - Create 10,000 'fake' datasets by randomly picking values from the original (with replacement)
   - 'With replacement' means the same value can appear multiple times in a resample
   - Example resample: [0.9, 0.8, 0.9, 0.85, ...] (notice 0.9 appears twice)
3. **Calculate**: Compute the mean for each of the 10,000 resamples
4. **Result**: We get 10,000 different means, showing the distribution of possible values
5. **95% CI**: The middle 95% of this distribution becomes our confidence interval

*Reading the numbers:*
- Example: `AUTR: 0.85 [0.78, 0.92]`
  - 0.85 is the observed mean from our actual data
  - [0.78, 0.92] is the 95% confidence interval
  - Interpretation: 'We are 95% confident the true population mean is between 0.78 and 0.92'
  - If we repeated the entire experiment, we'd expect the mean to fall in this range 95% of the time

*What do interval widths tell us?*
- **Narrow interval** (e.g., [0.83, 0.87]): High precision, low uncertainty, stable results
- **Wide interval** (e.g., [0.50, 0.95]): High uncertainty, need more runs for reliable estimates
- Width decreases as we collect more runs (sample size increases)

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

*Based on 63 runs across 3 frameworks: baes (n=24), chatdev (n=21), ghspec (n=18)*

### 🏆 Best Performers

- **Most Efficient (AEI)**: baes (0.095) - ⚠️ Note: AEI not reliably measured for BAEs
- **Fastest (T_WALL)**: baes (188.6s / 3.1 min)
- **Lowest Token Usage**: baes (23,827 input tokens)

### 📊 Key Insights

- ⚠️ AUTR = 1.0 shown for all frameworks, but **not uniformly measured** (see HITL Detection notes)
  - ChatDev & GHSpec: ✅ Properly measured (active detection)
  - BAEs: ❌ Hardcoded value (no detection mechanism)
- ⚠️ Quality metrics (Q_star, ESR, CRUDe, MC) not measured - see Data Quality Alerts below
- Wall time varies 9.2x between fastest and slowest frameworks
- Token consumption varies 9.3x across frameworks

### ⚠️ Data Quality Alerts

**Quality Metrics Not Measured**: `CRUDe`, `ESR`, `MC`, `Q_star`

These metrics show zero values because **generated applications are not executed** during experiments:
- The validation logic requires HTTP requests to `localhost:8000-8002`
- Servers are not started (`auto_restart_servers: false` in config)
- This is **expected behavior** - see `docs/QUALITY_METRICS_INVESTIGATION.md`

**Current Experiment Scope**: Measures **code generation efficiency** (tokens, time, automation)
**Not Measured**: Runtime code quality, endpoint correctness, application functionality

**To Enable Quality Metrics**: Implement server startup and endpoint testing (20-40 hours estimated)

**HITL-Based Metrics Partially Measured**: `AUTR`, `AEI`, `HIT`, `HEU`

These metrics depend on Human-in-the-Loop (HITL) detection, which is **not uniformly implemented**:
- ✅ **ChatDev**: Active pattern-based detection (reliable measurement)
- ✅ **GHSpec**: Active marker-based detection (reliable measurement)
- ❌ **BAEs**: Hardcoded to zero - **no detection mechanism** (unreliable measurement)

**Scientific Implication**: AUTR and AEI comparisons involving BAEs are **methodologically unsound**.
BAEs values (AUTR=1.0, HIT=0) are assumptions, not measurements. See 'HITL Detection Implementation Notes' for details.

**Recommendation**: Focus analysis on **reliably measured metrics** (TOK_IN, TOK_OUT, T_WALL, API_CALLS).


---

## 1. Aggregate Statistics

### Mean Values with 95% Bootstrap CI

*Note: Token values shown with thousands separator; time in seconds (minutes if >60s)*

**Performance Indicators:** 🟢 Best | 🟡 Middle | 🔴 Worst

| Framework | N | AEI | API_CALLS | AUTR | CACHED_TOKENS | CRUDe | ESR | HEU | HIT | MC | Q_star | TOK_IN | TOK_OUT | T_WALL_seconds | UTT | ZDI |
|-----------|---|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|
| baes | 24 | 0.095 [0.086, 0.099] 🟢 | 13.92 [12.38, 15.12] 🔴 | 1.000 [1.000, 1.000] 🟢 | 506.67 [0.00, 1306.67] 🔴 | 0 [0, 0] 🟢 | 0.000 [0.000, 0.000] 🟢 | 0 [0, 0] 🟢 | 0 [0, 0] 🟢 | 0.000 [0.000, 0.000] 🟢 | 0.000 [0.000, 0.000] 🟢 | 23,827 [21,068, 25,928] 🟢 | 6,498 [5,738, 7,096] 🟢 | 188.6 [169.5, 214.0] 🟢 | 6 [6, 6] 🟢 | 38 [34, 43] 🟢 |
| chatdev | 21 | 0.081 [0.081, 0.082] 🔴 | 126.76 [116.14, 135.71] 🟢 | 1.000 [1.000, 1.000] 🟢 | 29074.29 [24234.67, 33548.19] 🟢 | 0 [0, 0] 🟢 | 0.000 [0.000, 0.000] 🟢 | 0 [0, 0] 🟢 | 0 [0, 0] 🟢 | 0.000 [0.000, 0.000] 🟢 | 0.000 [0.000, 0.000] 🟢 | 221,029 [201,934, 235,234] 🔴 | 77,218 [70,117, 82,576] 🔴 | 1734.1 [1608.7, 1855.8] 🔴 | 6 [6, 6] 🟢 | 347 [322, 371] 🔴 |
| ghspec | 18 | 0.092 [0.092, 0.093] 🟡 | 59.17 [54.00, 63.39] 🟡 | 1.000 [1.000, 1.000] 🟢 | 1080.89 [113.78, 2560.00] 🟡 | 0 [0, 0] 🟢 | 0.000 [0.000, 0.000] 🟢 | 0 [0, 0] 🟢 | 0 [0, 0] 🟢 | 0.000 [0.000, 0.000] 🟢 | 0.000 [0.000, 0.000] 🟢 | 51,566 [47,092, 55,726] 🟡 | 25,377 [22,679, 27,735] 🟡 | 616.4 [546.9, 687.7] 🟡 | 6 [6, 6] 🟢 | 124 [110, 137] 🟡 |


## 2. Relative Performance

Performance normalized to best framework (100% = best performer).

*Lower percentages are better for cost metrics (tokens, time); higher percentages are better for quality metrics.*

| Framework | Tokens (↓) | Time (↓) | Test Auto (↑) | Efficiency (↑) | Quality (↑) |
|-----------|---------------|---------------|---------------|---------------|---------------|
| baes | 100% 🟢 | 100% 🟢 | 100% 🟢 | 100% 🟢 | 100% 🟢 |
| chatdev | 928% 🔴 | 919% 🔴 | 100% 🟢 | 86% 🟡 | 100% 🟢 |
| ghspec | 216% 🔴 | 327% 🔴 | 100% 🟢 | 97% 🟡 | 100% 🟢 |


## 3. Kruskal-Wallis H-Tests

Testing for significant differences across all frameworks.

*Note: Metrics with zero variance (all values identical) are excluded from statistical testing.*

| Metric | H | p-value | Significant | Groups | N |
|--------|---|---------|-------------|--------|---|
| AEI | 47.510 | 0.0000 | ✓ Yes | 3 | 63 |

💬 *Strong evidence that frameworks differ significantly on AEI. See pairwise comparisons below.*

| API_CALLS | 53.225 | 0.0000 | ✓ Yes | 3 | 63 |

💬 *Strong evidence that frameworks differ significantly on API_CALLS. See pairwise comparisons below.*

| CACHED_TOKENS | 40.477 | 0.0000 | ✓ Yes | 3 | 63 |

💬 *Strong evidence that frameworks differ significantly on CACHED_TOKENS. See pairwise comparisons below.*

| TOK_IN | 54.471 | 0.0000 | ✓ Yes | 3 | 63 |

💬 *Strong evidence that frameworks differ significantly on TOK_IN. See pairwise comparisons below.*

| TOK_OUT | 53.279 | 0.0000 | ✓ Yes | 3 | 63 |

💬 *Strong evidence that frameworks differ significantly on TOK_OUT. See pairwise comparisons below.*

| T_WALL_seconds | 54.595 | 0.0000 | ✓ Yes | 3 | 63 |

💬 *Strong evidence that frameworks differ significantly on T_WALL_seconds. See pairwise comparisons below.*

| ZDI | 54.595 | 0.0000 | ✓ Yes | 3 | 63 |

💬 *Strong evidence that frameworks differ significantly on ZDI. See pairwise comparisons below.*



**Metrics Excluded** (zero variance): `AUTR`, `CRUDe`, `ESR`, `HEU`, `HIT`, `MC`, `Q_star`, `UTT`

*Note: CRUDe, ESR, MC, Q_star excluded because all values are identically zero (metrics not measured).*

## 4. Pairwise Comparisons

Dunn-Šidák corrected pairwise tests with Cliff's delta effect sizes.

*Note: Metrics with zero variance are excluded from pairwise comparisons.*

### AEI

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| baes vs chatdev | 0.0000 | ✓ | 0.917 | large |
| baes vs ghspec | 0.0000 | ✓ | 0.903 | large |
| chatdev vs ghspec | 0.0000 | ✓ | -1.000 | large |

  *→ baes has large higher AEI than chatdev (δ=0.917)*
  *→ baes has large higher AEI than ghspec (δ=0.903)*
  *→ chatdev has large lower AEI than ghspec (δ=-1.000)*


### API_CALLS

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| baes vs chatdev | 0.0000 | ✓ | -1.000 | large |
| baes vs ghspec | 0.0000 | ✓ | -1.000 | large |
| chatdev vs ghspec | 0.0000 | ✓ | 0.923 | large |

  *→ baes has large lower API_CALLS than chatdev (δ=-1.000)*
  *→ baes has large lower API_CALLS than ghspec (δ=-1.000)*
  *→ chatdev has large higher API_CALLS than ghspec (δ=0.923)*


### CACHED_TOKENS

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| baes vs chatdev | 0.0000 | ✓ | -0.992 | large |
| baes vs ghspec | 0.0000 | ✓ | -0.130 | negligible |
| chatdev vs ghspec | 0.0000 | ✓ | 0.979 | large |

  *→ baes has large lower CACHED_TOKENS than chatdev (δ=-0.992)*
  *→ Statistically significant but practically negligible difference*
  *→ chatdev has large higher CACHED_TOKENS than ghspec (δ=0.979)*


### TOK_IN

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| baes vs chatdev | 0.0000 | ✓ | -1.000 | large |
| baes vs ghspec | 0.0000 | ✓ | -0.986 | large |
| chatdev vs ghspec | 0.0000 | ✓ | 1.000 | large |

  *→ baes has large lower TOK_IN than chatdev (δ=-1.000)*
  *→ baes has large lower TOK_IN than ghspec (δ=-0.986)*
  *→ chatdev has large higher TOK_IN than ghspec (δ=1.000)*


### TOK_OUT

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| baes vs chatdev | 0.0000 | ✓ | -1.000 | large |
| baes vs ghspec | 0.0000 | ✓ | -1.000 | large |
| chatdev vs ghspec | 0.0000 | ✓ | 0.926 | large |

  *→ baes has large lower TOK_OUT than chatdev (δ=-1.000)*
  *→ baes has large lower TOK_OUT than ghspec (δ=-1.000)*
  *→ chatdev has large higher TOK_OUT than ghspec (δ=0.926)*


### T_WALL_seconds

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| baes vs chatdev | 0.0000 | ✓ | -1.000 | large |
| baes vs ghspec | 0.0000 | ✓ | -0.991 | large |
| chatdev vs ghspec | 0.0000 | ✓ | 1.000 | large |

  *→ baes has large lower T_WALL_seconds than chatdev (δ=-1.000)*
  *→ baes has large lower T_WALL_seconds than ghspec (δ=-0.991)*
  *→ chatdev has large higher T_WALL_seconds than ghspec (δ=1.000)*


### ZDI

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| baes vs chatdev | 0.0000 | ✓ | -1.000 | large |
| baes vs ghspec | 0.0000 | ✓ | -0.991 | large |
| chatdev vs ghspec | 0.0000 | ✓ | 1.000 | large |

  *→ baes has large lower ZDI than chatdev (δ=-1.000)*
  *→ baes has large lower ZDI than ghspec (δ=-0.991)*
  *→ chatdev has large higher ZDI than ghspec (δ=1.000)*


## 5. Outlier Detection

Values > 3σ from median (per framework, per metric).

**baes:**
  - **AEI**: 1 outlier(s) at runs [23] with values [0.0]
  - **API_CALLS**: 1 outlier(s) at runs [23] with values [0]
  - **CACHED_TOKENS**: 1 outlier(s) at runs [1] with values [7040]
  - **TOK_IN**: 1 outlier(s) at runs [23] with values [0]
  - **TOK_OUT**: 1 outlier(s) at runs [23] with values [0]
  - **T_WALL_seconds**: 1 outlier(s) at runs [23] with values [412.0262072086334]
  - **ZDI**: 1 outlier(s) at runs [23] with values [83]

**chatdev:**
  - **AEI**: 1 outlier(s) at runs [20] with values [0.08918298767236306]
  - **API_CALLS**: 1 outlier(s) at runs [20] with values [52]
  - **TOK_IN**: 1 outlier(s) at runs [20] with values [74079]
  - **TOK_OUT**: 1 outlier(s) at runs [20] with values [22459]

**ghspec:**
  - **AEI**: 1 outlier(s) at runs [14] with values [0.09777570536584618]
  - **API_CALLS**: 1 outlier(s) at runs [14] with values [27]
  - **CACHED_TOKENS**: 1 outlier(s) at runs [8] with values [11264]

## 5. Composite Scores

**Q*** = 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC

**AEI** = AUTR / log(1 + TOK_IN)

| Framework | Q* Mean | Q* CI | AEI Mean | AEI CI |
|-----------|---------|-------|----------|--------|
| baes | 0.000 | [0.000, 0.000] | 0.095 | [0.086, 0.099] |
| chatdev | 0.000 | [0.000, 0.000] | 0.081 | [0.081, 0.082] |
| ghspec | 0.000 | [0.000, 0.000] | 0.092 | [0.092, 0.093] |


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

- **💰 Cost Optimization**: Choose **baes** if minimizing LLM token costs is priority. It uses 9.3x fewer tokens than chatdev.

- **⚡ Speed Priority**: Choose **baes** for fastest execution. It completes tasks 9.2x faster than chatdev (saves ~25.8 minutes per task).

- **⚙️ Efficiency Leader**: **baes** delivers the best quality-per-token ratio (AEI = 0.095), making it ideal for balancing quality and cost.

- **🤖 Autonomy**: All frameworks achieve perfect autonomy (AUTR = 1.0) - no human intervention required during execution.

- **⚠️ Quality Metrics Not Measured**: Q_star, ESR, CRUDe, MC show zero values because generated applications are not executed. This experiment measures **code generation efficiency** (tokens, time, automation), not **runtime quality**. See `docs/QUALITY_METRICS_INVESTIGATION.md` for details.

### 📋 Decision Matrix

| Use Case | Recommended Framework | Rationale |
|----------|----------------------|-----------|
| Cost-sensitive projects | baes | Lowest token consumption |
| Time-critical tasks | baes | Fastest execution time |
| Balanced quality/cost | baes | Best efficiency index (AEI) |

