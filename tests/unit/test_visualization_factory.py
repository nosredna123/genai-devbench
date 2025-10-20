"""Tests for VisualizationFactory - Config-Driven Chart Generation.

Test Categories:
1. Factory Initialization
2. Config Validation
3. Chart Registry
4. Chart Data Preparation
5. Chart Generation
6. Integration Tests
"""

import pytest
from pathlib import Path
import tempfile
import yaml
from unittest.mock import Mock, patch, MagicMock

from src.analysis.visualization_factory import VisualizationFactory


@pytest.fixture
def minimal_config():
    """Minimal valid config with visualizations section."""
    return {
        'visualizations': {
            'radar_chart': {
                'enabled': True,
                'title': 'Test Radar',
                'metrics': ['TOK_IN', 'TOK_OUT'],
                'filename': 'radar.svg'
            }
        }
    }


@pytest.fixture
def full_config():
    """Full config with all chart types."""
    return {
        'visualizations': {
            'radar_chart': {
                'enabled': True,
                'title': 'Framework Performance Profile',
                'metrics': ['TOK_IN', 'TOK_OUT', 'API_CALLS'],
                'scale': 'normalized',
                'filename': 'radar_framework_profile.png'
            },
            'token_efficiency_scatter': {
                'enabled': True,
                'title': 'Token Efficiency: Input vs Output',
                'x_metric': 'TOK_IN',
                'y_metric': 'TOK_OUT',
                'filename': 'scatter_token_efficiency.png'
            },
            'api_calls_timeline': {
                'enabled': True,
                'title': 'API Calls Timeline',
                'metric': 'API_CALLS',
                'x_axis': 'step_number',
                'aggregation': 'mean',
                'filename': 'timeline_api_calls.png'
            },
            'cost_boxplot': {
                'enabled': False,  # Disabled for testing
                'title': 'Cost Distribution',
                'metric': 'COST_USD',
                'filename': 'boxplot_cost.png'
            }
        }
    }


@pytest.fixture
def sample_frameworks_data():
    """Sample run-level data for multiple frameworks."""
    return {
        'baes': [
            {'TOK_IN': 100, 'TOK_OUT': 50, 'API_CALLS': 5, 'T_WALL_seconds': 10.0},
            {'TOK_IN': 110, 'TOK_OUT': 55, 'API_CALLS': 6, 'T_WALL_seconds': 11.0},
        ],
        'chatdev': [
            {'TOK_IN': 200, 'TOK_OUT': 100, 'API_CALLS': 10, 'T_WALL_seconds': 20.0},
            {'TOK_IN': 210, 'TOK_OUT': 105, 'API_CALLS': 11, 'T_WALL_seconds': 21.0},
        ]
    }


@pytest.fixture
def sample_aggregated_data():
    """Sample aggregated statistics."""
    return {
        'baes': {
            'TOK_IN': 105.0,
            'TOK_OUT': 52.5,
            'API_CALLS': 5.5,
            'T_WALL_seconds': 10.5,
            'CACHED_TOKENS': 10.0
        },
        'chatdev': {
            'TOK_IN': 205.0,
            'TOK_OUT': 102.5,
            'API_CALLS': 10.5,
            'T_WALL_seconds': 20.5,
            'CACHED_TOKENS': 20.0
        }
    }


@pytest.fixture
def sample_timeline_data():
    """Sample step-level timeline data."""
    return {
        'baes': {
            1: {'API_CALLS': 2, 'TOK_IN': 50},
            2: {'API_CALLS': 3, 'TOK_IN': 55}
        },
        'chatdev': {
            1: {'API_CALLS': 5, 'TOK_IN': 100},
            2: {'API_CALLS': 5, 'TOK_IN': 105}
        }
    }


# =============================================================================
# 1. FACTORY INITIALIZATION TESTS
# =============================================================================

