# API Contract: EducationalContentGenerator

**Module**: `src.paper_generation.educational_content`  
**Class**: `EducationalContentGenerator`  
**Purpose**: Generate accessible, plain-language explanations for statistical concepts

---

## Class Constructor

### `__init__(self, reading_level: int = 8)`

**Description**: Initialize educational content generator with target reading level.

**Parameters**:
- `reading_level` (int): Target Flesch-Kincaid grade level (default 8 = 8th grade)

**Returns**: None

**Example**:
```python
generator = EducationalContentGenerator(reading_level=8)
```

---

## Public Methods

### `explain_statistical_test(self, test: StatisticalTest) -> str`

**Description**: Generate "What/Why/How" explanation for a statistical test.

**Parameters**:
- `test` (StatisticalTest): Test result object

**Returns**: Markdown-formatted explanation string

**Example**:
```python
test = StatisticalTest(test_name="Mann-Whitney U", p_value=0.032, ...)
explanation = generator.explain_statistical_test(test)
```

**Output Format**:
```markdown
📚 **What is this?**
The Mann-Whitney U test checks if two groups have different typical values, without assuming data follows a bell curve (normal distribution).

💡 **Why use it?**
Used because the data wasn't normally distributed (Shapiro-Wilk test p=0.012). This test is more reliable than a t-test when data is skewed.

📊 **Results**
- Test statistic: U = 42.5
- p-value: 0.032 (3.2% chance this difference is random luck)
- Conclusion: ✅ Significant difference detected (p < 0.05)

🎓 **How to interpret?**
ChatDev and MetaGPT have genuinely different execution times (not just random variation). The p-value of 0.032 means only 3.2% chance of seeing this difference if they were actually the same.
```

---

### `explain_effect_size(self, effect: EffectSize) -> str`

**Description**: Generate plain-language explanation with practical analogy for effect size.

**Parameters**:
- `effect` (EffectSize): Effect size object

**Returns**: Markdown-formatted explanation with analogy

**Example**:
```python
effect = EffectSize(measure="Cohen's d", value=0.72, magnitude="medium", ...)
explanation = generator.explain_effect_size(effect)
```

**Output Format**:
```markdown
📏 **What is this?**
Cohen's d measures HOW MUCH two groups differ, measured in standard deviations. It tells you if the difference is large enough to matter in practice.

📊 **Results**
- Effect size: d = 0.72 (medium)
- 95% Confidence Interval: [0.28, 1.16]
- Direction: ChatDev is faster than MetaGPT

💡 **Real-world analogy**
d = 0.72 is similar to the height difference between a typical 13-year-old and a typical 16-year-old. It's noticeable and meaningful, not just a tiny difference.

✅ **Practical meaning**
This is a **medium effect** - the difference is substantial enough to consider in practice. ChatDev is meaningfully faster, not just statistically different.
```

---

### `explain_power_analysis(self, power: PowerAnalysis) -> str`

**Description**: Generate researcher-friendly explanation of statistical power and sample size recommendations.

**Parameters**:
- `power` (PowerAnalysis): Power analysis object

**Returns**: Markdown-formatted explanation

**Example**:
```python
power = PowerAnalysis(achieved_power=0.54, recommended_n=13, ...)
explanation = generator.explain_power_analysis(power)
```

**Output Format**:
```markdown
⚡ **What is statistical power?**
Power is the probability your experiment will detect a real difference if it exists. Think of it like the sensitivity of a medical test.

📊 **Current status**
- Achieved power: 54% (with 5 runs per framework)
- Target power: 80% (standard scientific threshold)
- Status: ⚠️ Underpowered

⚠️ **What this means**
With only 5 runs, you have a 54% chance of detecting this effect size. That's like flipping a coin - too unreliable for confident conclusions.

✅ **Recommendation**
Increase to **13 runs per framework** to achieve 80% power. This ensures:
- 80% chance of detecting real differences
- More reliable and reproducible results
- Stronger evidence for publication
```

---

### `explain_visualization(self, viz: Visualization, data_context: Dict) -> str`

**Description**: Generate caption and reading guide for statistical plot.

**Parameters**:
- `viz` (Visualization): Visualization metadata
- `data_context` (Dict): Additional context (effect sizes, test results)

**Returns**: Markdown-formatted caption with reading guide

**Example**:
```python
viz = Visualization(plot_type="violin_plot", metric_name="execution_time", ...)
caption = generator.explain_visualization(viz, data_context)
```

