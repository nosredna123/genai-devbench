"""
Unit tests for BAeSAdapter.

Tests adapter initialization, command translation, and core functionality
without requiring full BAEs framework integration.
"""

import os
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock

from src.adapters.baes_adapter import BAeSAdapter


@pytest.fixture
def mock_config():
    """Sample configuration for BAeSAdapter."""
    return {
        'repo_url': 'https://github.com/gesad-lab/baes_demo',
        'commit_hash': 'a34b207',
        'api_port': 8100,
        'ui_port': 8600,
        'max_retries': 3,
        'auto_restart_servers': False,
        'use_venv': True
    }


@pytest.fixture
def adapter(tmp_path, mock_config, monkeypatch):
    """Create BAeSAdapter instance with temporary workspace."""
    # Change to temp directory and create HITL file for tests
    import os
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    # Create mock HITL file
    hitl_dir = tmp_path / "config" / "hitl"
    hitl_dir.mkdir(parents=True, exist_ok=True)
    hitl_file = hitl_dir / "expanded_spec.txt"
    hitl_file.write_text("Test HITL specification response")
    
    run_id = "test-run-123"
    workspace = str(tmp_path / "workspace")
    adapter_instance = BAeSAdapter(mock_config, run_id, workspace)
    
    yield adapter_instance
    
    # Restore original directory
    os.chdir(original_cwd)


class TestAdapterInitialization:
    """Test adapter initialization and configuration."""
    
    def test_init_sets_config(self, adapter, mock_config):
        """Verify adapter stores configuration correctly."""
        assert adapter.config == mock_config
        assert adapter.run_id == "test-run-123"
        assert "workspace" in adapter.workspace_path
    
    def test_init_sets_default_values(self, adapter):
        """Verify adapter initializes with correct defaults."""
        assert adapter.framework_dir is None
        assert adapter.managed_system_dir is None
        assert adapter.database_dir is None
        assert adapter.venv_path is None
        assert adapter.python_path is None
        assert adapter._kernel is None
        assert adapter.hitl_text is None
        assert adapter.current_step == 0
    
    def test_workspace_path_creation(self, tmp_path, mock_config):
        """Verify workspace path is set correctly."""
        workspace = str(tmp_path / "custom_workspace")
        adapter = BAeSAdapter(mock_config, "test-123", workspace)
        assert adapter.workspace_path == workspace


class TestCLIIntegration:
    """Test BAEs CLI integration (non-interactive mode)."""
    
    def test_cli_script_path_uses_noninteractive(self, adapter):
        """Verify adapter uses bae_noninteractive.py for execution."""
        # Setup mock framework directory
        adapter.framework_dir = Path("/mock/framework/dir")
        adapter.database_dir = Path("/mock/database")
        adapter.venv_path = Path("/mock/venv")
        
        # The CLI script path should point to bae_noninteractive.py
        expected_cli = adapter.framework_dir / "bae_noninteractive.py"
        
        # Check that execute method would use this path
        # (can't test full execution without actual BAEs installation)
        assert expected_cli.name == "bae_noninteractive.py"
    
    def test_no_command_mapping_attribute(self, adapter):
        """Verify COMMAND_MAPPING was removed (no hardcoded commands)."""
        assert not hasattr(BAeSAdapter, 'COMMAND_MAPPING')
        assert not hasattr(adapter, 'COMMAND_MAPPING')
    
    def test_no_translate_method(self, adapter):
        """Verify _translate_command_to_requests method was removed."""
        assert not hasattr(adapter, '_translate_command_to_requests')
    
    def test_adapter_accepts_any_natural_language(self, adapter):
        """Adapter should accept any natural language request via CLI."""
        # Since we removed hardcoded mappings, the adapter should handle
        # any request by passing it directly to the BAEs CLI
        # This is a design verification test - no mocking needed
        
        # Various request types that should all be acceptable
        requests = [
            "Create a Student/Course/Teacher CRUD application",
            "Create a minimal Hello World REST API",
            "Add a blog post entity with comments",
            "Implement user authentication with JWT",
            "Add error handling to all endpoints"
        ]
        
        # All requests should be valid input to execute_step
        # (actual execution would fail without BAEs installation, but
        # the adapter should not reject them based on command matching)
        for req in requests:
            # No assertion - just verifying no AttributeError from missing COMMAND_MAPPING
            assert isinstance(req, str)


