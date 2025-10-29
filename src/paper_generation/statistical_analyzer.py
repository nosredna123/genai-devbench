"""
Statistical Analysis Data Models and Analyzer

Provides comprehensive statistical analysis for experiment results including:
- Normality and variance testing
- Appropriate statistical test selection
- Effect size calculations with confidence intervals
- Power analysis
- Visualization generation
- Educational explanations
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from pathlib import Path
import logging
from datetime import datetime

import numpy as np
from scipy import stats
from statsmodels.stats.power import TTestIndPower

from src.utils.statistical_helpers import (
    bootstrap_ci, cohens_d, cliffs_delta, interpret_effect_size
)
from .exceptions import StatisticalAnalysisError

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Statistical test types."""
    SHAPIRO_WILK = "shapiro_wilk"           # Normality test
    LEVENE = "levene"                        # Variance homogeneity test
    T_TEST = "t_test"                        # Parametric two-sample
    MANN_WHITNEY = "mann_whitney"            # Non-parametric two-sample
    ANOVA = "anova"                          # Parametric multi-group
    KRUSKAL_WALLIS = "kruskal_wallis"       # Non-parametric multi-group


class EffectSizeMeasure(Enum):
    """Effect size measure types."""
    COHENS_D = "cohens_d"        # Parametric
    CLIFFS_DELTA = "cliffs_delta"  # Non-parametric


class VisualizationType(Enum):
    """Statistical visualization types."""
    DISTRIBUTION = "distribution"        # Histogram + KDE
    BOXPLOT = "boxplot"                 # Box-and-whisker plot
    VIOLIN = "violin"                   # Violin plot
    QQ_PLOT = "qq_plot"                # Q-Q plot for normality
    EFFECT_FOREST = "effect_forest"     # Forest plot for effect sizes


@dataclass
class MetricDistribution:
    """
    Distribution characteristics for a single metric.
    
    Captures both descriptive statistics and distributional properties.
    """
    metric_name: str
    group_name: str
    
    # Sample data
    values: List[float]
    n_samples: int
    
    # Descriptive statistics
    mean: float
    median: float
    std_dev: float
    min_value: float
    max_value: float
    q1: float  # 25th percentile
    q3: float  # 75th percentile
    
    # Bootstrap confidence intervals (median)
    median_ci_lower: float
    median_ci_upper: float
    
    # Distribution characteristics
    is_normal: bool  # Based on Shapiro-Wilk test
    has_zero_variance: bool
    
    # Advanced statistics (T028)
    skewness: float = 0.0  # Measure of asymmetry
    kurtosis: float = 0.0  # Measure of tail heaviness
    
    # Outlier detection (T029)
    outliers: List[float] = None  # Values outside 1.5×IQR range
    n_outliers: int = 0  # Count of outliers
    
    def __post_init__(self):
        """Validate distribution data."""
        # Initialize outliers list if None
        if self.outliers is None:
            self.outliers = []
        
        if self.n_samples != len(self.values):
            raise ValueError(
                f"n_samples ({self.n_samples}) doesn't match "
                f"values length ({len(self.values)})"
            )
        if self.n_samples == 0:
            raise ValueError("MetricDistribution requires at least one sample")


@dataclass
class AssumptionCheck:
    """
    Results of statistical assumption testing.
    
    Validates assumptions required for parametric tests.
    """
    test_type: TestType
    metric_name: str
    
    # Test results
    statistic: float
    p_value: float
    passes: bool  # True if assumption met (α=0.05)
    
    # Context
    groups_tested: List[str]
    
    # Educational explanation
    interpretation: str  # Plain English explanation
    
    # Recommendations for violations (T030)
    recommendation: Optional[str] = None  # What to do if assumption violated
    
    def __post_init__(self):
        """Validate assumption check."""
        if not 0 <= self.p_value <= 1:
            raise ValueError(f"Invalid p-value: {self.p_value}")
        if self.test_type not in [TestType.SHAPIRO_WILK, TestType.LEVENE]:
            raise ValueError(
                f"AssumptionCheck expects normality or variance test, "
                f"got {self.test_type}"
            )


@dataclass
class StatisticalTest:
    """
    Results of hypothesis testing between groups.
    
    Includes test selection rationale and interpretation.
    """
    test_type: TestType
    metric_name: str
    
    # Groups compared
    groups: List[str]
    
    # Test results
    statistic: float
    p_value: float
    is_significant: bool  # p < 0.05
    
    # Test selection rationale
    rationale: str  # Why this test was chosen
    
    # Educational explanation
    interpretation: str  # Plain English explanation of results
    
    # Raw data for visualization
    group_data: Dict[str, List[float]]
    
    def __post_init__(self):
        """Validate statistical test."""
        if not 0 <= self.p_value <= 1:
            raise ValueError(f"Invalid p-value: {self.p_value}")
        if len(self.groups) < 2:
            raise ValueError("Statistical test requires at least 2 groups")
        if set(self.groups) != set(self.group_data.keys()):
            raise ValueError("Groups don't match group_data keys")


@dataclass
class EffectSize:
    """
    Effect size calculation with confidence interval.
    
    Measures practical significance beyond statistical significance.
    """
    measure: EffectSizeMeasure
    metric_name: str
    
    # Groups compared
    group1: str
    group2: str
    
    # Effect size
    value: float
    ci_lower: float  # 95% CI lower bound (bootstrap)
    ci_upper: float  # 95% CI upper bound (bootstrap)
    
    # Interpretation
    magnitude: str  # "negligible", "small", "medium", "large"
    interpretation: str  # Plain English explanation
    
    def __post_init__(self):
        """Validate effect size."""
        if self.measure == EffectSizeMeasure.COHENS_D:
            # Cohen's d can be any real number
            pass
        elif self.measure == EffectSizeMeasure.CLIFFS_DELTA:
            # Cliff's Delta must be in [-1, 1]
            if not -1 <= self.value <= 1:
                raise ValueError(
                    f"Cliff's Delta must be in [-1, 1], got {self.value}"
                )
        
        valid_magnitudes = ["negligible", "small", "medium", "large"]
        if self.magnitude not in valid_magnitudes:
            raise ValueError(
                f"Invalid magnitude: {self.magnitude}. "
                f"Must be one of {valid_magnitudes}"
            )