**Output Format**:
```markdown
📊 **Figure: Violin Plot of Execution Time**

![Execution time distribution](figures/statistical/violin_execution_time.svg)

**How to read this plot:**
- **Width**: Shows how common each value is (wider = more data points)
- **White dot**: Median (middle value)
- **Thick bar**: Middle 50% of data (between Q1 and Q3)
- **Thin line**: Range of most data (excluding outliers)

**What this shows:**
ChatDev (median 45s) is consistently faster than MetaGPT (median 78s). ChatDev's distribution is tighter (less variation), while MetaGPT shows more spread.

**Statistical evidence:**
- Mann-Whitney U test: p = 0.032 (significant)
- Cliff's delta = 0.65 (medium-large effect)
- This difference is both statistically significant AND practically meaningful.
```

---

### `generate_quick_start_guide(self, findings: StatisticalFindings) -> str`

**Description**: Create beginner-friendly guide for reading the statistical report.

**Parameters**:
- `findings` (StatisticalFindings): Complete analysis results

**Returns**: Markdown-formatted Quick Start Guide

**Example**:
```python
guide = generator.generate_quick_start_guide(findings)
```

**Output Format**:
```markdown
# 🎓 Quick Start Guide: Understanding Your Statistical Report

## For Beginners: Read This First

### Where to Start
1. **Executive Summary** (Section 1) - The bottom line in plain English
2. **Key Findings** (Section 2.1) - Main takeaways with effect sizes
3. **Visualizations** (Section 3) - Pictures tell the story

### If You Want More Details
4. **Methodology** (Section 4) - What tests were used and why
5. **Power Analysis** (Section 5) - Do you need more data?

### Skip (Unless You're a Statistician)
- Raw test statistics and technical assumptions

## Understanding the Icons
- 📚 **What is this?** - Explains concepts simply
- 💡 **Why use it?** - Justifies the method choice
- 📊 **Results** - The actual numbers
- ✅ **How to interpret?** - What it means for you
- ⚠️ **Warning** - Important limitations
- 🎓 **Analogy** - Real-world comparison

## Key Terms (Plain Language)

**p-value**: Probability the difference is just random luck (lower = more confident)
- p < 0.05 = "statistically significant" (reliable difference)
- p > 0.05 = "not significant" (could be random chance)

**Effect size**: HOW MUCH groups differ (more important than p-value!)
- Small (d=0.2): Noticeable to statisticians, not to users
- Medium (d=0.5): Noticeable in practice
- Large (d=0.8): Obvious difference

**Statistical power**: Probability of detecting a real effect
- 80% = Standard scientific threshold
- <80% = Need more runs for reliable results

**Confidence interval (CI)**: Range where the true value likely falls
- Narrow CI = More precise estimate
- Wide CI = More uncertainty, need more data

## Common Questions

**Q: Can I trust a "significant" result (p<0.05)?**
A: Yes, but ALSO check the effect size. Statistical significance just means it's not random - effect size tells you if it MATTERS.

**Q: What if my power is low (<80%)?**
A: Your results might be real, but you risk missing real differences. Consider adding more runs as recommended.

**Q: Which metric should I focus on?**
A: Start with the primary metric ({findings.primary_metric}), then check if patterns are consistent across other metrics.

**Q: What if results contradict each other?**
A: This is normal! Different metrics measure different things. Focus on the metric most relevant to your research question.
```

---

### `generate_glossary(self) -> str`

**Description**: Create glossary of statistical terms with plain-language definitions.

**Returns**: Markdown-formatted glossary

**Output Format**:
```markdown
# 📖 Glossary of Statistical Terms

**ANOVA (Analysis of Variance)**: Statistical test comparing 3+ groups to see if at least one is different. Like a t-test, but for multiple groups at once.

**Bonferroni Correction**: Adjustment to prevent false positives when doing multiple tests. Makes the required p-value stricter (e.g., 0.05 → 0.017 for 3 comparisons).

**Box Plot**: Chart showing median (middle line), middle 50% of data (box), typical range (whiskers), and outliers (dots).

**Cliff's Delta (δ)**: Effect size for non-normal data. Ranges from -1 to +1. Measures probability that random value from group 1 > group 2.

**Cohen's d**: Effect size measured in standard deviations. d=0.5 means groups differ by half a standard deviation.

... [comprehensive glossary]
```

---

### `generate_analogy(self, concept: str, value: float) -> str`

