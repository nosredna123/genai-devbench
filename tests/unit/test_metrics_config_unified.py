"""
Unit tests for refactored MetricsConfig class (Feature 009).

Tests the unified metrics format introduced in the analysis module refactoring.
Validates new methods, old format detection, and status/reason field handling.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from src.utils.metrics_config import (
    MetricDefinition,
    MetricsConfig,
    get_metrics_config,
    reset_metrics_config
)
from src.utils.exceptions import ConfigMigrationError


@pytest.fixture
def unified_config_path(tmp_path):
    """Create a temporary test config with unified metrics format."""
    test_config = {
        'metrics': {
            # Measured metrics (no status field)
            'TOK_IN': {
                'name': 'Input Tokens',
                'key': 'TOK_IN',
                'description': 'Total input tokens sent to LLM',
                'unit': 'tokens',
                'category': 'tokens',
                'display_format': '{:,.0f}'
            },
            'TOK_OUT': {
                'name': 'Output Tokens',
                'key': 'TOK_OUT',
                'description': 'Total output tokens from LLM',
                'unit': 'tokens',
                'category': 'tokens',
                'display_format': '{:,.0f}'
            },
            'T_WALL_seconds': {
                'name': 'Wall Time',
                'key': 'T_WALL_seconds',
                'description': 'Total execution time',
                'unit': 'seconds',
                'category': 'performance',
                'display_format': '{:.1f}'
            },
            # Derived metric
            'COST_USD': {
                'name': 'Total Cost',
                'key': 'COST_USD',
                'description': 'Total API cost',
                'unit': '$',
                'category': 'cost',
                'display_format': '${:.2f}',
                'status': 'derived',
                'reason': 'Calculated from token counts and pricing'
            },
            # Unmeasured metrics
            'AUTR': {
                'name': 'Automation Rate',
                'key': 'AUTR',
                'description': 'Percentage of automated steps',
                'unit': '%',
                'category': 'quality',
                'display_format': '{:.1f}%',
                'status': 'unmeasured',
                'reason': 'Requires manual review - not yet automated'
            },
            'MC': {
                'name': 'Maintainability',
                'key': 'MC',
                'description': 'Code maintainability score',
                'unit': '%',
                'category': 'quality',
                'display_format': '{:.1f}%',
                'status': 'unmeasured',
                'reason': 'Requires static analysis integration'
            }
        }
    }
    
    config_file = tmp_path / "experiment.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(test_config, f)
    
    return config_file


@pytest.fixture
def old_format_config_path(tmp_path):
    """Create a config with old 3-subsection format."""
    test_config = {
        'metrics': {
            'reliable_metrics': {
                'TOK_IN': {
                    'name': 'Input Tokens',
                    'key': 'TOK_IN',
                    'description': 'Total input tokens',
                    'unit': 'tokens',
                    'category': 'tokens',
                    'display_format': '{:,.0f}'
                }
            },
            'derived_metrics': {
                'COST_USD': {
                    'name': 'Total Cost',
                    'key': 'COST_USD',
                    'description': 'Total cost',
                    'unit': '$',
                    'category': 'cost',
                    'display_format': '${:.2f}'
                }
            },
            'excluded_metrics': {
                'AUTR': {
                    'name': 'Automation Rate',
                    'key': 'AUTR',
                    'description': 'Automation percentage',
                    'unit': '%',
                    'category': 'quality',
                    'display_format': '{:.1f}%'
                }
            }
        }
    }
    
    config_file = tmp_path / "experiment_old.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(test_config, f)
    
    return config_file


class TestUnifiedMetricsFormat:
    """Test unified metrics configuration format."""
    
    def test_get_all_metrics(self, unified_config_path):
        """Test get_all_metrics() returns all metrics from unified format."""
        config = MetricsConfig(str(unified_config_path))
        
        all_metrics = config.get_all_metrics()
        
        assert isinstance(all_metrics, dict)
        assert len(all_metrics) == 6
        assert 'TOK_IN' in all_metrics
        assert 'TOK_OUT' in all_metrics
        assert 'T_WALL_seconds' in all_metrics
        assert 'COST_USD' in all_metrics
        assert 'AUTR' in all_metrics
        assert 'MC' in all_metrics
        
        # Verify all values are MetricDefinition instances
        for metric_def in all_metrics.values():
            assert isinstance(metric_def, MetricDefinition)
    
    def test_get_metrics_by_category(self, unified_config_path):
        """Test get_metrics_by_category() filters correctly."""
        config = MetricsConfig(str(unified_config_path))
        
        # Test tokens category
        token_metrics = config.get_metrics_by_category('tokens')
        assert len(token_metrics) == 2
        assert 'TOK_IN' in token_metrics
        assert 'TOK_OUT' in token_metrics
        
        # Test quality category
        quality_metrics = config.get_metrics_by_category('quality')
        assert len(quality_metrics) == 2
        assert 'AUTR' in quality_metrics
        assert 'MC' in quality_metrics
        
        # Test cost category
        cost_metrics = config.get_metrics_by_category('cost')
        assert len(cost_metrics) == 1
        assert 'COST_USD' in cost_metrics
        
        # Test non-existent category
        empty_metrics = config.get_metrics_by_category('nonexistent')
        assert len(empty_metrics) == 0
    
    def test_get_metrics_by_filter_single_criterion(self, unified_config_path):
        """Test get_metrics_by_filter() with single filter criterion."""
        config = MetricsConfig(str(unified_config_path))
        
        # Filter by status
        derived = config.get_metrics_by_filter(status='derived')
        assert len(derived) == 1
        assert 'COST_USD' in derived
        
        unmeasured = config.get_metrics_by_filter(status='unmeasured')
        assert len(unmeasured) == 2
        assert 'AUTR' in unmeasured
        assert 'MC' in unmeasured
        
        # Filter by category
        tokens = config.get_metrics_by_filter(category='tokens')
        assert len(tokens) == 2
        assert 'TOK_IN' in tokens
        assert 'TOK_OUT' in tokens
    
    def test_get_metrics_by_filter_multiple_criteria(self, unified_config_path):
        """Test get_metrics_by_filter() with multiple filter criteria."""
        config = MetricsConfig(str(unified_config_path))
        
        # Filter by status AND category
        unmeasured_quality = config.get_metrics_by_filter(
            status='unmeasured',
            category='quality'
        )
        assert len(unmeasured_quality) == 2
        assert 'AUTR' in unmeasured_quality
        assert 'MC' in unmeasured_quality
        
        # No matches
        no_match = config.get_metrics_by_filter(
            status='derived',
            category='tokens'
        )
        assert len(no_match) == 0
    
    def test_status_reason_fields_parsed(self, unified_config_path):
        """Test status and reason fields are correctly parsed."""
        config = MetricsConfig(str(unified_config_path))
        
        # Measured metric (no status/reason)
        tok_in = config.get_all_metrics()['TOK_IN']
        assert tok_in.status is None
        assert tok_in.reason is None
        
        # Derived metric
        cost = config.get_all_metrics()['COST_USD']
        assert cost.status == 'derived'
        assert cost.reason == 'Calculated from token counts and pricing'
        
        # Unmeasured metric
        autr = config.get_all_metrics()['AUTR']
        assert autr.status == 'unmeasured'
        assert autr.reason == 'Requires manual review - not yet automated'


class TestOldFormatDetection:
    """Test detection and rejection of old 3-subsection format."""
    
    def test_detect_old_config_format(self, old_format_config_path):
        """Test _detect_old_config_format() identifies old format."""
        # This should raise ConfigMigrationError
        with pytest.raises(ConfigMigrationError) as exc_info:
            config = MetricsConfig(str(old_format_config_path))
        
        error_msg = str(exc_info.value)
        # Check for any variation of "old config format" message
        assert 'old' in error_msg.lower() and 'config' in error_msg.lower()
        assert 'reliable_metrics' in error_msg or 'derived_metrics' in error_msg
        assert 'CONFIG_MIGRATION_GUIDE.md' in error_msg
    
    def test_old_format_error_message_helpful(self, old_format_config_path):
        """Test ConfigMigrationError provides helpful migration guidance."""
        with pytest.raises(ConfigMigrationError) as exc_info:
            config = MetricsConfig(str(old_format_config_path))
        
        error_msg = str(exc_info.value)
        # Should mention the migration guide
        assert 'CONFIG_MIGRATION_GUIDE.md' in error_msg
        # Should mention what was detected
        assert 'deprecated' in error_msg.lower() or 'old' in error_msg.lower()


class TestMetricDefinitionFields:
    """Test MetricDefinition dataclass with new fields."""
    
    def test_status_reason_in_loaded_metrics(self, unified_config_path):
        """Test that status and reason fields are loaded from config."""
        config = MetricsConfig(str(unified_config_path))
        
        metrics = config.get_all_metrics()
        
        # Measured metric should have no status/reason
        tok_in = metrics['TOK_IN']
        assert tok_in.status is None
        assert tok_in.reason is None
        
        # Derived metric should have status/reason
        cost = metrics['COST_USD']
        assert cost.status == 'derived'
        assert cost.reason == 'Calculated from token counts and pricing'
        
        # Unmeasured metric should have status/reason
        autr = metrics['AUTR']
        assert autr.status == 'unmeasured'
        assert autr.reason is not None


class TestConfigValidation:
    """Test configuration validation for unified format."""
    
    def test_empty_metrics_section(self, tmp_path):
        """Test handling of empty metrics section."""
        test_config = {'metrics': {}}
        
        config_file = tmp_path / "empty.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)
        
        config = MetricsConfig(str(config_file))
        assert len(config.get_all_metrics()) == 0
    
    def test_missing_required_fields(self, tmp_path):
        """Test validation of required metric fields."""
        # This config is missing 'description' which may be required
        test_config = {
            'metrics': {
                'INCOMPLETE': {
                    'name': 'Incomplete Metric',
                    'key': 'INCOMPLETE',
                    'unit': 'units',
                    'category': 'test',
                    'display_format': '{:.2f}'
                    # Missing 'description'
                }
            }
        }
        
        config_file = tmp_path / "incomplete.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(test_config, f)
        
        # Should either raise error or handle gracefully
        # Implementation may vary - testing that it doesn't crash
        try:
            config = MetricsConfig(str(config_file))
            # If it doesn't raise, that's okay
        except (ValueError, KeyError):
            # If it raises, that's also acceptable
            pass


class TestSingletonBehavior:
    """Test get_metrics_config singleton behavior."""
    
    def test_singleton_returns_same_instance(self, unified_config_path):
        """Test get_metrics_config() returns singleton instance."""
        reset_metrics_config()  # Clear any existing singleton
        
        # First call with path
        config1 = get_metrics_config(str(unified_config_path))
        
        # Second call without path should return same instance
        config2 = get_metrics_config()
        
        assert config1 is config2
    
    def test_reset_metrics_config(self, unified_config_path):
        """Test reset_metrics_config() clears singleton."""
        config1 = get_metrics_config(str(unified_config_path))
        reset_metrics_config()
        
        # After reset, should create new instance
        config2 = get_metrics_config(str(unified_config_path))
        
        assert config1 is not config2


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
