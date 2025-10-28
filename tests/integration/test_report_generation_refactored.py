"""
Integration tests for report generation with refactored metrics (Feature 009).

Tests critical validation behaviors:
- Unknown metric detection
- Empty frameworks_data handling
- Old config format rejection
"""

import pytest
import yaml
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.analysis.report_generator import generate_statistical_report
from src.utils.exceptions import ConfigValidationError, ConfigMigrationError, MetricsValidationError
from src.utils.metrics_config import get_metrics_config, reset_metrics_config


@pytest.fixture
def sample_config():
    """Create minimal sample config dict with unified metrics."""
    return {
        'metrics': {
            'TOK_IN': {
                'name': 'Input Tokens',
                'key': 'TOK_IN',
                'description': 'Total input tokens',
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
                'description': 'Total output tokens',
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
                'description': 'Total execution time',
                'unit': 'seconds',
                'category': 'performance',
                'ideal_direction': 'minimize',
                'data_source': 'measured',
                'aggregation': 'sum',
                'display_format': '{:.1f}',
                'statistical_test': True,
                'stopping_rule_eligible': True
            },
            'MC': {
                'name': 'Maintainability',
                'key': 'MC',
                'description': 'Code maintainability score',
                'unit': '%',
                'category': 'quality',
                'ideal_direction': 'maximize',
                'data_source': 'static_analysis',
                'aggregation': 'mean',
                'display_format': '{:.1f}%',
                'statistical_test': False,
                'stopping_rule_eligible': False,
                'status': 'unmeasured',
                'reason': 'Requires static analysis tool integration'
            }
        }
    }


class TestReportValidation:
    """Test report generation validation behaviors."""
    
    def test_empty_frameworks_data_raises_error(self, sample_config):
        """Test that empty frameworks_data raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            generate_statistical_report(
                frameworks_data={},
                output_path="/tmp/report.md",
                config=sample_config
            )
        
        assert 'empty' in str(exc_info.value).lower()
    
    def test_unknown_metric_fails_fast(self, tmp_path, sample_config):
        """Test that unknown metric in data causes fast failure."""
        # Setup config file for MetricsConfig
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "experiment.yaml"
        
        with open(config_file, 'w') as f:
            yaml.dump(sample_config, f)
        
        # Initialize MetricsConfig
        reset_metrics_config()
        metrics_config = get_metrics_config(str(config_file))
        
        # Add unknown metric to data
        bad_data = {
            'chatdev': [
                {
                    'TOK_IN': 1000.0,
                    'UNKNOWN_METRIC': 999.0  # Not in config
                }
            ]
        }
        
        output_path = str(tmp_path / "report.md")
        
        # Should raise validation error
        with pytest.raises(MetricsValidationError) as exc_info:
            generate_statistical_report(
                frameworks_data=bad_data,
                output_path=output_path,
                config=sample_config
            )
        
        # Error should mention the unknown metric
        assert 'UNKNOWN_METRIC' in str(exc_info.value)
        assert 'unknown' in str(exc_info.value).lower()


class TestConfigFormatValidation:
    """Test config format validation."""
    
    def test_old_format_config_rejected(self, tmp_path):
        """Test that old format config is properly rejected."""
        # Create old format config
        old_config = {
            'framework': 'chatdev',
            'model': 'gpt-4',
            'metrics': {
                'reliable_metrics': {
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
                },
                'derived_metrics': {},
                'excluded_metrics': {}
            }
        }
        
        # Setup config file
        config_dir = tmp_path / "config"
        config_dir.mkdir()
        config_file = config_dir / "experiment.yaml"
        
        with open(config_file, 'w') as f:
            yaml.dump(old_config, f)
        
        # Should raise ConfigMigrationError when trying to load MetricsConfig
        reset_metrics_config()
        with pytest.raises(ConfigMigrationError):
            metrics_config = get_metrics_config(str(config_file))


class TestEmptyDataHandling:
    """Test handling of empty data."""
    
    def test_empty_runs_directory(self, sample_config):
        """Test that empty frameworks_data is handled appropriately."""
        # Empty data should raise error
        with pytest.raises(ValueError):
            generate_statistical_report(
                frameworks_data={},
                output_path="/tmp/report.md",
                config=sample_config
            )


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
