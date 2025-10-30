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
    bootstrap_ci, cohens_d, cliffs_delta, interpret_effect_size, format_pvalue
)
from .exceptions import StatisticalAnalysisError
from .config import StatisticalConfig

logger = logging.getLogger(__name__)


class TestType(Enum):
    """Statistical test types."""
    SHAPIRO_WILK = "shapiro_wilk"           # Normality test
    LEVENE = "levene"                        # Variance homogeneity test
    T_TEST = "t_test"                        # Parametric two-sample (equal variance)
    WELCH_T = "welch_t"                      # Parametric two-sample (unequal variance) - T021
    MANN_WHITNEY = "mann_whitney"            # Non-parametric two-sample
    ANOVA = "anova"                          # Parametric multi-group (equal variance)
    WELCH_ANOVA = "welch_anova"             # Parametric multi-group (unequal variance) - T021
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
    Enhanced with skewness classification for summary statistic selection.
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
    
    # NEW FIELDS (T009) - Skewness classification
    skewness_flag: str = "normal"       # "normal", "moderate", "high", "severe"
    primary_summary: str = "mean"       # "mean" or "median" - which to emphasize
    summary_explanation: str = ""       # Why this summary was chosen
    
    def __post_init__(self):
        """Validate distribution data and classify skewness."""
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
        
        # NEW LOGIC (T009) - Classify skewness and determine appropriate summary statistic
        abs_skew = abs(self.skewness)
        
        # FR-031: Flag metrics with |skewness| > 1.0
        if abs_skew < 0.5:
            self.skewness_flag = "normal"
            self.primary_summary = "mean"
            self.summary_explanation = "Distribution is nearly symmetric; mean ± SD appropriate."
        elif abs_skew <= 1.0:
            self.skewness_flag = "moderate"
            self.primary_summary = "median"  # FR-032
            self.summary_explanation = "Moderate skewness detected; median and IQR are more robust."
        elif abs_skew <= 2.0:
            self.skewness_flag = "high"
            self.primary_summary = "median"
            self.summary_explanation = "High skewness detected; median strongly preferred over mean."
        else:
            self.skewness_flag = "severe"  # FR-034
            self.primary_summary = "median"
            self.summary_explanation = (
                f"Severe skewness ({self.skewness:.2f}) detected; mean is substantially "
                f"biased by extreme values. Median provides more accurate central tendency."
            )


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
    Enhanced with multiple comparison corrections and power analysis.
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
    
    # NEW FIELDS (T007) - Multiple comparison corrections
    pvalue_raw: float = None                # Raw p-value before correction
    pvalue_adjusted: float = None           # Adjusted p-value (if multi-comparison)
    correction_method: str = None           # "holm" or None
    
    # NEW FIELDS (T007) - Test selection metadata
    test_rationale: str = ""                # Detailed rationale for test selection
    assumptions_checked: Dict[str, bool] = None  # {normality: True, equal_var: False}
    
    # NEW FIELDS (T007) - Power analysis
    achieved_power: float = None            # Calculated achieved power (0.0-1.0)
    recommended_n: int = None               # Sample size for 80% power (if underpowered)
    power_adequate: bool = None             # True if power ≥ 0.80
    
    def __post_init__(self):
        """Validate statistical test."""
        if not 0 <= self.p_value <= 1:
            raise ValueError(f"Invalid p-value: {self.p_value}")
        if len(self.groups) < 2:
            raise ValueError("Statistical test requires at least 2 groups")
        if set(self.groups) != set(self.group_data.keys()):
            raise ValueError("Groups don't match group_data keys")
        
        # Initialize assumptions_checked if None
        if self.assumptions_checked is None:
            self.assumptions_checked = {}


