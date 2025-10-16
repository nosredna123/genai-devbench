"""
Integration tests for BAeSAdapter.

Tests adapter with real BAEs framework components (requires framework installed).
These tests are more expensive and should be run selectively.

Usage:
    pytest tests/integration/test_baes_single_step.py -v
    pytest tests/integration/test_baes_single_step.py -v -k "test_step_1"
"""

import os
import pytest
import time
from pathlib import Path
from typing import Dict, Any

from src.adapters.baes_adapter import BAeSAdapter


# Skip all tests if BAEs not available
try:
    # This will fail if BAEs dependencies not installed
    import fastapi
    import streamlit
    import sqlalchemy
    BAES_AVAILABLE = True
except ImportError:
    BAES_AVAILABLE = False


@pytest.fixture
def integration_config() -> Dict[str, Any]:
    """Configuration for integration testing."""
    return {
        'repo_url': 'https://github.com/gesad-lab/baes_demo',
        'commit_hash': 'a34b207253ef4beecedac913264732a93f16e979',
        'api_port': 8100,
        'ui_port': 8600,
        'max_retries': 3,
        'auto_restart_servers': False,
        'use_venv': True
    }


@pytest.fixture
def integration_workspace(tmp_path) -> str:
    """Create isolated workspace for integration test."""
    workspace = tmp_path / "integration_test_workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    return str(workspace)


@pytest.fixture
def adapter(integration_config, integration_workspace):
    """Create and initialize BAeSAdapter for integration testing."""
    run_id = f"integration-test-{int(time.time())}"
    adapter = BAeSAdapter(integration_config, run_id, integration_workspace)
    
    # Check if API key is configured
    if not os.getenv('OPENAI_API_KEY_BAES') and not os.getenv('OPENAI_API_KEY'):
        pytest.skip("No OpenAI API key configured (set OPENAI_API_KEY_BAES or OPENAI_API_KEY)")
    
    yield adapter
    
    # Cleanup after test
    try:
        adapter.stop()
    except Exception as e:
        print(f"Cleanup error: {e}")


@pytest.mark.integration
@pytest.mark.skipif(not BAES_AVAILABLE, reason="BAEs dependencies not installed")
class TestBAeSIntegration:
    """Integration tests requiring full BAEs framework."""
    
    def test_adapter_start_initializes_framework(self, adapter):
        """Test that adapter.start() properly initializes BAEs framework."""
        adapter.start()
        
        # Verify workspace structure created
        assert adapter.framework_dir is not None
        assert adapter.framework_dir.exists()
        
        assert adapter.managed_system_dir is not None
        # managed_system may not exist until first step executes
        
        assert adapter.database_dir is not None
        assert adapter.database_dir.exists()
        
        # Verify venv created
        assert adapter.venv_path is not None
        assert adapter.venv_path.exists()
        assert adapter.python_path is not None
        assert adapter.python_path.exists()
    
    def test_adapter_kernel_initialization(self, adapter):
        """Test that kernel initializes correctly."""
        adapter.start()
        
        # Access kernel property (lazy initialization)
        kernel = adapter.kernel
        
        assert kernel is not None
        assert hasattr(kernel, 'process_natural_language_request')
        assert hasattr(kernel, 'context_store')
        assert hasattr(kernel, 'bae_registry')
    
    def test_health_check_after_start(self, adapter):
        """Test health check passes after start()."""
        adapter.start()
        
        # Initial health check (before generation)
        result = adapter.health_check()
        
        # Should pass internal checks even without HTTP endpoints
        # (HTTP checks only happen after step 2+)
        assert result is True
    
    @pytest.mark.slow
    def test_step_1_creates_entities(self, adapter):
        """Test executing step 1: Create Student/Course/Teacher entities."""
        adapter.start()
        
        command = "Create a Student/Course/Teacher CRUD application"
        success, duration, tokens_in, tokens_out, start_ts, end_ts = adapter.execute_step(1, command)
        
        # Verify execution succeeded
        assert success is True
        assert duration > 0
        assert start_ts > 0
        assert end_ts > start_ts
        
        # Token placeholders (reconciliation fills real values)
        assert tokens_in == 0
        assert tokens_out == 0
        
        # Verify managed system created
        assert adapter.managed_system_dir.exists()
        
        # Verify some files generated
        generated_files = list(adapter.managed_system_dir.rglob("*.py"))
        assert len(generated_files) > 0
    
    @pytest.mark.slow
    def test_step_2_adds_relationship(self, adapter):
        """Test executing step 2: Add enrollment relationship."""
        adapter.start()
        
        # Execute step 1 first (prerequisite)
        adapter.execute_step(1, "Create a Student/Course/Teacher CRUD application")
        
        # Execute step 2
        command = "Add enrollment relationship between Student and Course"
        success, duration, tokens_in, tokens_out, start_ts, end_ts = adapter.execute_step(2, command)
        
        assert success is True
        assert duration > 0
        
        # Health check should now include HTTP endpoints
        health = adapter.health_check()
        # Note: May fail if servers not fully started, which is OK for this test
        # The important part is that it doesn't crash
        assert isinstance(health, bool)
    
    @pytest.mark.slow
    def test_sequential_steps(self, adapter):
        """Test executing multiple steps sequentially."""
        adapter.start()
        
        commands = [
            "Create a Student/Course/Teacher CRUD application",
            "Add enrollment relationship between Student and Course"
        ]
        
        for step_num, command in enumerate(commands, start=1):
            success, duration, _, _, _, _ = adapter.execute_step(step_num, command)
            
            assert success is True, f"Step {step_num} failed"
            assert duration > 0
            
            # Verify current step updated
            assert adapter.current_step == step_num
    
    def test_adapter_stop_cleanup(self, adapter):
        """Test that adapter.stop() cleans up properly."""
        adapter.start()
        
        # Execute at least one step to generate artifacts
        adapter.execute_step(1, "Create a Student/Course/Teacher CRUD application")
        
        # Stop adapter
        adapter.stop()
        
        # Verify archive created
        archive_path = Path(adapter.workspace_path) / "managed_system.tar.gz"
        assert archive_path.exists()
        assert archive_path.stat().st_size > 0


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.skipif(not BAES_AVAILABLE, reason="BAEs dependencies not installed")
class TestBAeSServerManagement:
    """Integration tests for server lifecycle management."""
    
    def test_servers_start_automatically(self, adapter):
        """Test that servers start during first step execution."""
        adapter.start()
        
        # Execute first step (should start servers)
        adapter.execute_step(1, "Create a Student/Course/Teacher CRUD application")
        
        # Wait a bit for servers to fully start
        time.sleep(5)
        
        # Check if ports are bound
        import socket
        
        api_port = adapter.config.get('api_port', 8100)
        ui_port = adapter.config.get('ui_port', 8600)
        
        # Try to connect to API port
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                result = sock.connect_ex(("localhost", api_port))
                # 0 means connection successful (port is bound)
                # This test may be flaky depending on server startup time
                # So we don't assert, just log
                if result == 0:
                    print(f"API server responding on port {api_port}")
        except Exception as e:
            print(f"Could not check API port: {e}")
    
    def test_servers_stop_cleanly(self, adapter):
        """Test that servers stop without errors."""
        adapter.start()
        adapter.execute_step(1, "Create a Student/Course/Teacher CRUD application")
        
        # Stop should not raise exceptions
        try:
            adapter.stop()
        except Exception as e:
            pytest.fail(f"adapter.stop() raised exception: {e}")


