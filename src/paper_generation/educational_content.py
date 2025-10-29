"""
Educational Content Generator for Statistical Reports

Provides didactic "What/Why/How" explanations for statistical tests, plots,
and concepts to make statistics accessible to non-statisticians.

Target reading level: 8th grade (accessible to researchers without statistics background)
"""

from typing import Dict, Any
from .statistical_analyzer import (
    StatisticalTest, EffectSize, PowerAnalysis, AssumptionCheck,
    StatisticalFindings, TestType, EffectSizeMeasure
)


# T015: Explanation templates for all statistical concepts
EXPLANATION_TEMPLATES = {
    "shapiro_wilk": {
        "what": "The Shapiro-Wilk test checks if your data follows a bell curve (normal distribution)",
        "why": "Many statistical tests assume data is normally distributed. This test tells us if that assumption is reasonable",
        "how_to_interpret": {
            "passes": "✅ Data appears normally distributed - we can use standard statistical tests",
            "fails": "⚠️ Data is not normally distributed - we'll use non-parametric tests instead"
        }
    },
    "levene": {
        "what": "Levene's test checks if different groups have similar spread (variance)",
        "why": "Some tests assume all groups vary by the same amount. This test validates that assumption",
        "how_to_interpret": {
            "passes": "✅ Groups have similar variance - standard tests are appropriate",
            "fails": "⚠️ Groups have different variances - we'll use tests that don't assume equal variance"
        }
    },
    "t_test": {
        "what": "The t-test compares the average values of two groups",
        "why": "It tells us if the difference between groups is real or just random chance",
        "how_to_interpret": {
            "significant": "The groups are genuinely different (not just random variation)",
            "not_significant": "Any difference we see could easily be due to chance"
        },
        "assumptions": "Requires normally distributed data with similar variances in both groups"
    },
    "mann_whitney": {
        "what": "The Mann-Whitney U test compares two groups without assuming a normal distribution",
        "why": "It's a robust alternative to the t-test when data is skewed or has outliers",
        "how_to_interpret": {
            "significant": "One group tends to have systematically higher/lower values than the other",
            "not_significant": "The groups overlap substantially - no clear systematic difference"
        },
        "assumptions": "Makes fewer assumptions than t-test - works with any distribution shape"
    },
    "anova": {
        "what": "ANOVA (Analysis of Variance) compares averages across three or more groups",
        "why": "It tells us if at least one group is different from the others",
        "how_to_interpret": {
            "significant": "At least one group differs significantly from the others",
            "not_significant": "All groups are statistically similar"
        },
        "assumptions": "Requires normally distributed data with similar variances across all groups"
    },
    "kruskal_wallis": {
        "what": "The Kruskal-Wallis test compares three or more groups without assuming normality",
        "why": "It's a robust alternative to ANOVA when data is skewed or has outliers",
        "how_to_interpret": {
            "significant": "At least one group systematically differs from the others",
            "not_significant": "All groups have similar distributions"
        },
        "assumptions": "Makes fewer assumptions than ANOVA - works with any distribution shape"
    },
    "cohens_d": {
        "what": "Cohen's d measures how far apart two group averages are, in standard deviation units",
        "why": "Statistical significance (p-value) doesn't tell you if the difference matters practically. Effect size does.",
        "interpretation_guide": {
            "negligible": "< 0.2: Tiny difference, probably not practically important",
            "small": "0.2-0.5: Small but potentially meaningful difference",
            "medium": "0.5-0.8: Moderate difference, likely to be noticeable",
            "large": "≥ 0.8: Large difference, definitely important in practice"
        },
        "analogy": "Like measuring height difference between adults and teenagers in 'standard person heights'"
    },
    "cliffs_delta": {
        "what": "Cliff's Delta measures how often one group's values exceed the other group's values",
        "why": "It's a non-parametric effect size that works when data isn't normally distributed",
        "interpretation_guide": {
            "negligible": "< 0.147: Groups overlap almost completely",
            "small": "0.147-0.33: Noticeable but modest separation",
            "medium": "0.33-0.474: Clear separation between groups",
            "large": "≥ 0.474: Groups are distinctly different"
        },
        "analogy": "Like asking: if you pick one random value from each group, what's the probability the first is larger?"
    },
    "power_analysis": {
        "what": "Statistical power is the probability of detecting a real effect if it exists",
        "why": "Low power means you might miss real differences. High power means you're likely to detect them.",
        "interpretation_guide": {
            "adequate": "≥ 80%: Good chance of detecting real effects",
            "borderline": "70-80%: Marginal - might miss some real effects",
            "inadequate": "< 70%: High risk of missing real differences (Type II error)"
        },
        "recommendation": "Aim for 80% power. If you have low power, collect more data."
    }
}

