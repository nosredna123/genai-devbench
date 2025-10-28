"""
Integration tests for config migration from old to new format (Feature 009).

Tests the migration guide workflow and old format detection.
"""

import pytest
import yaml
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from utils.metrics_config import MetricsConfig
from utils.exceptions import ConfigMigrationError


@pytest.fixture
def old_format_config(tmp_path):
    """Create a config file with old 3-subsection format."""
    config_file = tmp_path / "old_experiment.yaml"
    
    old_config = {
        'framework': 'chatdev',
        'model': 'gpt-4',
        'metrics': {
            'reliable_metrics': {
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
                }
            },
            'derived_metrics': {
                'COST_USD': {
                    'name': 'Total Cost',
                    'key': 'COST_USD',
                    'description': 'Total API cost',
                    'unit': '$',
                    'category': 'cost',
                    'display_format': '${:.4f}'
                }
            },
            'excluded_metrics': {
                'AUTR': {
                    'name': 'Automation Rate',
                    'key': 'AUTR',
                    'description': 'Percentage of automated steps',
                    'unit': '%',
                    'category': 'quality',
                    'display_format': '{:.1f}%'
                }
            }
        }
    }
    
    with open(config_file, 'w') as f:
        yaml.dump(old_config, f)
    
    return config_file


@pytest.fixture
def migrated_config(tmp_path):
    """Create a properly migrated config in new format."""
    config_file = tmp_path / "new_experiment.yaml"
    
    new_config = {
        'framework': 'chatdev',
        'model': 'gpt-4',
        'metrics': {
            # Measured (from reliable_metrics)
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
            # Derived (from derived_metrics)
            'COST_USD': {
                'name': 'Total Cost',
                'key': 'COST_USD',
                'description': 'Total API cost',
                'unit': '$',
                'category': 'cost',
                'display_format': '${:.4f}',
                'status': 'derived',
                'reason': 'Calculated from token counts using API pricing'
            },
            # Unmeasured (from excluded_metrics)
            'AUTR': {
                'name': 'Automation Rate',
                'key': 'AUTR',
                'description': 'Percentage of automated steps',
                'unit': '%',
                'category': 'quality',
                'display_format': '{:.1f}%',
                'status': 'unmeasured',
                'reason': 'Manual tracking required - not yet implemented'
            }
        }
    }
    
    with open(config_file, 'w') as f:
        yaml.dump(new_config, f)
    
    return config_file


