"""Visualization Factory for Config-Driven Chart Generation.

This module provides a factory class that dynamically generates visualizations
based on the visualizations configuration in experiment.yaml. It maps chart types
to visualization functions and handles parameter transformation.

Architecture:
    - VisualizationFactory: Main factory class that orchestrates chart generation
    - Chart Registry: Maps chart type names to visualization functions
    - Config Mapping: Transforms YAML config parameters to function arguments
    - Error Handling: Comprehensive validation and logging

Example:
    >>> from src.analysis.visualization_factory import VisualizationFactory
    >>> from src.utils.config_loader import load_config
    >>> 
    >>> config = load_config('config/experiment.yaml')
    >>> factory = VisualizationFactory(config)
    >>> factory.generate_all(frameworks_data, output_dir='./analysis_output')
"""

from typing import Dict, List, Any, Callable, Optional
from pathlib import Path

from src.analysis.visualizations import (
    radar_chart,
    token_efficiency_chart,
    api_calls_timeline,
    time_distribution_chart,
    api_efficiency_bar_chart,
    cache_efficiency_chart,
    api_efficiency_chart,
)
from src.utils.logger import get_logger

logger = get_logger(__name__)


class VisualizationFactory:
    """Factory for generating visualizations based on config."""
    
    # Registry mapping chart type names to visualization functions
    CHART_REGISTRY: Dict[str, Callable] = {
        'radar_chart': radar_chart,
        'token_efficiency_scatter': token_efficiency_chart,
        'api_calls_timeline': api_calls_timeline,
        'cost_boxplot': time_distribution_chart,  # Reuse time_distribution for cost
        'api_calls_evolution': api_calls_timeline,  # Same function, different params
        'api_efficiency_bar': api_efficiency_bar_chart,
        'cache_efficiency': cache_efficiency_chart,
        'api_efficiency_chart': api_efficiency_chart,
    }
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize visualization factory.
        
        Args:
            config: Complete experiment configuration dictionary
            
        Raises:
            ValueError: If config is missing required sections
        """
        if 'visualizations' not in config:
            raise ValueError("Config missing 'visualizations' section")
        
        self.config = config
        self.visualizations_config = config['visualizations']
        logger.info("VisualizationFactory initialized with %d chart definitions",
                   len(self.visualizations_config))
    
    def generate_all(
        self,
        frameworks_data: Dict[str, List[Dict[str, Any]]],
        aggregated_data: Optional[Dict[str, Dict[str, float]]] = None,
        timeline_data: Optional[Dict[str, Dict[int, Dict[str, float]]]] = None,
        output_dir: str = './analysis_output',
    ) -> Dict[str, bool]:
        """Generate all enabled visualizations.
        
        Args:
            frameworks_data: Raw run-level data for each framework
                {framework_name: [run1_metrics, run2_metrics, ...]}
            aggregated_data: Pre-computed aggregate statistics for each framework
                {framework_name: {metric: mean_value, ...}}
            timeline_data: Step-level metrics for timeline charts
                {framework_name: {step_num: {metric: value, ...}}}
            output_dir: Directory to save visualization files
            
        Returns:
            Dictionary mapping chart names to success status (True/False)
            
        Example:
            >>> results = factory.generate_all(
            ...     frameworks_data={'baes': [{'TOK_IN': 100}, ...]},
            ...     aggregated_data={'baes': {'TOK_IN': 100.5}},
            ...     output_dir='./output'
            ... )
            >>> print(results)
            {'radar_chart': True, 'token_efficiency_scatter': True, ...}
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for chart_name, chart_config in self.visualizations_config.items():
            # Skip disabled charts
            if not chart_config.get('enabled', True):
                logger.debug("Skipping disabled chart: %s", chart_name)
                results[chart_name] = False
                continue
            
            try:
                success = self._generate_chart(
                    chart_name,
                    chart_config,
                    frameworks_data,
                    aggregated_data,
                    timeline_data,
                    output_path
                )
                results[chart_name] = success
                
                if success:
                    logger.info("✓ Generated chart: %s", chart_name)
                else:
                    logger.warning("✗ Failed to generate chart: %s", chart_name)
                    
            except (ValueError, KeyError, TypeError, IOError) as e:
                logger.error("Error generating chart %s: %s", chart_name, e, exc_info=True)
                results[chart_name] = False
        
        # Summary
        total = len(results)
        succeeded = sum(1 for success in results.values() if success)
        logger.info("Chart generation complete: %d/%d succeeded", succeeded, total)
        
        return results
    
    def _generate_chart(
        self,
        chart_name: str,
        chart_config: Dict[str, Any],
        frameworks_data: Dict[str, List[Dict[str, Any]]],
        aggregated_data: Optional[Dict[str, Dict[str, float]]],
        timeline_data: Optional[Dict[str, Dict[int, Dict[str, float]]]],
        output_dir: Path,
    ) -> bool:
        """Generate a single chart based on configuration.
        
        Args:
            chart_name: Name of the chart (e.g., 'radar_chart')
            chart_config: Configuration dictionary for this chart
            frameworks_data: Raw run-level data
            aggregated_data: Pre-computed aggregate statistics
            timeline_data: Step-level metrics
            output_dir: Output directory path
            
        Returns:
            True if chart was generated successfully, False otherwise
        """
        # Get the visualization function
        chart_func = self.CHART_REGISTRY.get(chart_name)
        if chart_func is None:
            logger.error("Unknown chart type: %s", chart_name)
            return False
        
        # Prepare output filename
        filename = chart_config.get('filename', f'{chart_name}.png')
        if not filename.endswith(('.png', '.svg', '.pdf')):
            filename += '.svg'  # Default to SVG
        output_file = output_dir / filename
        
        # Prepare chart data based on chart type
        try:
            chart_data, kwargs = self._prepare_chart_data(
                chart_name,
                chart_config,
                frameworks_data,
                aggregated_data,
                timeline_data
            )
            
            if chart_data is None:
                logger.warning("Insufficient data for chart: %s", chart_name)
                return False
            
            # Generate the chart
            chart_func(chart_data, str(output_file), **kwargs)
            return True
            
        except (ValueError, KeyError, TypeError, IOError) as e:
            logger.error("Failed to prepare/generate chart %s: %s", chart_name, e)
            return False
    
    def _prepare_chart_data(
        self,
        chart_name: str,
        chart_config: Dict[str, Any],
        frameworks_data: Dict[str, List[Dict[str, Any]]],
        aggregated_data: Optional[Dict[str, Dict[str, float]]],
        timeline_data: Optional[Dict[str, Dict[int, Dict[str, float]]]],
    ) -> tuple[Optional[Dict], Dict[str, Any]]:
        """Prepare data and kwargs for a specific chart type.
        
        Args:
            chart_name: Name of the chart type
            chart_config: Configuration for this chart
            frameworks_data: Raw run-level data
            aggregated_data: Aggregate statistics
            timeline_data: Step-level metrics
            
        Returns:
            Tuple of (chart_data, kwargs) where:
                - chart_data: Data dict to pass to visualization function
                - kwargs: Additional keyword arguments (title, metrics, etc.)
            Returns (None, {}) if data is insufficient
        """
        kwargs = {}
        
        # Add title if specified
        if 'title' in chart_config:
            kwargs['title'] = chart_config['title']
        
        # Chart-specific data preparation
        if chart_name == 'radar_chart':
            return self._prepare_radar_chart(chart_config, aggregated_data, kwargs)
            
        elif chart_name == 'token_efficiency_scatter':
            return self._prepare_scatter_chart(chart_config, frameworks_data, kwargs)
            
        elif chart_name in ['api_calls_timeline', 'api_calls_evolution']:
            return self._prepare_timeline_chart(chart_config, timeline_data, kwargs)
            
        elif chart_name == 'cost_boxplot':
            return self._prepare_boxplot(chart_config, frameworks_data, kwargs)
            
        elif chart_name == 'api_efficiency_bar':
            return self._prepare_api_bar(chart_config, aggregated_data, kwargs)
            
        elif chart_name == 'cache_efficiency':
            return self._prepare_cache_chart(chart_config, aggregated_data, kwargs)
            
        elif chart_name == 'api_efficiency_chart':
            return self._prepare_api_efficiency(chart_config, aggregated_data, kwargs)
        
        else:
            logger.warning("No data preparation handler for chart type: %s", chart_name)
            return None, {}
    
    def _prepare_radar_chart(
        self,
        chart_config: Dict[str, Any],
        aggregated_data: Optional[Dict[str, Dict[str, float]]],
        kwargs: Dict[str, Any]
    ) -> tuple[Optional[Dict], Dict[str, Any]]:
        """Prepare data for radar chart."""
        if aggregated_data is None:
            return None, kwargs
        
        metrics = chart_config.get('metrics', [])
        if not metrics:
            logger.warning("No metrics specified for radar chart")
            return None, kwargs
        
        # Filter data to only include specified metrics
        chart_data = {
            fw: {m: data[m] for m in metrics if m in data}
            for fw, data in aggregated_data.items()
        }
        
        # Pass metrics list to function
        kwargs['metrics'] = metrics
        
        return chart_data, kwargs
    
    def _prepare_scatter_chart(
        self,
        _chart_config: Dict[str, Any],
        frameworks_data: Optional[Dict[str, List[Dict[str, Any]]]],
        kwargs: Dict[str, Any]
    ) -> tuple[Optional[Dict], Dict[str, Any]]:
        """Prepare data for scatter plot (uses run-level data)."""
        if frameworks_data is None:
            return None, kwargs
        
        # Scatter plots use raw run data, not aggregated
        x_metric = _chart_config.get('x_metric', 'TOK_IN')
        y_metric = _chart_config.get('y_metric', 'TOK_OUT')
        
        # Validate that frameworks have the required metrics
        valid_data = {}
        for fw, runs in frameworks_data.items():
            if any(x_metric in run and y_metric in run for run in runs):
                valid_data[fw] = runs
        
        if not valid_data:
            return None, kwargs
        
        return valid_data, kwargs
    
    def _prepare_timeline_chart(
        self,
        chart_config: Dict[str, Any],
        timeline_data: Optional[Dict[str, Dict[int, Dict[str, float]]]],
        kwargs: Dict[str, Any]
    ) -> tuple[Optional[Dict], Dict[str, Any]]:
        """Prepare data for timeline/evolution charts."""
        if timeline_data is None or not timeline_data:
            return None, kwargs
        
        metric = chart_config.get('metric', 'API_CALLS')
        
        # Filter timeline data to only include specified metric
        chart_data = {}
        for fw, steps in timeline_data.items():
            chart_data[fw] = {
                step_num: {metric: step_data.get(metric, 0)}
                for step_num, step_data in steps.items()
                if metric in step_data
            }
        
        if not chart_data:
            return None, kwargs
        
        return chart_data, kwargs
    
    def _prepare_boxplot(
        self,
        chart_config: Dict[str, Any],
        frameworks_data: Optional[Dict[str, List[Dict[str, Any]]]],
        kwargs: Dict[str, Any]
    ) -> tuple[Optional[Dict], Dict[str, Any]]:
        """Prepare data for box plot (uses run-level data for distribution).
        
        Raises:
            ValueError: If any framework is missing the required metric
        """
        if frameworks_data is None:
            return None, kwargs
        
        # Box plots use raw run data to show distributions
        metric = chart_config.get('metric', 'COST_USD')
        
        # Validate that ALL frameworks have the required metric
        missing_metric_frameworks = []
        valid_data = {}
        
        for fw, runs in frameworks_data.items():
            has_metric = any(metric in run for run in runs)
            if has_metric:
                valid_data[fw] = runs
            else:
                missing_metric_frameworks.append(fw)
        
        # Fail explicitly if any framework is missing the metric
        if missing_metric_frameworks:
            raise ValueError(
                f"Boxplot requires metric '{metric}' but missing in frameworks: "
                f"{missing_metric_frameworks}. Cannot generate partial chart."
            )
        
        if not valid_data:
            raise ValueError(f"No frameworks have data for metric '{metric}'")
        
        return valid_data, kwargs
    
    def _prepare_api_bar(
        self,
        _chart_config: Dict[str, Any],
        aggregated_data: Optional[Dict[str, Dict[str, float]]],
        kwargs: Dict[str, Any]
    ) -> tuple[Optional[Dict], Dict[str, Any]]:
        """Prepare data for API efficiency bar chart."""
        if aggregated_data is None:
            return None, kwargs
        
        # Filter to frameworks with API_CALLS and TOK_IN
        chart_data = {
            fw: {
                'API_CALLS': data.get('API_CALLS', 0),
                'TOK_IN': data.get('TOK_IN', 0)
            }
            for fw, data in aggregated_data.items()
            if 'API_CALLS' in data and 'TOK_IN' in data
        }
        
        if not chart_data:
            return None, kwargs
        
        return chart_data, kwargs
    
    def _prepare_cache_chart(
        self,
        _chart_config: Dict[str, Any],
        aggregated_data: Optional[Dict[str, Dict[str, float]]],
        kwargs: Dict[str, Any]
    ) -> tuple[Optional[Dict], Dict[str, Any]]:
        """Prepare data for cache efficiency chart."""
        if aggregated_data is None:
            return None, kwargs
        
        # Filter to frameworks with cache data
        chart_data = {
            fw: {
                'TOK_IN': data.get('TOK_IN', 0),
                'CACHED_TOKENS': data.get('CACHED_TOKENS', 0)
            }
            for fw, data in aggregated_data.items()
            if 'CACHED_TOKENS' in data
        }
        
        if not chart_data:
            return None, kwargs
        
        return chart_data, kwargs
    
    def _prepare_api_efficiency(
        self,
        _chart_config: Dict[str, Any],
        aggregated_data: Optional[Dict[str, Dict[str, float]]],
        kwargs: Dict[str, Any]
    ) -> tuple[Optional[Dict], Dict[str, Any]]:
        """Prepare data for API efficiency chart."""
        if aggregated_data is None:
            return None, kwargs
        
        # Filter to frameworks with API efficiency data
        chart_data = {
            fw: {
                'API_CALLS': data.get('API_CALLS', 0),
                'TOK_IN': data.get('TOK_IN', 0),
                'TOK_OUT': data.get('TOK_OUT', 0)
            }
            for fw, data in aggregated_data.items()
            if 'API_CALLS' in data
        }
        
        if not chart_data:
            return None, kwargs
        
        return chart_data, kwargs
    
    def list_available_charts(self) -> List[str]:
        """List all chart types registered in the factory.
        
        Returns:
            List of chart type names that can be used in config
        """
        return list(self.CHART_REGISTRY.keys())
    
    def validate_config(self) -> List[str]:
        """Validate visualization configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        for chart_name, chart_config in self.visualizations_config.items():
            # Check if chart type is supported
            if chart_name not in self.CHART_REGISTRY:
                errors.append(f"Unknown chart type '{chart_name}'")
                continue
            
            # Check for required fields based on chart type
            if chart_name == 'radar_chart':
                if 'metrics' not in chart_config:
                    errors.append(f"{chart_name}: missing required field 'metrics'")
                elif not isinstance(chart_config['metrics'], list):
                    errors.append(f"{chart_name}: 'metrics' must be a list")
                    
            elif chart_name == 'token_efficiency_scatter':
                if 'x_metric' not in chart_config:
                    errors.append(f"{chart_name}: missing required field 'x_metric'")
                if 'y_metric' not in chart_config:
                    errors.append(f"{chart_name}: missing required field 'y_metric'")
                    
            elif chart_name in ['api_calls_timeline', 'api_calls_evolution', 'cost_boxplot']:
                if 'metric' not in chart_config:
                    errors.append(f"{chart_name}: missing required field 'metric'")
            
            # Check filename format
            if 'filename' in chart_config:
                filename = chart_config['filename']
                if not isinstance(filename, str):
                    errors.append(f"{chart_name}: 'filename' must be a string")
        
        return errors