class TestFactoryInitialization:
    """Test VisualizationFactory initialization."""
    
    def test_init_with_valid_config(self, minimal_config):
        """Factory should initialize with valid config."""
        factory = VisualizationFactory(minimal_config)
        assert factory.config == minimal_config
        assert factory.visualizations_config == minimal_config['visualizations']
    
    def test_init_missing_visualizations_section(self):
        """Factory should raise ValueError if config missing visualizations."""
        config = {'other_section': {}}
        
        with pytest.raises(ValueError, match="missing 'visualizations' section"):
            VisualizationFactory(config)
    
    def test_init_empty_visualizations(self):
        """Factory should accept empty visualizations section."""
        config = {'visualizations': {}}
        factory = VisualizationFactory(config)
        assert factory.visualizations_config == {}


# =============================================================================
# 2. CONFIG VALIDATION TESTS
# =============================================================================

class TestConfigValidation:
    """Test configuration validation."""
    
    def test_validate_valid_config(self, full_config):
        """Valid config should return no errors."""
        factory = VisualizationFactory(full_config)
        errors = factory.validate_config()
        assert errors == []
    
    def test_validate_unknown_chart_type(self, minimal_config):
        """Unknown chart type should return error."""
        minimal_config['visualizations']['unknown_chart'] = {'enabled': True}
        factory = VisualizationFactory(minimal_config)
        
        errors = factory.validate_config()
        assert len(errors) == 1
        assert "Unknown chart type 'unknown_chart'" in errors[0]
    
    def test_validate_radar_chart_missing_metrics(self, minimal_config):
        """Radar chart without metrics should return error."""
        del minimal_config['visualizations']['radar_chart']['metrics']
        factory = VisualizationFactory(minimal_config)
        
        errors = factory.validate_config()
        assert len(errors) == 1
        assert "missing required field 'metrics'" in errors[0]
    
    def test_validate_radar_chart_invalid_metrics_type(self, minimal_config):
        """Radar chart with non-list metrics should return error."""
        minimal_config['visualizations']['radar_chart']['metrics'] = 'not_a_list'
        factory = VisualizationFactory(minimal_config)
        
        errors = factory.validate_config()
        assert len(errors) == 1
        assert "'metrics' must be a list" in errors[0]
    
    def test_validate_scatter_missing_metrics(self, full_config):
        """Scatter chart without x_metric/y_metric should return errors."""
        del full_config['visualizations']['token_efficiency_scatter']['x_metric']
        del full_config['visualizations']['token_efficiency_scatter']['y_metric']
        factory = VisualizationFactory(full_config)
        
        errors = factory.validate_config()
        assert len(errors) == 2
        assert any("missing required field 'x_metric'" in e for e in errors)
        assert any("missing required field 'y_metric'" in e for e in errors)
    
    def test_validate_timeline_missing_metric(self, full_config):
        """Timeline chart without metric should return error."""
        del full_config['visualizations']['api_calls_timeline']['metric']
        factory = VisualizationFactory(full_config)
        
        errors = factory.validate_config()
        assert len(errors) == 1
        assert "missing required field 'metric'" in errors[0]
    
    def test_validate_invalid_filename_type(self, minimal_config):
        """Non-string filename should return error."""
        minimal_config['visualizations']['radar_chart']['filename'] = 123
        factory = VisualizationFactory(minimal_config)
        
        errors = factory.validate_config()
        assert len(errors) == 1
        assert "'filename' must be a string" in errors[0]


# =============================================================================
# 3. CHART REGISTRY TESTS
# =============================================================================

class TestChartRegistry:
    """Test chart registry functionality."""
    
    def test_list_available_charts(self, minimal_config):
        """Should list all registered chart types."""
        factory = VisualizationFactory(minimal_config)
        charts = factory.list_available_charts()
        
        assert isinstance(charts, list)
        assert 'radar_chart' in charts
        assert 'token_efficiency_scatter' in charts
        assert 'api_calls_timeline' in charts
        assert len(charts) > 0
    
    def test_chart_registry_has_functions(self, minimal_config):
        """Registry should map to actual functions."""
        factory = VisualizationFactory(minimal_config)
        
        for chart_name in factory.list_available_charts():
            chart_func = factory.CHART_REGISTRY[chart_name]
            assert callable(chart_func)


# =============================================================================
# 4. CHART DATA PREPARATION TESTS
# =============================================================================