class TestOldFormatDetection:
    """Test detection of old config format."""
    
    def test_reliable_metrics_detected(self, old_format_config):
        """Test that reliable_metrics triggers old format detection."""
        with pytest.raises(ConfigMigrationError) as exc_info:
            MetricsConfig(str(old_format_config))
        
        error_msg = str(exc_info.value)
        assert 'reliable_metrics' in error_msg or 'old' in error_msg.lower()
    
    def test_derived_metrics_detected(self, tmp_path):
        """Test that derived_metrics triggers old format detection."""
        config_file = tmp_path / "test.yaml"
        config = {
            'metrics': {
                'derived_metrics': {
                    'COST_USD': {'name': 'Cost', 'key': 'COST_USD'}
                }
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        with pytest.raises(ConfigMigrationError):
            MetricsConfig(str(config_file))
    
    def test_excluded_metrics_detected(self, tmp_path):
        """Test that excluded_metrics triggers old format detection."""
        config_file = tmp_path / "test.yaml"
        config = {
            'metrics': {
                'excluded_metrics': {
                    'AUTR': {'name': 'Automation Rate', 'key': 'AUTR'}
                }
            }
        }
        with open(config_file, 'w') as f:
            yaml.dump(config, f)
        
        with pytest.raises(ConfigMigrationError):
            MetricsConfig(str(config_file))


class TestMigrationGuidance:
    """Test that migration errors provide helpful guidance."""
    
    def test_error_references_migration_guide(self, old_format_config):
        """Test that error message references CONFIG_MIGRATION_GUIDE.md."""
        with pytest.raises(ConfigMigrationError) as exc_info:
            MetricsConfig(str(old_format_config))
        
        error_msg = str(exc_info.value)
        assert 'CONFIG_MIGRATION_GUIDE.md' in error_msg
    
    def test_error_shows_detected_subsections(self, old_format_config):
        """Test that error shows which old subsections were found."""
        with pytest.raises(ConfigMigrationError) as exc_info:
            MetricsConfig(str(old_format_config))
        
        error_msg = str(exc_info.value)
        # Should mention at least one of the subsections
        has_subsection = any(
            subsec in error_msg 
            for subsec in ['reliable_metrics', 'derived_metrics', 'excluded_metrics']
        )
        assert has_subsection
    
    def test_error_provides_migration_steps(self, old_format_config):
        """Test that error provides actionable migration steps."""
        with pytest.raises(ConfigMigrationError) as exc_info:
            MetricsConfig(str(old_format_config))
        
        error_msg = str(exc_info.value)
        # Should have actionable guidance
        has_guidance = any(
            word in error_msg.lower()
            for word in ['migrate', 'update', 'convert', 'see', 'refer']
        )
        assert has_guidance


class TestMigratedConfigWorks:
    """Test that properly migrated configs work correctly."""
    
    def test_migrated_config_loads(self, migrated_config):
        """Test that migrated config loads without errors."""
        # Should load successfully
        config = MetricsConfig(str(migrated_config))
        assert config is not None
    
    def test_migrated_metrics_accessible(self, migrated_config):
        """Test that all migrated metrics are accessible."""
        config = MetricsConfig(str(migrated_config))
        
        all_metrics = config.get_all_metrics()
        
        # All 4 metrics should be present
        assert len(all_metrics) == 4
        assert 'TOK_IN' in all_metrics
        assert 'TOK_OUT' in all_metrics
        assert 'COST_USD' in all_metrics
        assert 'AUTR' in all_metrics
    
    def test_migrated_status_fields_preserved(self, migrated_config):
        """Test that status/reason fields from migration are preserved."""
        config = MetricsConfig(str(migrated_config))
        
        metrics = config.get_all_metrics()
        
        # Measured metrics should have no status
        assert metrics['TOK_IN'].status is None
        assert metrics['TOK_OUT'].status is None
        
        # Derived metric should have status
        assert metrics['COST_USD'].status == 'derived'
        assert metrics['COST_USD'].reason is not None
        
        # Unmeasured metric should have status
        assert metrics['AUTR'].status == 'unmeasured'
        assert metrics['AUTR'].reason is not None


class TestMixedFormatRejection:
    """Test that mixed old/new format is rejected."""
    
    def test_mixed_format_rejected(self, tmp_path):
        """Test config with both old and new format is rejected."""
        config_file = tmp_path / "mixed.yaml"
        
        mixed_config = {
            'metrics': {
                # Old format
                'reliable_metrics': {
                    'TOK_IN': {'name': 'Input Tokens', 'key': 'TOK_IN'}
                },
                # New format (direct metric)
                'TOK_OUT': {
                    'name': 'Output Tokens',
                    'key': 'TOK_OUT',
                    'description': 'Output tokens',
                    'unit': 'tokens',
                    'category': 'tokens',
                    'display_format': '{:,.0f}'
                }
            }
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(mixed_config, f)
        
        # Should reject mixed format
        with pytest.raises(ConfigMigrationError):
            MetricsConfig(str(config_file))


class TestMigrationDocumentationExists:
    """Test that migration documentation exists and is accessible."""
    
    def test_migration_guide_exists(self):
        """Test that CONFIG_MIGRATION_GUIDE.md exists in docs."""
        # Look for the migration guide
        docs_dir = Path(__file__).parent.parent.parent / 'docs'
        migration_guide = docs_dir / 'CONFIG_MIGRATION_GUIDE.md'
        
        assert migration_guide.exists(), \
            "CONFIG_MIGRATION_GUIDE.md should exist in docs/ directory"
    
    def test_migration_guide_not_empty(self):
        """Test that migration guide has content."""
        docs_dir = Path(__file__).parent.parent.parent / 'docs'
        migration_guide = docs_dir / 'CONFIG_MIGRATION_GUIDE.md'
        
        if migration_guide.exists():
            content = migration_guide.read_text()
            assert len(content) > 100, \
                "Migration guide should have substantial content"
            
            # Should contain key migration terms
            assert 'migration' in content.lower()
            assert any(term in content for term in ['before', 'after', 'old', 'new'])


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
