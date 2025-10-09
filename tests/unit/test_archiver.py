"""
Unit tests for the Archiver component.

Tests archiving, hash computation, metadata creation, and verification.
"""

import pytest
import tempfile
import shutil
import json
import tarfile
from pathlib import Path
from src.orchestrator.archiver import Archiver


@pytest.fixture
def temp_run_dir():
    """Create temporary run directory."""
    temp_dir = tempfile.mkdtemp(prefix="archiver_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sample_workspace(temp_run_dir):
    """Create sample workspace with files."""
    workspace_dir = temp_run_dir / "workspace"
    workspace_dir.mkdir()
    
    # Create some sample files
    (workspace_dir / "file1.txt").write_text("Sample content 1")
    (workspace_dir / "file2.txt").write_text("Sample content 2")
    
    # Create subdirectory with files
    subdir = workspace_dir / "subdir"
    subdir.mkdir()
    (subdir / "file3.txt").write_text("Sample content 3")
    
    return workspace_dir


@pytest.fixture
def sample_metrics(temp_run_dir):
    """Create sample metrics.json file."""
    metrics_file = temp_run_dir / "metrics.json"
    metrics_data = {
        "step_1": {"tokens_in": 100, "tokens_out": 200},
        "step_2": {"tokens_in": 150, "tokens_out": 250}
    }
    with open(metrics_file, 'w') as f:
        json.dump(metrics_data, f, indent=2)
    
    return metrics_file


@pytest.fixture
def sample_logs(temp_run_dir):
    """Create sample log files."""
    logs = {}
    
    log1 = temp_run_dir / "execution.log"
    log1.write_text("Log line 1\nLog line 2\n")
    logs['execution.log'] = log1
    
    log2 = temp_run_dir / "error.log"
    log2.write_text("Error line 1\n")
    logs['error.log'] = log2
    
    return logs


@pytest.fixture
def archiver(temp_run_dir):
    """Create Archiver instance."""
    run_id = "test_archiver_run"
    return Archiver(run_id=run_id, run_dir=temp_run_dir)


class TestArchiverInitialization:
    """Test Archiver initialization."""
    
    def test_init_creates_archiver(self, temp_run_dir):
        """Test that Archiver can be initialized."""
        run_id = "test_run_123"
        archiver = Archiver(run_id=run_id, run_dir=temp_run_dir)
        
        assert archiver.run_id == run_id
        assert archiver.run_dir == temp_run_dir
    
    def test_init_with_different_paths(self):
        """Test initialization with various path types."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test with string path
            archiver1 = Archiver("run1", Path(temp_dir))
            assert archiver1.run_dir.exists()
            
            # Test with Path object
            archiver2 = Archiver("run2", Path(temp_dir))
            assert archiver2.run_dir.exists()


class TestArchiveCreation:
    """Test archive creation functionality."""
    
    def test_create_archive_basic(self, archiver, sample_workspace, sample_metrics, sample_logs):
        """Test basic archive creation with all components."""
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=sample_metrics,
            logs=sample_logs
        )
        
        # Verify archive exists
        assert archive_path.exists()
        assert archive_path.name == "run.tar.gz"
        assert archive_path.stat().st_size > 0
        
        # Verify archive is valid tar.gz
        assert tarfile.is_tarfile(archive_path)
        
        # Verify contents
        with tarfile.open(archive_path, 'r:gz') as tar:
            members = tar.getnames()
            
            # Check workspace is archived
            assert any('workspace' in m for m in members)
            assert any('workspace/file1.txt' in m for m in members)
            assert any('workspace/file2.txt' in m for m in members)
            assert any('workspace/subdir/file3.txt' in m for m in members)
            
            # Check metrics is archived
            assert 'metrics.json' in members
            
            # Check logs are archived
            assert 'execution.log' in members
            assert 'error.log' in members
    
    def test_create_archive_workspace_only(self, archiver, sample_workspace, temp_run_dir):
        """Test archive creation with only workspace."""
        # Create empty/non-existent files
        metrics_file = temp_run_dir / "nonexistent_metrics.json"
        logs = {}
        
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=metrics_file,
            logs=logs
        )
        
        assert archive_path.exists()
        
        with tarfile.open(archive_path, 'r:gz') as tar:
            members = tar.getnames()
            assert any('workspace' in m for m in members)
            assert 'metrics.json' not in members
    
    def test_create_archive_preserves_structure(self, archiver, sample_workspace, sample_metrics, sample_logs):
        """Test that archive preserves directory structure."""
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=sample_metrics,
            logs=sample_logs
        )
        
        # Extract and verify structure
        extract_dir = archiver.run_dir / "extracted"
        extract_dir.mkdir()
        
        with tarfile.open(archive_path, 'r:gz') as tar:
            tar.extractall(extract_dir)
        
        # Verify structure
        assert (extract_dir / "workspace" / "file1.txt").exists()
        assert (extract_dir / "workspace" / "subdir" / "file3.txt").exists()
        assert (extract_dir / "metrics.json").exists()
        assert (extract_dir / "execution.log").exists()
        
        # Verify content
        content = (extract_dir / "workspace" / "file1.txt").read_text()
        assert content == "Sample content 1"
    
    def test_create_archive_returns_correct_path(self, archiver, sample_workspace, sample_metrics, sample_logs):
        """Test that create_archive returns the correct path."""
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=sample_metrics,
            logs=sample_logs
        )
        
        assert archive_path == archiver.run_dir / "run.tar.gz"
        assert archive_path.parent == archiver.run_dir


class TestHashComputation:
    """Test hash computation functionality."""
    
    def test_compute_hash_basic(self, archiver, sample_workspace, sample_metrics, sample_logs):
        """Test basic hash computation."""
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=sample_metrics,
            logs=sample_logs
        )
        
        hash_value = archiver.compute_hash(archive_path)
        
        # Verify hash format
        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA-256 hex length
        assert all(c in '0123456789abcdef' for c in hash_value)
    
    def test_compute_hash_deterministic(self, archiver, sample_workspace, sample_metrics, sample_logs):
        """Test that hash computation is deterministic."""
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=sample_metrics,
            logs=sample_logs
        )
        
        hash1 = archiver.compute_hash(archive_path)
        hash2 = archiver.compute_hash(archive_path)
        
        assert hash1 == hash2
    
    def test_compute_hash_different_content(self, temp_run_dir):
        """Test that different content produces different hashes."""
        archiver = Archiver("test_run", temp_run_dir)
        
        # Create two different archives
        workspace1 = temp_run_dir / "workspace1"
        workspace1.mkdir()
        (workspace1 / "file.txt").write_text("Content A")
        
        workspace2 = temp_run_dir / "workspace2"
        workspace2.mkdir()
        (workspace2 / "file.txt").write_text("Content B")
        
        metrics = temp_run_dir / "metrics.json"
        metrics.write_text("{}")
        
        # Create first archive
        archive1 = archiver.create_archive(workspace1, metrics, {})
        hash1 = archiver.compute_hash(archive1)
        
        # Rename first archive
        archive1.rename(temp_run_dir / "run1.tar.gz")
        
        # Create second archive
        archive2 = archiver.create_archive(workspace2, metrics, {})
        hash2 = archiver.compute_hash(archive2)
        
        # Hashes should differ
        assert hash1 != hash2


class TestMetadataCreation:
    """Test metadata creation functionality."""
    
    def test_create_metadata_basic(self, archiver, sample_workspace, sample_metrics, sample_logs):
        """Test basic metadata creation."""
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=sample_metrics,
            logs=sample_logs
        )
        archive_hash = archiver.compute_hash(archive_path)
        
        metadata_path = archiver.create_metadata(
            archive_path=archive_path,
            archive_hash=archive_hash,
            framework="chatdev",
            commit_hash="abc123def456"
        )
        
        # Verify metadata file exists
        assert metadata_path.exists()
        assert metadata_path.name == "metadata.json"
        
        # Verify metadata content
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert metadata['run_id'] == archiver.run_id
        assert metadata['framework'] == "chatdev"
        assert metadata['framework_commit'] == "abc123def456"
        assert metadata['archive_path'] == "run.tar.gz"
        assert metadata['archive_hash'] == archive_hash
        assert metadata['archive_size_bytes'] == archive_path.stat().st_size
    
    def test_create_metadata_valid_json(self, archiver, sample_workspace, sample_metrics, sample_logs):
        """Test that metadata is valid JSON."""
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=sample_metrics,
            logs=sample_logs
        )
        archive_hash = archiver.compute_hash(archive_path)
        
        metadata_path = archiver.create_metadata(
            archive_path=archive_path,
            archive_hash=archive_hash,
            framework="test_framework",
            commit_hash="test_commit"
        )
        
        # Should not raise exception
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert isinstance(metadata, dict)
    
    def test_create_metadata_includes_size(self, archiver, sample_workspace, sample_metrics, sample_logs):
        """Test that metadata includes archive size."""
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=sample_metrics,
            logs=sample_logs
        )
        archive_hash = archiver.compute_hash(archive_path)
        
        metadata_path = archiver.create_metadata(
            archive_path=archive_path,
            archive_hash=archive_hash,
            framework="chatdev",
            commit_hash="abc123"
        )
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert 'archive_size_bytes' in metadata
        assert metadata['archive_size_bytes'] > 0
        assert metadata['archive_size_bytes'] == archive_path.stat().st_size


class TestCommitInfo:
    """Test commit info saving functionality."""
    
    def test_save_commit_info(self, archiver):
        """Test saving commit information."""
        commit_hash = "abc123def456789"
        commit_file = archiver.save_commit_info(commit_hash)
        
        assert commit_file.exists()
        assert commit_file.name == "commit.txt"
        
        content = commit_file.read_text()
        assert content == commit_hash
    
    def test_save_commit_info_overwrites(self, archiver):
        """Test that saving commit info overwrites existing file."""
        # Save first commit
        archiver.save_commit_info("commit1")
        
        # Save second commit (should overwrite)
        commit_file = archiver.save_commit_info("commit2")
        
        content = commit_file.read_text()
        assert content == "commit2"


class TestArchiveVerification:
    """Test archive verification functionality."""
    
    def test_verify_archive_success(self, archiver, sample_workspace, sample_metrics, sample_logs):
        """Test successful archive verification."""
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=sample_metrics,
            logs=sample_logs
        )
        expected_hash = archiver.compute_hash(archive_path)
        
        result = archiver.verify_archive(archive_path, expected_hash)
        
        assert result is True
    
    def test_verify_archive_failure(self, archiver, sample_workspace, sample_metrics, sample_logs):
        """Test failed archive verification with wrong hash."""
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=sample_metrics,
            logs=sample_logs
        )
        
        # Use incorrect hash
        wrong_hash = "0" * 64
        
        result = archiver.verify_archive(archive_path, wrong_hash)
        
        assert result is False
    
    def test_verify_archive_detects_modification(self, archiver, sample_workspace, sample_metrics, sample_logs):
        """Test that verification detects archive modification."""
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=sample_metrics,
            logs=sample_logs
        )
        original_hash = archiver.compute_hash(archive_path)
        
        # Modify archive by appending data
        with open(archive_path, 'ab') as f:
            f.write(b"CORRUPTED DATA")
        
        # Verification should fail
        result = archiver.verify_archive(archive_path, original_hash)
        
        assert result is False


class TestArchiveIntegration:
    """Integration tests for complete archiving workflow."""
    
    def test_complete_workflow(self, archiver, sample_workspace, sample_metrics, sample_logs):
        """Test complete archiving workflow from creation to verification."""
        # Step 1: Create archive
        archive_path = archiver.create_archive(
            workspace_dir=sample_workspace,
            metrics_file=sample_metrics,
            logs=sample_logs
        )
        assert archive_path.exists()
        
        # Step 2: Compute hash
        archive_hash = archiver.compute_hash(archive_path)
        assert len(archive_hash) == 64
        
        # Step 3: Create metadata
        metadata_path = archiver.create_metadata(
            archive_path=archive_path,
            archive_hash=archive_hash,
            framework="chatdev",
            commit_hash="test_commit_abc123"
        )
        assert metadata_path.exists()
        
        # Step 4: Save commit info
        commit_file = archiver.save_commit_info("test_commit_abc123")
        assert commit_file.exists()
        
        # Step 5: Verify archive
        verification_result = archiver.verify_archive(archive_path, archive_hash)
        assert verification_result is True
        
        # Verify all artifacts exist
        assert (archiver.run_dir / "run.tar.gz").exists()
        assert (archiver.run_dir / "metadata.json").exists()
        assert (archiver.run_dir / "commit.txt").exists()
    
    def test_workflow_with_chatdev_outputs(self, temp_run_dir):
        """Test archiving workflow with ChatDev-like outputs."""
        archiver = Archiver("chatdev_run_123", temp_run_dir)
        
        # Create ChatDev-like workspace
        workspace = temp_run_dir / "chatdev_framework" / "WareHouse"
        workspace.mkdir(parents=True)
        
        # Create multiple step outputs
        for step in range(1, 7):
            step_dir = workspace / f"BAEs_Step{step}_TestProject"
            step_dir.mkdir()
            (step_dir / "meta.txt").write_text(f"Step {step} metadata")
            (step_dir / "main.py").write_text(f"# Step {step} code")
        
        # Create metrics
        metrics_file = temp_run_dir / "metrics.json"
        metrics = {
            f"step_{i}": {
                "tokens_in": i * 100,
                "tokens_out": i * 200,
                "duration_seconds": i * 60.5
            }
            for i in range(1, 7)
        }
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        # Create logs
        logs = {
            "execution.log": temp_run_dir / "execution.log",
            "error.log": temp_run_dir / "error.log"
        }
        for log_file in logs.values():
            log_file.write_text("Log content\n")
        
        # Run complete workflow
        archive_path = archiver.create_archive(
            workspace_dir=workspace.parent.parent,  # chatdev_framework
            metrics_file=metrics_file,
            logs=logs
        )
        
        # Verify archive contents
        with tarfile.open(archive_path, 'r:gz') as tar:
            members = tar.getnames()
            
            # Check all 6 steps are archived
            for step in range(1, 7):
                assert any(f"Step{step}" in m for m in members), f"Step {step} not in archive"
            
            # Check metrics and logs
            assert 'metrics.json' in members
            assert 'execution.log' in members
            assert 'error.log' in members
        
        # Verify metadata
        archive_hash = archiver.compute_hash(archive_path)
        metadata_path = archiver.create_metadata(
            archive_path=archive_path,
            archive_hash=archive_hash,
            framework="chatdev",
            commit_hash="52edb89997b4312ad27d8c54584d0a6c59940135"
        )
        
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        
        assert metadata['framework'] == "chatdev"
        assert metadata['run_id'] == "chatdev_run_123"
        assert metadata['archive_size_bytes'] > 0


if __name__ == "__main__":
    """
    Run archiver unit tests.
    
    Quick run:
        pytest tests/unit/test_archiver.py -v
    
    With coverage:
        pytest tests/unit/test_archiver.py -v --cov=src.orchestrator.archiver --cov-report=term-missing
    """
    pytest.main([__file__, "-v"])