**Description**: Generate relatable real-world analogy for statistical concept.

**Parameters**:
- `concept` (str): Statistical concept ("cohens_d", "power", "p_value")
- `value` (float): Numerical value to contextualize

**Returns**: Plain-language analogy string

**Examples**:
```python
# Cohen's d analogy
analogy = generator.generate_analogy("cohens_d", 0.8)
# "Like the height difference between a 13-year-old and an 18-year-old"

# Power analogy
analogy = generator.generate_analogy("power", 0.54)
# "Like a smoke detector that only works 54% of the time - better than nothing, but not reliable enough for critical decisions"

# p-value analogy
analogy = generator.generate_analogy("p_value", 0.032)
# "3.2% chance is like rolling a 20-sided die and getting a 1 - unlikely but possible"
```

**Analogy Database**:
```python
ANALOGIES = {
    "cohens_d": {
        0.2: "Height difference between siblings 1 year apart",
        0.5: "Height difference between 13 and 16 year-olds",
        0.8: "Height difference between 13 and 18 year-olds",
        1.2: "Height difference between 10 and 18 year-olds"
    },
    "power": {
        0.50: "Coin flip - too unreliable",
        0.65: "Better than guessing, but still risky",
        0.80: "Standard scientific threshold - reliable",
        0.95: "Very high confidence - excellent"
    },
    "cliffs_delta": {
        0.15: "Slight preference - like choosing chocolate vs vanilla",
        0.35: "Moderate preference - like choosing summer vs winter",
        0.50: "Strong preference - like choosing weekend vs Monday",
        0.70: "Very strong preference - like choosing vacation vs dentist"
    }
}
```

---

## Private Helper Methods

### `_validate_reading_level(self, text: str) -> Dict[str, float]`

**Description**: Compute readability scores for text.

**Parameters**:
- `text` (str): Text to analyze

**Returns**: Dict with scores:
  - `flesch_kincaid_grade`: Grade level (target ≤10)
  - `flesch_reading_ease`: Reading ease score (target 60-70)
  - `passes_target`: bool (within target range)

**Implementation**:
Uses Flesch-Kincaid formula:
```
FK Grade = 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
```

---

### `_simplify_technical_term(self, term: str, definition: str) -> str`

**Description**: Pair technical term with plain-language equivalent.

**Parameters**:
- `term` (str): Technical term (e.g., "heteroscedasticity")
- `definition` (str): Plain-language definition

**Returns**: Formatted string for inline use

**Example**:
```python
result = generator._simplify_technical_term(
    "heteroscedasticity",
    "unequal variance"
)
# "heteroscedasticity (unequal variance)"
```

---

### `_format_percentage(self, value: float) -> str`

**Description**: Format probability/proportion as intuitive percentage.

**Parameters**:
- `value` (float): Probability (0-1)

**Returns**: Formatted string with context

**Examples**:
```python
_format_percentage(0.032)  # "3.2% (about 3 in 100)"
_format_percentage(0.80)   # "80% (4 in 5)"
_format_percentage(0.001)  # "0.1% (1 in 1,000)"
```

---

## Constants

### EXPLANATION_TEMPLATES

**Description**: Dictionary of pre-written explanations for common statistical concepts.

**Structure**:
```python
EXPLANATION_TEMPLATES = {
    "shapiro_wilk": {
        "what": "Checks if your data follows a bell curve (normal distribution)",
        "why": "Determines which statistical tests are appropriate",
        "how": "p > 0.05 = normal, p < 0.05 = not normal",
        "example": "Test scores usually follow a bell curve (most B/C grades, fewer A/F)"
    },
    "mann_whitney": { ... },
    "cohens_d": { ... },
    # ... complete template library
}
```

---

## Dependencies

- `re`: For text parsing (word/sentence counting)
- `math`: For readability formula calculations
- `typing`: Type hints

**Optional** (development only):
- `textstat`: For automated readability scoring validation

---

## Quality Assurance

### Readability Validation

All generated explanations should pass:
1. Flesch-Kincaid grade level ≤ 10
2. Flesch reading ease ≥ 60
3. No undefined technical jargon
4. At least one analogy per complex concept

### User Testing Target

90%+ comprehension rate by non-statisticians when tested with:
- Graduate students (non-statistics backgrounds)
- Software engineers without ML experience
- Domain researchers (e.g., social scientists)

---

**Next**: Visualization generator contract.
