"""
Unit tests for metric discovery functionality (Feature 009).

Tests the _discover_metrics_with_data() function and MetricsDiscoveryResult.
Validates partitioning of metrics and unknown metric detection.
"""

import pytest
import json
import yaml
import tempfile
from pathlib import Path
from src.utils.exceptions import MetricsValidationError
from src.utils.metrics_config import MetricsConfig


# Import discovery function and result dataclass
from src.analysis.report_generator import _discover_metrics_with_data
from src.analysis.types import MetricsDiscoveryResult


@pytest.fixture
def sample_run_data(tmp_path):
    """Create sample run data files for testing discovery."""
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    
    run1_dir = runs_dir / "run_1"
    run1_dir.mkdir()
    
    # Create run 1 with TOK_IN, TOK_OUT, T_WALL_seconds
    run1 = {
        'aggregate_metrics': {
            'TOK_IN': 1000,
            'TOK_OUT': 500,
            'T_WALL_seconds': 120.5
        }
    }
    with open(run1_dir / "metrics.json", 'w') as f:
        json.dump(run1, f)
    
    run2_dir = runs_dir / "run_2"
    run2_dir.mkdir()
    
    # Create run 2 with same metrics
    run2 = {
        'aggregate_metrics': {
            'TOK_IN': 1500,
            'TOK_OUT': 750,
            'T_WALL_seconds': 180.3
        }
    }
    with open(run2_dir / "metrics.json", 'w') as f:
        json.dump(run2, f)
    
    return runs_dir


@pytest.fixture
def sample_metrics_config(tmp_path):
    """Create sample metrics config file and return MetricsConfig instance."""
    config_file = tmp_path / "experiment.yaml"
    
    config = {
        'framework': 'chatdev',
        'model': 'gpt-4',
        'metrics': {
            'TOK_IN': {
                'name': 'Input Tokens',
                'key': 'TOK_IN',
                'description': 'Input tokens',
                'unit': 'tokens',
                'category': 'tokens',
                'ideal_direction': 'minimize',
                'data_source': 'openai',
                'aggregation': 'sum',
                'display_format': '{:,.0f}',
                'statistical_test': True,
                'stopping_rule_eligible': True
            },
            'TOK_OUT': {
                'name': 'Output Tokens',
                'key': 'TOK_OUT',
                'description': 'Output tokens',
                'unit': 'tokens',
                'category': 'tokens',
                'ideal_direction': 'minimize',
                'data_source': 'openai',
                'aggregation': 'sum',
                'display_format': '{:,.0f}',
                'statistical_test': True,
                'stopping_rule_eligible': True
            },
            'T_WALL_seconds': {
                'name': 'Wall Time',
                'key': 'T_WALL_seconds',
                'description': 'Wall time',
                'unit': 'seconds',
                'category': 'performance',
                'ideal_direction': 'minimize',
                'data_source': 'measured',
                'aggregation': 'sum',
                'display_format': '{:.1f}',
                'statistical_test': True,
                'stopping_rule_eligible': True
            },
            'COST_USD': {
                'name': 'Cost',
                'key': 'COST_USD',
                'description': 'Total cost',
                'unit': '$',
                'category': 'cost',
                'ideal_direction': 'minimize',
                'data_source': 'calculated',
                'aggregation': 'sum',
                'display_format': '${:.4f}',
                'statistical_test': True,
                'stopping_rule_eligible': False,
                'status': 'derived',
                'reason': 'Calculated from token counts'
            },
            'AUTR': {
                'name': 'Automation Rate',
                'key': 'AUTR',
                'description': 'Automation percentage',
                'unit': '%',
                'category': 'quality',
                'ideal_direction': 'maximize',
                'data_source': 'manual',
                'aggregation': 'mean',
                'display_format': '{:.1f}%',
                'statistical_test': False,
                'stopping_rule_eligible': False,
                'status': 'unmeasured',
                'reason': 'Not yet implemented'
            }
        }
    }
    
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
    
    return MetricsConfig(str(config_file))


