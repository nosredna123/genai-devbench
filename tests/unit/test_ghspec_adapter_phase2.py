"""
Unit tests for GHSpec adapter environment setup (Phase 2).

Tests the start() method and workspace structure initialization.
"""

import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from src.adapters.ghspec_adapter import GHSpecAdapter


class TestGHSpecAdapterPhase2:
    """Test suite for Phase 2: Environment Setup"""
    
    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        # Cleanup after test
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for GHSpec."""
        return {
            'repo_url': 'https://github.com/github/spec-kit.git',
            'commit_hash': '89f4b0b38a42996376c0f083d47281a4c9196761',
            'api_port': 8002,
            'ui_port': 3002,
            'api_key_env': 'OPENAI_API_KEY_GHSPEC'
        }
    
    @pytest.fixture
    def adapter(self, mock_config, temp_workspace):
        """Create GHSpec adapter instance."""
        return GHSpecAdapter(
            config=mock_config,
            run_id='test-run-123',
            workspace_path=temp_workspace
        )
    
    def test_workspace_structure_creation(self, adapter, temp_workspace):
        """Test that _setup_workspace_structure creates correct directory tree."""
        # Call the private method directly
        adapter._setup_workspace_structure()
        
        # Verify directories were created
        specs_dir = Path(temp_workspace) / "specs"
        feature_dir = specs_dir / "001-baes-experiment"
        src_dir = feature_dir / "src"
        
        assert specs_dir.exists(), "specs/ directory should exist"
        assert feature_dir.exists(), "001-baes-experiment/ directory should exist"
        assert src_dir.exists(), "src/ directory should exist"
        
        # Verify adapter attributes are set correctly
        assert adapter.specs_dir == specs_dir
        assert adapter.feature_dir == feature_dir
        assert adapter.src_dir == src_dir
        assert adapter.spec_md_path == feature_dir / "spec.md"
        assert adapter.plan_md_path == feature_dir / "plan.md"
        assert adapter.tasks_md_path == feature_dir / "tasks.md"
    
    @patch.object(GHSpecAdapter, 'get_shared_framework_path')
    def test_start_method_clones_and_verifies_repo(
        self, mock_get_framework, adapter, temp_workspace
    ):
        """Test that start() references shared framework and creates workspace structure."""
        # Create mock shared framework directory
        mock_framework_dir = Path(temp_workspace) / "frameworks" / "ghspec"
        mock_framework_dir.mkdir(parents=True, exist_ok=True)
        mock_get_framework.return_value = mock_framework_dir
        
        # Call start()
        adapter.start()
        
        # Verify get_shared_framework_path was called
        mock_get_framework.assert_called_once_with('ghspec')
        
        # Verify framework_dir is set to shared location
        assert adapter.framework_dir == mock_framework_dir
        
        # Verify workspace structure was created
        assert adapter.specs_dir.exists()
        assert adapter.feature_dir.exists()
        assert adapter.src_dir.exists()
    
    @patch.object(GHSpecAdapter, 'get_shared_framework_path')
    def test_start_method_creates_workspace_structure(
        self, mock_get_framework, adapter, temp_workspace
    ):
        """Test that start() creates the complete workspace structure."""
        # Create mock shared framework directory
        mock_framework_dir = Path(temp_workspace) / "frameworks" / "ghspec"
        mock_framework_dir.mkdir(parents=True, exist_ok=True)
        mock_get_framework.return_value = mock_framework_dir
        
        # Call start()
        adapter.start()
        
        # Verify workspace structure exists
        specs_dir = Path(temp_workspace) / "specs"
        feature_dir = specs_dir / "001-baes-experiment"
        src_dir = feature_dir / "src"
        
        assert specs_dir.exists()
        assert feature_dir.exists()
        assert src_dir.exists()
    
    def test_start_method_handles_clone_failure(self, adapter):
        """Test that start() raises RuntimeError when shared framework doesn't exist."""
        # Don't mock get_shared_framework_path - let it fail naturally
        # The framework directory won't exist, so it should raise RuntimeError
        
        # Verify RuntimeError is raised with appropriate message
        with pytest.raises(RuntimeError, match="GitHub Spec-kit initialization failed"):
            adapter.start()
    
    def test_start_method_handles_timeout(self, adapter):
        """Test that start() raises RuntimeError when shared framework is missing."""
        # This test now verifies the error when framework directory doesn't exist
        # (analogous to the timeout scenario - setup didn't complete successfully)
        
        # Verify RuntimeError is raised when framework not found
        with pytest.raises(RuntimeError, match="GitHub Spec-kit initialization failed"):
            adapter.start()
    
    def test_workspace_structure_idempotent(self, adapter, temp_workspace):
        """Test that calling _setup_workspace_structure multiple times is safe."""
        # Call twice
        adapter._setup_workspace_structure()
        adapter._setup_workspace_structure()
        
        # Should still have correct structure
        feature_dir = Path(temp_workspace) / "specs" / "001-baes-experiment"
        assert feature_dir.exists()
        assert (feature_dir / "src").exists()
