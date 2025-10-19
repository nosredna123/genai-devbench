"""
Unit tests for report generation with dynamic configuration.

Tests cover:
- Dynamic value substitution (model, frameworks, stopping rules, etc.)
- Strict validation (missing/incomplete configs raise clear errors)
- Framework metadata extraction
- Edge cases (single run, unicode, unknown models)
- Full report structure validation

Run with:
    pytest tests/unit/test_report_generation.py -v
    pytest tests/unit/test_report_generation.py --cov=src.analysis.report_generator
"""

import pytest
import tempfile
from pathlib import Path
from src.analysis.report_generator import generate_statistical_report


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def minimal_valid_config():
    """
    Minimal valid configuration for testing.
    
    This represents the minimum required config to generate a report.
    All required fields are present with valid values.
    """
    return {
        'model': 'gpt-4o-mini',
        'frameworks': {
            'test_fw': {
                'repo_url': 'https://github.com/test/repo.git',
                'commit_hash': 'abc123def456789012345678901234567890',
                'api_key_env': 'OPENAI_API_KEY_TEST'
            }
        },
        'stopping_rule': {
            'min_runs': 5,
            'max_runs': 100,
            'confidence_level': 0.95,
            'max_half_width_pct': 10
        },
        'timeouts': {
            'step_timeout_seconds': 600
        },
        'prompts_dir': 'config/prompts',  # Uses actual prompts directory
        'analysis': {
            'bootstrap_samples': 10000,
            'significance_level': 0.05,
            'confidence_level': 0.95
        }
    }


@pytest.fixture
def minimal_run_data():
    """
    Minimal run data for testing.
    
    Single framework with single run containing required metrics.
    """
    return {
        'test_fw': [
            {
                'AUTR': 1.0,
                'TOK_IN': 1000,
                'TOK_OUT': 500,
                'T_WALL': 100,
                'CRUDe': 1.0,
                'ESR': 1.0,
                'MC': 5
            }
        ]
    }


# =============================================================================
# 1. Dynamic Value Tests
# =============================================================================

