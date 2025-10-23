"""Integration tests for multi-sprint execution."""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from src.utils.isolation import create_sprint_workspace, create_final_symlink


@pytest.fixture
def mock_run_dir(tmp_path):
    """Create a mock run directory structure."""
    run_dir = tmp_path / "runs" / "baes" / "test-run-123"
    run_dir.mkdir(parents=True)
    return run_dir


def test_three_sprint_run(mock_run_dir):
    """Test complete 3-sprint scenario with all artifacts preserved."""
    # Create 3 sprints with deterministic data
    sprint_data = [
        {"sprint_num": 1, "tokens_in": 100, "tokens_out": 200, "api_calls": 5},
        {"sprint_num": 2, "tokens_in": 150, "tokens_out": 250, "api_calls": 7},
        {"sprint_num": 3, "tokens_in": 120, "tokens_out": 220, "api_calls": 6},
    ]
    
    for data in sprint_data:
        sprint_num = data["sprint_num"]
        
        # Create sprint workspace
        sprint_dir, workspace_dir = create_sprint_workspace(mock_run_dir, sprint_num)
        
        # Verify sprint directory structure
        assert sprint_dir.exists()
        assert (sprint_dir / "generated_artifacts").exists()
        assert (sprint_dir / "logs").exists()
        
        # Create mock artifacts
        artifact_file = sprint_dir / "generated_artifacts" / f"sprint_{sprint_num}_artifact.txt"
        artifact_file.write_text(f"Sprint {sprint_num} content")
        
        # Save sprint metadata
        metadata = {
            "sprint_number": sprint_num,
            "step_id": f"step_{sprint_num}",
            "framework": "baes",
            "run_id": "test-run-123",
            "status": "completed"
        }
        metadata_path = sprint_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Save sprint metrics
        metrics = {
            "tokens": {
                "input": data["tokens_in"],
                "output": data["tokens_out"],
                "cached": 0,
                "total": data["tokens_in"] + data["tokens_out"]
            },
            "api_calls": data["api_calls"],
            "execution_time": 10.5 + sprint_num
        }
        metrics_path = sprint_dir / "metrics.json"
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=2)
    
    # Create final symlink
    create_final_symlink(mock_run_dir, 3)
    
    # Verify all sprint directories exist
    for sprint_num in [1, 2, 3]:
        sprint_dir = mock_run_dir / f"sprint_{sprint_num:03d}"
        assert sprint_dir.exists(), f"Sprint {sprint_num} directory missing"
        assert (sprint_dir / "metadata.json").exists()
        assert (sprint_dir / "metrics.json").exists()
        assert (sprint_dir / "generated_artifacts").exists()
    
    # Verify final symlink points to last sprint
    final_link = mock_run_dir / "final"
    assert final_link.exists(), "Final symlink missing"
    assert final_link.is_symlink(), "Final is not a symlink"
    
    # Resolve symlink and verify it points to sprint_003
    resolved = final_link.resolve()
    assert resolved == (mock_run_dir / "sprint_003"), \
        f"Final symlink points to {resolved}, expected sprint_003"
    
    # Verify we can access artifacts through the symlink
    artifact_via_symlink = final_link / "generated_artifacts" / "sprint_3_artifact.txt"
    assert artifact_via_symlink.exists()
    assert artifact_via_symlink.read_text() == "Sprint 3 content"


def test_final_symlink_points_to_last_sprint(mock_run_dir):
    """Test that final/ symlink points to last successful sprint."""
    # Create 2 sprints
    for sprint_num in [1, 2]:
        sprint_dir, _ = create_sprint_workspace(mock_run_dir, sprint_num)
        
        # Create a marker file
        marker = sprint_dir / "generated_artifacts" / f"marker_{sprint_num}.txt"
        marker.write_text(f"Sprint {sprint_num}")
    
    # Create final symlink to sprint 2
    create_final_symlink(mock_run_dir, 2)
    
    # Verify symlink resolution
    final_link = mock_run_dir / "final"
    assert final_link.is_symlink()
    
    resolved_path = final_link.resolve()
    assert resolved_path.name == "sprint_002"
    
    # Verify we can read the correct marker file
    marker_via_link = final_link / "generated_artifacts" / "marker_2.txt"
    assert marker_via_link.exists()
    assert marker_via_link.read_text() == "Sprint 2"


