"""
Centralized metrics configuration loader.

Provides a single source of truth for all metrics definitions, loaded from
experiment.yaml. This ensures consistency across reporting, analysis, and
visualization subsystems.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml


@dataclass
class MetricDefinition:
    """
    Definition of a single metric.
    
    Attributes:
        key: Metric identifier (e.g., 'TOK_IN', 'COST_USD')
        name: Human-readable name
        description: Detailed description of what the metric measures
        unit: Unit of measurement (e.g., 'tokens', 'USD', 'seconds')
        category: Category for grouping (e.g., 'efficiency', 'interaction', 'cost')
        ideal_direction: 'minimize' or 'maximize' for optimization
        data_source: Where the data comes from (e.g., 'openai_usage_api', 'calculated')
        aggregation: How to aggregate across steps (e.g., 'sum', 'mean', 'count')
        display_format: Python format string for display (e.g., '{:,.0f}', '${:.4f}')
        statistical_test: Whether to include in statistical tests
        stopping_rule_eligible: Whether to use in stopping rule evaluation
        visualization_types: List of chart types that can display this metric
        calculation: Optional calculation details for derived metrics
    """
    key: str
    name: str
    description: str
    unit: str
    category: str
    ideal_direction: str
    data_source: str
    aggregation: str
    display_format: str
    statistical_test: bool
    stopping_rule_eligible: bool
    visualization_types: List[str] = field(default_factory=list)
    calculation: Optional[Dict[str, Any]] = None
    
    def format_value(self, value: Any) -> str:
        """
        Format a value according to this metric's display format.
        
        Args:
            value: Raw metric value
            
        Returns:
            Formatted string representation
        """
        if value is None:
            return "N/A"
        
        try:
            return self.display_format.format(value)
        except (ValueError, TypeError):
            return str(value)
    
    def should_invert_for_normalization(self) -> bool:
        """
        Check if metric should be inverted for normalization.
        
        For radar charts and other normalized visualizations, 'minimize' metrics
        should be inverted so that better performance points outward.
        
        Returns:
            True if metric should be inverted (ideal_direction == 'minimize')
        """
        return self.ideal_direction == 'minimize'


class MetricsConfig:
    """
    Centralized metrics configuration loaded from experiment.yaml.
    
    Provides methods to query metrics by category, type, and flags.
    Ensures consistency across all subsystems that use metrics.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize metrics configuration.
        
        Args:
            config_path: Path to config file (defaults to config.yaml)
        """
        if config_path is None:
            # Default to config.yaml relative to project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config.yaml"
        
        self.config_path = Path(config_path)
        self._config: Dict[str, Any] = {}
        self._metrics: Dict[str, MetricDefinition] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from YAML file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = yaml.safe_load(f)
        
        # Parse metrics into MetricDefinition objects
        self._parse_metrics()
    
    def _parse_metrics(self) -> None:
        """Parse metrics section into MetricDefinition objects."""
        metrics_section = self._config.get('metrics', {})
        
        # Parse reliable metrics
        reliable = metrics_section.get('reliable_metrics', {})
        for key, data in reliable.items():
            self._metrics[key] = MetricDefinition(
                key=key,
                name=data.get('name', key),
                description=data.get('description', ''),
                unit=data.get('unit', ''),
                category=data.get('category', 'unknown'),
                ideal_direction=data.get('ideal_direction', 'minimize'),
                data_source=data.get('data_source', 'unknown'),
                aggregation=data.get('aggregation', 'sum'),
                display_format=data.get('display_format', '{:.2f}'),
                statistical_test=data.get('statistical_test', False),
                stopping_rule_eligible=data.get('stopping_rule_eligible', False),
                visualization_types=data.get('visualization_types', [])
            )
        
        # Parse derived metrics
        derived = metrics_section.get('derived_metrics', {})
        for key, data in derived.items():
            self._metrics[key] = MetricDefinition(
                key=key,
                name=data.get('name', key),
                description=data.get('description', ''),
                unit=data.get('unit', ''),
                category=data.get('category', 'unknown'),
                ideal_direction=data.get('ideal_direction', 'minimize'),
                data_source=data.get('data_source', 'calculated'),
                aggregation=data.get('aggregation', 'calculated'),
                display_format=data.get('display_format', '{:.2f}'),
                statistical_test=data.get('statistical_test', False),
                stopping_rule_eligible=data.get('stopping_rule_eligible', False),
                visualization_types=data.get('visualization_types', []),
                calculation=data.get('calculation')
            )
    
    def get_reliable_metrics(self) -> Dict[str, MetricDefinition]:
        """
        Get all reliable metrics (directly measured).
        
        Returns:
            Dictionary mapping metric keys to definitions
        """
        metrics_section = self._config.get('metrics', {})
        reliable_keys = metrics_section.get('reliable_metrics', {}).keys()
        return {k: v for k, v in self._metrics.items() if k in reliable_keys}
    
    def get_derived_metrics(self) -> Dict[str, MetricDefinition]:
        """
        Get all derived metrics (calculated from other metrics).
        
        Returns:
            Dictionary mapping metric keys to definitions
        """
        metrics_section = self._config.get('metrics', {})
        derived_keys = metrics_section.get('derived_metrics', {}).keys()
        return {k: v for k, v in self._metrics.items() if k in derived_keys}
    
    def get_all_metrics(self) -> Dict[str, MetricDefinition]:
        """
        Get all metrics (reliable + derived).
        
        Returns:
            Dictionary mapping metric keys to definitions
        """
        return self._metrics.copy()
    
    def get_metric(self, key: str) -> Optional[MetricDefinition]:
        """
        Get a specific metric definition by key.
        
        Args:
            key: Metric identifier (e.g., 'TOK_IN')
            
        Returns:
            MetricDefinition or None if not found
        """
        return self._metrics.get(key)
    
    def get_metrics_for_statistics(self) -> List[str]:
        """
        Get list of metric keys eligible for statistical testing.
        
        Returns:
            List of metric keys where statistical_test=True
        """
        return [
            key for key, metric in self._metrics.items()
            if metric.statistical_test
        ]
    
    def get_metrics_for_stopping_rule(self) -> List[str]:
        """
        Get list of metric keys eligible for stopping rule evaluation.
        
        Returns:
            List of metric keys where stopping_rule_eligible=True
        """
        return [
            key for key, metric in self._metrics.items()
            if metric.stopping_rule_eligible
        ]
    
    def get_metrics_by_category(self, category: str) -> Dict[str, MetricDefinition]:
        """
        Get all metrics in a specific category.
        
        Args:
            category: Category name (e.g., 'efficiency', 'interaction', 'cost')
            
        Returns:
            Dictionary mapping metric keys to definitions
        """
        return {
            key: metric for key, metric in self._metrics.items()
            if metric.category == category
        }
    
    def get_visualization_config(self, viz_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific visualization.
        
        Args:
            viz_name: Visualization identifier (e.g., 'radar_chart')
            
        Returns:
            Visualization configuration dictionary or None if not found
        """
        viz_section = self._config.get('visualizations', {})
        return viz_section.get(viz_name)
    
    def get_all_visualizations(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all visualization configurations.
        
        Returns:
            Dictionary mapping visualization names to their configurations
        """
        return self._config.get('visualizations', {})
    
    def get_excluded_metrics(self) -> Dict[str, Dict[str, Any]]:
        """
        Get all excluded metrics (unmeasured or partially measured).
        
        Returns:
            Dictionary mapping metric keys to their metadata:
            {
                'AUTR': {
                    'name': 'Autonomy Rate',
                    'reason': 'Hardcoded HITL detection...',
                    'status': 'partial_measurement',
                    'original_formula': '1 - (HIT / 6)'
                },
                ...
            }
        """
        metrics_section = self._config.get('metrics', {})
        return metrics_section.get('excluded_metrics', {})
    
    def get_excluded_metrics(self) -> Dict[str, Dict[str, str]]:
        """
        Get all excluded metrics with their exclusion reasons.
        
        Returns:
            Dictionary mapping metric keys to exclusion information
        """
        metrics_section = self._config.get('metrics', {})
        return metrics_section.get('excluded_metrics', {})
    
    def get_categories(self) -> List[Dict[str, str]]:
        """
        Get all metric categories.
        
        Returns:
            List of category dictionaries with name, description, and color
        """
        metrics_section = self._config.get('metrics', {})
        return metrics_section.get('categories', [])
    
    def get_pricing_config(self, model: str) -> Optional[Dict[str, float]]:
        """
        Get pricing configuration for a specific model.
        
        Args:
            model: Model name (e.g., 'gpt-4o-mini')
            
        Returns:
            Dictionary with input_price, cached_price, output_price or None
        """
        pricing_section = self._config.get('pricing', {})
        models = pricing_section.get('models', {})
        return models.get(model)
    
    def get_report_config(self) -> Dict[str, Any]:
        """
        Get report configuration.
        
        Returns:
            Dictionary with report title and sections
        """
        return self._config.get('report', {})
    
    def get_report_sections(self) -> List[Dict[str, Any]]:
        """
        Get all enabled report sections sorted by order.
        
        Returns:
            List of section dictionaries sorted by 'order' field
        """
        report = self._config.get('report', {})
        sections = report.get('sections', [])
        
        # Filter enabled sections and sort by order
        enabled_sections = [s for s in sections if s.get('enabled', True)]
        return sorted(enabled_sections, key=lambda s: s.get('order', 999))
    
    def get_report_section(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific report section by name.
        
        Args:
            name: Section name (e.g., 'aggregate_statistics')
            
        Returns:
            Section configuration dictionary or None if not found
        """
        report = self._config.get('report', {})
        sections = report.get('sections', [])
        
        for section in sections:
            if section.get('name') == name:
                return section
        return None
    
    def format_value(self, metric_key: str, value: Any) -> str:
        """
        Format a value according to its metric's display format.
        
        Args:
            metric_key: Metric identifier
            value: Raw value
            
        Returns:
            Formatted string representation
        """
        metric = self.get_metric(metric_key)
        if metric:
            return metric.format_value(value)
        return str(value)
    
    def validate_metrics_data(self, data: Dict[str, Any]) -> List[str]:
        """
        Validate that metrics data contains all expected fields.
        
        Args:
            data: Dictionary of metric values
            
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        # Check for missing metrics
        expected_metrics = set(self._metrics.keys())
        provided_metrics = set(data.keys())
        
        missing = expected_metrics - provided_metrics
        if missing:
            errors.append(f"Missing metrics: {', '.join(sorted(missing))}")
        
        # Check for unexpected metrics
        unexpected = provided_metrics - expected_metrics
        if unexpected:
            errors.append(f"Unexpected metrics: {', '.join(sorted(unexpected))}")
        
        # Validate data types (basic check for numeric values)
        for key, value in data.items():
            if key in self._metrics and value is not None:
                if not isinstance(value, (int, float)):
                    errors.append(f"Metric {key} has non-numeric value: {type(value).__name__}")
        
        return errors


# Singleton instance for global access
_metrics_config_instance: Optional[MetricsConfig] = None


def get_metrics_config(config_path: Optional[Path] = None) -> MetricsConfig:
    """
    Get the singleton MetricsConfig instance.
    
    Args:
        config_path: Path to experiment.yaml (only used on first call)
        
    Returns:
        Global MetricsConfig instance
    """
    global _metrics_config_instance
    
    if _metrics_config_instance is None:
        _metrics_config_instance = MetricsConfig(config_path)
    
    return _metrics_config_instance


def reset_metrics_config() -> None:
    """
    Reset the singleton instance (primarily for testing).
    """
    global _metrics_config_instance
    _metrics_config_instance = None