def test_model_configuration_dynamic(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that model name appears dynamically in report."""
    test_models = ['gpt-4o-mini', 'gpt-4o', 'o1-mini']
    
    for model in test_models:
        config = minimal_valid_config.copy()
        config['model'] = model
        
        output_file = tmp_path / f"report_{model}.md"
        generate_statistical_report(minimal_run_data, str(output_file), config)
        
        content = output_file.read_text()
        assert f"Model: `{model}`" in content, f"Model {model} not found in report"


def test_bootstrap_samples_dynamic(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that bootstrap samples appear dynamically in report."""
    test_values = [5000, 10000, 20000]
    
    for n_bootstrap in test_values:
        config = minimal_valid_config.copy()
        config['analysis']['bootstrap_samples'] = n_bootstrap
        
        output_file = tmp_path / f"report_{n_bootstrap}.md"
        generate_statistical_report(minimal_run_data, str(output_file), config)
        
        content = output_file.read_text()
        expected = f"({n_bootstrap:,} resamples)"  # With thousand separator
        assert expected in content, f"Bootstrap count {expected} not found in report"


def test_stopping_rule_dynamic(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that stopping rule values appear dynamically in report."""
    config = minimal_valid_config.copy()
    config['stopping_rule']['max_runs'] = 50
    config['stopping_rule']['max_half_width_pct'] = 15
    config['stopping_rule']['confidence_level'] = 0.99
    
    output_file = tmp_path / "report.md"
    generate_statistical_report(minimal_run_data, str(output_file), config)
    
    content = output_file.read_text()
    assert "max 50 runs" in content, "max_runs not found in report"
    assert "≤ 15%" in content or "≤ 15 %" in content, "max_half_width_pct not found"
    assert "99%" in content, "confidence_level not found"


def test_confidence_level_percentage_conversion(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that confidence level is converted from decimal to percentage."""
    config = minimal_valid_config.copy()
    config['stopping_rule']['confidence_level'] = 0.90
    
    output_file = tmp_path / "report.md"
    generate_statistical_report(minimal_run_data, str(output_file), config)
    
    content = output_file.read_text()
    assert "90%" in content, "Confidence level not converted to percentage"


# =============================================================================
# 2. Strict Validation Tests
# =============================================================================

def test_missing_model_raises_error(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that missing model raises clear error."""
    config = minimal_valid_config.copy()
    del config['model']
    
    with pytest.raises(ValueError) as exc_info:
        generate_statistical_report(minimal_run_data, str(tmp_path / "report.md"), config)
    
    error_msg = str(exc_info.value)
    assert "Missing required configuration: 'model'" in error_msg
    assert "root config" in error_msg
    assert "config/experiment.yaml" in error_msg


def test_missing_frameworks_raises_error(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that missing frameworks raises clear error."""
    config = minimal_valid_config.copy()
    del config['frameworks']
    
    with pytest.raises(ValueError) as exc_info:
        generate_statistical_report(minimal_run_data, str(tmp_path / "report.md"), config)
    
    error_msg = str(exc_info.value)
    assert "Missing required configuration: 'frameworks'" in error_msg


def test_missing_nested_stopping_rule_raises_error(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that missing nested config raises path-aware error."""
    config = minimal_valid_config.copy()
    del config['stopping_rule']['max_runs']
    
    with pytest.raises(ValueError) as exc_info:
        generate_statistical_report(minimal_run_data, str(tmp_path / "report.md"), config)
    
    error_msg = str(exc_info.value)
    assert "stopping_rule.max_runs" in error_msg, "Path not shown in error"


def test_missing_entire_stopping_rule_raises_error(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that missing entire stopping_rule section raises error."""
    config = minimal_valid_config.copy()
    del config['stopping_rule']
    
    with pytest.raises(ValueError) as exc_info:
        generate_statistical_report(minimal_run_data, str(tmp_path / "report.md"), config)
    
    error_msg = str(exc_info.value)
    assert "stopping_rule" in error_msg


def test_missing_analysis_config_raises_error(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that missing analysis config raises error."""
    config = minimal_valid_config.copy()
    del config['analysis']
    
    with pytest.raises(ValueError) as exc_info:
        generate_statistical_report(minimal_run_data, str(tmp_path / "report.md"), config)
    
    error_msg = str(exc_info.value)
    assert "analysis" in error_msg


def test_incomplete_framework_config_raises_error(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that incomplete framework config raises field-specific error."""
    config = minimal_valid_config.copy()
    del config['frameworks']['test_fw']['repo_url']
    
    with pytest.raises(ValueError) as exc_info:
        generate_statistical_report(minimal_run_data, str(tmp_path / "report.md"), config)
    
    error_msg = str(exc_info.value)
    assert "Framework 'test_fw'" in error_msg, "Framework name not in error"
    assert "repo_url" in error_msg, "Missing field not identified"


def test_framework_missing_commit_hash(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that framework missing commit_hash raises error."""
    config = minimal_valid_config.copy()
    del config['frameworks']['test_fw']['commit_hash']
    
    with pytest.raises(ValueError) as exc_info:
        generate_statistical_report(minimal_run_data, str(tmp_path / "report.md"), config)
    
    error_msg = str(exc_info.value)
    assert "commit_hash" in error_msg


def test_framework_missing_api_key_env(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that framework missing api_key_env raises error."""
    config = minimal_valid_config.copy()
    del config['frameworks']['test_fw']['api_key_env']
    
    with pytest.raises(ValueError) as exc_info:
        generate_statistical_report(minimal_run_data, str(tmp_path / "report.md"), config)
    
    error_msg = str(exc_info.value)
    assert "api_key_env" in error_msg


def test_nonexistent_prompts_dir_raises_error(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that non-existent prompts directory raises clear error."""
    config = minimal_valid_config.copy()
    config['prompts_dir'] = '/nonexistent/directory/path'
    
    with pytest.raises(ValueError) as exc_info:
        generate_statistical_report(minimal_run_data, str(tmp_path / "report.md"), config)
    
    error_msg = str(exc_info.value)
    assert "Prompts directory not found" in error_msg
    assert "/nonexistent/directory/path" in error_msg


def test_framework_not_in_config_raises_error(minimal_valid_config, tmp_path):
    """Test that framework in data but not in config raises error."""
    # Run data has 'unknown_fw' but config doesn't
    run_data = {
        'unknown_fw': [{'AUTR': 1.0, 'TOK_IN': 1000, 'T_WALL': 100}]
    }
    
    with pytest.raises(ValueError) as exc_info:
        generate_statistical_report(run_data, str(tmp_path / "report.md"), minimal_valid_config)
    
    error_msg = str(exc_info.value)
    assert "unknown_fw" in error_msg
    assert "not in config" in error_msg


# =============================================================================
# 3. Framework Metadata Tests
# =============================================================================

def test_multiple_frameworks_appear(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that all frameworks appear in report."""
    config = minimal_valid_config.copy()
    config['frameworks']['fw2'] = {
        'repo_url': 'https://github.com/test/repo2.git',
        'commit_hash': 'xyz789abc123def456',
        'api_key_env': 'OPENAI_API_KEY_FW2'
    }
    
    run_data = {
        'test_fw': minimal_run_data['test_fw'],
        'fw2': minimal_run_data['test_fw']
    }
    
    output_file = tmp_path / "report.md"
    generate_statistical_report(run_data, str(output_file), config)
    
    content = output_file.read_text()
    assert 'test_fw' in content
    assert 'fw2' in content
    assert 'abc123d' in content  # Short form of test_fw commit
    assert 'xyz789a' in content  # Short form of fw2 commit


def test_commit_hash_short_form(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that commit hashes are shown in short form (7 chars)."""
    config = minimal_valid_config.copy()
    long_hash = 'a' * 40
    config['frameworks']['test_fw']['commit_hash'] = long_hash
    
    output_file = tmp_path / "report.md"
    generate_statistical_report(minimal_run_data, str(output_file), config)
    
    content = output_file.read_text()
    assert 'aaaaaaa' in content  # Short form (7 chars)


def test_api_key_env_appears(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that API key environment variable appears in report."""
    config = minimal_valid_config.copy()
    config['frameworks']['test_fw']['api_key_env'] = 'CUSTOM_API_KEY'
    
    output_file = tmp_path / "report.md"
    generate_statistical_report(minimal_run_data, str(output_file), config)
    
    content = output_file.read_text()
    assert 'CUSTOM_API_KEY' in content


def test_repo_url_display(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that repository URL is displayed correctly."""
    output_file = tmp_path / "report.md"
    generate_statistical_report(minimal_run_data, str(output_file), minimal_valid_config)
    
    content = output_file.read_text()
    # Should show cleaned repo URL (without https://github.com/ and .git)
    assert 'test/repo' in content


# =============================================================================
# 4. Edge Case Tests
# =============================================================================

def test_single_run_per_framework(minimal_valid_config, tmp_path):
    """Test report generation with single run."""
    run_data = {
        'test_fw': [
            {'AUTR': 1.0, 'TOK_IN': 1000, 'T_WALL': 100, 'CRUDe': 1.0, 'ESR': 1.0, 'MC': 5}
        ]
    }
    
    output_file = tmp_path / "report.md"
    # Should not crash
    generate_statistical_report(run_data, str(output_file), minimal_valid_config)
    assert output_file.exists()
    assert output_file.stat().st_size > 0


def test_multiple_runs_per_framework(minimal_valid_config, tmp_path):
    """Test report generation with multiple runs."""
    run_data = {
        'test_fw': [
            {'AUTR': 1.0, 'TOK_IN': 1000, 'T_WALL': 100, 'CRUDe': 1.0, 'ESR': 1.0, 'MC': 5},
            {'AUTR': 0.9, 'TOK_IN': 1200, 'T_WALL': 110, 'CRUDe': 0.95, 'ESR': 0.9, 'MC': 6},
            {'AUTR': 1.0, 'TOK_IN': 900, 'T_WALL': 95, 'CRUDe': 1.0, 'ESR': 1.0, 'MC': 4}
        ]
    }
    
    output_file = tmp_path / "report.md"
    generate_statistical_report(run_data, str(output_file), minimal_valid_config)
    
    content = output_file.read_text()
    assert '3 runs' in content or '3 independent runs' in content


def test_unicode_in_content(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that report handles Unicode characters gracefully."""
    output_file = tmp_path / "report.md"
    generate_statistical_report(minimal_run_data, str(output_file), minimal_valid_config)
    
    content = output_file.read_text()
    # Should be valid UTF-8
    assert isinstance(content, str)
    # Report should contain Unicode characters (e.g., ≤, ±)
    assert '≤' in content or '±' in content


def test_unknown_model_name(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that unknown model names don't crash (use model name as display)."""
    config = minimal_valid_config.copy()
    config['model'] = 'unknown-model-xyz-2025'
    
    output_file = tmp_path / "report.md"
    generate_statistical_report(minimal_run_data, str(output_file), config)
    
    content = output_file.read_text()
    # Unknown model should appear as-is (not in display name mapping)
    assert 'unknown-model-xyz-2025' in content


def test_very_long_commit_hash(minimal_valid_config, minimal_run_data, tmp_path):
    """Test handling of very long commit hashes."""
    config = minimal_valid_config.copy()
    # Longer than standard 40 chars
    config['frameworks']['test_fw']['commit_hash'] = 'a' * 60
    
    output_file = tmp_path / "report.md"
    # Should not crash
    generate_statistical_report(minimal_run_data, str(output_file), config)
    assert output_file.exists()


# =============================================================================
# 5. Integration Tests
# =============================================================================

def test_full_report_structure(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that report contains all expected major sections."""
    output_file = tmp_path / "report.md"
    generate_statistical_report(minimal_run_data, str(output_file), minimal_valid_config)
    
    content = output_file.read_text()
    
    # Check major sections exist
    assert "# Statistical Analysis Report" in content
    assert "## Experimental Methodology" in content  # Updated section name
    assert "### 🔬 Research Design" in content
    assert "### 📋 Experimental Protocol" in content
    assert "#### **Standardized Task Sequence**" in content
    assert "#### **Controlled Variables**" in content
    assert "#### **Conclusion Validity**" in content
    assert "## Metric Definitions" in content


def test_report_is_valid_markdown(minimal_valid_config, minimal_run_data, tmp_path):
    """Test that generated report is valid Markdown."""
    output_file = tmp_path / "report.md"
    generate_statistical_report(minimal_run_data, str(output_file), minimal_valid_config)
    
    content = output_file.read_text()
    
    # Basic Markdown structure checks
    assert content.startswith('# ')  # Should start with H1
    assert '##' in content  # Should have H2 headers
    assert '**' in content  # Should have bold text
    assert '`' in content  # Should have code blocks/inline code


def test_empty_frameworks_data_raises_error(minimal_valid_config, tmp_path):
    """Test that empty frameworks_data raises error."""
    with pytest.raises(ValueError) as exc_info:
        generate_statistical_report({}, str(tmp_path / "report.md"), minimal_valid_config)
    
    assert "frameworks_data cannot be empty" in str(exc_info.value)


# =============================================================================
# Test Execution Summary
# =============================================================================

if __name__ == "__main__":
    """
    Run tests directly:
        python tests/unit/test_report_generation.py
    
    Better to use pytest:
        pytest tests/unit/test_report_generation.py -v
        pytest tests/unit/test_report_generation.py --cov=src.analysis.statistics
    """
    pytest.main([__file__, '-v'])
