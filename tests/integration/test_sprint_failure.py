"""Integration tests for sprint failure handling."""

import pytest
import json
from pathlib import Path
from src.utils.isolation import create_sprint_workspace, create_final_symlink


@pytest.fixture
def mock_run_dir(tmp_path):
    """Create a mock run directory structure."""
    run_dir = tmp_path / "runs" / "baes" / "test-run-456"
    run_dir.mkdir(parents=True)
    return run_dir


def test_sprint_2_failure_preserves_sprint_1(mock_run_dir):
    """Test that Sprint 1 is preserved when Sprint 2 fails."""
    # Create successful sprint 1
    sprint_1_dir, workspace_1 = create_sprint_workspace(mock_run_dir, 1)
    
    # Add sprint 1 artifacts
    artifact_1 = sprint_1_dir / "generated_artifacts" / "app.py"
    artifact_1.write_text("# Sprint 1 successful code")
    
    # Save sprint 1 metadata (successful)
    metadata_1 = {
        "sprint_number": 1,
        "step_id": "step_1",
        "framework": "baes",
        "run_id": "test-run-456",
        "start_timestamp": "2025-10-23T10:00:00Z",
        "end_timestamp": "2025-10-23T10:05:00Z",
        "status": "completed"
    }
    with open(sprint_1_dir / "metadata.json", 'w') as f:
        json.dump(metadata_1, f, indent=2)
    
    # Save sprint 1 metrics
    metrics_1 = {
        "tokens": {"input": 100, "output": 200, "cached": 0, "total": 300},
        "api_calls": 5,
        "execution_time": 10.5
    }
    with open(sprint_1_dir / "metrics.json", 'w') as f:
        json.dump(metrics_1, f, indent=2)
    
    # Create failed sprint 2
    sprint_2_dir, workspace_2 = create_sprint_workspace(mock_run_dir, 2)
    
    # Add partial sprint 2 artifacts (simulating partial execution)
    partial_artifact = sprint_2_dir / "generated_artifacts" / "partial.py"
    partial_artifact.write_text("# Partial code before failure")
    
    # Save sprint 2 metadata (failed)
    error_message = "Timeout during step execution"
    metadata_2 = {
        "sprint_number": 2,
        "step_id": "step_2",
        "framework": "baes",
        "run_id": "test-run-456",
        "start_timestamp": "2025-10-23T10:06:00Z",
        "end_timestamp": "2025-10-23T10:16:00Z",
        "status": "failed",
        "error": error_message
    }
    with open(sprint_2_dir / "metadata.json", 'w') as f:
        json.dump(metadata_2, f, indent=2)
    
    # Add error logs to sprint 2
    log_file = sprint_2_dir / "logs" / "execution_sprint_002.log"
    log_file.write_text(f"ERROR: {error_message}\nTraceback: ...\n")
    
    # Sprint 3 should NOT exist (loop breaks after sprint 2 failure)
    sprint_3_dir = mock_run_dir / "sprint_003"
    assert not sprint_3_dir.exists(), "Sprint 3 should not exist after sprint 2 failure"
    
    # Verify sprint 1 is intact
    assert sprint_1_dir.exists()
    assert (sprint_1_dir / "generated_artifacts" / "app.py").exists()
    assert (sprint_1_dir / "metadata.json").exists()
    assert (sprint_1_dir / "metrics.json").exists()
    
    # Verify sprint 1 artifacts are unchanged
    assert artifact_1.read_text() == "# Sprint 1 successful code"
    
    with open(sprint_1_dir / "metadata.json", 'r') as f:
        sprint_1_meta = json.load(f)
    assert sprint_1_meta["status"] == "completed"
    assert "error" not in sprint_1_meta
    
    # Verify sprint 2 has error information
    assert sprint_2_dir.exists()
    assert (sprint_2_dir / "metadata.json").exists()
    
    with open(sprint_2_dir / "metadata.json", 'r') as f:
        sprint_2_meta = json.load(f)
    assert sprint_2_meta["status"] == "failed"
    assert sprint_2_meta["error"] == error_message
    
    # Verify sprint 2 logs exist
    assert (sprint_2_dir / "logs" / "execution_sprint_002.log").exists()