@dataclass
class PowerAnalysis:
    """
    Statistical power analysis for a test.
    
    Assesses ability to detect true effects (Type II error risk).
    Enhanced with sample size recommendations for target power.
    """
    test_type: TestType
    metric_name: str
    
    # Sample sizes
    n_group1: int
    
    # Effect size used for power calculation
    effect_size: float
    
    # Power analysis results
    statistical_power: float  # 1 - β (probability of detecting true effect)
    
    # Interpretation
    is_adequate: bool  # Power ≥ 0.8 (conventional threshold)
    interpretation: str  # Plain English explanation
    
    # Optional fields
    n_group2: Optional[int] = None  # None for single-sample tests
    alpha: float = 0.05  # Significance level
    
    # T013: Enhanced power analysis fields
    target_power: float = 0.80  # Target power level
    recommended_n_per_group: Optional[int] = None  # Recommended sample size to achieve target_power
    
    def __post_init__(self):
        """Validate power analysis."""
        if not 0 <= self.statistical_power <= 1:
            raise ValueError(
                f"Statistical power must be in [0, 1], got {self.statistical_power}"
            )
        if not 0 < self.alpha < 1:
            raise ValueError(f"Alpha must be in (0, 1), got {self.alpha}")
        if not 0 < self.target_power < 1:
            raise ValueError(f"Target power must be in (0, 1), got {self.target_power}")
        if self.n_group1 < 2:
            raise ValueError("Sample size must be at least 2")
        if self.n_group2 is not None and self.n_group2 < 2:
            raise ValueError("Sample size must be at least 2")



@dataclass
class Visualization:
    """
    Statistical visualization metadata.
    
    Tracks generated plots for paper integration.
    """
    viz_type: VisualizationType
    metric_name: str
    
    # File output
    file_path: Path
    format: str  # "svg" or "png"
    
    # Content description
    title: str
    caption: str  # LaTeX/Markdown caption for paper
    
    # Grouping (if applicable)
    groups: Optional[List[str]] = None
    
    def __post_init__(self):
        """Validate visualization metadata."""
        if self.format not in ["svg", "png"]:
            raise ValueError(f"Invalid format: {self.format}. Use 'svg' or 'png'")
        if not self.file_path.suffix in [".svg", ".png"]:
            raise ValueError(
                f"File path extension doesn't match format: "
                f"{self.file_path.suffix} vs {self.format}"
            )


@dataclass
class StatisticalFindings:
    """
    Complete statistical analysis results for an experiment.
    
    Aggregates all analyses, tests, and visualizations.
    Enhanced with power warnings for inadequate sample sizes.
    """
    experiment_name: str
    timestamp: str  # ISO 8601 format
    
    # Metrics analyzed
    metrics_analyzed: List[str]
    
    # Distribution characteristics
    distributions: List[MetricDistribution]
    
    # Assumption testing
    assumption_checks: List[AssumptionCheck]
    
    # Hypothesis tests
    statistical_tests: List[StatisticalTest]
    
    # Effect sizes
    effect_sizes: List[EffectSize]
    
    # Power analyses
    power_analyses: List[PowerAnalysis]
    
    # Visualizations
    visualizations: List[Visualization]
    
    # Summary statistics
    n_significant_tests: int = 0
    n_large_effects: int = 0
    n_underpowered_tests: int = 0
    
    # T014: Power warnings for inadequate sample sizes
    power_warnings: List[str] = field(default_factory=list)
    
    # T031-T032: Reproducibility metadata and methodology documentation
    metadata: Dict[str, Any] = field(default_factory=dict)
    methodology_text: str = ""
    
    def __post_init__(self):
        """Calculate summary statistics and generate power warnings."""
        self.n_significant_tests = sum(
            1 for test in self.statistical_tests if test.is_significant
        )
        self.n_large_effects = sum(
            1 for effect in self.effect_sizes if effect.magnitude == "large"
        )
        self.n_underpowered_tests = sum(
            1 for power in self.power_analyses if not power.is_adequate
        )
        
        # T014: Generate power warnings for low power (< 0.70)
        self.power_warnings = []
        for power in self.power_analyses:
            if power.statistical_power < 0.70:
                warning = self._format_power_warning(power)
                self.power_warnings.append(warning)
    
    def _format_power_warning(self, power: PowerAnalysis) -> str:
        """
        Format power warning as researcher-friendly recommendation.
        
        Args:
            power: PowerAnalysis with inadequate power
        
        Returns:
            Formatted warning message
        """
        current_n = power.n_group1
        recommended_n = power.recommended_n_per_group if power.recommended_n_per_group else "unknown"
        
        if power.recommended_n_per_group:
            additional_runs = power.recommended_n_per_group - current_n
            warning = (
                f"⚠️ **Low statistical power for {power.metric_name}**: "
                f"Current power is {power.statistical_power:.1%} (below recommended 80%). "
                f"With n={current_n} per group, there is a {(1-power.statistical_power)*100:.0f}% "
                f"chance of missing a true effect of size {power.effect_size:.2f}. "
                f"**Recommendation**: Collect {additional_runs} additional runs per group "
                f"(target: n={recommended_n}) to achieve {power.target_power:.0%} power."
            )
        else:
            warning = (
                f"⚠️ **Low statistical power for {power.metric_name}**: "
                f"Current power is {power.statistical_power:.1%} (below recommended 80%). "
                f"Consider collecting additional experimental runs to increase statistical power."
            )
        
        return warning

    
    def get_findings_for_metric(self, metric_name: str) -> Dict[str, Any]:
        """
        Get all findings related to a specific metric.
        
        Args:
            metric_name: Name of the metric
        
        Returns:
            Dictionary with distributions, tests, effects, power, and visualizations
        """
        return {
            "distributions": [
                d for d in self.distributions if d.metric_name == metric_name
            ],
            "assumption_checks": [
                a for a in self.assumption_checks if a.metric_name == metric_name
            ],
            "statistical_tests": [
                t for t in self.statistical_tests if t.metric_name == metric_name
            ],
            "effect_sizes": [
                e for e in self.effect_sizes if e.metric_name == metric_name
            ],
            "power_analyses": [
                p for p in self.power_analyses if p.metric_name == metric_name
            ],
            "visualizations": [
                v for v in self.visualizations if v.metric_name == metric_name
            ],
        }