class TestChartDataPreparation:
    """Test data preparation for different chart types."""
    
    def test_prepare_radar_chart_data(
        self, minimal_config, sample_aggregated_data
    ):
        """Radar chart should filter data by configured metrics."""
        factory = VisualizationFactory(minimal_config)
        
        chart_data, kwargs = factory._prepare_radar_chart(
            minimal_config['visualizations']['radar_chart'],
            sample_aggregated_data,
            {}
        )
        
        # Should only include TOK_IN and TOK_OUT
        assert chart_data is not None
        assert 'baes' in chart_data
        assert 'TOK_IN' in chart_data['baes']
        assert 'TOK_OUT' in chart_data['baes']
        assert 'API_CALLS' not in chart_data['baes']  # Not in config metrics
        assert kwargs['metrics'] == ['TOK_IN', 'TOK_OUT']
    
    def test_prepare_radar_no_aggregated_data(self, minimal_config):
        """Radar chart with no data should return None."""
        factory = VisualizationFactory(minimal_config)
        
        chart_data, kwargs = factory._prepare_radar_chart(
            minimal_config['visualizations']['radar_chart'],
            None,
            {}
        )
        
        assert chart_data is None
    
    def test_prepare_scatter_chart_data(
        self, full_config, sample_frameworks_data
    ):
        """Scatter chart should use run-level data."""
        factory = VisualizationFactory(full_config)
        scatter_config = full_config['visualizations']['token_efficiency_scatter']
        
        chart_data, kwargs = factory._prepare_scatter_chart(
            scatter_config,
            sample_frameworks_data,
            {}
        )
        
        assert chart_data is not None
        assert 'baes' in chart_data
        assert isinstance(chart_data['baes'], list)
        assert len(chart_data['baes']) == 2
    
    def test_prepare_timeline_chart_data(
        self, full_config, sample_timeline_data
    ):
        """Timeline chart should filter by configured metric."""
        factory = VisualizationFactory(full_config)
        timeline_config = full_config['visualizations']['api_calls_timeline']
        
        chart_data, kwargs = factory._prepare_timeline_chart(
            timeline_config,
            sample_timeline_data,
            {}
        )
        
        assert chart_data is not None
        assert 'baes' in chart_data
        assert 1 in chart_data['baes']
        assert 'API_CALLS' in chart_data['baes'][1]
    
    def test_prepare_boxplot_data(
        self, full_config, sample_frameworks_data
    ):
        """Box plot should raise ValueError when metric is missing."""
        factory = VisualizationFactory(full_config)
        boxplot_config = full_config['visualizations']['cost_boxplot']
        
        # Sample data doesn't have COST_USD, so should raise ValueError
        with pytest.raises(ValueError, match="Boxplot requires metric 'COST_USD' but missing in frameworks"):
            factory._prepare_boxplot(
                boxplot_config,
                sample_frameworks_data,
                {}
            )


# =============================================================================
# 5. CHART GENERATION TESTS
# =============================================================================