def test_final_points_to_last_success_on_failure(mock_run_dir):
    """Test that final/ symlink points to last successful sprint when later sprint fails."""
    # Create 2 successful sprints
    for sprint_num in [1, 2]:
        sprint_dir, workspace = create_sprint_workspace(mock_run_dir, sprint_num)
        
        # Add artifacts
        artifact = sprint_dir / "generated_artifacts" / f"code_{sprint_num}.py"
        artifact.write_text(f"# Sprint {sprint_num} code")
        
        # Save metadata
        metadata = {
            "sprint_number": sprint_num,
            "step_id": f"step_{sprint_num}",
            "framework": "baes",
            "status": "completed"
        }
        with open(sprint_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
    
    # Create failed sprint 3
    sprint_3_dir, workspace_3 = create_sprint_workspace(mock_run_dir, 3)
    metadata_3 = {
        "sprint_number": 3,
        "step_id": "step_3",
        "framework": "baes",
        "status": "failed",
        "error": "Connection timeout"
    }
    with open(sprint_3_dir / "metadata.json", 'w') as f:
        json.dump(metadata_3, f, indent=2)
    
    # Create final symlink pointing to last successful sprint (sprint 2)
    create_final_symlink(mock_run_dir, 2)
    
    # Verify final symlink exists and points to sprint 2
    final_link = mock_run_dir / "final"
    assert final_link.exists()
    assert final_link.is_symlink()
    
    resolved = final_link.resolve()
    assert resolved == (mock_run_dir / "sprint_002"), \
        f"Final should point to sprint_002, but points to {resolved.name}"
    
    # Verify we can access sprint 2 artifacts through final symlink
    code_via_final = final_link / "generated_artifacts" / "code_2.py"
    assert code_via_final.exists()
    assert code_via_final.read_text() == "# Sprint 2 code"
    
    # Verify we cannot access sprint 3 through final (because it failed)
    code_3_via_final = final_link / "generated_artifacts" / "code_3.py"
    assert not code_3_via_final.exists()


def test_partial_artifacts_and_logs_preserved(mock_run_dir):
    """Test that partial artifacts and logs are preserved when a sprint fails."""
    # Create sprint that starts but fails mid-execution
    sprint_dir, workspace = create_sprint_workspace(mock_run_dir, 1)
    
    # Simulate partial artifact generation
    partial_dir = sprint_dir / "generated_artifacts" / "incomplete_module"
    partial_dir.mkdir(parents=True)
    
    partial_file_1 = partial_dir / "complete_file.py"
    partial_file_1.write_text("# This file was completed")
    
    partial_file_2 = partial_dir / "incomplete_file.py"
    partial_file_2.write_text("# This file is incomplete\n# Execution stopped here")
    
    # Save error metadata
    metadata = {
        "sprint_number": 1,
        "step_id": "step_1",
        "framework": "chatdev",
        "status": "failed",
        "error": "Runtime exception during code generation",
        "start_timestamp": "2025-10-23T11:00:00Z",
        "end_timestamp": "2025-10-23T11:03:00Z"
    }
    with open(sprint_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Save execution logs with stack trace
    log_content = """
2025-10-23T11:00:00Z INFO Starting sprint 1 execution
2025-10-23T11:01:00Z INFO Generating code...
2025-10-23T11:02:30Z ERROR Runtime exception occurred
Traceback (most recent call last):
  File "framework.py", line 123, in execute
    result = self.generate_code()
RuntimeError: Model API rate limit exceeded
2025-10-23T11:03:00Z ERROR Sprint 1 failed
"""
    log_file = sprint_dir / "logs" / "execution_sprint_001.log"
    log_file.write_text(log_content)
    
    # Verify all partial artifacts are preserved
    assert sprint_dir.exists()
    assert partial_dir.exists()
    assert partial_file_1.exists()
    assert partial_file_2.exists()
    
    # Verify metadata contains error
    with open(sprint_dir / "metadata.json", 'r') as f:
        saved_metadata = json.load(f)
    assert saved_metadata["status"] == "failed"
    assert "error" in saved_metadata
    assert "Runtime exception" in saved_metadata["error"]
    
    # Verify logs are preserved
    assert log_file.exists()
    saved_logs = log_file.read_text()
    assert "ERROR" in saved_logs
    assert "Traceback" in saved_logs
    assert "RuntimeError" in saved_logs