@dataclass
class EffectSize:
    """
    Effect size calculation with confidence interval.
    
    Measures practical significance beyond statistical significance.
    Enhanced with CI validation and test type alignment.
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
    
    # NEW FIELDS (T008) - Bootstrap metadata
    bootstrap_iterations: int = 10000      # Number of bootstrap samples used
    ci_method: str = "bootstrap"           # "bootstrap" or "analytic"
    ci_valid: bool = True                  # Whether CI contains point estimate
    test_type_alignment: TestType = None   # Which test this aligns with
    
    def __post_init__(self):
        """Validate effect size and CI."""
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
        
        # NEW VALIDATION (T008) - Validate that CI contains point estimate (FR-002)
        from ..utils.statistical_helpers import validate_ci
        self.ci_valid = validate_ci(self.value, self.ci_lower, self.ci_upper)
        
        if not self.ci_valid:
            from .exceptions import StatisticalAnalysisError
            raise StatisticalAnalysisError(
                f"Invalid confidence interval: point estimate {self.value:.3f} "
                f"is outside CI [{self.ci_lower:.3f}, {self.ci_upper:.3f}]. "
                f"This indicates a bootstrap resampling bug."
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
    
    # Feature 013: Analysis warnings for data quality and assumption violations
    warnings: List[str] = field(default_factory=list)
    
    def add_warning(self, category: str, message: str):
        """
        Add a categorized warning about data quality or analysis assumptions.
        
        Args:
            category: Warning category (e.g., 'Zero Variance', 'Assumption Violation')
            message: Descriptive warning message
        """
        self.warnings.append(f'**{category}**: {message}')
    
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
    
    def __init__(
        self,
        alpha: float = 0.05,
        random_seed: int = 42,
        config: Optional[StatisticalConfig] = None
    ):
        """
        Initialize statistical analyzer.
        
        Args:
            alpha: Significance level for hypothesis tests (default: 0.05)
            random_seed: Random seed for reproducibility (default: 42)
            config: Statistical configuration (default: StatisticalConfig())
        """
        self.alpha = alpha
        self.random_seed = random_seed
        self.rng = np.random.RandomState(random_seed)
        self.config = config if config is not None else StatisticalConfig()
        logger.info(
            f"StatisticalAnalyzer initialized (α={alpha}, seed={random_seed}, "
            f"variance_threshold={self.config.variance_threshold})"
        )
    
    def _check_variance_quality(
        self,
        values: np.ndarray,
        variance_threshold: Optional[float] = None,
        iqr_threshold: Optional[float] = None
    ) -> bool:
        """
        Check if a distribution has sufficient variance for meaningful analysis.
        
        Feature 013: Centralized variance quality checking.
        
        A distribution is considered to have zero or near-zero variance if:
        - Standard deviation is exactly 0
        - All values are identical
        - Standard deviation < variance_threshold
        - IQR < iqr_threshold
        
        Args:
            values: Array of numeric values
            variance_threshold: Minimum acceptable standard deviation (default: from config)
            iqr_threshold: Minimum acceptable IQR (default: from config)
            
        Returns:
            True if distribution has sufficient variance, False otherwise
        """
        # Use config defaults if not specified
        variance_threshold = variance_threshold if variance_threshold is not None else self.config.variance_threshold
        iqr_threshold = iqr_threshold if iqr_threshold is not None else self.config.iqr_threshold
        
        # Exact zero variance check
        if np.std(values) == 0.0 or len(set(values)) == 1:
            return False
        
        # Near-zero variance checks
        std_dev = np.std(values)
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        
        if std_dev < variance_threshold or iqr < iqr_threshold:
            return False
        
        return True
    
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
        
        # Feature 013: Create early findings object for warning collection
        findings_for_warnings = StatisticalFindings(
            experiment_name=self._infer_experiment_name(frameworks_data),
            timestamp=datetime.now().isoformat(),
            metrics_analyzed=[],  # Will be populated later
            distributions=[],
            assumption_checks=[],
            statistical_tests=[],
            effect_sizes=[],
            power_analyses=[],
            visualizations=[],
            metadata={}
        )
        
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
                normality_checks = self._check_normality(
                    metric_name, metric_data, findings=findings_for_warnings
                )
                assumption_checks.extend(normality_checks)
                
                # T008: Check variance homogeneity (if multiple groups)
                if len(metric_data) >= 2:
                    variance_check = self._check_variance_homogeneity(
                        metric_name, metric_data, findings=findings_for_warnings
                    )
                    if variance_check:
                        assumption_checks.append(variance_check)
                
                # T009: Select and perform appropriate statistical tests
                if len(metric_data) >= 2:
                    test_results = self._perform_statistical_tests(
                        metric_name, metric_data, metric_distributions
                    )
                    
                    # T044-T046: Apply multiple comparison correction to p-values
                    if len(test_results) > 0:
                        # Extract p-values and comparison labels
                        pvalues = [test.p_value for test in test_results]
                        comparison_labels = [
                            "_vs_".join(test.groups) for test in test_results
                        ]
                        
                        # Apply correction (T041-T043)
                        correction = self._apply_multiple_comparison_correction(
                            pvalues=pvalues,
                            comparison_labels=comparison_labels,
                            metric_name=metric_name,
                            alpha=self.alpha,
                            method="holm"  # FR-022
                        )
                        
                        # T045: Populate test fields with raw, adjusted p-values and correction method
                        for i, test in enumerate(test_results):
                            test.pvalue_raw = correction.raw_pvalues[i]
                            test.pvalue_adjusted = correction.adjusted_pvalues[i]
                            test.correction_method = correction.correction_method
                            
                            # T046: Update significance decision using adjusted p-value (FR-023, FR-024)
                            test.is_significant = correction.reject_decisions[i]
                    
                    statistical_tests.extend(test_results)
                    
                    # T010, T036: Calculate effect sizes with test alignment
                    effects = self._calculate_effect_sizes(
                        metric_name, metric_data, metric_distributions, test_results,
                        findings=findings_for_warnings
                    )
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
            metadata=metadata,
            warnings=findings_for_warnings.warnings  # Feature 013: Copy collected warnings
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
            
            # Feature 013: Use centralized variance quality check
            has_zero_variance = not self._check_variance_quality(values_array)
            
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
        metric_data: Dict[str, List[float]],
        findings: 'StatisticalFindings' = None
    ) -> List[AssumptionCheck]:
        """
        Perform Shapiro-Wilk normality tests for each group.
        
        Updates distribution.is_normal based on test results.
        
        Args:
            findings: StatisticalFindings object for warning collection (Feature 013)
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
                f"W={statistic:.4f}, {format_pvalue(p_value)}. "
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
                # Feature 013: Add warning for assumption violation
                if findings:
                    findings.add_warning(
                        'Assumption Violation',
                        f"Normality assumption violated for metric '{metric_name}' in group '{group_name}' (p={p_value:.4f}); non-parametric test recommended"
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
        metric_data: Dict[str, List[float]],
        findings: 'StatisticalFindings' = None
    ) -> Optional[AssumptionCheck]:
        """
        Perform Levene's test for homogeneity of variance across groups.
        
        Required for parametric tests like ANOVA and t-test.
        
        Args:
            findings: StatisticalFindings object for warning collection (Feature 013)
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
            f"W={statistic:.4f}, {format_pvalue(p_value)}. "
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
            # Feature 013: Add warning for assumption violation
            if findings:
                findings.add_warning(
                    'Assumption Violation',
                    f"Variance homogeneity assumption violated for metric '{metric_name}' (Levene's test p={p_value:.4f}); robust test recommended"
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
        - Two groups + normal + unequal variance → Welch's t-test (T019)
        - Two groups + non-normal → Mann-Whitney U
        - Multiple groups + normal + equal variance → One-way ANOVA
        - Multiple groups + normal + unequal variance → Welch's ANOVA (T020)
        - Multiple groups + non-normal → Kruskal-Wallis
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
    
    # T016-T021: Three-way statistical test selection
    def _select_statistical_test(
        self,
        distributions: List[MetricDistribution],
        alpha: float = 0.05
    ) -> Tuple[TestType, Dict[str, bool], str]:
        """
        Select appropriate statistical test based on normality and variance equality.
        
        Implements three-way decision tree per FR-005 to FR-012.
        
        Args:
            distributions: List of MetricDistribution objects (one per group)
            alpha: Significance level for assumption tests (default 0.05)
        
        Returns:
            Tuple of (test_type, assumptions, rationale)
            - test_type: Selected test (T_TEST, WELCH_T, MANN_WHITNEY, ANOVA, WELCH_ANOVA, KRUSKAL_WALLIS)
            - assumptions: {normality: bool, equal_variance: bool}
            - rationale: Explanation of test selection
        """
        n_groups = len(distributions)
        
        # Preconditions
        if n_groups < 2:
            raise ValueError("Need at least 2 groups for statistical test")
        
        # T017: Check normality for each group (Shapiro-Wilk test, FR-005)
        all_normal = True
        for dist in distributions:
            if len(dist.values) >= 3:
                _, p = stats.shapiro(dist.values)
                if p <= alpha:
                    all_normal = False
                    break
            else:
                all_normal = False  # Too few samples for normality test
                break
        
        # T018: Check variance equality (Levene's test, FR-005)
        values_list = [dist.values for dist in distributions]
        _, p_levene = stats.levene(*values_list, center='median')
        equal_variance = p_levene > alpha
        
        # Build assumptions dict (T023)
        assumptions = {
            'normality': all_normal,
            'equal_variance': equal_variance
        }
        
        # T019-T020: Three-way decision tree
        if n_groups == 2:
            # Pairwise comparison
            if all_normal:
                if equal_variance:
                    # FR-009: Student's t-test
                    test_type = TestType.T_TEST
                    rationale = (
                        "Student's t-test selected: both groups normally distributed "
                        f"(Shapiro-Wilk test) and variances equal (Levene's {format_pvalue(p_levene)}, exceeds α={alpha})"
                    )
                else:
                    # FR-010: Welch's t-test
                    test_type = TestType.WELCH_T
                    rationale = (
                        "Welch's t-test selected: both groups normally distributed "
                        f"(Shapiro-Wilk test) but variances unequal (Levene's {format_pvalue(p_levene)}, ≤α={alpha})"
                    )
            else:
                # FR-011: Mann-Whitney U
                test_type = TestType.MANN_WHITNEY
                rationale = (
                    "Mann-Whitney U test selected: at least one group non-normally distributed "
                    f"(Shapiro-Wilk p≤{alpha}). Non-parametric test appropriate."
                )
        else:
            # Multi-group comparison (k ≥ 3)
            if all_normal:
                if equal_variance:
                    # FR-006: Standard ANOVA
                    test_type = TestType.ANOVA
                    rationale = (
                        f"One-way ANOVA selected: all {n_groups} groups normally distributed "
                        f"and variances equal (Levene's {format_pvalue(p_levene)}, exceeds α={alpha})"
                    )
                else:
                    # FR-007: Welch's ANOVA
                    test_type = TestType.WELCH_ANOVA
                    rationale = (
                        f"Welch's ANOVA selected: all {n_groups} groups normally distributed "
                        f"but variances unequal (Levene's {format_pvalue(p_levene)}, ≤α={alpha})"
                    )
            else:
                # FR-008: Kruskal-Wallis
                test_type = TestType.KRUSKAL_WALLIS
                rationale = (
                    f"Kruskal-Wallis test selected: at least one group non-normally distributed "
                    f"(Shapiro-Wilk p≤{alpha}). Non-parametric test appropriate."
                )
        
        return test_type, assumptions, rationale
    
    def _select_effect_size_measure(self, test_type: TestType) -> EffectSizeMeasure:
        """
        Select appropriate effect size measure based on test type.
        
        Implements FR-013, FR-014: Match effect size to test assumptions
        - Parametric tests (t-test, ANOVA, Welch's variants) → Cohen's d
        - Non-parametric tests (Mann-Whitney, Kruskal-Wallis) → Cliff's Delta
        
        Args:
            test_type: The statistical test that was selected
            
        Returns:
            EffectSizeMeasure: COHENS_D for parametric, CLIFFS_DELTA for non-parametric
        """
        # FR-013: Parametric tests use Cohen's d
        if test_type in (TestType.T_TEST, TestType.WELCH_T, TestType.ANOVA, TestType.WELCH_ANOVA):
            return EffectSizeMeasure.COHENS_D
        
        # FR-014: Non-parametric tests use Cliff's Delta
        elif test_type in (TestType.MANN_WHITNEY, TestType.KRUSKAL_WALLIS):
            return EffectSizeMeasure.CLIFFS_DELTA
        
        else:
            raise ValueError(f"Unknown test type for effect size selection: {test_type}")
    
    def _perform_two_group_test(
        self,
        metric_name: str,
        metric_data: Dict[str, List[float]],
        distributions: List[MetricDistribution]
    ) -> Optional[StatisticalTest]:
        """Perform two-group comparison using three-way test selection."""
        groups = list(metric_data.keys())
        group1_name, group2_name = groups[0], groups[1]
        group1_vals = metric_data[group1_name]
        group2_vals = metric_data[group2_name]
        
        # T022: Get distributions for this metric
        metric_dists = [d for d in distributions if d.metric_name == metric_name]
        
        # T016-T022: Use three-way test selection logic
        test_type, assumptions, rationale = self._select_statistical_test(metric_dists, self.alpha)
        
        # Execute the selected test
        if test_type == TestType.T_TEST:
            # FR-009: Student's t-test (equal variance)
            statistic, p_value = stats.ttest_ind(group1_vals, group2_vals)
        elif test_type == TestType.WELCH_T:
            # FR-010: Welch's t-test (unequal variance)
            statistic, p_value = stats.ttest_ind(group1_vals, group2_vals, equal_var=False)
        elif test_type == TestType.MANN_WHITNEY:
            # FR-011: Mann-Whitney U (non-parametric)
            statistic, p_value = stats.mannwhitneyu(
                group1_vals, group2_vals, alternative='two-sided'
            )
        else:
            raise ValueError(f"Unexpected test type for two-group comparison: {test_type}")
        
        is_significant = p_value < self.alpha
        
        # T064: Power-aware interpretation for non-significant results (FR-038)
        # Calculate power first to inform interpretation
        effect_size = abs(cohens_d(group1_vals, group2_vals))
        power_result = self._calculate_power_analysis(
            test_type=test_type,
            effect_size=effect_size,
            n1=len(group1_vals),
            n2=len(group2_vals),
            alpha=self.alpha,
            target_power=0.80
        )
        
        # Use neutral language in interpretation
        if is_significant:
            conclusion = "Groups differ meaningfully"
        else:
            # FR-038: Avoid claiming "no effect exists" when power is low
            if power_result.achieved_power < 0.80:
                conclusion = (
                    f"Insufficient evidence to detect a difference "
                    f"(achieved power: {power_result.achieved_power:.1%})"
                )
            else:
                conclusion = "Insufficient evidence to conclude a difference exists"
        
        interpretation = (
            f"Comparing {group1_name} vs {group2_name}: "
            f"{'Significant difference' if is_significant else 'No significant difference'} "
            f"detected ({format_pvalue(p_value)}, α={self.alpha}). "
            f"{conclusion}."
        )
        
        # T022-T023, T030: Create test with new fields
        return StatisticalTest(
            test_type=test_type,
            metric_name=metric_name,
            groups=groups,
            statistic=float(statistic),
            p_value=float(p_value),
            is_significant=is_significant,
            rationale=rationale,
            interpretation=interpretation,
            group_data=metric_data,
            test_rationale=rationale,  # T022
            assumptions_checked=assumptions,  # T023
            achieved_power=power_result.achieved_power,  # T030
            recommended_n=power_result.recommended_n_per_group,  # T030 - Fixed field name
            power_adequate=power_result.power_adequate  # T030
        )
    
    def _perform_multi_group_test(
        self,
        metric_name: str,
        metric_data: Dict[str, List[float]],
        distributions: List[MetricDistribution]
    ) -> Optional[StatisticalTest]:
        """Perform multi-group comparison using three-way test selection."""
        groups = list(metric_data.keys())
        values_list = [metric_data[g] for g in groups]
        
        # T022: Get distributions for this metric
        metric_dists = [d for d in distributions if d.metric_name == metric_name]
        
        # T016-T022: Use three-way test selection logic
        test_type, assumptions, rationale = self._select_statistical_test(metric_dists, self.alpha)
        
        # Execute the selected test
        if test_type == TestType.ANOVA:
            # FR-006: Standard ANOVA (equal variance)
            statistic, p_value = stats.f_oneway(*values_list)
        elif test_type == TestType.WELCH_ANOVA:
            # FR-007, T021: Welch's ANOVA (unequal variance)
            statistic, p_value = self._welch_anova(*values_list)
        elif test_type == TestType.KRUSKAL_WALLIS:
            # FR-008: Kruskal-Wallis (non-parametric)
            statistic, p_value = stats.kruskal(*values_list)
        else:
            raise ValueError(f"Unexpected test type for multi-group comparison: {test_type}")
        
        is_significant = p_value < self.alpha
        
        # T064: Power-aware interpretation for non-significant results (FR-038)
        # Calculate power first to inform interpretation (approximation for multi-group)
        all_values = np.concatenate(values_list)
        group_means = [np.mean(vals) for vals in values_list]
        grand_mean = np.mean(all_values)
        pooled_std = np.std(all_values, ddof=1)
        
        # Approximate Cohen's f from between-group variance
        if pooled_std > 0:
            between_group_variance = np.mean([(m - grand_mean)**2 for m in group_means])
            cohens_f = np.sqrt(between_group_variance) / pooled_std
        else:
            cohens_f = 0.0
        
        n_per_group = int(np.mean([len(vals) for vals in values_list]))
        
        power_result = self._calculate_power_analysis(
            test_type=test_type,
            effect_size=cohens_f,
            n1=n_per_group,
            n_groups=len(groups),
            alpha=self.alpha,
            target_power=0.80
        )
        
        # Use neutral language in interpretation
        if is_significant:
            conclusion = "At least one group differs"
        else:
            # FR-038: Avoid claiming "no differences exist" when power is low
            if power_result.achieved_power < 0.80:
                conclusion = (
                    f"Insufficient evidence to detect differences "
                    f"(achieved power: {power_result.achieved_power:.1%})"
                )
            else:
                conclusion = "Insufficient evidence to conclude differences exist"
        
        interpretation = (
            f"Comparing {len(groups)} groups ({', '.join(groups)}): "
            f"{'Significant differences' if is_significant else 'No significant differences'} "
            f"detected ({format_pvalue(p_value)}, α={self.alpha}). "
            f"{conclusion}."
        )
        
        # T022-T023, T030: Create test with new fields
        return StatisticalTest(
            test_type=test_type,
            metric_name=metric_name,
            groups=groups,
            statistic=float(statistic),
            p_value=float(p_value),
            is_significant=is_significant,
            rationale=rationale,
            interpretation=interpretation,
            group_data=metric_data,
            test_rationale=rationale,  # T022
            assumptions_checked=assumptions,  # T023
            achieved_power=power_result.achieved_power,  # T030
            recommended_n=power_result.recommended_n_per_group,  # T030 - Fixed field name
            power_adequate=power_result.power_adequate  # T030
        )
    
    # T021: Welch's ANOVA implementation
    def _welch_anova(self, *groups):
        """
        Perform Welch's ANOVA (heterogeneous variances one-way ANOVA).
        
        Uses the Welch F-statistic which doesn't assume equal variances.
        Based on Welch (1951) methodology.
        
        Args:
            *groups: Variable number of group arrays
        
        Returns:
            Tuple of (statistic, pvalue)
        
        Reference:
            Welch, B. L. (1951). On the comparison of several mean values: 
            an alternative approach. Biometrika, 38(3/4), 330-336.
        """
        k = len(groups)  # Number of groups
        if k < 2:
            raise ValueError("Need at least 2 groups for Welch's ANOVA")
        
        # Calculate group statistics
        n_i = np.array([len(g) for g in groups])
        mean_i = np.array([np.mean(g) for g in groups])
        var_i = np.array([np.var(g, ddof=1) for g in groups])
        w_i = n_i / var_i  # Weights
        
        # Grand weighted mean
        grand_mean = np.sum(w_i * mean_i) / np.sum(w_i)
        
        # Welch F-statistic (numerator)
        numerator = np.sum(w_i * (mean_i - grand_mean)**2) / (k - 1)
        
        # Welch F-statistic (denominator correction)
        denominator_term = np.sum((1 - w_i / np.sum(w_i))**2 / (n_i - 1))
        denominator = 1 + (2 * (k - 2) / (k**2 - 1)) * denominator_term
        
        # Welch F-statistic
        f_statistic = numerator / denominator
        
        # Degrees of freedom
        df1 = k - 1
        df2 = (k**2 - 1) / (3 * denominator_term)
        
        # P-value from F-distribution
        p_value = 1 - stats.f.cdf(f_statistic, df1, df2)
        
        return f_statistic, p_value
    
    # T024-T029: Power analysis implementation
    def _calculate_power_analysis(
        self,
        test_type: TestType,
        effect_size: float,
        n1: int,
        n2: Optional[int] = None,
        n_groups: Optional[int] = None,
        alpha: float = 0.05,
        target_power: float = 0.80
    ) -> 'PowerAnalysis':
        """
        Calculate achieved statistical power and sample size recommendations.
        
        Uses statsmodels power analysis modules to compute:
        1. Achieved power given effect size and sample sizes
        2. Recommended sample size if power is inadequate
        
        Args:
            test_type: Type of statistical test (T_TEST, WELCH_T, ANOVA, etc.)
            effect_size: Cohen's d for t-tests, Cohen's f for ANOVA
            n1: Sample size of group 1 (or per-group for ANOVA)
            n2: Sample size of group 2 (for pairwise tests, optional)
            n_groups: Number of groups (for ANOVA tests, optional)
            alpha: Significance level (default 0.05)
            target_power: Desired power threshold (default 0.80)
        
        Returns:
            PowerAnalysis object with achieved_power, power_adequate, recommended_n
        
        References:
            - Cohen, J. (1988). Statistical Power Analysis for the Behavioral Sciences
            - statsmodels.stats.power documentation
        """
        from statsmodels.stats.power import TTestIndPower, FTestAnovaPower
        from .models import PowerAnalysis
        
        # T029: Edge case handling
        if n1 < 5 or (n2 is not None and n2 < 5):
            return PowerAnalysis(
                test_type=test_type.value,
                effect_size=effect_size,
                sample_size_group1=n1,
                sample_size_group2=n2,
                n_groups=n_groups,
                alpha=alpha,
                achieved_power=None,
                target_power=target_power,
                power_adequate=False,
                adequacy_flag="indeterminate",
                recommended_n=None,
                warning_message="Sample size too small (n<5) for reliable power calculation"
            )
        
        if abs(effect_size) > 5.0:
            return PowerAnalysis(
                test_type=test_type.value,
                effect_size=effect_size,
                sample_size_group1=n1,
                sample_size_group2=n2,
                n_groups=n_groups,
                alpha=alpha,
                achieved_power=1.0,
                target_power=target_power,
                power_adequate=True,
                adequacy_flag="adequate",
                recommended_n=None,
                warning_message="Effect size extremely large (|d|>5), power ~1.0"
            )
        
        achieved_power = None
        recommended_n = None
        warning_message = None
        
        try:
            # T025-T026: Power calculations based on test type
            if test_type in [TestType.T_TEST, TestType.WELCH_T, TestType.MANN_WHITNEY]:
                # T025: Pairwise tests use TTestIndPower
                power_analyzer = TTestIndPower()
                
                # T027: Calculate achieved power
                if n2 is None:
                    n2 = n1  # Assume equal groups if not specified
                
                ratio = n2 / n1 if n1 > 0 else 1.0
                
                achieved_power = power_analyzer.solve_power(
                    effect_size=abs(effect_size),
                    nobs1=n1,
                    ratio=ratio,
                    alpha=alpha,
                    power=None,  # Solve for power
                    alternative='two-sided'
                )
                
                # T028: Calculate recommended sample size if power inadequate
                if achieved_power < target_power:
                    recommended_n = power_analyzer.solve_power(
                        effect_size=abs(effect_size),
                        nobs1=None,  # Solve for n
                        ratio=1.0,   # Assume equal groups for recommendation
                        alpha=alpha,
                        power=target_power,
                        alternative='two-sided'
                    )
                    recommended_n = int(np.ceil(recommended_n))
                
            elif test_type in [TestType.ANOVA, TestType.WELCH_ANOVA, TestType.KRUSKAL_WALLIS]:
                # T026: Multi-group tests use FTestAnovaPower
                if n_groups is None or n_groups < 2:
                    raise ValueError("n_groups required for ANOVA power analysis")
                
                power_analyzer = FTestAnovaPower()
                
                # Convert Cohen's d to Cohen's f if needed (approximation)
                # Cohen's f ≈ d / 2 for two groups, use directly for ANOVA
                cohens_f = abs(effect_size) if test_type == TestType.ANOVA else abs(effect_size) / 2
                
                total_n = n1 * n_groups
                
                # T027: Calculate achieved power
                achieved_power = power_analyzer.solve_power(
                    effect_size=cohens_f,
                    nobs=total_n,
                    alpha=alpha,
                    k_groups=n_groups,
                    power=None  # Solve for power
                )
                
                # T028: Calculate recommended sample size per group
                if achieved_power < target_power:
                    recommended_total_n = power_analyzer.solve_power(
                        effect_size=cohens_f,
                        nobs=None,  # Solve for total n
                        alpha=alpha,
                        k_groups=n_groups,
                        power=target_power
                    )
                    recommended_n = int(np.ceil(recommended_total_n / n_groups))
            
            # Determine adequacy
            if achieved_power is None:
                adequacy_flag = "indeterminate"
                power_adequate = False
            elif achieved_power >= target_power:
                adequacy_flag = "adequate"
                power_adequate = True
                # Add warning about post-hoc power
                if warning_message is None:
                    warning_message = ""
                else:
                    warning_message += " "
                warning_message += (
                    "NOTE: This is post-hoc power (calculated from observed data). "
                    "Post-hoc power is directly related to p-values and does not provide "
                    "independent information about study adequacy. "
                    "Use sample size recommendations for prospective planning."
                )
            elif achieved_power >= 0.50:
                adequacy_flag = "marginal"
                power_adequate = False
            else:
                adequacy_flag = "inadequate"
                power_adequate = False
                warning_message = (
                    f"Achieved power ({achieved_power:.2f}) is very low (<0.50). "
                    "Results may be unreliable due to insufficient sample size."
                )
        
        except Exception as e:
            # T029: Graceful error handling
            achieved_power = None
            power_adequate = False
            adequacy_flag = "error"
            warning_message = f"Power calculation failed: {str(e)}"
        
        # Build group_names from context (this will need to be passed in properly)
        # For now, use generic names
        if n_groups and n_groups > 2:
            group_names = [f"Group{i+1}" for i in range(n_groups)]
        elif n2 is not None:
            group_names = ["Group1", "Group2"]
        else:
            group_names = ["Group1"]
        
        return PowerAnalysis(
            comparison_id="power_analysis",  # Will be set properly by caller
            metric_name="metric",  # Will be set properly by caller
            group_names=group_names,
            effect_size_value=abs(effect_size),
            effect_size_type="cohens_d" if test_type in [TestType.T_TEST, TestType.WELCH_T, TestType.MANN_WHITNEY] else "cohens_f",
            n_group1=n1,
            n_group2=n2,
            achieved_power=achieved_power if achieved_power is not None else 0.0,
            target_power=target_power,
            alpha=alpha,
            power_adequate=power_adequate,
            recommended_n_per_group=recommended_n,
            adequacy_flag=adequacy_flag,
            warning_message=warning_message
        )
    
    # T010-T015: Bootstrap confidence interval with independent group resampling
    def _bootstrap_confidence_interval(
        self,
        group1_values: List[float],
        group2_values: List[float],
        effect_size_func,
        n_iterations: int = 10000,
        confidence_level: float = 0.95,
        random_seed: Optional[int] = None
    ) -> Tuple[float, float, bool]:
        """
        Compute bootstrap confidence interval for effect sizes using independent group resampling.
        
        This is the CORRECT approach - each group is resampled independently, preserving
        group structure. The broken approach resamples from a combined array, which
        scrambles group assignments and produces invalid CIs.
        
        Args:
            group1_values: First group's data
            group2_values: Second group's data
            effect_size_func: Function that computes effect size (cohens_d or cliffs_delta)
            n_iterations: Number of bootstrap samples (must be ≥ 10,000 per FR-003)
            confidence_level: CI level (default 0.95 for 95% CI)
            random_seed: Optional seed for reproducibility
        
        Returns:
            Tuple of (ci_lower, ci_upper, ci_valid)
            - ci_lower: Lower bound of CI
            - ci_upper: Upper bound of CI
            - ci_valid: True if CI contains point estimate (should always be True)
        
        Raises:
            StatisticalAnalysisError: If bootstrap fails or CI doesn't contain point estimate
        """
        from .exceptions import StatisticalAnalysisError
        
        # FR-003: Require at least 10,000 iterations
        if n_iterations < 10000:
            raise ValueError(f"n_iterations must be ≥ 10,000, got {n_iterations}")
        
        # Preconditions
        if len(group1_values) < 2 or len(group2_values) < 2:
            raise ValueError("Each group must have at least 2 samples for bootstrap")
        
        # Compute point estimate on original data
        try:
            point_estimate = effect_size_func(group1_values, group2_values)
        except Exception as e:
            raise StatisticalAnalysisError(f"Failed to compute point estimate: {e}")
        
        # Use provided seed or class random state
        rng = np.random.RandomState(random_seed) if random_seed is not None else self.rng
        
        # Bootstrap resampling - INDEPENDENT GROUP RESAMPLING (FR-001)
        bootstrap_stats = []
        n1, n2 = len(group1_values), len(group2_values)
        
        for _ in range(n_iterations):
            try:
                # FR-001: Resample each group INDEPENDENTLY (preserves group structure)
                g1_sample = rng.choice(group1_values, size=n1, replace=True)
                g2_sample = rng.choice(group2_values, size=n2, replace=True)
                
                # Compute effect size on resampled groups
                effect = effect_size_func(g1_sample.tolist(), g2_sample.tolist())
                bootstrap_stats.append(effect)
            except Exception:
                # FR-004: Handle bootstrap failures gracefully
                continue
        
        # FR-004: Check if bootstrap failed
        if len(bootstrap_stats) < n_iterations * 0.9:  # Allow 10% failure rate
            raise StatisticalAnalysisError(
                f"Bootstrap failed: only {len(bootstrap_stats)}/{n_iterations} iterations succeeded"
            )
        
        # Compute percentile-based CI
        alpha = 1 - confidence_level
        ci_lower = float(np.percentile(bootstrap_stats, (alpha / 2) * 100))
        ci_upper = float(np.percentile(bootstrap_stats, (1 - alpha / 2) * 100))
        
        # FR-002: Validate that CI contains point estimate
        from ..utils.statistical_helpers import validate_ci
        ci_valid = validate_ci(point_estimate, ci_lower, ci_upper)
        
        if not ci_valid:
            # This should NEVER happen with correct independent resampling
            raise StatisticalAnalysisError(
                f"CRITICAL BUG: Bootstrap CI [{ci_lower:.3f}, {ci_upper:.3f}] "
                f"does not contain point estimate {point_estimate:.3f}. "
                f"This indicates the bootstrap implementation is broken."
            )
        
        return ci_lower, ci_upper, ci_valid
    
    # T040-T043: Multiple comparison correction (NEW METHOD)
    def _apply_multiple_comparison_correction(
        self,
        pvalues: List[float],
        comparison_labels: List[str],
        metric_name: str,
        alpha: float = 0.05,
        method: str = "holm"
    ) -> 'MultipleComparisonCorrection':
        """
        Apply multiple testing correction to control family-wise error rate.
        
        Implements FR-022 to FR-026: Holm-Bonferroni correction for multiple comparisons.
        
        Args:
            pvalues: List of raw p-values from statistical tests
            comparison_labels: Identifiers for each comparison (e.g., "group1_vs_group2")
            metric_name: Name of metric family being corrected
            alpha: Family-wise error rate threshold (default 0.05)
            method: Correction method - "holm", "bonferroni", "fdr_bh", or "none"
            
        Returns:
            MultipleComparisonCorrection object with adjusted p-values and decisions
            
        Raises:
            ValueError: If method="none" when n_comparisons > 1 (T043)
        """
        from statsmodels.stats.multitest import multipletests
        from ..paper_generation.models import MultipleComparisonCorrection
        
        n_comparisons = len(pvalues)
        
        # FR-026: No correction needed for single comparison (T042)
        if n_comparisons == 1:
            method = "none"
            adjusted_pvalues = pvalues
            reject_decisions = [p < alpha for p in pvalues]
            corrected_alpha = alpha
        else:
            # FR-022: Apply Holm-Bonferroni correction for multiple comparisons (T041)
            # T043: Validation - must use correction when n > 1
            if method == "none":
                raise ValueError(
                    f"Must apply correction when n_comparisons > 1. "
                    f"Got {n_comparisons} comparisons but method='none'"
                )
            
            # T041: Use statsmodels multipletests with Holm method
            reject, adjusted_pvalues, alphacSidak, alphacBonf = multipletests(
                pvalues, alpha=alpha, method=method
            )
            reject_decisions = list(reject)
            adjusted_pvalues = list(adjusted_pvalues)
            corrected_alpha = alphacBonf
        
        # Create MultipleComparisonCorrection object
        return MultipleComparisonCorrection(
            metric_name=metric_name,
            correction_method=method,
            n_comparisons=n_comparisons,
            alpha=alpha,
            raw_pvalues=list(pvalues),
            adjusted_pvalues=adjusted_pvalues,
            comparison_labels=list(comparison_labels),
            reject_decisions=reject_decisions,
            corrected_alpha=corrected_alpha
        )
    
    # T010: Calculate effect sizes (T036: Updated to use test_type for alignment)
    def _calculate_effect_sizes(
        self,
        metric_name: str,
        metric_data: Dict[str, List[float]],
        distributions: List[MetricDistribution],
        test_results: List[StatisticalTest] = None,
        findings: 'StatisticalFindings' = None
    ) -> List[EffectSize]:
        """
        Calculate effect sizes for all pairwise comparisons.
        
        T036: Now uses test_type to select effect size measure (FR-013, FR-014, FR-015)
        - Parametric tests → Cohen's d
        - Non-parametric tests → Cliff's Delta
        
        Args:
            metric_name: Name of the metric being analyzed
            metric_data: Dict mapping group names to value lists
            distributions: MetricDistribution objects for normality checks
            test_results: Statistical test results for this metric (T036: NEW)
            findings: StatisticalFindings object for warning collection (Feature 013)
            
        Returns:
            List of EffectSize objects with proper measure-test alignment
        """
        effects = []
        groups = list(metric_data.keys())
        
        # Check for zero variance
        dist_map = {d.group_name: d for d in distributions if d.metric_name == metric_name}
        
        # T036: Build test type lookup for this metric's pairwise comparisons
        test_type_map = {}
        if test_results:
            for test in test_results:
                if test.metric_name == metric_name and len(test.groups) == 2:
                    # Create sorted key to match pairwise logic
                    key = tuple(sorted(test.groups))
                    test_type_map[key] = test.test_type
        
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
                
                # T036: Use test type to select effect size measure (FR-013, FR-014)
                comparison_key = tuple(sorted([group1, group2]))
                
                # Feature 013: Use centralized variance quality check
                has_variance1 = self._check_variance_quality(vals1)
                has_variance2 = self._check_variance_quality(vals2)
                zero_variance_detected = not (has_variance1 and has_variance2)
                
                if comparison_key in test_type_map:
                    # T036: Get measure based on test type
                    test_type = test_type_map[comparison_key]
                    measure = self._select_effect_size_measure(test_type)
                else:
                    # Fallback: Use normality check (backward compatibility)
                    _, p1 = stats.shapiro(vals1) if len(vals1) >= 3 else (None, 0.0)
                    _, p2 = stats.shapiro(vals2) if len(vals2) >= 3 else (None, 0.0)
                    both_normal = (p1 > self.alpha) and (p2 > self.alpha)
                    measure = EffectSizeMeasure.COHENS_D if both_normal else EffectSizeMeasure.CLIFFS_DELTA
                    test_type = None  # T038: Will be set below
                
                # T036-T037: Calculate effect based on selected measure
                if measure == EffectSizeMeasure.COHENS_D:
                    # Skip Cohen's d if zero variance (would produce inflated/invalid d)
                    if zero_variance_detected:
                        # Skip this comparison entirely - will not be added to results
                        warning_msg = (
                            f"Skipping Cohen's d for {group1} vs {group2} on {metric_name}: "
                            f"zero/near-zero variance detected. Effect size would be invalid."
                        )
                        logger.warning(warning_msg)
                        if findings:
                            findings.add_warning(
                                'Zero Variance',
                                f"Framework '{group1}' or '{group2}' showed zero variance for metric '{metric_name}'; Cohen's d calculation skipped"
                            )
                        continue
                    
                    # Use Cohen's d
                    effect_value = cohens_d(vals1, vals2)
                    effect_func = cohens_d
                    measure_str = "cohens_d"
                    
                    # T010-T015: Bootstrap CI using INDEPENDENT group resampling
                    ci_lower, ci_upper, ci_valid = self._bootstrap_confidence_interval(
                        vals1, vals2, effect_func, n_iterations=10000
                    )
                    
                    magnitude = interpret_effect_size(effect_value, measure_str)
                    # T061-T062: Use neutral language (FR-035, FR-036)
                    if effect_value > 0:
                        direction_phrase = f"shows higher values than"
                    elif effect_value < 0:
                        direction_phrase = f"shows lower values than"
                    else:
                        direction_phrase = f"shows similar values to"
                    
                    interpretation = (
                        f"Cohen's d = {effect_value:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]: "
                        f"{magnitude} effect size. "
                        f"{group1} {direction_phrase} "
                        f"{group2} by {abs(effect_value):.2f} pooled standard deviations."
                    )
                
                elif measure == EffectSizeMeasure.CLIFFS_DELTA:
                    # Use Cliff's Delta
                    effect_value = cliffs_delta(vals1, vals2)
                    effect_func = cliffs_delta
                    measure_str = "cliffs_delta"
                    
                    # T010-T015: Bootstrap CI using INDEPENDENT group resampling
                    ci_lower, ci_upper, ci_valid = self._bootstrap_confidence_interval(
                        vals1, vals2, effect_func, n_iterations=10000
                    )
                    
                    # Warn if zero variance produces deterministic CI
                    if zero_variance_detected and abs(ci_upper - ci_lower) < 0.01:
                        warning_msg = (
                            f"Cliff's Delta CI for {group1} vs {group2} on {metric_name} "
                            f"is deterministic [{ci_lower:.3f}, {ci_upper:.3f}] due to "
                            f"zero/near-zero variance. This represents categorical "
                            f"separation rather than continuous effect size."
                        )
                        logger.warning(warning_msg)
                        if findings:
                            findings.add_warning(
                                'Deterministic CI',
                                f"Cliff's Delta for metric '{metric_name}' comparison '{group1} vs {group2}' is {effect_value:.3f} with CI [{ci_lower:.3f}, {ci_upper:.3f}], indicating complete separation between groups"
                            )
                    
                    magnitude = interpret_effect_size(effect_value, measure_str)
                    
                    # T063: Special handling for extreme Cliff's Delta values (FR-037)
                    if abs(effect_value) >= 0.999:
                        # Extreme case: all values in one group exceed the other
                        if effect_value > 0:
                            dominance_phrase = (
                                f"all observed values in {group1} exceed those in {group2}"
                            )
                        else:
                            dominance_phrase = (
                                f"all observed values in {group1} are less than those in {group2}"
                            )
                    else:
                        # Normal case: probability interpretation with neutral language (FR-036)
                        probability = abs(effect_value) * 50 + 50
                        if effect_value > 0:
                            dominance_phrase = (
                                f"{group1} has systematically higher values compared to {group2} "
                                f"(probability: {probability:.1f}%)"
                            )
                        elif effect_value < 0:
                            dominance_phrase = (
                                f"{group1} has systematically lower values compared to {group2} "
                                f"(probability: {100 - probability:.1f}%)"
                            )
                        else:
                            dominance_phrase = f"{group1} and {group2} show similar distributions"
                    
                    interpretation = (
                        f"Cliff's Delta = {effect_value:.3f} [{ci_lower:.3f}, {ci_upper:.3f}]: "
                        f"{magnitude} effect size. "
                        f"{dominance_phrase}."
                    )
                
                else:
                    # T037: Validation - this should never happen
                    raise ValueError(f"Invalid effect size measure selected: {measure}")
                
                # T014, T038: Set EffectSize fields including test_type_alignment
                effect = EffectSize(
                    measure=measure,
                    metric_name=metric_name,
                    group1=group1,
                    group2=group2,
                    value=float(effect_value),
                    ci_lower=ci_lower,
                    ci_upper=ci_upper,
                    magnitude=magnitude,
                    interpretation=interpretation,
                    bootstrap_iterations=10000,  # T014
                    ci_method="bootstrap",        # T014
                    ci_valid=ci_valid,           # T014
                    test_type_alignment=test_type if test_type else None  # T038
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
                logger.debug(
                    f"Skipping power analysis for {metric_name}: "
                    f"zero variance in {group1} or {group2}"
                )
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
        
        # T048: Multiple comparison corrections (FR-025)
        tests_with_correction = [
            t for t in findings.statistical_tests 
            if hasattr(t, 'correction_method') and t.correction_method != "none"
        ]
        
        if tests_with_correction:
            # Get unique correction methods used
            correction_methods = set(t.correction_method for t in tests_with_correction)
            
            if "holm" in correction_methods:
                sections.append(
                    "Multiple comparison correction was applied using the Holm-Bonferroni method "
                    f"(Holm, 1979) to control family-wise error rate at α={self.alpha}. "
                    "This sequential procedure is less conservative than the standard Bonferroni "
                    "correction while maintaining strong control of Type I error. "
                    "Both raw and adjusted p-values are reported. "
                )
            elif "bonferroni" in correction_methods:
                sections.append(
                    "Bonferroni correction was applied to control family-wise error rate. "
                )
        
        # Bootstrap confidence intervals
        if findings.effect_sizes:
            sections.append(
                f"95% confidence intervals for effect sizes were computed using bootstrap resampling "
                f"(n=10,000 iterations, seed={self.random_seed}). "
            )
            
            # Document zero-variance detection (FR-034: Data quality checks)
            sections.append(
                "Effect size calculations included data quality checks: "
                "groups with zero or near-zero variance (standard deviation < 0.01 or "
                "interquartile range < 0.01) were flagged, as standardized effect sizes "
                "(e.g., Cohen's d) are inappropriate for such data. "
                "In these cases, Cohen's d was skipped, and Cliff's Delta confidence intervals "
                "flagged as 'deterministic' to indicate categorical separation rather than "
                "continuous effect magnitude. "
            )
            
            # Document outlier detection policy (FR-035: Data quality transparency)
            sections.append(
                "Outliers were identified using Tukey's method (values beyond Q1 - 1.5×IQR or "
                "Q3 + 1.5×IQR) and reported in descriptive statistics. "
                "**Outliers were retained in all analyses** (no winsorization or trimming), "
                "as they may represent genuine variation in framework performance. "
                "Robust non-parametric methods (Mann-Whitney U, Kruskal-Wallis, Cliff's Delta) "
                "were preferentially used when outliers were present, as these methods are "
                "resistant to extreme values. "
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


