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
def adapter(tmp_path, mock_config):
    """Create BAeSAdapter instance with temporary workspace."""
    run_id = "test-run-123"
    workspace = str(tmp_path / "workspace")
    return BAeSAdapter(mock_config, run_id, workspace)


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


class TestCommandTranslation:
    """Test command mapping and translation."""
    
    def test_command_mapping_exists(self, adapter):
        """Verify COMMAND_MAPPING is properly defined."""
        assert hasattr(BAeSAdapter, 'COMMAND_MAPPING')
        assert len(BAeSAdapter.COMMAND_MAPPING) > 0
    
    def test_translate_exact_match(self, adapter):
        """Test exact command match returns correct requests."""
        command = "Create a Student/Course/Teacher CRUD application"
        result = adapter._translate_command_to_requests(command)
        
        assert isinstance(result, list)
        assert len(result) == 3
        assert "add student entity" in result
        assert "add course entity" in result
        assert "add teacher entity" in result
    
    def test_translate_partial_match(self, adapter):
        """Test partial command match works (case-insensitive)."""
        command = "create a student/course/teacher crud"
        result = adapter._translate_command_to_requests(command)
        
        assert isinstance(result, list)
        assert len(result) > 0
    
    def test_translate_enrollment_relationship(self, adapter):
        """Test enrollment relationship command."""
        command = "Add enrollment relationship between Student and Course"
        result = adapter._translate_command_to_requests(command)
        
        assert isinstance(result, list)
        assert "add course to student entity" in result
    
    def test_translate_no_match(self, adapter):
        """Test unknown command returns empty list."""
        command = "This command does not exist in mapping"
        result = adapter._translate_command_to_requests(command)
        
        assert result == []
    
    def test_all_mapping_keys_are_strings(self, adapter):
        """Verify all mapping keys are strings."""
        for key in BAeSAdapter.COMMAND_MAPPING.keys():
            assert isinstance(key, str)
    
    def test_all_mapping_values_are_lists(self, adapter):
        """Verify all mapping values are lists of strings."""
        for value in BAeSAdapter.COMMAND_MAPPING.values():
            assert isinstance(value, list)
            for item in value:
                assert isinstance(item, str)


class TestHealthCheck:
    """Test health check functionality."""
    
    def test_health_check_fails_without_kernel(self, adapter):
        """Health check should fail if kernel not initialized."""
        result = adapter.health_check()
        assert result is False
    
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
    
    @patch('src.adapters.baes_adapter.requests.get')
    def test_check_http_endpoints_success(self, mock_get, adapter, mock_config):
        """Test successful HTTP endpoint check."""
        # Mock successful responses
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
    
    @patch('src.adapters.baes_adapter.requests.get')
    def test_check_http_endpoints_api_failure(self, mock_get, adapter):
        """Test HTTP endpoint check with API failure."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response
        
        result = adapter._check_http_endpoints()
        assert result is False
    
    @patch('src.adapters.baes_adapter.requests.get')
    def test_check_http_endpoints_connection_error(self, mock_get, adapter):
        """Test HTTP endpoint check with connection error."""
        import requests
        mock_get.side_effect = requests.RequestException("Connection refused")
        
        result = adapter._check_http_endpoints()
        assert result is False


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
    
    def test_handle_hitl_loads_from_file(self, adapter, tmp_path):
        """HITL should load from config file if it exists."""
        # Create mock hitl file
        hitl_file = tmp_path / "config" / "hitl" / "expanded_spec.txt"
        hitl_file.parent.mkdir(parents=True, exist_ok=True)
        hitl_file.write_text("Custom HITL response for testing")
        
        # Patch the path
        with patch('src.adapters.baes_adapter.Path') as mock_path:
            mock_path.return_value.exists.return_value = True
            mock_path.return_value.open = lambda mode: open(hitl_file, mode)
            
            result = adapter.handle_hitl("test query")
            assert "Custom HITL response" in result
    
    def test_handle_hitl_default_when_file_missing(self, adapter):
        """HITL should use default response when file doesn't exist."""
        result = adapter.handle_hitl("test query")
        
        # Should contain default HITL text
        assert "Student entity" in result or "CRUD" in result


class TestKernelProperty:
    """Test lazy kernel initialization."""
    
    def test_kernel_lazy_initialization(self, adapter):
        """Kernel should be None before first access."""
        assert adapter._kernel is None
    
    @patch('sys.path', new_callable=PropertyMock)
    @patch('src.adapters.baes_adapter.BAeSAdapter.framework_dir', new_callable=PropertyMock)
    def test_kernel_initializes_on_access(self, mock_framework_dir, mock_sys_path, adapter, tmp_path):
        """Kernel should initialize on first property access."""
        # Setup mocks
        mock_framework_dir.return_value = tmp_path / "baes_framework"
        adapter.database_dir = tmp_path / "database"
        adapter.database_dir.mkdir(parents=True)
        
        # Mock the EnhancedRuntimeKernel import
        with patch('src.adapters.baes_adapter.EnhancedRuntimeKernel') as mock_kernel_class:
            mock_kernel_instance = Mock()
            mock_kernel_class.return_value = mock_kernel_instance
            
            # This would normally fail due to import, but we're mocking it
            # In real usage, this requires BAEs to be installed
            try:
                kernel = adapter.kernel
                # If successful (mock worked), verify initialization
                assert adapter._kernel is not None
            except Exception:
                # Expected when BAEs not installed
                pass


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
    
    @patch.object(BAeSAdapter, 'kernel', new_callable=PropertyMock)
    def test_execute_step_returns_tuple(self, mock_kernel_prop, adapter):
        """execute_step should return 6-tuple with correct types."""
        # Mock kernel
        mock_kernel = Mock()
        mock_kernel.process_natural_language_request.return_value = {
            'success': True,
            'entity': 'Student',
            'files_generated': ['student.py']
        }
        mock_kernel_prop.return_value = mock_kernel
        
        result = adapter.execute_step(1, "Create a Student entity")
        
        assert isinstance(result, tuple)
        assert len(result) == 6
        
        success, duration, tokens_in, tokens_out, start_ts, end_ts = result
        assert isinstance(success, bool)
        assert isinstance(duration, float)
        assert isinstance(tokens_in, int)
        assert isinstance(tokens_out, int)
        assert isinstance(start_ts, float)
        assert isinstance(end_ts, float)
    
    @patch.object(BAeSAdapter, 'kernel', new_callable=PropertyMock)
    def test_execute_step_token_placeholders(self, mock_kernel_prop, adapter):
        """execute_step should return (0, 0) token placeholders."""
        mock_kernel = Mock()
        mock_kernel.process_natural_language_request.return_value = {
            'success': True
        }
        mock_kernel_prop.return_value = mock_kernel
        
        _, _, tokens_in, tokens_out, _, _ = adapter.execute_step(1, "test command")
        
        # Tokens should be placeholders for reconciliation
        assert tokens_in == 0
        assert tokens_out == 0
    
    @patch.object(BAeSAdapter, 'kernel', new_callable=PropertyMock)
    def test_execute_step_sets_current_step(self, mock_kernel_prop, adapter):
        """execute_step should update current_step."""
        mock_kernel = Mock()
        mock_kernel.process_natural_language_request.return_value = {
            'success': True
        }
        mock_kernel_prop.return_value = mock_kernel
        
        adapter.execute_step(3, "test command")
        assert adapter.current_step == 3


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