class StatisticalAnalyzer:
    """
    Comprehensive statistical analyzer for experiment results.
    
    Provides rigorous statistical analysis including:
    - Distribution analysis with normality testing (Shapiro-Wilk)
    - Variance homogeneity testing (Levene's test)
    - Appropriate test selection (parametric vs. non-parametric)
    - Effect size calculations with bootstrap confidence intervals
    - Statistical power analysis
    - Zero-variance handling
    
    Usage:
        >>> analyzer = StatisticalAnalyzer()
        >>> findings = analyzer.analyze_experiment(frameworks_data)
        >>> # Access results
        >>> for test in findings.statistical_tests:
        ...     if test.is_significant:
        ...         print(f"{test.metric_name}: p={test.p_value:.4f}")
    """
    
    def __init__(self, alpha: float = 0.05, random_seed: int = 42):
        """
        Initialize statistical analyzer.
        
        Args:
            alpha: Significance level for hypothesis tests (default: 0.05)
            random_seed: Random seed for reproducibility (default: 42)
        """
        self.alpha = alpha
        self.random_seed = random_seed
        self.rng = np.random.RandomState(random_seed)
        logger.info(f"StatisticalAnalyzer initialized (α={alpha}, seed={random_seed})")
    
    def analyze_experiment(
        self,
        frameworks_data: Dict[str, Any],
        metrics_to_analyze: Optional[List[str]] = None
    ) -> StatisticalFindings:
        """
        Perform complete statistical analysis on experiment data.
        
        Args:
            frameworks_data: Experiment data from ExperimentAnalyzer
                Format: {framework_name: {metric_name: {mean, std, ...}, runs: [...]}}
            metrics_to_analyze: List of metrics to analyze (None = all available)
        
        Returns:
            StatisticalFindings with complete analysis results
        
        Raises:
            StatisticalAnalysisError: If data is invalid or insufficient
        """
        logger.info(f"Starting statistical analysis for {len(frameworks_data)} frameworks")
        
        # Validate input
        if not frameworks_data:
            raise StatisticalAnalysisError(
                "No framework data provided for analysis",
                remediation="Ensure experiment has completed and generated metrics"
            )
        
        # Determine metrics to analyze
        if metrics_to_analyze is None:
            metrics_to_analyze = self._get_available_metrics(frameworks_data)
        
        logger.info(f"Analyzing {len(metrics_to_analyze)} metrics: {metrics_to_analyze}")
        
        # Initialize result containers
        distributions = []
        assumption_checks = []
        statistical_tests = []
        effect_sizes = []
        power_analyses = []
        
        # Analyze each metric
        for metric_name in metrics_to_analyze:
            logger.debug(f"Analyzing metric: {metric_name}")
            
            try:
                # Extract metric data for all frameworks
                metric_data = self._extract_metric_data(frameworks_data, metric_name)
                
                if not metric_data:
                    logger.warning(f"No data found for metric: {metric_name}")
                    continue
                
                # T006: Analyze distributions
                metric_distributions = self._analyze_distributions(metric_name, metric_data)
                distributions.extend(metric_distributions)
                
                # T007: Check normality assumptions
                normality_checks = self._check_normality(metric_name, metric_data)
                assumption_checks.extend(normality_checks)
                
                # T008: Check variance homogeneity (if multiple groups)
                if len(metric_data) >= 2:
                    variance_check = self._check_variance_homogeneity(metric_name, metric_data)
                    if variance_check:
                        assumption_checks.append(variance_check)
                
                # T009: Select and perform appropriate statistical tests
                if len(metric_data) >= 2:
                    test_results = self._perform_statistical_tests(
                        metric_name, metric_data, metric_distributions
                    )
                    statistical_tests.extend(test_results)
                    
                    # T010: Calculate effect sizes
                    effects = self._calculate_effect_sizes(metric_name, metric_data, metric_distributions)
                    effect_sizes.extend(effects)
                    
                    # T011: Perform power analysis
                    power_results = self._perform_power_analysis(
                        metric_name, metric_data, metric_distributions
                    )
                    power_analyses.extend(power_results)
                
            except Exception as e:
                logger.error(f"Error analyzing metric {metric_name}: {e}", exc_info=True)
                # Continue with other metrics
                continue
        
        # T031: Prepare reproducibility metadata
        import scipy
        import statsmodels
        
        metadata = {
            "analysis_date": datetime.now().isoformat(),
            "scipy_version": scipy.__version__,
            "statsmodels_version": statsmodels.__version__,
            "numpy_version": np.__version__,
            "random_seed": self.random_seed,
            "alpha": self.alpha,
            "bootstrap_iterations": 10000,
            "target_power": 0.80
        }
        
        # Create preliminary findings object (for methodology generation)
        findings = StatisticalFindings(
            experiment_name=self._infer_experiment_name(frameworks_data),
            timestamp=datetime.now().isoformat(),
            metrics_analyzed=metrics_to_analyze,
            distributions=distributions,
            assumption_checks=assumption_checks,
            statistical_tests=statistical_tests,
            effect_sizes=effect_sizes,
            power_analyses=power_analyses,
            visualizations=[],  # Will be populated by visualization generator
            metadata=metadata
        )
        
        # T032: Generate methodology text
        findings.methodology_text = self._generate_methodology_text(findings)
        
        logger.info(
            f"Analysis complete: {len(findings.statistical_tests)} tests, "
            f"{len(findings.effect_sizes)} effect sizes, "
            f"{findings.n_significant_tests} significant results"
        )
        
        return findings
    
    def _get_available_metrics(self, frameworks_data: Dict[str, Any]) -> List[str]:
        """Extract list of available metrics from framework data."""
        metrics = set()
        for framework_data in frameworks_data.values():
            for key in framework_data.keys():
                if key not in ['num_runs', 'runs'] and isinstance(framework_data[key], dict):
                    if 'mean' in framework_data[key]:
                        metrics.add(key)
        return sorted(list(metrics))
    
    def _extract_metric_data(
        self,
        frameworks_data: Dict[str, Any],
        metric_name: str
    ) -> Dict[str, List[float]]:
        """
        Extract raw values for a metric across all frameworks.
        
        Returns:
            Dict mapping framework names to lists of values
        """
        metric_data = {}
        
        for framework_name, framework_info in frameworks_data.items():
            # Get individual run data
            if 'runs' in framework_info:
                values = []
                for run in framework_info['runs']:
                    if metric_name in run and run[metric_name] is not None:
                        values.append(float(run[metric_name]))
                
                if values:
                    metric_data[framework_name] = values
        
        return metric_data
    
    def _infer_experiment_name(self, frameworks_data: Dict[str, Any]) -> str:
        """Infer experiment name from framework data."""
        # Use framework names to create a descriptive name
        frameworks = sorted(frameworks_data.keys())
        if len(frameworks) <= 3:
            return f"experiment_{'_vs_'.join(frameworks)}"
        else:
            return f"experiment_{len(frameworks)}_frameworks"
    
    # T006: Analyze distributions
    def _analyze_distributions(
        self,
        metric_name: str,
        metric_data: Dict[str, List[float]]
    ) -> List[MetricDistribution]:
        """
        Analyze distribution characteristics for each group.
        
        Calculates descriptive statistics and bootstrap confidence intervals.
        """
        distributions = []
        
        for group_name, values in metric_data.items():
            if len(values) == 0:
                continue
            
            # Calculate descriptive statistics
            values_array = np.array(values)
            mean = float(np.mean(values_array))
            median = float(np.median(values_array))
            std_dev = float(np.std(values_array, ddof=1)) if len(values) > 1 else 0.0
            min_val = float(np.min(values_array))
            max_val = float(np.max(values_array))
            q1 = float(np.percentile(values_array, 25))
            q3 = float(np.percentile(values_array, 75))
            
            # Bootstrap confidence interval for median
            if len(values) >= 2:
                _, ci_lower, ci_upper = bootstrap_ci(
                    values, statistic_fn=np.median,
                    random_seed=self.random_seed
                )
            else:
                ci_lower = median
                ci_upper = median
            
            # Check for zero variance (T012)
            has_zero_variance = (std_dev == 0.0) or (len(set(values)) == 1)
            
            # Calculate skewness and kurtosis (T028)
            if len(values) >= 3 and not has_zero_variance:
                skewness = float(stats.skew(values_array))
                kurtosis = float(stats.kurtosis(values_array))
            else:
                skewness = 0.0
                kurtosis = 0.0
            
            # Detect outliers using IQR method (T029)
            outliers = []
            if len(values) >= 4 and not has_zero_variance:  # Need sufficient data for IQR
                iqr = q3 - q1
                lower_fence = q1 - 1.5 * iqr
                upper_fence = q3 + 1.5 * iqr
                outliers = [v for v in values if v < lower_fence or v > upper_fence]
            
            # Normality test (will be done separately in _check_normality)
            is_normal = False  # Placeholder, will be updated
            
            dist = MetricDistribution(
                metric_name=metric_name,
                group_name=group_name,
                values=values,
                n_samples=len(values),
                mean=mean,
                median=median,
                std_dev=std_dev,
                min_value=min_val,
                max_value=max_val,
                q1=q1,
                q3=q3,
                median_ci_lower=float(ci_lower),
                median_ci_upper=float(ci_upper),
                is_normal=is_normal,
                has_zero_variance=has_zero_variance,
                skewness=skewness,
                kurtosis=kurtosis,
                outliers=outliers,
                n_outliers=len(outliers),
            )
            
            distributions.append(dist)
            
            if has_zero_variance:
                logger.warning(
                    f"Zero variance detected for {metric_name} in {group_name} "
                    f"(all values = {values[0]})"
                )
        
        return distributions
    
    # T007: Check normality
    def _check_normality(
        self,
        metric_name: str,
        metric_data: Dict[str, List[float]]
    ) -> List[AssumptionCheck]:
        """
        Perform Shapiro-Wilk normality tests for each group.
        
        Updates distribution.is_normal based on test results.
        """
        normality_checks = []
        
        for group_name, values in metric_data.items():
            if len(values) < 3:
                # Shapiro-Wilk requires n >= 3
                interpretation = (
                    f"Normality test not performed for {group_name} "
                    f"(n={len(values)} < 3, insufficient sample size)"
                )
                logger.debug(interpretation)
                continue
            
            # Handle zero variance case
            if len(set(values)) == 1:
                interpretation = (
                    f"Normality assumption not applicable for {group_name} "
                    f"(zero variance: all values = {values[0]})"
                )
                check = AssumptionCheck(
                    test_type=TestType.SHAPIRO_WILK,
                    metric_name=metric_name,
                    statistic=1.0,
                    p_value=1.0,
                    passes=False,  # Cannot assume normality with no variance
                    groups_tested=[group_name],
                    interpretation=interpretation
                )
                normality_checks.append(check)
                continue
            
            # Perform Shapiro-Wilk test
            statistic, p_value = stats.shapiro(values)
            passes = p_value > self.alpha
            
            interpretation = (
                f"Shapiro-Wilk test for {group_name}: "
                f"W={statistic:.4f}, p={p_value:.4f}. "
                f"Data {'appears normally distributed' if passes else 'deviates from normality'} "
                f"(α={self.alpha})."
            )
            
            # Add recommendation if normality violated (T030)
            recommendation = None
            if not passes:
                recommendation = (
                    "Consider using non-parametric tests (Mann-Whitney U for 2 groups, "
                    "Kruskal-Wallis for 3+ groups) or applying data transformations "
                    "(log, square root, Box-Cox) to achieve normality."
                )
            
            check = AssumptionCheck(
                test_type=TestType.SHAPIRO_WILK,
                metric_name=metric_name,
                statistic=float(statistic),
                p_value=float(p_value),
                passes=passes,
                groups_tested=[group_name],
                interpretation=interpretation,
                recommendation=recommendation
            )
            
            normality_checks.append(check)
        
        return normality_checks
    
    # T008: Check variance homogeneity
    def _check_variance_homogeneity(
        self,
        metric_name: str,
        metric_data: Dict[str, List[float]]
    ) -> Optional[AssumptionCheck]:
        """
        Perform Levene's test for homogeneity of variance across groups.
        
        Required for parametric tests like ANOVA and t-test.
        """
        groups = list(metric_data.keys())
        values_list = list(metric_data.values())
        
        # Need at least 2 groups
        if len(values_list) < 2:
            return None
        
        # Check if any group has zero variance
        has_zero_variance = any(len(set(vals)) == 1 for vals in values_list)
        if has_zero_variance:
            interpretation = (
                f"Levene's test not applicable: one or more groups have zero variance"
            )
            return AssumptionCheck(
                test_type=TestType.LEVENE,
                metric_name=metric_name,
                statistic=0.0,
                p_value=0.0,
                passes=False,
                groups_tested=groups,
                interpretation=interpretation
            )
        
        # Perform Levene's test (uses median, more robust than mean)
        statistic, p_value = stats.levene(*values_list, center='median')
        passes = p_value > self.alpha
        
        interpretation = (
            f"Levene's test across {len(groups)} groups: "
            f"W={statistic:.4f}, p={p_value:.4f}. "
            f"Variances {'are homogeneous' if passes else 'differ significantly'} "
            f"(α={self.alpha})."
        )
        
        # Add recommendation if variance homogeneity violated (T030)
        recommendation = None
        if not passes:
            if len(groups) == 2:
                recommendation = (
                    "Consider using Welch's t-test (does not assume equal variances) "
                    "instead of Student's t-test, or use non-parametric Mann-Whitney U test."
                )
            else:
                recommendation = (
                    "Consider using Welch's ANOVA (does not assume equal variances) "
                    "or non-parametric Kruskal-Wallis test."
                )
        
        return AssumptionCheck(
            test_type=TestType.LEVENE,
            metric_name=metric_name,
            statistic=float(statistic),
            p_value=float(p_value),
            passes=passes,
            groups_tested=groups,
            interpretation=interpretation,
            recommendation=recommendation
        )
    
    # T009: Perform statistical tests with selection logic
    def _perform_statistical_tests(
        self,
        metric_name: str,
        metric_data: Dict[str, List[float]],
        distributions: List[MetricDistribution]
    ) -> List[StatisticalTest]:
        """
        Select and perform appropriate statistical tests.
        
        Decision logic:
        - Zero variance: Skip testing (report descriptively)
        - Two groups + normal + equal variance → Independent t-test
        - Two groups + (non-normal OR unequal variance) → Mann-Whitney U
        - Multiple groups + normal + equal variance → One-way ANOVA
        - Multiple groups + (non-normal OR unequal variance) → Kruskal-Wallis
        """
        tests = []
        groups = list(metric_data.keys())
        n_groups = len(groups)
        
        # Check for zero variance (T012)
        dist_map = {d.group_name: d for d in distributions if d.metric_name == metric_name}
        has_zero_variance = any(d.has_zero_variance for d in dist_map.values())
        
        if has_zero_variance:
            logger.info(
                f"Skipping statistical tests for {metric_name}: "
                f"one or more groups have zero variance"
            )
            return tests
        
        # Two-group comparison
        if n_groups == 2:
            test = self._perform_two_group_test(metric_name, metric_data, distributions)
            if test:
                tests.append(test)
        
        # Multiple-group comparison
        elif n_groups > 2:
            test = self._perform_multi_group_test(metric_name, metric_data, distributions)
            if test:
                tests.append(test)
        
        return tests
    
    def _perform_two_group_test(
        self,
        metric_name: str,
        metric_data: Dict[str, List[float]],
        distributions: List[MetricDistribution]
    ) -> Optional[StatisticalTest]:
        """Perform two-group comparison (t-test or Mann-Whitney U)."""
        groups = list(metric_data.keys())
        group1_name, group2_name = groups[0], groups[1]
        group1_vals = metric_data[group1_name]
        group2_vals = metric_data[group2_name]
        
        # Check assumptions from normality checks (would need to pass them in)
        # For now, use simple heuristic: Shapiro-Wilk test
        _, p1 = stats.shapiro(group1_vals) if len(group1_vals) >= 3 else (None, 0.0)
        _, p2 = stats.shapiro(group2_vals) if len(group2_vals) >= 3 else (None, 0.0)
        both_normal = (p1 > self.alpha) and (p2 > self.alpha)
        
        # Check variance homogeneity
        _, p_levene = stats.levene(group1_vals, group2_vals, center='median')
        equal_variance = p_levene > self.alpha
        
        # Select test
        if both_normal and equal_variance:
            # Parametric: Independent t-test
            statistic, p_value = stats.ttest_ind(group1_vals, group2_vals)
            test_type = TestType.T_TEST
            rationale = (
                "Independent t-test selected: both groups normally distributed "
                "(Shapiro-Wilk p>0.05) and variances are equal (Levene's p>0.05)"
            )
        else:
            # Non-parametric: Mann-Whitney U
            statistic, p_value = stats.mannwhitneyu(
                group1_vals, group2_vals, alternative='two-sided'
            )
            test_type = TestType.MANN_WHITNEY
            
            reasons = []
            if not both_normal:
                reasons.append("non-normal distribution")
            if not equal_variance:
                reasons.append("unequal variances")
            
            rationale = (
                f"Mann-Whitney U test selected: {' and '.join(reasons)}. "
                "Non-parametric test appropriate for ordinal data or "
                "when parametric assumptions violated."
            )
        
        is_significant = p_value < self.alpha
        
        interpretation = (
            f"Comparing {group1_name} vs {group2_name}: "
            f"{'Significant difference' if is_significant else 'No significant difference'} "
            f"detected (p={p_value:.4f}, α={self.alpha}). "
            f"{'Groups differ meaningfully' if is_significant else 'Groups are similar statistically'}."
        )
        
        return StatisticalTest(
            test_type=test_type,
            metric_name=metric_name,
            groups=groups,
            statistic=float(statistic),
            p_value=float(p_value),
            is_significant=is_significant,
            rationale=rationale,
            interpretation=interpretation,
            group_data=metric_data
        )
    
    def _perform_multi_group_test(
        self,
        metric_name: str,
        metric_data: Dict[str, List[float]],
        distributions: List[MetricDistribution]
    ) -> Optional[StatisticalTest]:
        """Perform multi-group comparison (ANOVA or Kruskal-Wallis)."""
        groups = list(metric_data.keys())
        values_list = [metric_data[g] for g in groups]
        
        # Check normality for all groups
        all_normal = True
        for vals in values_list:
            if len(vals) >= 3:
                _, p = stats.shapiro(vals)
                if p <= self.alpha:
                    all_normal = False
                    break
            else:
                all_normal = False
                break
        
        # Check variance homogeneity
        _, p_levene = stats.levene(*values_list, center='median')
        equal_variance = p_levene > self.alpha
        
        # Select test
        if all_normal and equal_variance:
            # Parametric: One-way ANOVA
            statistic, p_value = stats.f_oneway(*values_list)
            test_type = TestType.ANOVA
            rationale = (
                f"One-way ANOVA selected: all {len(groups)} groups normally distributed "
                "and variances are equal. Parametric test appropriate."
            )
        else:
            # Non-parametric: Kruskal-Wallis
            statistic, p_value = stats.kruskal(*values_list)
            test_type = TestType.KRUSKAL_WALLIS
            
            reasons = []
            if not all_normal:
                reasons.append("non-normal distributions")
            if not equal_variance:
                reasons.append("unequal variances")
            
            rationale = (
                f"Kruskal-Wallis test selected: {' and '.join(reasons)}. "
                "Non-parametric test appropriate for ordinal data."
            )
        
        is_significant = p_value < self.alpha
        
        interpretation = (
            f"Comparing {len(groups)} groups ({', '.join(groups)}): "
            f"{'Significant differences' if is_significant else 'No significant differences'} "
            f"detected (p={p_value:.4f}, α={self.alpha}). "
            f"{'At least one group differs' if is_significant else 'Groups are similar statistically'}."
        )
        
        return StatisticalTest(
            test_type=test_type,
            metric_name=metric_name,
            groups=groups,
            statistic=float(statistic),
            p_value=float(p_value),
            is_significant=is_significant,
            rationale=rationale,
            interpretation=interpretation,
            group_data=metric_data
        )
    
    # T010: Calculate effect sizes
    def _calculate_effect_sizes(
        self,
        metric_name: str,
        metric_data: Dict[str, List[float]],
        distributions: List[MetricDistribution]
    ) -> List[EffectSize]:
        """
        Calculate effect sizes for all pairwise comparisons.
        
        Uses Cohen's d for parametric comparisons and Cliff's Delta for non-parametric.
        Includes bootstrap confidence intervals.
        """
        effects = []
        groups = list(metric_data.keys())
        
        # Check for zero variance
        dist_map = {d.group_name: d for d in distributions if d.metric_name == metric_name}
        
        # Pairwise comparisons
        for i, group1 in enumerate(groups):
            for group2 in groups[i+1:]:
                vals1 = metric_data[group1]
                vals2 = metric_data[group2]
                
                # Skip if either group has zero variance
                if dist_map[group1].has_zero_variance or dist_map[group2].has_zero_variance:
                    logger.debug(
                        f"Skipping effect size for {group1} vs {group2}: zero variance"
                    )
                    continue
                
                # Check normality
                _, p1 = stats.shapiro(vals1) if len(vals1) >= 3 else (None, 0.0)
                _, p2 = stats.shapiro(vals2) if len(vals2) >= 3 else (None, 0.0)
                both_normal = (p1 > self.alpha) and (p2 > self.alpha)
                
                if both_normal:
                    # Use Cohen's d
                    effect_value = cohens_d(vals1, vals2)
                    measure = EffectSizeMeasure.COHENS_D
                    
                    # Bootstrap CI for Cohen's d
                    def cohens_d_bootstrap(combined_data, n1):
                        """Calculate Cohen's d from bootstrap sample."""
                        return cohens_d(
                            combined_data[:n1].tolist(),
                            combined_data[n1:].tolist()
                        )
                    
                    combined = np.array(vals1 + vals2)
                    n1 = len(vals1)
                    bootstrap_stats = []
                    for _ in range(10000):
                        sample = self.rng.choice(len(combined), size=len(combined), replace=True)
                        resampled = combined[sample]
                        try:
                            d = cohens_d_bootstrap(resampled, n1)
                            bootstrap_stats.append(d)
                        except:
                            continue
                    
                    ci_lower = float(np.percentile(bootstrap_stats, 2.5))
                    ci_upper = float(np.percentile(bootstrap_stats, 97.5))
                    
                    magnitude = interpret_effect_size(effect_value, "cohens_d")
                    interpretation = (
                        f"Cohen's d = {effect_value:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]: "
                        f"{magnitude} effect size. "
                        f"{group1} {'outperforms' if effect_value > 0 else 'underperforms'} "
                        f"{group2} by {abs(effect_value):.2f} pooled standard deviations."
                    )
                else:
                    # Use Cliff's Delta
                    effect_value = cliffs_delta(vals1, vals2)
                    measure = EffectSizeMeasure.CLIFFS_DELTA
                    
                    # Bootstrap CI for Cliff's Delta
                    def cliffs_delta_bootstrap(data1, data2):
                        """Calculate Cliff's Delta from bootstrap samples."""
                        return cliffs_delta(data1.tolist(), data2.tolist())
                    
                    bootstrap_stats = []
                    for _ in range(10000):
                        sample1 = self.rng.choice(vals1, size=len(vals1), replace=True)
                        sample2 = self.rng.choice(vals2, size=len(vals2), replace=True)
                        try:
                            delta = cliffs_delta_bootstrap(sample1, sample2)
                            bootstrap_stats.append(delta)
                        except:
                            continue
                    
                    ci_lower = float(np.percentile(bootstrap_stats, 2.5))
                    ci_upper = float(np.percentile(bootstrap_stats, 97.5))
                    
                    magnitude = interpret_effect_size(effect_value, "cliffs_delta")
                    interpretation = (
                        f"Cliff's Delta = {effect_value:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]: "
                        f"{magnitude} effect size. "
                        f"Probability that {group1} {'exceeds' if effect_value > 0 else 'is less than'} "
                        f"{group2} is {abs(effect_value) * 50 + 50:.1f}%."
                    )
                
                effect = EffectSize(
                    measure=measure,
                    metric_name=metric_name,
                    group1=group1,
                    group2=group2,
                    value=float(effect_value),
                    ci_lower=ci_lower,
                    ci_upper=ci_upper,
                    magnitude=magnitude,
                    interpretation=interpretation
                )
                
                effects.append(effect)
        
        return effects
    
    # T011 & T013: Enhanced power analysis with sample size recommendations
    def _perform_power_analysis(
        self,
        metric_name: str,
        metric_data: Dict[str, List[float]],
        distributions: List[MetricDistribution]
    ) -> List[PowerAnalysis]:
        """
        Calculate statistical power for each test.
        
        Enhanced with:
        - Uses statsmodels.stats.power.TTestIndPower for parametric tests
        - Simulation-based power for non-parametric tests
        - Calculates achieved power with current sample size
        - Calculates recommended n for target_power=0.80
        
        Power ≥ 0.8 is conventionally considered adequate.
        """
        power_results = []
        groups = list(metric_data.keys())
        
        # Check for zero variance
        dist_map = {d.group_name: d for d in distributions if d.metric_name == metric_name}
        
        # For two-group comparisons
        if len(groups) == 2:
            group1, group2 = groups[0], groups[1]
            vals1 = metric_data[group1]
            vals2 = metric_data[group2]
            
            # Skip if zero variance
            if dist_map[group1].has_zero_variance or dist_map[group2].has_zero_variance:
                logger.debug(f"Skipping power analysis: zero variance")
                return power_results
            
            # Calculate effect size (use Cohen's d for power)
            effect_size = abs(cohens_d(vals1, vals2))
            
            # Check if data is normal (parametric vs non-parametric)
            _, p1 = stats.shapiro(vals1) if len(vals1) >= 3 else (None, 0.0)
            _, p2 = stats.shapiro(vals2) if len(vals2) >= 3 else (None, 0.0)
            both_normal = (p1 > self.alpha) and (p2 > self.alpha)
            
            n1, n2 = len(vals1), len(vals2)
            target_power = 0.80
            
            if both_normal:
                # T013: Use statsmodels for parametric power analysis
                power_analysis_tool = TTestIndPower()
                
                # Calculate achieved power
                achieved_power = power_analysis_tool.solve_power(
                    effect_size=effect_size,
                    nobs1=n1,
                    ratio=n2/n1,
                    alpha=self.alpha,
                    alternative='two-sided'
                )
                achieved_power = float(np.clip(achieved_power, 0, 1))
                
                # Calculate recommended sample size for target power
                try:
                    recommended_n = power_analysis_tool.solve_power(
                        effect_size=effect_size,
                        nobs1=None,  # Solve for sample size
                        ratio=1.0,  # Assume equal groups
                        alpha=self.alpha,
                        power=target_power,
                        alternative='two-sided'
                    )
                    recommended_n = int(np.ceil(recommended_n))
                except:
                    recommended_n = None
                
                test_type = TestType.T_TEST
                
            else:
                # T013: Simulation-based power for non-parametric tests (conservative)
                # Use permutation test simulation
                achieved_power = self._simulate_nonparametric_power(
                    vals1, vals2, effect_size
                )
                
                # Conservative estimate for recommended n (use parametric as upper bound)
                power_analysis_tool = TTestIndPower()
                try:
                    recommended_n = power_analysis_tool.solve_power(
                        effect_size=effect_size,
                        nobs1=None,
                        ratio=1.0,
                        alpha=self.alpha,
                        power=target_power,
                        alternative='two-sided'
                    )
                    # Add 20% buffer for non-parametric (conservative)
                    recommended_n = int(np.ceil(recommended_n * 1.2))
                except:
                    recommended_n = None
                
                test_type = TestType.MANN_WHITNEY
            
            is_adequate = achieved_power >= target_power
            
            # Enhanced interpretation with sample size recommendation
            if recommended_n and not is_adequate:
                additional = recommended_n - n1
                interpretation = (
                    f"Statistical power = {achieved_power:.3f} for detecting effect size d={effect_size:.3f} "
                    f"with n₁={n1}, n₂={n2}, α={self.alpha}. "
                    f"Power is inadequate (<{target_power:.0%} threshold). "
                    f"Recommend collecting {additional} additional runs per group "
                    f"(target: n={recommended_n}) to achieve {target_power:.0%} power."
                )
            elif is_adequate:
                interpretation = (
                    f"Statistical power = {achieved_power:.3f} for detecting effect size d={effect_size:.3f} "
                    f"with n₁={n1}, n₂={n2}, α={self.alpha}. "
                    f"Power is adequate (≥{target_power:.0%} threshold). "
                    f"Sufficient sample size to detect true effects reliably."
                )
            else:
                interpretation = (
                    f"Statistical power = {achieved_power:.3f} for detecting effect size d={effect_size:.3f} "
                    f"with n₁={n1}, n₂={n2}, α={self.alpha}. "
                    f"Power is inadequate (<{target_power:.0%} threshold). "
                    f"Consider collecting additional experimental runs."
                )
            
            power_analysis = PowerAnalysis(
                test_type=test_type,
                metric_name=metric_name,
                n_group1=n1,
                effect_size=effect_size,
                statistical_power=achieved_power,
                is_adequate=is_adequate,
                interpretation=interpretation,
                n_group2=n2,
                target_power=target_power,
                recommended_n_per_group=recommended_n
            )
            
            power_results.append(power_analysis)
        
        return power_results
    
    def _simulate_nonparametric_power(
        self,
        group1: List[float],
        group2: List[float],
        effect_size: float,
        n_simulations: int = 1000
    ) -> float:
        """
        Simulate statistical power for non-parametric tests.
        
        Uses permutation test approach to estimate power conservatively.
        
        Args:
            group1: First group data
            group2: Second group data
            effect_size: Expected effect size (Cohen's d)
            n_simulations: Number of simulation iterations
        
        Returns:
            Estimated statistical power
        """
        n1, n2 = len(group1), len(group2)
        significant_count = 0
        
        # Simulate under alternative hypothesis (effect exists)
        for _ in range(n_simulations):
            # Resample with replacement
            sim_group1 = self.rng.choice(group1, size=n1, replace=True)
            sim_group2 = self.rng.choice(group2, size=n2, replace=True)
            
            # Perform Mann-Whitney U test
            try:
                _, p_value = stats.mannwhitneyu(
                    sim_group1, sim_group2, alternative='two-sided'
                )
                if p_value < self.alpha:
                    significant_count += 1
            except:
                # Handle edge cases
                continue
        
        power = significant_count / n_simulations
        return float(power)
    
    # T013: Standalone power analysis method (can be called independently)
    def perform_power_analysis(
        self,
        effect: EffectSize,
        n_per_group: int,
        target_power: float = 0.80
    ) -> PowerAnalysis:
        """
        Perform power analysis for a given effect size and sample size.
        
        T013: Standalone method for power analysis that can be used independently
        of full experiment analysis.
        
        Args:
            effect: EffectSize object with observed or expected effect
            n_per_group: Current sample size per group
            target_power: Target power level (default: 0.80)
        
        Returns:
            PowerAnalysis with achieved power and recommendations
        
        Example:
            >>> effect = EffectSize(...)  # From previous analysis
            >>> power = analyzer.perform_power_analysis(effect, n_per_group=10)
            >>> print(f"Power: {power.statistical_power:.2%}")
            >>> if not power.is_adequate:
            ...     print(f"Recommend n={power.recommended_n_per_group}")
        """
        effect_size_value = abs(effect.value)
        
        # Use Cohen's d for power calculations (convert if needed)
        if effect.measure == EffectSizeMeasure.CLIFFS_DELTA:
            # Approximate conversion: Cliff's Delta ≈ 2 * Φ(d/√2) - 1
            # Inverse: d ≈ √2 * Φ⁻¹((δ + 1)/2)
            from scipy.stats import norm
            effect_size_value = np.sqrt(2) * norm.ppf((effect_size_value + 1) / 2)
        
        # Use statsmodels for parametric power analysis
        power_analysis_tool = TTestIndPower()
        
        # Calculate achieved power
        achieved_power = power_analysis_tool.solve_power(
            effect_size=effect_size_value,
            nobs1=n_per_group,
            ratio=1.0,  # Assume equal groups
            alpha=self.alpha,
            alternative='two-sided'
        )
        achieved_power = float(np.clip(achieved_power, 0, 1))
        
        # Calculate recommended sample size
        try:
            recommended_n = power_analysis_tool.solve_power(
                effect_size=effect_size_value,
                nobs1=None,
                ratio=1.0,
                alpha=self.alpha,
                power=target_power,
                alternative='two-sided'
            )
            recommended_n = int(np.ceil(recommended_n))
        except:
            recommended_n = None
        
        is_adequate = achieved_power >= target_power
        
        # Generate interpretation
        if recommended_n and not is_adequate:
            additional = recommended_n - n_per_group
            interpretation = (
                f"Statistical power = {achieved_power:.3f} for effect size {effect.measure.value}={effect.value:.3f} "
                f"with n={n_per_group} per group. "
                f"Power is inadequate (<{target_power:.0%}). "
                f"Recommend {additional} additional runs per group (target: n={recommended_n})."
            )
        else:
            interpretation = (
                f"Statistical power = {achieved_power:.3f} for effect size {effect.measure.value}={effect.value:.3f} "
                f"with n={n_per_group} per group. "
                f"Power is {'adequate' if is_adequate else 'inadequate'}."
            )
        
        return PowerAnalysis(
            test_type=TestType.T_TEST,
            metric_name=effect.metric_name,
            n_group1=n_per_group,
            effect_size=effect_size_value,
            statistical_power=achieved_power,
            is_adequate=is_adequate,
            interpretation=interpretation,
            n_group2=n_per_group,
            target_power=target_power,
            recommended_n_per_group=recommended_n
        )
    
    def _generate_methodology_text(self, findings: StatisticalFindings) -> str:
        """
        Generate pre-formatted methodology text for paper Methodology section.
        
        T032: Documents statistical methods, test selection criteria, effect sizes,
        corrections, bootstrap methodology, significance threshold, and software versions.
        
        Args:
            findings: Complete statistical findings with all analyses
        
        Returns:
            Formatted markdown text describing statistical methodology
        """
        sections = []
        
        # Normality assessment
        sections.append(
            "**Statistical Analysis**: Data normality was assessed using the Shapiro-Wilk test "
            f"(α={self.alpha}). "
        )
        
        # Test selection criteria
        normality_tests = [t for t in findings.assumption_checks if t.test_type == TestType.SHAPIRO_WILK]
        variance_tests = [t for t in findings.assumption_checks if t.test_type == TestType.LEVENE]
        
        if normality_tests:
            sections.append(
                "Statistical test selection was based on distribution characteristics: "
                "parametric tests (Student's t-test for 2 groups, ANOVA for 3+ groups) were used "
                "when data met normality assumptions; non-parametric tests (Mann-Whitney U for 2 groups, "
                "Kruskal-Wallis for 3+ groups) were used otherwise. "
            )
        
        # Variance homogeneity
        if variance_tests:
            sections.append(
                "Variance homogeneity was assessed using Levene's test (median-centered). "
            )
        
        # Effect size measures
        parametric_effects = [e for e in findings.effect_sizes if e.measure == EffectSizeMeasure.COHENS_D]
        nonparametric_effects = [e for e in findings.effect_sizes if e.measure == EffectSizeMeasure.CLIFFS_DELTA]
        
        if parametric_effects and nonparametric_effects:
            sections.append(
                "Effect sizes were quantified using Cohen's d for parametric comparisons and "
                "Cliff's Delta for non-parametric comparisons. "
            )
        elif parametric_effects:
            sections.append("Effect sizes were quantified using Cohen's d. ")
        elif nonparametric_effects:
            sections.append("Effect sizes were quantified using Cliff's Delta. ")
        
        # Multiple comparison corrections
        tests_with_bonferroni = [t for t in findings.statistical_tests 
                                 if 'Bonferroni' in t.rationale]
        if tests_with_bonferroni:
            sections.append(
                "For experiments with 3+ groups, Bonferroni correction was applied to pairwise "
                "comparisons to control family-wise error rate. "
            )
        
        # Bootstrap confidence intervals
        if findings.effect_sizes:
            sections.append(
                f"95% confidence intervals for effect sizes were computed using bootstrap resampling "
                f"(n=10,000 iterations, seed={self.random_seed}). "
            )
        
        # Power analysis
        if findings.power_analyses:
            sections.append(
                "Statistical power analysis was performed using statsmodels for parametric tests "
                "(target power=80%). "
            )
        
        # Significance threshold
        sections.append(f"Statistical significance was assessed at α={self.alpha}. ")
        
        # Software versions (T031 metadata)
        import scipy
        import statsmodels
        
        sections.append(
            f"Statistical analyses were performed using SciPy {scipy.__version__} and "
            f"statsmodels {statsmodels.__version__}."
        )
        
        return "".join(sections)


