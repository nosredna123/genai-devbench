"""
Unit tests for MetricsConfig class.

Tests the centralized metrics configuration loader to ensure it correctly
parses experiment.yaml and provides consistent metric definitions.
"""

import pytest
from pathlib import Path
from src.utils.metrics_config import (
    MetricDefinition,
    MetricsConfig,
    get_metrics_config,
    reset_metrics_config
)


@pytest.fixture
def config_path():
    """Path to experiment.yaml configuration file."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "config" / "experiment.yaml"


@pytest.fixture
def metrics_config(config_path):
    """Create a MetricsConfig instance for testing."""
    reset_metrics_config()  # Reset singleton
    return MetricsConfig(config_path)


class TestMetricDefinition:
    """Tests for MetricDefinition dataclass."""
    
    def test_format_value_numeric(self):
        """Test formatting numeric values."""
        metric = MetricDefinition(
            key='TOK_IN',
            name='Input Tokens',
            description='Test',
            unit='tokens',
            category='efficiency',
            ideal_direction='minimize',
            data_source='test',
            aggregation='sum',
            display_format='{:,.0f}',
            statistical_test=True,
            stopping_rule_eligible=True
        )
        assert metric.format_value(1234567) == '1,234,567'
    
    def test_format_value_currency(self):
        """Test formatting currency values."""
        metric = MetricDefinition(
            key='COST_USD',
            name='Cost',
            description='Test',
            unit='USD',
            category='cost',
            ideal_direction='minimize',
            data_source='calculated',
            aggregation='calculated',
            display_format='${:.4f}',
            statistical_test=True,
            stopping_rule_eligible=True
        )
        assert metric.format_value(0.1234) == '$0.1234'
    
    def test_format_value_none(self):
        """Test formatting None values."""
        metric = MetricDefinition(
            key='TEST',
            name='Test',
            description='Test',
            unit='',
            category='test',
            ideal_direction='minimize',
            data_source='test',
            aggregation='sum',
            display_format='{:.2f}',
            statistical_test=False,
            stopping_rule_eligible=False
        )
        assert metric.format_value(None) == 'N/A'
    
    def test_should_invert_for_normalization_minimize(self):
        """Test inversion flag for minimize metrics."""
        metric = MetricDefinition(
            key='TOK_IN',
            name='Input Tokens',
            description='Test',
            unit='tokens',
            category='efficiency',
            ideal_direction='minimize',
            data_source='test',
            aggregation='sum',
            display_format='{:,.0f}',
            statistical_test=True,
            stopping_rule_eligible=True
        )
        assert metric.should_invert_for_normalization() is True
    
    def test_should_invert_for_normalization_maximize(self):
        """Test inversion flag for maximize metrics."""
        metric = MetricDefinition(
            key='CACHED_TOKENS',
            name='Cached Tokens',
            description='Test',
            unit='tokens',
            category='efficiency',
            ideal_direction='maximize',
            data_source='test',
            aggregation='sum',
            display_format='{:,.0f}',
            statistical_test=True,
            stopping_rule_eligible=False
        )
        assert metric.should_invert_for_normalization() is False


class TestMetricsConfig:
    """Tests for MetricsConfig class."""
    
    def test_metrics_config_loads(self, metrics_config):
        """Test that config loads successfully."""
        assert metrics_config is not None
        assert len(metrics_config._config) > 0
    
    def test_reliable_metrics_structure(self, metrics_config):
        """Test that all reliable metrics have required fields."""
        reliable = metrics_config.get_reliable_metrics()
        
        # Should have 7 reliable metrics
        assert len(reliable) == 7
        
        # Check that TOK_IN is present
        assert 'TOK_IN' in reliable
        
        # Verify structure of a reliable metric
        tok_in = reliable['TOK_IN']
        assert tok_in.key == 'TOK_IN'
        assert tok_in.name == 'Input Tokens'
        assert tok_in.unit == 'tokens'
        assert tok_in.category == 'efficiency'
        assert tok_in.ideal_direction == 'minimize'
        assert tok_in.data_source == 'openai_usage_api'
        assert tok_in.statistical_test is True
    
    def test_derived_metrics_structure(self, metrics_config):
        """Test that derived metrics are properly loaded."""
        derived = metrics_config.get_derived_metrics()
        
        # Should have 1 derived metric (COST_USD)
        assert len(derived) == 1
        assert 'COST_USD' in derived
        
        cost = derived['COST_USD']
        assert cost.key == 'COST_USD'
        assert cost.name == 'Total Cost'
        assert cost.unit == 'USD'
        assert cost.category == 'cost'
        assert cost.data_source == 'calculated'
        assert cost.calculation is not None
    
    def test_get_all_metrics(self, metrics_config):
        """Test getting all metrics (reliable + derived)."""
        all_metrics = metrics_config.get_all_metrics()
        
        # Should have 8 metrics total (7 reliable + 1 derived)
        assert len(all_metrics) == 8
        
        # Check for key metrics
        assert 'TOK_IN' in all_metrics
        assert 'TOK_OUT' in all_metrics
        assert 'API_CALLS' in all_metrics
        assert 'COST_USD' in all_metrics
    
    def test_get_metric(self, metrics_config):
        """Test retrieving a specific metric."""
        tok_in = metrics_config.get_metric('TOK_IN')
        assert tok_in is not None
        assert tok_in.key == 'TOK_IN'
        
        # Non-existent metric
        fake = metrics_config.get_metric('FAKE_METRIC')
        assert fake is None
    
    def test_get_metrics_for_statistics(self, metrics_config):
        """Test filtering metrics by statistical_test flag."""
        stats_metrics = metrics_config.get_metrics_for_statistics()
        
        # All 8 metrics should be eligible for statistical testing
        assert len(stats_metrics) == 8
        assert 'TOK_IN' in stats_metrics
        assert 'COST_USD' in stats_metrics
    
    def test_get_metrics_for_stopping_rule(self, metrics_config):
        """Test filtering metrics by stopping_rule_eligible flag."""
        stopping_metrics = metrics_config.get_metrics_for_stopping_rule()
        
        # Should have metrics marked as stopping_rule_eligible
        # TOK_IN, TOK_OUT, API_CALLS, T_WALL_seconds, COST_USD = 5 metrics
        assert len(stopping_metrics) >= 4
        assert 'TOK_IN' in stopping_metrics
        assert 'COST_USD' in stopping_metrics
    
    def test_metrics_by_category(self, metrics_config):
        """Test filtering metrics by category."""
        efficiency_metrics = metrics_config.get_metrics_by_category('efficiency')
        
        # Should have efficiency metrics (TOK_IN, TOK_OUT, API_CALLS, etc.)
        assert len(efficiency_metrics) >= 5
        assert 'TOK_IN' in efficiency_metrics
        assert 'TOK_OUT' in efficiency_metrics
        
        cost_metrics = metrics_config.get_metrics_by_category('cost')
        assert len(cost_metrics) == 1
        assert 'COST_USD' in cost_metrics
    
    def test_metric_formatting(self, metrics_config):
        """Test value formatting according to display_format."""
        # Test TOK_IN formatting (integer with thousands separator)
        formatted = metrics_config.format_value('TOK_IN', 1234567)
        assert formatted == '1,234,567'
        
        # Test COST_USD formatting (currency with 4 decimals)
        formatted = metrics_config.format_value('COST_USD', 0.1234)
        assert formatted == '$0.1234'
        
        # Test T_WALL_seconds formatting (1 decimal)
        formatted = metrics_config.format_value('T_WALL_seconds', 123.456)
        assert formatted == '123.5'
    
    def test_excluded_metrics(self, metrics_config):
        """Test retrieving excluded metrics with reasons."""
        excluded = metrics_config.get_excluded_metrics()
        
        # Should have 8 excluded metrics
        assert len(excluded) == 8
        
        # Check AUTR exclusion
        assert 'AUTR' in excluded
        assert 'reason' in excluded['AUTR']
        assert 'Hardcoded' in excluded['AUTR']['reason']
        
        # Check quality metrics exclusion
        assert 'Q_star' in excluded
        assert 'ESR' in excluded
        assert 'CRUDe' in excluded
        assert 'MC' in excluded
    
    def test_visualization_config(self, metrics_config):
        """Test retrieving visualization configurations."""
        radar = metrics_config.get_visualization_config('radar_chart')
        
        assert radar is not None
        assert radar['enabled'] is True
        assert 'metrics' in radar
        assert 'TOK_IN' in radar['metrics']
        assert 'COST_USD' in radar['metrics']
    
    def test_all_visualizations(self, metrics_config):
        """Test retrieving all visualization configs."""
        viz = metrics_config.get_all_visualizations()
        
        assert len(viz) >= 5
        assert 'radar_chart' in viz
        assert 'token_efficiency_scatter' in viz
        assert 'api_calls_timeline' in viz
        assert 'cost_boxplot' in viz
    
    def test_pricing_config(self, metrics_config):
        """Test retrieving pricing configuration."""
        gpt4o_mini = metrics_config.get_pricing_config('gpt-4o-mini')
        
        assert gpt4o_mini is not None
        assert 'input_price' in gpt4o_mini
        assert 'cached_price' in gpt4o_mini
        assert 'output_price' in gpt4o_mini
        assert gpt4o_mini['input_price'] == 0.150
        assert gpt4o_mini['cached_price'] == 0.075
        assert gpt4o_mini['output_price'] == 0.600
    
    def test_report_config(self, metrics_config):
        """Test retrieving report configuration."""
        report = metrics_config.get_report_config()
        
        assert report is not None
        assert 'title' in report
        assert 'sections' in report
        assert len(report['sections']) >= 5
    
    def test_validate_metrics_data_valid(self, metrics_config):
        """Test validation with complete valid data."""
        data = {
            'TOK_IN': 1000,
            'TOK_OUT': 500,
            'API_CALLS': 10,
            'CACHED_TOKENS': 200,
            'T_WALL_seconds': 60.5,
            'ZDI': 5.2,
            'UTT': 6,
            'COST_USD': 0.05
        }
        errors = metrics_config.validate_metrics_data(data)
        assert len(errors) == 0
    
    def test_validate_metrics_data_missing(self, metrics_config):
        """Test validation with missing metrics."""
        data = {
            'TOK_IN': 1000,
            'TOK_OUT': 500
        }
        errors = metrics_config.validate_metrics_data(data)
        assert len(errors) > 0
        assert any('Missing metrics' in err for err in errors)
    
    def test_validate_metrics_data_unexpected(self, metrics_config):
        """Test validation with unexpected metrics."""
        data = {
            'TOK_IN': 1000,
            'TOK_OUT': 500,
            'API_CALLS': 10,
            'CACHED_TOKENS': 200,
            'T_WALL_seconds': 60.5,
            'ZDI': 5.2,
            'UTT': 6,
            'COST_USD': 0.05,
            'FAKE_METRIC': 999  # Unexpected
        }
        errors = metrics_config.validate_metrics_data(data)
        assert len(errors) > 0
        assert any('Unexpected metrics' in err for err in errors)
    
    def test_validate_metrics_data_wrong_type(self, metrics_config):
        """Test validation with wrong data types."""
        data = {
            'TOK_IN': 'not a number',  # Wrong type
            'TOK_OUT': 500,
            'API_CALLS': 10,
            'CACHED_TOKENS': 200,
            'T_WALL_seconds': 60.5,
            'ZDI': 5.2,
            'UTT': 6,
            'COST_USD': 0.05
        }
        errors = metrics_config.validate_metrics_data(data)
        assert len(errors) > 0
        assert any('non-numeric' in err for err in errors)
    
    def test_singleton_pattern(self, config_path):
        """Test that get_metrics_config returns the same instance."""
        reset_metrics_config()
        
        instance1 = get_metrics_config(config_path)
        instance2 = get_metrics_config()
        
        assert instance1 is instance2
    
    def test_categories(self, metrics_config):
        """Test retrieving metric categories."""
        categories = metrics_config.get_categories()
        
        assert len(categories) >= 3
        
        # Check category structure
        category_names = [cat['name'] for cat in categories]
        assert 'efficiency' in category_names
        assert 'interaction' in category_names
        assert 'cost' in category_names


class TestMetricsConfigEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_config_file_not_found(self):
        """Test handling of missing config file."""
        reset_metrics_config()
        fake_path = Path('/nonexistent/config.yaml')
        
        with pytest.raises(FileNotFoundError):
            MetricsConfig(fake_path)
    
    def test_format_value_nonexistent_metric(self, metrics_config):
        """Test formatting value for nonexistent metric."""
        result = metrics_config.format_value('NONEXISTENT', 123)
        assert result == '123'
    
    def test_get_pricing_nonexistent_model(self, metrics_config):
        """Test getting pricing for nonexistent model."""
        pricing = metrics_config.get_pricing_config('nonexistent-model')
        assert pricing is None
    
    def test_get_visualization_nonexistent(self, metrics_config):
        """Test getting nonexistent visualization config."""
        viz = metrics_config.get_visualization_config('nonexistent_viz')
        assert viz is None
