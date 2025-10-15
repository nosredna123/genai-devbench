# Statistical Analysis Report

**Generated:** 2025-10-15 12:37:44 UTC

**Frameworks:** chatdev

---

## 1. Aggregate Statistics

### Mean Values with 95% Bootstrap CI

| Framework | AEI | AUTR | CRUDe | ESR | HEU | HIT | MC | Q_star | TOK_IN | TOK_OUT | T_WALL_seconds | UTT | ZDI |
|-----------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|
| chatdev | 0.081 [0.081, 0.081] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 219917.000 [219917.000, 219917.000] | 78915.000 [78915.000, 78915.000] | 2023.125 [2023.125, 2023.125] | 6.000 [6.000, 6.000] | 405.000 [405.000, 405.000] |


## 2. Kruskal-Wallis H-Tests

Testing for significant differences across all frameworks.

| Metric | H | p-value | Significant | Groups | N |
|--------|---|---------|-------------|--------|---|
| AEI | 0.000 | 1.0000 | ✗ No | 1 | 1 |
| AUTR | 0.000 | 1.0000 | ✗ No | 1 | 1 |
| CRUDe | 0.000 | 1.0000 | ✗ No | 1 | 1 |
| ESR | 0.000 | 1.0000 | ✗ No | 1 | 1 |
| HEU | 0.000 | 1.0000 | ✗ No | 1 | 1 |
| HIT | 0.000 | 1.0000 | ✗ No | 1 | 1 |
| MC | 0.000 | 1.0000 | ✗ No | 1 | 1 |
| Q_star | 0.000 | 1.0000 | ✗ No | 1 | 1 |
| TOK_IN | 0.000 | 1.0000 | ✗ No | 1 | 1 |
| TOK_OUT | 0.000 | 1.0000 | ✗ No | 1 | 1 |
| T_WALL_seconds | 0.000 | 1.0000 | ✗ No | 1 | 1 |
| UTT | 0.000 | 1.0000 | ✗ No | 1 | 1 |
| ZDI | 0.000 | 1.0000 | ✗ No | 1 | 1 |


## 3. Pairwise Comparisons

Dunn-Šidák corrected pairwise tests with Cliff's delta effect sizes.

## 4. Outlier Detection

Values > 3σ from median (per framework, per metric).

No outliers detected.

## 5. Composite Scores

**Q*** = 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC

**AEI** = AUTR / log(1 + TOK_IN)

| Framework | Q* Mean | Q* CI | AEI Mean | AEI CI |
|-----------|---------|-------|----------|--------|
| chatdev | 0.000 | [0.000, 0.000] | 0.081 | [0.081, 0.081] |