class TestMetricsDiscoveryResult:
    """Test MetricsDiscoveryResult dataclass."""
    
    def test_create_discovery_result(self):
        """Test creating MetricsDiscoveryResult instance."""
        result = MetricsDiscoveryResult(
            metrics_with_data={'TOK_IN', 'TOK_OUT'},
            metrics_without_data={'AUTR', 'MC'},
            unknown_metrics=set(),
            run_count=5
        )
        
        assert result.metrics_with_data == {'TOK_IN', 'TOK_OUT'}
        assert result.metrics_without_data == {'AUTR', 'MC'}
        assert result.unknown_metrics == set()
        assert result.run_count == 5
    
    def test_discovery_result_with_unknown_metrics(self):
        """Test MetricsDiscoveryResult with unknown metrics."""
        result = MetricsDiscoveryResult(
            metrics_with_data={'TOK_IN'},
            metrics_without_data={'AUTR'},
            unknown_metrics={'UNKNOWN_METRIC'},
            run_count=3
        )
        
        assert result.unknown_metrics == {'UNKNOWN_METRIC'}


class TestDiscoverMetricsWithData:
    """Test _discover_metrics_with_data() function."""
    
    def test_discover_metrics_basic(self, sample_run_data, sample_metrics_config):
        """Test basic metric discovery from run data."""
        run_files = list(sample_run_data.glob("*/metrics.json"))
        
        result = _discover_metrics_with_data(run_files, sample_metrics_config)
        
        assert isinstance(result, MetricsDiscoveryResult)
        assert result.run_count == 2
        
        # TOK_IN, TOK_OUT, T_WALL_seconds should have data
        assert 'TOK_IN' in result.metrics_with_data
        assert 'TOK_OUT' in result.metrics_with_data
        assert 'T_WALL_seconds' in result.metrics_with_data
        
        # COST_USD (derived) and AUTR (unmeasured) should be without data
        assert 'COST_USD' in result.metrics_without_data
        assert 'AUTR' in result.metrics_without_data
        
        # No unknown metrics
        assert len(result.unknown_metrics) == 0
    
    def test_discover_with_unknown_metrics(self, tmp_path):
        """Test discovery raises error when unknown metrics found."""
        # Create config
        config_file = tmp_path / "experiment.yaml"
        config = {
            'framework': 'chatdev',
            'model': 'gpt-4',
            'metrics': {
                'TOK_IN': {
                    'name': 'Input Tokens',
                    'key': 'TOK_IN',
                    'description': 'Tokens',
                    'unit': 'tokens',
                    'category': 'tokens',
                    'ideal_direction': 'minimize',
                    'data_source': 'openai',
                    'aggregation': 'sum',
                    'display_format': '{:,.0f}',
                    'statistical_test': True,
                    'stopping_rule_eligible': True
                }
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        metrics_config = MetricsConfig(str(config_file))
        
        # Create run with unknown metric
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        run_dir = runs_dir / "run_1"
        run_dir.mkdir()
        
        run_data = {
            'aggregate_metrics': {
                'TOK_IN': 1000,
                'UNKNOWN_METRIC': 42
            }
        }
        with open(run_dir / "metrics.json", 'w') as f:
            json.dump(run_data, f)
        
        run_files = list(runs_dir.glob("*/metrics.json"))
        
        # Should raise MetricsValidationError
        with pytest.raises(MetricsValidationError) as exc_info:
            _discover_metrics_with_data(run_files, metrics_config)
        
        error_msg = str(exc_info.value)
        assert 'UNKNOWN_METRIC' in error_msg
    
    def test_discover_empty_runs_directory(self, sample_metrics_config):
        """Test discovery with no run files."""
        run_files = []
        
        result = _discover_metrics_with_data(run_files, sample_metrics_config)
        
        assert result.run_count == 0
        assert len(result.metrics_with_data) == 0
    
    def test_discover_partial_metrics_across_runs(self, tmp_path, sample_metrics_config):
        """Test discovery when different runs have different metrics."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        
        # Run 1 has TOK_IN, TOK_OUT
        run1_dir = runs_dir / "run_1"
        run1_dir.mkdir()
        run1 = {
            'aggregate_metrics': {
                'TOK_IN': 1000,
                'TOK_OUT': 500
            }
        }
        with open(run1_dir / "metrics.json", 'w') as f:
            json.dump(run1, f)
        
        # Run 2 has TOK_IN, T_WALL_seconds
        run2_dir = runs_dir / "run_2"
        run2_dir.mkdir()
        run2 = {
            'aggregate_metrics': {
                'TOK_IN': 1500,
                'T_WALL_seconds': 120.5
            }
        }
        with open(run2_dir / "metrics.json", 'w') as f:
            json.dump(run2, f)
        
        run_files = list(runs_dir.glob("*/metrics.json"))
        
        result = _discover_metrics_with_data(run_files, sample_metrics_config)
        
        # All three metrics should be in metrics_with_data
        assert 'TOK_IN' in result.metrics_with_data
        assert 'TOK_OUT' in result.metrics_with_data
        assert 'T_WALL_seconds' in result.metrics_with_data


class TestUnknownMetricValidation:
    """Test validation and error reporting for unknown metrics."""
    
    def test_unknown_metric_error_message_helpful(self, tmp_path):
        """Test that unknown metric error provides helpful guidance."""
        # Create minimal config
        config_file = tmp_path / "experiment.yaml"
        config = {
            'framework': 'chatdev',
            'model': 'gpt-4',
            'metrics': {
                'TOK_IN': {
                    'name': 'Input Tokens',
                    'key': 'TOK_IN',
                    'description': 'Tokens',
                    'unit': 'tokens',
                    'category': 'tokens',
                    'ideal_direction': 'minimize',
                    'data_source': 'openai',
                    'aggregation': 'sum',
                    'display_format': '{:,.0f}',
                    'statistical_test': True,
                    'stopping_rule_eligible': True
                }
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        metrics_config = MetricsConfig(str(config_file))
        
        # Create run with unknown metric
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        run_dir = runs_dir / "run_1"
        run_dir.mkdir()
        
        run_data = {
            'aggregate_metrics': {
                'TOTALLY_UNKNOWN': 123
            }
        }
        with open(run_dir / "metrics.json", 'w') as f:
            json.dump(run_data, f)
        
        run_files = list(runs_dir.glob("*/metrics.json"))
        
        with pytest.raises(MetricsValidationError) as exc_info:
            _discover_metrics_with_data(run_files, metrics_config)
        
        error_msg = str(exc_info.value)
        # Should mention the unknown metric
        assert 'TOTALLY_UNKNOWN' in error_msg
        # Should suggest adding to config
        assert 'metrics' in error_msg.lower() or 'experiment.yaml' in error_msg


class TestDiscoveryEdgeCases:
    """Test edge cases in metric discovery."""
    
    def test_missing_aggregate_metrics_key(self, tmp_path, sample_metrics_config):
        """Test handling of run files without aggregate_metrics key."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        run_dir = runs_dir / "run_1"
        run_dir.mkdir()
        
        # Run file without aggregate_metrics
        run_data = {'some_other_key': 'value'}
        with open(run_dir / "metrics.json", 'w') as f:
            json.dump(run_data, f)
        
        run_files = list(runs_dir.glob("*/metrics.json"))
        
        # Should raise MetricsValidationError
        with pytest.raises(MetricsValidationError) as exc_info:
            _discover_metrics_with_data(run_files, sample_metrics_config)
        
        error_msg = str(exc_info.value)
        assert 'aggregate_metrics' in error_msg


if __name__ == '__main__':
    pytest.main([__file__, '-v'])



class TestMetricsDiscoveryResult:
    """Test MetricsDiscoveryResult dataclass."""
    
    def test_create_discovery_result(self):
        """Test creating MetricsDiscoveryResult instance."""
        result = MetricsDiscoveryResult(
            metrics_with_data={'TOK_IN', 'TOK_OUT'},
            metrics_without_data={'AUTR', 'MC'},
            unknown_metrics=set(),
            run_count=5
        )
        
        assert result.metrics_with_data == {'TOK_IN', 'TOK_OUT'}
        assert result.metrics_without_data == {'AUTR', 'MC'}
        assert result.unknown_metrics == set()
        assert result.run_count == 5
    
    def test_discovery_result_with_unknown_metrics(self):
        """Test MetricsDiscoveryResult with unknown metrics."""
        result = MetricsDiscoveryResult(
            metrics_with_data={'TOK_IN'},
            metrics_without_data={'AUTR'},
            unknown_metrics={'UNKNOWN_METRIC'},
            run_count=3
        )
        
        assert result.unknown_metrics == {'UNKNOWN_METRIC'}


class TestDiscoverMetricsWithData:
    """Test _discover_metrics_with_data() function."""
    
    def test_discover_metrics_basic(self, sample_run_data, sample_metrics_config):
        """Test basic metric discovery from run data."""
        run_files = list(sample_run_data.glob("*/metrics.json"))
        
        result = _discover_metrics_with_data(run_files, sample_metrics_config)
        
        assert isinstance(result, MetricsDiscoveryResult)
        assert result.run_count == 2
        
        # TOK_IN, TOK_OUT, T_WALL_seconds should have data
        assert 'TOK_IN' in result.metrics_with_data
        assert 'TOK_OUT' in result.metrics_with_data
        assert 'T_WALL_seconds' in result.metrics_with_data
        
        # COST_USD (derived) and AUTR (unmeasured) should be without data
        assert 'COST_USD' in result.metrics_without_data
        assert 'AUTR' in result.metrics_without_data
        
        # No unknown metrics
        assert len(result.unknown_metrics) == 0
    
    def test_discover_with_unknown_metrics(self, tmp_path):
        """Test discovery raises error when unknown metrics found."""
        # Create config
        config_file = tmp_path / "experiment.yaml"
        config = {
            'framework': 'chatdev',
            'model': 'gpt-4',
            'metrics': {
                'TOK_IN': {
                    'name': 'Input Tokens',
                    'key': 'TOK_IN',
                    'description': 'Tokens',
                    'unit': 'tokens',
                    'category': 'tokens',
                    'ideal_direction': 'minimize',
                    'data_source': 'openai',
                    'aggregation': 'sum',
                    'display_format': '{:,.0f}',
                    'statistical_test': True,
                    'stopping_rule_eligible': True
                }
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        metrics_config = MetricsConfig(str(config_file))
        
        # Create run with unknown metric
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        run_dir = runs_dir / "run_1"
        run_dir.mkdir()
        
        run_data = {
            'aggregate_metrics': {
                'TOK_IN': 1000,
                'UNKNOWN_METRIC': 42
            }
        }
        with open(run_dir / "metrics.json", 'w') as f:
            json.dump(run_data, f)
        
        run_files = list(runs_dir.glob("*/metrics.json"))
        
        # Should raise MetricsValidationError
        with pytest.raises(MetricsValidationError) as exc_info:
            _discover_metrics_with_data(run_files, metrics_config)
        
        error_msg = str(exc_info.value)
        assert 'UNKNOWN_METRIC' in error_msg
    
    def test_discover_empty_runs_directory(self, sample_metrics_config):
        """Test discovery with no run files."""
        run_files = []
        
        result = _discover_metrics_with_data(run_files, sample_metrics_config)
        
        assert result.run_count == 0
        assert len(result.metrics_with_data) == 0
    
    def test_discover_partial_metrics_across_runs(self, tmp_path, sample_metrics_config):
        """Test discovery when different runs have different metrics."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        
        # Run 1 has TOK_IN, TOK_OUT
        run1_dir = runs_dir / "run_1"
        run1_dir.mkdir()
        run1 = {
            'aggregate_metrics': {
                'TOK_IN': 1000,
                'TOK_OUT': 500
            }
        }
        with open(run1_dir / "metrics.json", 'w') as f:
            json.dump(run1, f)
        
        # Run 2 has TOK_IN, T_WALL_seconds
        run2_dir = runs_dir / "run_2"
        run2_dir.mkdir()
        run2 = {
            'aggregate_metrics': {
                'TOK_IN': 1500,
                'T_WALL_seconds': 120.5
            }
        }
        with open(run2_dir / "metrics.json", 'w') as f:
            json.dump(run2, f)
        
        run_files = list(runs_dir.glob("*/metrics.json"))
        
        result = _discover_metrics_with_data(run_files, sample_metrics_config)
        
        # All three metrics should be in metrics_with_data
        assert 'TOK_IN' in result.metrics_with_data
        assert 'TOK_OUT' in result.metrics_with_data
        assert 'T_WALL_seconds' in result.metrics_with_data


class TestUnknownMetricValidation:
    """Test validation and error reporting for unknown metrics."""
    
    def test_unknown_metric_error_message_helpful(self, tmp_path):
        """Test that unknown metric error provides helpful guidance."""
        # Create minimal config
        config_file = tmp_path / "experiment.yaml"
        config = {
            'framework': 'chatdev',
            'model': 'gpt-4',
            'metrics': {
                'TOK_IN': {
                    'name': 'Input Tokens',
                    'key': 'TOK_IN',
                    'description': 'Tokens',
                    'unit': 'tokens',
                    'category': 'tokens',
                    'ideal_direction': 'minimize',
                    'data_source': 'openai',
                    'aggregation': 'sum',
                    'display_format': '{:,.0f}',
                    'statistical_test': True,
                    'stopping_rule_eligible': True
                }
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        metrics_config = MetricsConfig(str(config_file))
        
        # Create run with unknown metric
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        run_dir = runs_dir / "run_1"
        run_dir.mkdir()
        
        run_data = {
            'aggregate_metrics': {
                'TOTALLY_UNKNOWN': 123
            }
        }
        with open(run_dir / "metrics.json", 'w') as f:
            json.dump(run_data, f)
        
        run_files = list(runs_dir.glob("*/metrics.json"))
        
        with pytest.raises(MetricsValidationError) as exc_info:
            _discover_metrics_with_data(run_files, metrics_config)
        
        error_msg = str(exc_info.value)
        # Should mention the unknown metric
        assert 'TOTALLY_UNKNOWN' in error_msg
        # Should suggest adding to config
        assert 'metrics' in error_msg.lower() or 'experiment.yaml' in error_msg


class TestDiscoveryEdgeCases:
    """Test edge cases in metric discovery."""
    
    def test_missing_aggregate_metrics_key(self, tmp_path, sample_metrics_config):
        """Test handling of run files without aggregate_metrics key."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        run_dir = runs_dir / "run_1"
        run_dir.mkdir()
        
        # Run file without aggregate_metrics
        run_data = {'some_other_key': 'value'}
        with open(run_dir / "metrics.json", 'w') as f:
            json.dump(run_data, f)
        
        run_files = list(runs_dir.glob("*/metrics.json"))
        
        # Should raise MetricsValidationError
        with pytest.raises(MetricsValidationError) as exc_info:
            _discover_metrics_with_data(run_files, sample_metrics_config)
        
        error_msg = str(exc_info.value)
        assert 'aggregate_metrics' in error_msg
    
    def test_malformed_json_file(self, tmp_path, sample_metrics_config):
        """Test handling of malformed JSON files."""
        runs_dir = tmp_path / "runs"
        runs_dir.mkdir()
        run_dir = runs_dir / "run_1"
        run_dir.mkdir()
        
        # Create malformed JSON
        with open(run_dir / "metrics.json", 'w') as f:
            f.write("{ this is not valid json }")
        
        run_files = list(runs_dir.glob("*/metrics.json"))
        
        # Malformed JSON should be skipped with a warning (logged)
        # The function should continue gracefully
        result = _discover_metrics_with_data(run_files, sample_metrics_config)
        
        # run_count reflects files passed in, not successfully processed
        assert result.run_count == 1
        # But no metrics should be discovered from the malformed file
        assert len(result.metrics_with_data) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
