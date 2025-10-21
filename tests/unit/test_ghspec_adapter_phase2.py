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
    
    @patch('subprocess.run')
    @patch.object(GHSpecAdapter, 'verify_commit_hash')
    def test_start_method_clones_and_verifies_repo(
        self, mock_verify, mock_subprocess, adapter, temp_workspace
    ):
        """Test that start() clones repo, checks out commit, and verifies hash."""
        # Mock successful subprocess calls
        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_verify.return_value = None
        
        # Call start()
        adapter.start()
        
        # Verify git clone was called
        clone_call = mock_subprocess.call_args_list[0]
        assert clone_call[0][0][0] == 'git'
        assert clone_call[0][0][1] == 'clone'
        assert 'spec-kit.git' in clone_call[0][0][2]
        
        # Verify git checkout was called
        checkout_call = mock_subprocess.call_args_list[1]
        assert checkout_call[0][0][0] == 'git'
        assert checkout_call[0][0][1] == 'checkout'
        assert checkout_call[0][0][2] == '89f4b0b38a42996376c0f083d47281a4c9196761'
        
        # Verify commit hash verification was called
        mock_verify.assert_called_once()
        
        # Verify framework_dir is set
        assert adapter.framework_dir == Path(temp_workspace) / "ghspec_framework"
    
    @patch('subprocess.run')
    @patch.object(GHSpecAdapter, 'verify_commit_hash')
    def test_start_method_creates_workspace_structure(
        self, mock_verify, mock_subprocess, adapter, temp_workspace
    ):
        """Test that start() creates the complete workspace structure."""
        # Mock successful subprocess calls
        mock_subprocess.return_value = MagicMock(returncode=0)
        mock_verify.return_value = None
        
        # Call start()
        adapter.start()
        
        # Verify workspace structure exists
        specs_dir = Path(temp_workspace) / "specs"
        feature_dir = specs_dir / "001-baes-experiment"
        src_dir = feature_dir / "src"
        
        assert specs_dir.exists()
        assert feature_dir.exists()
        assert src_dir.exists()
    
    @patch('subprocess.run')
    def test_start_method_handles_clone_failure(self, mock_subprocess, adapter):
        """Test that start() raises RuntimeError when git clone fails."""
        # Mock failed subprocess call
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=['git', 'clone'],
            stderr=b'fatal: repository not found'
        )
        
        # Verify RuntimeError is raised (error message now comes from base adapter)
        with pytest.raises(RuntimeError, match="Failed to setup ghspec repository"):
            adapter.start()
    
    @patch('subprocess.run')
    def test_start_method_handles_timeout(self, mock_subprocess, adapter):
        """Test that start() raises RuntimeError when git clone times out."""
        # Mock timeout
        mock_subprocess.side_effect = subprocess.TimeoutExpired(
            cmd=['git', 'clone'],
            timeout=120
        )
        
        # Verify RuntimeError is raised (error message now comes from base adapter)
        with pytest.raises(RuntimeError, match="ghspec repository setup timed out"):
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
