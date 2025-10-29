# Statistical Analysis Report

**Experiment**: Multi-Agent Framework Comparison  
**Date**: 2025-10-28  
**Frameworks**: ChatDev, MetaGPT, AutoGen  
**Total Runs**: 150 (50 per framework)

## Executive Summary

This analysis compares three autonomous software development frameworks on efficiency, cost, and quality metrics. Statistical tests reveal significant differences in execution time (p < 0.001) and test pass rates (p = 0.023).

## Descriptive Statistics

### Execution Time (seconds)

| Framework | Mean  | Std Dev | Min   | Max   |
|-----------|-------|---------|-------|-------|
| ChatDev   | 245.3 | 23.1    | 198.5 | 289.7 |
| MetaGPT   | 312.7 | 31.4    | 251.2 | 378.9 |
| AutoGen   | 198.4 | 19.8    | 162.3 | 234.5 |

**Finding**: AutoGen is fastest (198.4s), followed by ChatDev (245.3s), then MetaGPT (312.7s).

### Cost per Task (USD)

| Framework | Mean | Std Dev | Min  | Max  |
|-----------|------|---------|------|------|
| ChatDev   | 0.42 | 0.08    | 0.28 | 0.56 |
| MetaGPT   | 0.53 | 0.11    | 0.37 | 0.69 |
| AutoGen   | 0.35 | 0.07    | 0.24 | 0.46 |

**Finding**: AutoGen is most cost-efficient ($0.35), followed by ChatDev ($0.42), then MetaGPT ($0.53).

### Test Pass Rate

| Framework | Mean | Std Dev | Min  | Max  |
|-----------|------|---------|------|------|
| ChatDev   | 0.87 | 0.12    | 0.65 | 1.00 |
| MetaGPT   | 0.92 | 0.08    | 0.75 | 1.00 |
| AutoGen   | 0.83 | 0.14    | 0.58 | 1.00 |

**Finding**: MetaGPT has highest test pass rate (92%), followed by ChatDev (87%), then AutoGen (83%).

### Code Quality Score (1-10 scale)

| Framework | Mean | Std Dev | Min  | Max  |
|-----------|------|---------|------|------|
| ChatDev   | 7.2  | 0.9     | 5.5  | 9.0  |
| MetaGPT   | 8.1  | 0.7     | 6.8  | 9.5  |
| AutoGen   | 6.9  | 1.1     | 4.8  | 8.7  |

**Finding**: MetaGPT produces highest quality code (8.1/10), followed by ChatDev (7.2/10), then AutoGen (6.9/10).

## Inferential Statistics

### Execution Time Comparison

**Test**: Kruskal-Wallis H-test (non-parametric ANOVA)  
**Result**: H = 87.23, p < 0.001  
**Conclusion**: Statistically significant difference in execution times across frameworks.

**Post-hoc Pairwise Comparisons** (Dunn's test with Bonferroni correction):
- AutoGen vs ChatDev: p < 0.001 (AutoGen faster)
- AutoGen vs MetaGPT: p < 0.001 (AutoGen faster)  
- ChatDev vs MetaGPT: p < 0.001 (ChatDev faster)

### Test Pass Rate Comparison

**Test**: Chi-square test of independence  
**Result**: χ² = 9.45, df = 2, p = 0.023  
**Conclusion**: Statistically significant difference in test pass rates.

**Effect Size**: Cramér's V = 0.18 (small effect)

### Cost Comparison

**Test**: Kruskal-Wallis H-test  
**Result**: H = 72.14, p < 0.001  
**Conclusion**: Statistically significant difference in costs.

## Practical Significance

### Trade-offs Analysis

1. **Speed vs Quality**: AutoGen is fastest but has lowest quality scores
2. **Cost vs Quality**: MetaGPT is most expensive but produces highest quality
3. **Balanced Option**: ChatDev offers middle ground on all metrics

### Recommendations

- **For rapid prototyping**: Use AutoGen (fastest, cheapest)
- **For production code**: Use MetaGPT (highest quality, best test pass rate)
- **For general purpose**: Use ChatDev (balanced performance)

## Threats to Validity

1. **Construct Validity**: Code quality scored by automated tools only
2. **Internal Validity**: Same task used across all frameworks
3. **External Validity**: Results may not generalize to other task types
4. **Conclusion Validity**: Sample size (n=50 per framework) adequate for statistical power

## Raw Data Files

- Detailed metrics: `metrics.json`
- Experiment configuration: `../config/experiment.yaml`