def test_cumulative_metrics_generation(mock_run_dir):
    """Test that cumulative metrics are correctly aggregated."""
    from src.orchestrator.runner import OrchestratorRunner
    
    # Create a runner instance
    runner = OrchestratorRunner("baes", run_id="test-run-123")
    
    # Mock sprint results
    sprint_results = [
        {"sprint_num": 1, "step_id": "1", "status": "completed", 
         "tokens_in": 100, "tokens_out": 200, "api_calls": 5, "execution_time": 10.0},
        {"sprint_num": 2, "step_id": "2", "status": "completed",
         "tokens_in": 150, "tokens_out": 250, "api_calls": 7, "execution_time": 12.0},
        {"sprint_num": 3, "step_id": "3", "status": "completed",
         "tokens_in": 120, "tokens_out": 220, "api_calls": 6, "execution_time": 11.0},
    ]
    
    # Generate cumulative metrics
    runner._create_cumulative_metrics(mock_run_dir, sprint_results)
    
    # Verify summary directory and file exist
    summary_dir = mock_run_dir / "summary"
    assert summary_dir.exists()
    
    cumulative_file = summary_dir / "metrics_cumulative.json"
    assert cumulative_file.exists()
    
    # Load and verify cumulative metrics
    with open(cumulative_file, 'r') as f:
        cumulative = json.load(f)
    
    assert cumulative["total_sprints"] == 3
    assert cumulative["cumulative"]["tokens_in"] == 370  # 100+150+120
    assert cumulative["cumulative"]["tokens_out"] == 670  # 200+250+220
    assert cumulative["cumulative"]["tokens_total"] == 1040
    assert cumulative["cumulative"]["api_calls"] == 18  # 5+7+6
    assert cumulative["cumulative"]["execution_time"] == 33.0  # 10+12+11
    
    # Verify averages
    assert cumulative["sprint_efficiency"]["tokens_per_sprint_avg"] == pytest.approx(1040/3)
    assert cumulative["sprint_efficiency"]["api_calls_per_sprint_avg"] == pytest.approx(18/3)
    
    # Verify trend is calculated
    assert "tokens_trend" in cumulative["sprint_efficiency"]
    assert cumulative["sprint_efficiency"]["tokens_trend"] in ["increasing", "decreasing", "stable"]


def test_adapters_receive_previous_sprint_artifacts(mock_run_dir):
    """Test that adapters receive previous_sprint_artifacts property correctly."""
    from src.adapters.baes_adapter import BAeSAdapter
    from src.adapters.chatdev_adapter import ChatDevAdapter
    from src.adapters.ghspec_adapter import GHSpecAdapter
    
    # Create sprint 1 with artifacts
    sprint_1_dir, workspace_1 = create_sprint_workspace(mock_run_dir, 1)
    artifact_1 = sprint_1_dir / "generated_artifacts" / "code.py"
    artifact_1.write_text("# Sprint 1 code")
    
    # Test BAeS adapter for sprint 1 (no previous artifacts)
    config = {"api_port": 8100, "ui_port": 8600, "commit_hash": "abc123"}
    adapter_1 = BAeSAdapter(
        config=config,
        run_id="test-run-123",
        workspace_path=str(workspace_1),
        sprint_num=1,
        run_dir=mock_run_dir
    )
    
    assert adapter_1.sprint_num == 1
    assert adapter_1.run_dir == mock_run_dir
    assert adapter_1.previous_sprint_artifacts is None, \
        "Sprint 1 should have no previous artifacts"
    
    # Create sprint 2
    sprint_2_dir, workspace_2 = create_sprint_workspace(mock_run_dir, 2)
    
    # Test adapter for sprint 2 (should have previous artifacts)
    adapter_2 = BAeSAdapter(
        config=config,
        run_id="test-run-123",
        workspace_path=str(workspace_2),
        sprint_num=2,
        run_dir=mock_run_dir
    )
    
    assert adapter_2.sprint_num == 2
    assert adapter_2.previous_sprint_artifacts is not None, \
        "Sprint 2 should have previous artifacts"
    assert adapter_2.previous_sprint_artifacts == (sprint_1_dir / "generated_artifacts"), \
        f"Previous artifacts path incorrect: {adapter_2.previous_sprint_artifacts}"
    
    # Verify we can access previous sprint artifacts
    prev_code = adapter_2.previous_sprint_artifacts / "code.py"
    assert prev_code.exists()
    assert prev_code.read_text() == "# Sprint 1 code"
    
    # Test ChatDev adapter
    adapter_chatdev = ChatDevAdapter(
        config=config,
        run_id="test-run-123",
        workspace_path=str(workspace_2),
        sprint_num=2,
        run_dir=mock_run_dir
    )
    assert adapter_chatdev.previous_sprint_artifacts == (sprint_1_dir / "generated_artifacts")
    
    # Test GHSpec adapter
    adapter_ghspec = GHSpecAdapter(
        config=config,
        run_id="test-run-123",
        workspace_path=str(workspace_2),
        sprint_num=2,
        run_dir=mock_run_dir
    )
    assert adapter_ghspec.previous_sprint_artifacts == (sprint_1_dir / "generated_artifacts")


def test_sprint_log_dir_property(mock_run_dir):
    """Test that adapters have correct sprint_log_dir property."""
    from src.adapters.baes_adapter import BAeSAdapter
    
    # Create sprint 2
    sprint_2_dir, workspace_2 = create_sprint_workspace(mock_run_dir, 2)
    
    config = {"api_port": 8100, "ui_port": 8600, "commit_hash": "abc123"}
    adapter = BAeSAdapter(
        config=config,
        run_id="test-run-123",
        workspace_path=str(workspace_2),
        sprint_num=2,
        run_dir=mock_run_dir
    )
    
    # Verify sprint_log_dir points to correct location
    expected_log_dir = sprint_2_dir / "logs"
    assert adapter.sprint_log_dir == expected_log_dir
    assert adapter.sprint_log_dir.exists()