class TestChartGeneration:
    """Test chart generation process."""
    
    def test_generate_enabled_chart(
        self, minimal_config, sample_aggregated_data
    ):
        """Enabled chart should be generated."""
        # Patch where it's used, not where it's defined
        with patch.object(VisualizationFactory, '_generate_chart', return_value=True):
            factory = VisualizationFactory(minimal_config)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                results = factory.generate_all(
                    frameworks_data={},
                    aggregated_data=sample_aggregated_data,
                    output_dir=tmpdir
                )
                
                assert 'radar_chart' in results
                assert results['radar_chart'] is True
    
    def test_skip_disabled_chart(self, full_config):
        """Disabled chart should not be generated."""
        factory = VisualizationFactory(full_config)
        
        with tempfile.TemporaryDirectory() as tmpdir:
            results = factory.generate_all(
                frameworks_data={},
                aggregated_data={},
                output_dir=tmpdir
            )
            
            # cost_boxplot is disabled in full_config
            assert 'cost_boxplot' in results
            assert results['cost_boxplot'] is False
    
    def test_generate_creates_output_dir(
        self, minimal_config, sample_aggregated_data
    ):
        """generate_all should create output directory."""
        with patch.object(VisualizationFactory, '_generate_chart', return_value=True):
            factory = VisualizationFactory(minimal_config)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                output_path = Path(tmpdir) / 'subdir' / 'output'
                results = factory.generate_all(
                    frameworks_data={},
                    aggregated_data=sample_aggregated_data,
                    output_dir=str(output_path)
                )
                
                assert output_path.exists()
                assert output_path.is_dir()
    
    def test_generate_handles_extension(
        self, minimal_config, sample_aggregated_data
    ):
        """Chart generation should add .svg if no extension provided."""
        # Remove extension from filename
        minimal_config['visualizations']['radar_chart']['filename'] = 'radar'
        
        mock_func = Mock()
        with patch.dict(VisualizationFactory.CHART_REGISTRY, {'radar_chart': mock_func}):
            factory = VisualizationFactory(minimal_config)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                factory.generate_all(
                    frameworks_data={},
                    aggregated_data=sample_aggregated_data,
                    output_dir=tmpdir
                )
                
                # Check that function was called with .svg extension
                assert mock_func.called
                call_args = mock_func.call_args
                filepath = call_args[0][1]
                assert filepath.endswith('.svg')
    
    def test_generate_handles_chart_errors(
        self, minimal_config, sample_aggregated_data
    ):
        """Errors in chart generation should be caught and logged."""
        mock_func = Mock(side_effect=ValueError("Test error"))
        with patch.dict(VisualizationFactory.CHART_REGISTRY, {'radar_chart': mock_func}):
            factory = VisualizationFactory(minimal_config)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                results = factory.generate_all(
                    frameworks_data={},
                    aggregated_data=sample_aggregated_data,
                    output_dir=tmpdir
                )
                
                # Should fail gracefully
                assert 'radar_chart' in results
                assert results['radar_chart'] is False


# =============================================================================
# 6. INTEGRATION TESTS
# =============================================================================

class TestIntegration:
    """Integration tests with realistic scenarios."""
    
    def test_generate_multiple_charts(
        self, full_config,
        sample_frameworks_data, sample_aggregated_data
    ):
        """Should generate all enabled charts."""
        mock_radar = Mock()
        mock_token = Mock()
        mock_timeline = Mock()
        
        with patch.dict(VisualizationFactory.CHART_REGISTRY, {
            'radar_chart': mock_radar,
            'token_efficiency_scatter': mock_token,
            'api_calls_timeline': mock_timeline
        }):
            factory = VisualizationFactory(full_config)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                results = factory.generate_all(
                    frameworks_data=sample_frameworks_data,
                    aggregated_data=sample_aggregated_data,
                    timeline_data={},
                    output_dir=tmpdir
                )
                
                # Enabled charts
                assert results['radar_chart'] is True
                assert results['token_efficiency_scatter'] is True
                
                # Disabled chart
                assert results['cost_boxplot'] is False
                
                # Both functions called
                assert mock_radar.called
                assert mock_token.called
    
    def test_end_to_end_with_real_data(
        self, full_config, sample_frameworks_data,
        sample_aggregated_data, sample_timeline_data
    ):
        """End-to-end test with mocked visualization functions."""
        mock_radar = Mock()
        mock_token = Mock()
        mock_timeline = Mock()
        
        with patch.dict(VisualizationFactory.CHART_REGISTRY, {
            'radar_chart': mock_radar,
            'token_efficiency_scatter': mock_token,
            'api_calls_timeline': mock_timeline
        }):
            factory = VisualizationFactory(full_config)
            
            with tempfile.TemporaryDirectory() as tmpdir:
                results = factory.generate_all(
                    frameworks_data=sample_frameworks_data,
                    aggregated_data=sample_aggregated_data,
                    timeline_data=sample_timeline_data,
                    output_dir=tmpdir
                )
                
                # Check results
                succeeded = sum(1 for v in results.values() if v)
                assert succeeded >= 2  # At least 2 charts succeeded
                
                # Verify function calls with correct data structures
                if mock_radar.called:
                    call_args = mock_radar.call_args
                    data = call_args[0][0]
                    assert isinstance(data, dict)
                    assert 'baes' in data or 'chatdev' in data