# T019: Analogies database for concrete understanding
ANALOGIES = {
    "cohens_d": {
        0.2: "Like the height difference between 15 and 16 year olds - small but measurable",
        0.5: "Like the height difference between 13 and 18 year olds - clearly noticeable",
        0.8: "Like the height difference between 14 year old girls and adult men - very obvious",
        1.2: "Like comparing elementary school children to professional basketball players"
    },
    "cliffs_delta": {
        0.15: "Imagine two overlapping circles - you can barely tell them apart",
        0.33: "Like comparing test scores of B students vs A students - overlap but clearly different",
        0.47: "Like comparing amateur athletes to semi-professionals - distinct groups",
        0.70: "Like comparing high school players to Olympic athletes - almost no overlap"
    },
    "power": {
        0.50: "Flipping a coin to detect differences - might as well guess",
        0.70: "Like a smoke detector with old batteries - works sometimes but unreliable",
        0.80: "Like a reliable car - usually gets you where you need to go",
        0.95: "Like a high-precision instrument - rarely misses what it's looking for"
    }
}


class EducationalContentGenerator:
    """
    Generates educational explanations for statistical content.
    
    Produces What/Why/How sections, analogies, and glossaries to make
    statistics accessible to researchers without statistics background.
    
    Target: 8th grade reading level with domain-appropriate terminology.
    """
    
    def __init__(self, reading_level: int = 8):
        """
        Initialize educational content generator.
        
        Args:
            reading_level: Target grade level for explanations (default: 8)
        """
        self.reading_level = reading_level
        self.templates = EXPLANATION_TEMPLATES
        self.analogies = ANALOGIES
    
    # T016: Explain statistical tests
    def explain_statistical_test(self, test: StatisticalTest) -> str:
        """
        Generate educational explanation for a statistical test.
        
        Args:
            test: StatisticalTest object with test results
        
        Returns:
            Markdown-formatted explanation with What/Why/Results/How sections
        
        Example:
            >>> test = StatisticalTest(test_type=TestType.MANN_WHITNEY, ...)
            >>> explanation = generator.explain_statistical_test(test)
            >>> print(explanation)
        """
        test_key = test.test_type.value
        template = self.templates.get(test_key, {})
        
        explanation = []
        
        # Header
        test_name = test_key.replace('_', ' ').title()
        explanation.append(f"### 📚 Understanding the {test_name}\n")
        
        # What section
        if "what" in template:
            explanation.append(f"**What is this test?**\n")
            explanation.append(f"{template['what']}\n")
        
        # Why section
        if "why" in template:
            explanation.append(f"**💡 Why did we use it?**\n")
            explanation.append(f"{template['why']}\n")
            if test.rationale:
                explanation.append(f"*Specific reason:* {test.rationale}\n")
        
        # Results section
        explanation.append(f"**📊 What did we find?**\n")
        explanation.append(f"- Groups compared: {', '.join(test.groups)}\n")
        explanation.append(f"- Test statistic: {test.statistic:.4f}\n")
        explanation.append(f"- p-value: {test.p_value:.4f}\n")
        explanation.append(f"- Result: {'Significant difference detected' if test.is_significant else 'No significant difference'}\n")
        
        # Interpretation section
        explanation.append(f"**🎓 How to interpret this:**\n")
        
        if "how_to_interpret" in template:
            key = "significant" if test.is_significant else "not_significant"
            if key in template["how_to_interpret"]:
                explanation.append(f"{template['how_to_interpret'][key]}\n")
        
        # Add the test's own interpretation
        if test.interpretation:
            explanation.append(f"\n*In plain English:* {test.interpretation}\n")
        
        # Assumptions note
        if "assumptions" in template:
            explanation.append(f"\n**ℹ️ Technical note:** {template['assumptions']}\n")
        
        return "\n".join(explanation)
    
    # T017: Explain effect sizes
    def explain_effect_size(self, effect: EffectSize) -> str:
        """
        Generate educational explanation for an effect size.
        
        Args:
            effect: EffectSize object with calculated effect
        
        Returns:
            Markdown-formatted explanation with What/Results/Analogy/Meaning sections
        
        Example:
            >>> effect = EffectSize(measure=EffectSizeMeasure.COHENS_D, ...)
            >>> explanation = generator.explain_effect_size(effect)
        """
        measure_key = effect.measure.value
        template = self.templates.get(measure_key, {})
        
        explanation = []
        
        # Header
        measure_name = "Cohen's d" if measure_key == "cohens_d" else "Cliff's Delta"
        explanation.append(f"### 📏 Effect Size: {measure_name}\n")
        
        # What section
        if "what" in template:
            explanation.append(f"**What is {measure_name}?**\n")
            explanation.append(f"{template['what']}\n")
        
        # Why section
        if "why" in template:
            explanation.append(f"**Why does it matter?**\n")
            explanation.append(f"{template['why']}\n")
        
        # Results section
        explanation.append(f"**📊 Your results:**\n")
        explanation.append(f"- Comparing: {effect.group1} vs {effect.group2}\n")
        explanation.append(f"- {measure_name} = {effect.value:.3f}\n")
        explanation.append(f"- 95% Confidence Interval: [{effect.ci_lower:.3f}, {effect.ci_upper:.3f}]\n")
        explanation.append(f"- Magnitude: **{effect.magnitude.upper()}**\n")
        
        # Interpretation guide
        if "interpretation_guide" in template:
            explanation.append(f"\n**Interpretation scale:**\n")
            for magnitude, desc in template["interpretation_guide"].items():
                marker = "👉" if magnitude == effect.magnitude else "  "
                explanation.append(f"{marker} {desc}\n")
        
        # Real-world analogy
        explanation.append(f"\n**💡 Real-world analogy:**\n")
        analogy = self.generate_analogy(measure_key, abs(effect.value))
        explanation.append(f"{analogy}\n")
        
        # Practical meaning
        explanation.append(f"\n**✅ What this means for your research:**\n")
        explanation.append(f"{effect.interpretation}\n")
        
        direction = "outperforms" if effect.value > 0 else "underperforms"
        explanation.append(f"\nBottom line: {effect.group1} {direction} {effect.group2} ")
        explanation.append(f"with a **{effect.magnitude}** practical difference.\n")
        
        return "\n".join(explanation)
    
    # T018: Explain power analysis
    def explain_power_analysis(self, power: PowerAnalysis) -> str:
        """
        Generate educational explanation for power analysis.
        
        Args:
            power: PowerAnalysis object with power calculations
        
        Returns:
            Markdown-formatted explanation with What/Status/Meaning/Recommendation sections
        
        Example:
            >>> power = PowerAnalysis(statistical_power=0.65, ...)
            >>> explanation = generator.explain_power_analysis(power)
        """
        template = self.templates.get("power_analysis", {})
        
        explanation = []
        
        # Header
        explanation.append(f"### ⚡ Statistical Power Analysis\n")
        
        # What section
        if "what" in template:
            explanation.append(f"**What is statistical power?**\n")
            explanation.append(f"{template['what']}\n")
        
        # Why section
        if "why" in template:
            explanation.append(f"**Why does it matter?**\n")
            explanation.append(f"{template['why']}\n")
        
        # Current status
        explanation.append(f"**📊 Your current situation:**\n")
        explanation.append(f"- Metric: {power.metric_name}\n")
        explanation.append(f"- Sample size: {power.n_group1} per group\n")
        explanation.append(f"- Achieved power: **{power.statistical_power:.1%}**\n")
        explanation.append(f"- Target power: {power.target_power:.0%} (conventional threshold)\n")
        explanation.append(f"- Status: {'✅ Adequate' if power.is_adequate else '⚠️ Inadequate'}\n")
        
        # Interpretation
        explanation.append(f"\n**⚠️ What this means:**\n")
        
        if power.statistical_power >= 0.80:
            category = "adequate"
            explanation.append(
                f"Great! With {power.statistical_power:.1%} power, you have a good chance "
                f"of detecting real effects if they exist. Your sample size is sufficient.\n"
            )
        elif power.statistical_power >= 0.70:
            category = "borderline"
            explanation.append(
                f"Your power ({power.statistical_power:.1%}) is borderline. "
                f"You might miss some real effects. Consider collecting more data if possible.\n"
            )
        else:
            category = "inadequate"
            miss_rate = (1 - power.statistical_power) * 100
            explanation.append(
                f"⚠️ Warning: With {power.statistical_power:.1%} power, "
                f"there's a {miss_rate:.0f}% chance of missing a real effect (Type II error). "
                f"Your sample size is likely too small.\n"
            )
        
        # Analogy
        explanation.append(f"\n**💡 Think of it this way:**\n")
        analogy = self.generate_analogy("power", power.statistical_power)
        explanation.append(f"{analogy}\n")
        
        # Recommendation
        explanation.append(f"\n**✅ Recommendation:**\n")
        if power.recommended_n_per_group and not power.is_adequate:
            additional = power.recommended_n_per_group - power.n_group1
            explanation.append(
                f"To achieve {power.target_power:.0%} power for detecting an effect size of "
                f"{power.effect_size:.2f}, you should collect **{additional} additional runs** "
                f"per group (target: {power.recommended_n_per_group} total per group).\n"
            )
        elif power.is_adequate:
            explanation.append(
                f"Your current sample size is adequate. No additional data collection needed "
                f"for this comparison.\n"
            )
        else:
            explanation.append(
                f"Consider collecting additional experimental runs to increase your "
                f"ability to detect real effects.\n"
            )
        
        return "\n".join(explanation)
    
    # T019: Generate analogies
    def generate_analogy(self, concept: str, value: float) -> str:
        """
        Generate real-world analogy for a statistical concept.
        
        Args:
            concept: Statistical concept (cohens_d, cliffs_delta, power)
            value: Numeric value to find analogy for
        
        Returns:
            Relatable real-world comparison string
        
        Example:
            >>> analogy = generator.generate_analogy("cohens_d", 0.8)
            >>> print(analogy)  # Returns height difference analogy
        """
        if concept not in self.analogies:
            return f"A {concept} of {value:.2f}"
        
        analogies = self.analogies[concept]
        
        # Find closest threshold
        thresholds = sorted(analogies.keys())
        closest_threshold = min(thresholds, key=lambda x: abs(x - abs(value)))
        
        return analogies[closest_threshold]
    
    # T020: Generate Quick Start Guide
    def generate_quick_start_guide(self, findings: StatisticalFindings) -> str:
        """
        Generate beginner-friendly Quick Start Guide for navigating report.
        
        Args:
            findings: StatisticalFindings with complete analysis results
        
        Returns:
            Markdown-formatted Quick Start Guide
        
        Example:
            >>> guide = generator.generate_quick_start_guide(findings)
        """
        guide = []
        
        guide.append("# 🚀 Quick Start: How to Read This Statistical Report\n")
        guide.append("*Don't know statistics? No problem! This guide will help you navigate.*\n\n")
        
        # Where to start
        guide.append("## 📍 Where to Start\n")
        guide.append("**If you just want the key findings:**\n")
        guide.append("1. Jump to the \"Executive Summary\" section below\n")
        guide.append("2. Look at the visualizations (pictures tell the story!)\n")
        guide.append("3. Read the \"Key Findings\" bullets\n\n")
        
        guide.append("**If you want to understand the statistics:**\n")
        guide.append("1. Each statistical test has a 📚 \"Understanding\" section\n")
        guide.append("2. Start with the \"What is this test?\" paragraph\n")
        guide.append("3. Skip the technical details unless you're curious\n")
        guide.append("4. Focus on the \"How to interpret\" section\n\n")
        
        # Icon legend
        guide.append("## 🎨 Icon Guide\n")
        guide.append("We use emojis to make the report easier to scan:\n\n")
        guide.append("- 📚 **Understanding** = What/Why explanations\n")
        guide.append("- 💡 **Why** = Rationale and reasoning\n")
        guide.append("- 📊 **Results** = Numbers and findings\n")
        guide.append("- 🎓 **Interpret** = What it means in plain English\n")
        guide.append("- ✅ **Recommendation** = What to do next\n")
        guide.append("- ⚠️ **Warning** = Important limitations or concerns\n")
        guide.append("- 📏 **Effect Size** = How big is the difference?\n")
        guide.append("- ⚡ **Power** = Can we trust these results?\n\n")
        
        # What to skip
        guide.append("## ⏭️ What You Can Skip (If You Want)\n")
        guide.append("These sections are for statistical review - feel free to skip:\n\n")
        guide.append("- Assumption validation details\n")
        guide.append("- Q-Q plots (unless you're checking normality)\n")
        guide.append("- Detailed test statistics\n")
        guide.append("- Methodology section (unless needed for peer review)\n\n")
        
        # Key terms
        guide.append("## 📖 Key Terms in 10 Seconds\n")
        guide.append("- **p-value**: Probability results are due to chance (lower = more confident)\n")
        guide.append("- **Effect size**: How big is the difference? (more important than p-value!)\n")
        guide.append("- **Confidence interval**: Range where true value likely falls (95% sure)\n")
        guide.append("- **Power**: Ability to detect real effects (want 80%+)\n")
        guide.append("- **Significant**: Unlikely to be random chance (p < 0.05)\n\n")
        
        # Common questions
        guide.append("## ❓ Common Questions\n\n")
        guide.append("**Q: What's more important - p-value or effect size?**\n")
        guide.append("A: Effect size! A tiny, meaningless difference can have p < 0.05 with enough data. ")
        guide.append("Focus on whether the effect size is large enough to matter.\n\n")
        
        guide.append("**Q: What if the test says 'not significant'?**\n")
        guide.append("A: Could mean (1) no real difference, (2) difference too small to detect, or ")
        guide.append("(3) not enough data. Check the power analysis!\n\n")
        
        guide.append("**Q: Which plot should I include in my paper?**\n")
        guide.append("A: Box plots show distributions clearly. Forest plots show effect sizes with uncertainty. ")
        guide.append("Pick what tells your story best.\n\n")
        
        guide.append("**Q: What's the difference between t-test and Mann-Whitney?**\n")
        guide.append("A: Both compare two groups. t-test assumes normal data. Mann-Whitney doesn't - ")
        guide.append("use it when data is skewed or has outliers.\n\n")
        
        # Report summary
        guide.append("## 📋 Your Report at a Glance\n")
        guide.append(f"- Experiment: {findings.experiment_name}\n")
        guide.append(f"- Metrics analyzed: {len(findings.metrics_analyzed)}\n")
        guide.append(f"- Statistical tests performed: {len(findings.statistical_tests)}\n")
        guide.append(f"- Significant results: {findings.n_significant_tests}/{len(findings.statistical_tests)}\n")
        guide.append(f"- Large effect sizes: {findings.n_large_effects}/{len(findings.effect_sizes)}\n")
        
        if findings.power_warnings:
            guide.append(f"- ⚠️ Power warnings: {len(findings.power_warnings)} (see recommendations below)\n")
        
        guide.append("\n---\n\n")
        
        return "".join(guide)
    
    # T021: Generate glossary
    def generate_glossary(self) -> str:
        """
        Generate comprehensive glossary of statistical terms.
        
        Returns:
            Markdown-formatted glossary with plain-language definitions
        
        Example:
            >>> glossary = generator.generate_glossary()
        """
        glossary = []
        
        glossary.append("# 📚 Statistical Terms Glossary\n")
        glossary.append("*Plain-language definitions for common statistical terms*\n\n")
        
        terms = {
            "Alpha (α)": "The significance level, usually 0.05. It's the probability of saying there's a difference when there isn't one (false alarm rate).",
            
            "ANOVA": "Analysis of Variance - compares averages across 3+ groups to see if at least one is different from the others.",
            
            "Assumption": "A requirement for a statistical test to work correctly (e.g., normal distribution, equal variances).",
            
            "Bonferroni Correction": "Adjustment made when doing multiple comparisons to avoid false positives. Makes the significance threshold stricter.",
            
            "Bootstrap": "A resampling method where we repeatedly sample our data (with replacement) to estimate uncertainty. Like simulation using your own data.",
            
            "Box Plot": "Visual showing the median (middle line), quartiles (box edges), range (whiskers), and outliers (dots) of data.",
            
            "Cliff's Delta (δ)": "Non-parametric effect size. Measures how often one group's values are larger than another's. Range: -1 to +1.",
            
            "Cohen's d": "Standardized effect size for comparing two groups. Measures difference in standard deviation units. |d| ≥ 0.8 is considered large.",
            
            "Confidence Interval (CI)": "Range of values likely to contain the true value. A 95% CI means we're 95% confident the true value is in this range.",
            
            "Effect Size": "Measure of how big a difference is, regardless of sample size. Answers: 'Is this difference meaningful?' Examples: Cohen's d, Cliff's Delta.",
            
            "Forest Plot": "Visual showing effect sizes and their confidence intervals across multiple comparisons. Dots = effect size, lines = uncertainty.",
            
            "Homogeneity of Variance": "The assumption that all groups have similar spread (variability). Tested with Levene's test.",
            
            "Kruskal-Wallis Test": "Non-parametric test comparing 3+ groups. Like ANOVA but doesn't assume normal distribution.",
            
            "Levene's Test": "Tests if groups have equal variance (similar spread). If it fails, use Welch's t-test or non-parametric tests.",
            
            "Mann-Whitney U Test": "Non-parametric test comparing two groups. Like a t-test but doesn't assume normal distribution. Good for skewed data.",
            
            "Median": "The middle value when data is sorted. Less affected by outliers than the mean (average).",
            
            "Non-parametric": "Statistical methods that don't assume specific distribution shapes (like normal). More robust but slightly less powerful.",
            
            "Normal Distribution": "Bell-shaped curve. Many statistical tests assume data follows this pattern. Tested with Shapiro-Wilk test.",
            
            "Null Hypothesis": "The 'nothing special is happening' assumption. Tests try to reject this. Example: 'The groups are the same.'",
            
            "Outlier": "Data point far from the others. Might be real or error. Can strongly affect some analyses.",
            
            "p-value": "Probability of seeing results this extreme if the null hypothesis (no effect) is true. p < 0.05 typically means 'significant'.",
            
            "Parametric": "Statistical methods assuming specific distribution (usually normal). More powerful but require assumptions.",
            
            "Power (1-β)": "Probability of detecting a real effect if it exists. Want 80%+. Low power means you might miss real differences.",
            
            "Q-Q Plot": "Quantile-Quantile plot. Checks if data follows normal distribution. Points on diagonal = normal. Curves away = non-normal.",
            
            "Quartile": "Data split into four parts. Q1 = 25th percentile, Q2 = median (50th), Q3 = 75th percentile.",
            
            "Shapiro-Wilk Test": "Tests if data is normally distributed. If p > 0.05, data appears normal and parametric tests are OK.",
            
            "Significance": "When results are unlikely to be due to chance alone. Conventionally p < 0.05. But also check effect size!",
            
            "Standard Deviation (SD)": "Measure of spread. About 68% of data falls within 1 SD of the mean in normal distributions.",
            
            "t-test": "Compares averages of two groups. Assumes normal distribution and equal variances. Common and powerful when assumptions met.",
            
            "Type I Error": "False positive - saying there's a difference when there isn't. Controlled by alpha (α).",
            
            "Type II Error": "False negative - missing a real difference. Related to power (1-β). Low power = high Type II error risk.",
            
            "Variance": "Measure of spread (squared standard deviation). Higher variance = more spread out data.",
            
            "Violin Plot": "Like a box plot but shows full distribution shape. Wider = more data at that value.",
            
            "Welch's t-test": "Modified t-test that doesn't assume equal variances. Use when Levene's test fails.",
        }
        
        for term, definition in sorted(terms.items()):
            glossary.append(f"**{term}**\n")
            glossary.append(f": {definition}\n\n")
        
        glossary.append("---\n\n")
        glossary.append("*For more detailed explanations, see the main sections of this report.*\n")
        
        return "".join(glossary)