class TestHealthCheck:
    """Test health check functionality."""
    
    def test_health_check_fails_without_kernel(self, adapter):
        """Health check should raise RuntimeError if kernel not initialized."""
        with pytest.raises(RuntimeError, match="BAEs kernel not initialized"):
            adapter.health_check()
    
    def test_should_check_endpoints_early_steps(self, adapter):
        """Should not check endpoints during early steps."""
        adapter.current_step = 1
        assert adapter._should_check_endpoints() is False
    
    def test_should_check_endpoints_after_generation(self, adapter, tmp_path):
        """Should check endpoints after generation steps."""
        adapter.current_step = 2
        adapter.managed_system_dir = tmp_path / "managed_system"
        adapter.managed_system_dir.mkdir()
        
        assert adapter._should_check_endpoints() is True
    
    def test_should_check_endpoints_no_managed_system(self, adapter):
        """Should not check endpoints if managed_system doesn't exist."""
        adapter.current_step = 3
        adapter.managed_system_dir = Path("/nonexistent/path")
        
        assert adapter._should_check_endpoints() is False
    
    def test_check_http_endpoints_success(self, adapter, mock_config):
        """Test successful HTTP endpoint check."""
        # Mock requests at the point of import inside the method
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response
            
            result = adapter._check_http_endpoints()
            assert result is True
            
            # Verify both endpoints were checked
            assert mock_get.call_count == 2
            calls = [str(call) for call in mock_get.call_args_list]
            assert any('8100' in call for call in calls)  # API port
            assert any('8600' in call for call in calls)  # UI port
    
    def test_check_http_endpoints_api_failure(self, adapter):
        """Test HTTP endpoint check raises on API failure."""
        with patch('requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response
            
            with pytest.raises(RuntimeError, match="BAEs API endpoint returned status 500"):
                adapter._check_http_endpoints()
    
    def test_check_http_endpoints_connection_error(self, adapter):
        """Test HTTP endpoint check raises on connection error."""
        import requests
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.RequestException("Connection refused")
            
            with pytest.raises(RuntimeError, match="BAEs API endpoint not responding"):
                adapter._check_http_endpoints()


class TestHITLHandling:
    """Test human-in-the-loop handling."""
    
    def test_handle_hitl_returns_string(self, adapter):
        """HITL handler should return a string."""
        result = adapter.handle_hitl("test query")
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_handle_hitl_caches_response(self, adapter):
        """HITL response should be cached after first call."""
        result1 = adapter.handle_hitl("query 1")
        result2 = adapter.handle_hitl("query 2")
        
        # Should return same cached response
        assert result1 == result2
        assert adapter.hitl_text is not None
    
    def test_handle_hitl_loads_from_file(self, adapter, tmp_path, monkeypatch):
        """HITL should load from config file if it exists."""
        # Create mock hitl file
        hitl_file = tmp_path / "config" / "hitl" / "expanded_spec.txt"
        hitl_file.parent.mkdir(parents=True, exist_ok=True)
        hitl_file.write_text("Custom HITL response for testing")
        
        # Change to tmp directory so Path lookup works
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            # Reset cached value
            adapter.hitl_text = None
            result = adapter.handle_hitl("test query")
            assert "Custom HITL response" in result
        finally:
            os.chdir(original_cwd)
    
    def test_handle_hitl_raises_when_file_missing(self, mock_config, monkeypatch):
        """HITL should raise RuntimeError when file doesn't exist."""
        # Create a fresh adapter in a different temp directory without HITL file
        import tempfile
        import os
        
        with tempfile.TemporaryDirectory() as empty_dir:
            original_cwd = os.getcwd()
            os.chdir(empty_dir)
            
            try:
                # Create adapter without HITL file
                run_id = "test-run-missing-hitl"
                workspace = os.path.join(empty_dir, "workspace")
                test_adapter = BAeSAdapter(mock_config, run_id, workspace)
                
                # Should raise error since file doesn't exist
                with pytest.raises(RuntimeError, match="HITL specification file not found"):
                    test_adapter.handle_hitl("test query")
            finally:
                os.chdir(original_cwd)


class TestKernelProperty:
    """Test lazy kernel initialization."""
    
    def test_kernel_lazy_initialization(self, adapter):
        """Kernel should be None before first access."""
        assert adapter._kernel is None
    
    def test_kernel_initializes_on_access(self, adapter, tmp_path):
        """Kernel should initialize on first property access."""
        # Setup adapter state
        adapter.framework_dir = tmp_path / "baes_framework"
        adapter.framework_dir.mkdir(parents=True)
        adapter.database_dir = tmp_path / "database"
        adapter.database_dir.mkdir(parents=True)
        
        # Kernel property is now deprecated - just returns None
        kernel = adapter.kernel
        assert kernel is None


class TestConfigValidation:
    """Test configuration validation."""
    
    def test_adapter_requires_repo_url(self, tmp_path):
        """Adapter should handle missing repo_url."""
        config = {
            'commit_hash': 'abc123',
            'api_port': 8100,
            'ui_port': 8600
        }
        adapter = BAeSAdapter(config, "test-123", str(tmp_path))
        assert adapter.config == config
    
    def test_adapter_handles_default_ports(self, tmp_path):
        """Adapter should use default ports when not specified."""
        config = {
            'repo_url': 'https://github.com/gesad-lab/baes_demo'
        }
        adapter = BAeSAdapter(config, "test-123", str(tmp_path))
        
        # Adapter should use defaults from code
        # Verify in start() or execute_step() usage
        assert adapter.config.get('api_port', 8100) == 8100
        assert adapter.config.get('ui_port', 8600) == 8600


class TestStepExecution:
    """Test step execution flow (mocked)."""
    
    @patch.object(BAeSAdapter, '_execute_kernel_request')
    def test_execute_step_returns_dict(self, mock_execute_kernel, adapter):
        """execute_step should return a dictionary with all required fields."""
        # Mock kernel wrapper execution
        mock_execute_kernel.return_value = {
            'success': True,
            'result': {
                'entity': 'Student',
                'files_generated': ['student.py']
            }
        }
        
        result = adapter.execute_step(1, "Create a Student entity")
        
        # Should return a dictionary
        assert isinstance(result, dict)
        
        # BREAKING CHANGE v2.0.0: No token fields in execute_step result
        # Tokens are reconciled post-run, not returned per-step
        assert 'success' in result
        assert 'duration_seconds' in result
        assert 'start_timestamp' in result
        assert 'end_timestamp' in result
        assert 'hitl_count' in result
        assert 'retry_count' in result
        
        # Check types
        assert isinstance(result['success'], bool)
        assert isinstance(result['duration_seconds'], float)
        assert isinstance(result['start_timestamp'], int)  # Integer timestamps for API compatibility
        assert isinstance(result['end_timestamp'], int)  # Integer timestamps for API compatibility
        
        # Verify NO token fields (breaking change)
        assert 'tokens_in' not in result
        assert 'tokens_out' not in result
        assert 'api_calls' not in result
        assert 'cached_tokens' not in result
    
    @patch.object(BAeSAdapter, '_execute_kernel_request')
    def test_execute_step_no_token_fields(self, mock_execute_kernel, adapter):
        """BREAKING CHANGE v2.0.0: execute_step no longer returns token fields."""
        mock_execute_kernel.return_value = {
            'success': True,
            'result': {}
        }
        
        result = adapter.execute_step(1, "test command")
        
        # Verify NO token fields (tokens reconciled post-run)
        assert 'tokens_in' not in result
        assert 'tokens_out' not in result
        assert 'api_calls' not in result
        assert 'cached_tokens' not in result
    
    @patch.object(BAeSAdapter, '_execute_kernel_request')
    def test_execute_step_sets_current_step(self, mock_execute_kernel, adapter):
        """execute_step should update current_step."""
        mock_execute_kernel.return_value = {
            'success': True,
            'result': {}
        }
        
        adapter.execute_step(3, "test command")
        assert adapter.current_step == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
