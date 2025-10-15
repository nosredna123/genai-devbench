# Statistical Analysis Report

**Generated:** 2025-10-15 21:05:08 UTC

**Frameworks:** ghspec, chatdev

---

## 1. Aggregate Statistics

### Mean Values with 95% Bootstrap CI

| Framework | AEI | AUTR | CRUDe | ESR | HEU | HIT | MC | Q_star | TOK_IN | TOK_OUT | T_WALL_seconds | UTT | ZDI |
|-----------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|------------|
| ghspec | 0.091 [0.091, 0.091] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 59040.000 [59040.000, 59040.000] | 23542.000 [23542.000, 23542.000] | 718.730 [718.730, 718.730] | 6.000 [6.000, 6.000] | 144.000 [144.000, 144.000] |
| chatdev | 0.081 [0.081, 0.081] | 1.000 [1.000, 1.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 217055.000 [217055.000, 217055.000] | 74482.000 [74482.000, 74482.000] | 1748.347 [1748.347, 1748.347] | 6.000 [6.000, 6.000] | 350.000 [350.000, 350.000] |


## 2. Kruskal-Wallis H-Tests

Testing for significant differences across all frameworks.

| Metric | H | p-value | Significant | Groups | N |
|--------|---|---------|-------------|--------|---|
| AEI | 0.000 | 1.0000 | ✗ No | 2 | 2 |
| AUTR | 0.000 | 1.0000 | ✗ No | 2 | 2 |
| CRUDe | 0.000 | 1.0000 | ✗ No | 2 | 2 |
| ESR | 0.000 | 1.0000 | ✗ No | 2 | 2 |
| HEU | 0.000 | 1.0000 | ✗ No | 2 | 2 |
| HIT | 0.000 | 1.0000 | ✗ No | 2 | 2 |
| MC | 0.000 | 1.0000 | ✗ No | 2 | 2 |
| Q_star | 0.000 | 1.0000 | ✗ No | 2 | 2 |
| TOK_IN | 0.000 | 1.0000 | ✗ No | 2 | 2 |
| TOK_OUT | 0.000 | 1.0000 | ✗ No | 2 | 2 |
| T_WALL_seconds | 0.000 | 1.0000 | ✗ No | 2 | 2 |
| UTT | 0.000 | 1.0000 | ✗ No | 2 | 2 |
| ZDI | 0.000 | 1.0000 | ✗ No | 2 | 2 |


## 3. Pairwise Comparisons

Dunn-Šidák corrected pairwise tests with Cliff's delta effect sizes.

### AEI

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | 1.000 | large |


### AUTR

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | 0.000 | negligible |


### CRUDe

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | 0.000 | negligible |


### ESR

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | 0.000 | negligible |


### HEU

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | 0.000 | negligible |


### HIT

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | 0.000 | negligible |


### MC

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | 0.000 | negligible |


### Q_star

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | 0.000 | negligible |


### TOK_IN

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | -1.000 | large |


### TOK_OUT

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | -1.000 | large |


### T_WALL_seconds

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | -1.000 | large |


### UTT

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | 0.000 | negligible |


### ZDI

| Comparison | p-value | Significant | Cliff's δ | Effect Size |
|------------|---------|-------------|-----------|-------------|
| ghspec vs chatdev | 0.3173 | ✗ | -1.000 | large |


## 4. Outlier Detection

Values > 3σ from median (per framework, per metric).

No outliers detected.

## 5. Composite Scores

**Q*** = 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC

**AEI** = AUTR / log(1 + TOK_IN)

| Framework | Q* Mean | Q* CI | AEI Mean | AEI CI |
|-----------|---------|-------|----------|--------|
| ghspec | 0.000 | [0.000, 0.000] | 0.091 | [0.091, 0.091] |
| chatdev | 0.000 | [0.000, 0.000] | 0.081 | [0.081, 0.081] |

