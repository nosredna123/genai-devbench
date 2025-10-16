# Statistical Analysis Report

**Generated:** 2025-10-16 13:26:53 UTC

**Frameworks:** ghspec, chatdev, baes

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

| Framework | AEI | AUTR | CRUDe | ESR | HEU | HIT | MC | Q_star | TOK_IN | TOK_OUT | T_WALL_seconds | UTT | ZDI |
|-----------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|
| ghspec | 0.109 [0.091, 0.128] | 1.000 [1.000, 1.000] | 0 [0, 0] | 0.000 [0.000, 0.000] | 0 [0, 0] | 0 [0, 0] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 30,772 [2,503, 59,040] | 12,234 [925, 23,542] | 399.5 [80.3, 718.7] | 6 [6, 6] | 80 [17, 144] |
| chatdev | 0.081 [0.080, 0.081] | 1.000 [1.000, 1.000] | 0 [0, 0] | 0.000 [0.000, 0.000] | 0 [0, 0] | 0 [0, 0] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 240,714 [217,055, 264,373] | 75,653 [74,482, 76,824] | 1781.5 [1748.3, 1814.7] | 6 [6, 6] | 356 [350, 363] |
| baes | 0.099 [0.099, 0.099] | 1.000 [1.000, 1.000] | 0 [0, 0] | 0.000 [0.000, 0.000] | 0 [0, 0] | 0 [0, 0] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 25,607 [25,607, 25,607] | 6,694 [6,694, 6,694] | 238.5 [238.5, 238.5] | 6 [6, 6] | 48 [48, 48] |


## 2. Kruskal-Wallis H-Tests

Testing for significant differences across all frameworks.

| Metric | H | p-value | Significant | Groups | N |
|--------|---|---------|-------------|--------|---|
| AEI | 3.000 | 0.2231 | ✗ No | 3 | 5 |
| AUTR | 0.000 | 1.0000 | ✗ No | 3 | 5 |
| CRUDe | 0.000 | 1.0000 | ✗ No | 3 | 5 |
| ESR | 0.000 | 1.0000 | ✗ No | 3 | 5 |
| HEU | 0.000 | 1.0000 | ✗ No | 3 | 5 |
| HIT | 0.000 | 1.0000 | ✗ No | 3 | 5 |
| MC | 0.000 | 1.0000 | ✗ No | 3 | 5 |
| Q_star | 0.000 | 1.0000 | ✗ No | 3 | 5 |
| TOK_IN | 3.000 | 0.2231 | ✗ No | 3 | 5 |
| TOK_OUT | 3.000 | 0.2231 | ✗ No | 3 | 5 |
| T_WALL_seconds | 3.000 | 0.2231 | ✗ No | 3 | 5 |
| UTT | 0.000 | 1.0000 | ✗ No | 3 | 5 |
| ZDI | 3.000 | 0.2231 | ✗ No | 3 | 5 |


## 3. Pairwise Comparisons

Dunn-Šidák corrected pairwise tests with Cliff's delta effect sizes.

### AEI

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | 1.000 | large |
| ghspec vs baes | 1.0000 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | -1.000 | large |


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


### TOK_OUT

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | -1.000 | large |
| ghspec vs baes | 1.0000 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 1.000 | large |


### T_WALL_seconds

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.1213 | ✗ | -1.000 | large |
| ghspec vs baes | 1.0000 | ✗ | 0.000 | negligible |
| chatdev vs baes | 0.2207 | ✗ | 1.000 | large |


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


## 4. Outlier Detection

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