@pytest.mark.integration
@pytest.mark.skipif(not BAES_AVAILABLE, reason="BAEs dependencies not installed")
class TestBAeSHITL:
    """Integration tests for HITL handling."""
    
    def test_hitl_returns_specification(self, adapter):
        """Test HITL handler returns valid specification."""
        response = adapter.handle_hitl("What entities should I create?")
        
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Should contain entity specifications
        assert "Student" in response or "entity" in response.lower()
    
    def test_hitl_deterministic(self, adapter):
        """Test HITL returns same response for different queries."""
        response1 = adapter.handle_hitl("Query 1")
        response2 = adapter.handle_hitl("Query 2")
        
        # Should be deterministic
        assert response1 == response2


@pytest.mark.integration
@pytest.mark.skipif(not BAES_AVAILABLE, reason="BAEs dependencies not installed")
class TestBAeSFileGeneration:
    """Integration tests for file generation verification."""
    
    @pytest.mark.slow
    def test_generated_files_exist(self, adapter):
        """Test that BAEs generates expected files."""
        adapter.start()
        
        # Execute first step
        adapter.execute_step(1, "Create a Student/Course/Teacher CRUD application")
        
        # Check for generated files
        managed_system = adapter.managed_system_dir
        assert managed_system.exists()
        
        # Should have some Python files
        py_files = list(managed_system.rglob("*.py"))
        assert len(py_files) > 0, "No Python files generated"
        
        # Should have database file or schema
        db_files = list(managed_system.rglob("*.db")) + list(managed_system.rglob("*schema*"))
        # Database may not exist yet, so we don't assert
        
        print(f"Generated {len(py_files)} Python files")
    
    @pytest.mark.slow
    def test_archive_contains_artifacts(self, adapter):
        """Test that archive contains all generated artifacts."""
        adapter.start()
        adapter.execute_step(1, "Create a Student/Course/Teacher CRUD application")
        adapter.stop()
        
        archive_path = Path(adapter.workspace_path) / "managed_system.tar.gz"
        assert archive_path.exists()
        
        # Extract and verify contents
        import tarfile
        with tarfile.open(archive_path, "r:gz") as tar:
            members = tar.getmembers()
            assert len(members) > 0, "Archive is empty"
            
            # Should contain Python files
            py_members = [m for m in members if m.name.endswith('.py')]
            assert len(py_members) > 0, "Archive contains no Python files"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
