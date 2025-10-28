"""
Unit tests for report validation helpers (Feature 009).

Tests fail-fast validation functions introduced in Phase 5:
- _require_config_value()
- _require_nested_config()

Validates that error messages are helpful and context-aware.
"""

import pytest
from src.utils.exceptions import ConfigValidationError


# Import the validation functions from report_generator
# These are private functions, so importing may need adjustment
from src.analysis.report_generator import (
    _require_config_value,
    _require_nested_config
)


class TestRequireConfigValue:
    """Test _require_config_value() fail-fast validation."""
    
    def test_value_present_returns_value(self):
        """Test that present value is returned without error."""
        config = {'model': 'gpt-4', 'framework': 'chatdev'}
        
        result = _require_config_value(config, 'model', 'test config')
        assert result == 'gpt-4'
        
        result = _require_config_value(config, 'framework', 'test config')
        assert result == 'chatdev'
    
    def test_missing_value_raises_error(self):
        """Test that missing required value raises ConfigValidationError."""
        config = {'framework': 'chatdev'}
        
        with pytest.raises(ConfigValidationError) as exc_info:
            _require_config_value(config, 'model', 'test config')
        
        error_msg = str(exc_info.value)
        assert 'model' in error_msg
        assert 'required' in error_msg.lower()
    
    def test_error_message_includes_context(self):
        """Test error message includes helpful context."""
        config = {}
        
        with pytest.raises(ConfigValidationError) as exc_info:
            _require_config_value(config, 'model', 'framework configuration')
        
        error_msg = str(exc_info.value)
        assert 'model' in error_msg
        assert 'framework configuration' in error_msg
    
    def test_error_message_includes_docs_reference(self):
        """Test error message references documentation."""
        config = {}
        
        with pytest.raises(ConfigValidationError) as exc_info:
            _require_config_value(config, 'framework', 'root config')
        
        error_msg = str(exc_info.value)
        # Should mention documentation or migration guide
        assert 'docs/' in error_msg or 'CONFIG_MIGRATION_GUIDE' in error_msg or 'See' in error_msg
    
    def test_none_value_treated_as_missing(self):
        """Test that None value is treated as missing."""
        config = {'model': None}
        
        with pytest.raises(ConfigValidationError) as exc_info:
            _require_config_value(config, 'model', 'test config')
        
        error_msg = str(exc_info.value)
        assert 'null' in error_msg.lower() or 'none' in error_msg.lower()
    
    def test_empty_string_accepted(self):
        """Test that empty string is accepted (may be intentional)."""
        config = {'model': ''}
        
        # Empty string should be accepted (caller can validate further)
        result = _require_config_value(config, 'model', 'test config')
        assert result == ''


class TestRequireNestedConfig:
    """Test _require_nested_config() nested validation."""
    
    def test_nested_value_present_returns_value(self):
        """Test that present nested value is returned."""
        config = {
            'cost_analysis': {
                'model': 'gpt-4'
            }
        }
        
        result = _require_nested_config(config, ['cost_analysis', 'model'])
        assert result == 'gpt-4'
    
    def test_missing_parent_section_raises_error(self):
        """Test error when parent section is missing."""
        config = {}
        
        with pytest.raises(ConfigValidationError) as exc_info:
            _require_nested_config(config, ['cost_analysis', 'model'])
        
        error_msg = str(exc_info.value)
        assert 'cost_analysis' in error_msg
    
    def test_missing_nested_key_raises_error(self):
        """Test error when nested key is missing."""
        config = {
            'cost_analysis': {}
        }
        
        with pytest.raises(ConfigValidationError) as exc_info:
            _require_nested_config(config, ['cost_analysis', 'model'])
        
        error_msg = str(exc_info.value)
        assert 'model' in error_msg
        assert 'cost_analysis' in error_msg
    
    def test_error_shows_full_path(self):
        """Test error message shows full config path."""
        config = {
            'cost_analysis': {}
        }
        
        with pytest.raises(ConfigValidationError) as exc_info:
            _require_nested_config(config, ['cost_analysis', 'model'])
        
        error_msg = str(exc_info.value)
        # Should show path like "cost_analysis.model" or "cost_analysis['model']"
        assert 'cost_analysis' in error_msg
        assert 'model' in error_msg
    
    def test_error_includes_structure_example(self):
        """Test error message includes expected structure example."""
        config = {}
        
        with pytest.raises(ConfigValidationError) as exc_info:
            _require_nested_config(config, ['cost_analysis', 'model'])
        
        error_msg = str(exc_info.value)
        # Should show expected structure
        assert 'cost_analysis' in error_msg or 'structure' in error_msg.lower()


class TestValidationErrorMessages:
    """Test that validation errors provide actionable guidance."""
    
    def test_framework_validation_error_helpful(self):
        """Test framework validation gives specific guidance."""
        config = {}
        
        with pytest.raises(ConfigValidationError) as exc_info:
            _require_config_value(config, 'framework', 'root config')
        
        error_msg = str(exc_info.value)
        # Should mention framework and how to fix
        assert 'framework' in error_msg.lower()
        # Should have fix instructions
        assert 'fix' in error_msg.lower() or 'add' in error_msg.lower()
    
    def test_model_validation_error_helpful(self):
        """Test model validation gives specific guidance."""
        config = {}
        
        with pytest.raises(ConfigValidationError) as exc_info:
            _require_config_value(config, 'model', 'root config')
        
        error_msg = str(exc_info.value)
        assert 'model' in error_msg.lower()
        # Should have actionable guidance
        assert 'experiment.yaml' in error_msg
    
    def test_error_distinguishes_missing_vs_invalid(self):
        """Test errors clearly indicate missing vs invalid values."""
        # Missing key
        config1 = {}
        with pytest.raises(ConfigValidationError) as exc_info:
            _require_config_value(config1, 'model', 'test config')
        
        error_msg = str(exc_info.value)
        assert 'missing' in error_msg.lower() or 'required' in error_msg.lower()
        
        # Present but None
        config2 = {'model': None}
        with pytest.raises(ConfigValidationError) as exc_info:
            _require_config_value(config2, 'model', 'test config')
        
        error_msg = str(exc_info.value)
        # Should indicate value issue, not just missing key
        assert 'null' in error_msg.lower() or 'none' in error_msg.lower()


class TestValidationIntegration:
    """Integration tests for validation in report generation context."""
    
    def test_multiple_validations_fail_on_first(self):
        """Test that multiple validations fail on first error (fail-fast)."""
        config = {}
        
        # Should fail on first missing value
        with pytest.raises(ConfigValidationError):
            _require_config_value(config, 'framework', 'test config')
            _require_config_value(config, 'model', 'test config')  # Should not reach this
    
    def test_validation_preserves_original_config(self):
        """Test that validation doesn't modify original config."""
        config = {'model': 'gpt-4'}
        original = config.copy()
        
        _require_config_value(config, 'model', 'test config')
        
        assert config == original


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
