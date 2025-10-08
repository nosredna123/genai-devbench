"""
Integration test for ChatDev adapter - single step execution.

Tests T071: ChatDev Single-Step Test
Verifies that the ChatDev adapter can execute one step successfully.

This test validates:
1. Environment setup (venv creation, dependency installation)
2. Command execution (run.py invocation)
3. Output generation (WareHouse directory)
4. Metric collection (tokens > 0 if available)
5. No crashes or timeouts
"""

import os
import pytest
import tempfile
import shutil
from pathlib import Path
from src.adapters.chatdev_adapter import ChatDevAdapter
from src.orchestrator.config_loader import load_config


@pytest.fixture
def test_config():
    """Load experiment configuration for testing."""
    config = load_config()
    return config['frameworks']['chatdev']


@pytest.fixture
def test_workspace():
    """Create temporary workspace for testing."""
    temp_dir = tempfile.mkdtemp(prefix="chatdev_test_")
    yield temp_dir
    # Cleanup after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def chatdev_adapter(test_config, test_workspace):
    """Initialize ChatDev adapter for testing."""
    run_id = "test_chatdev_single_step"
    adapter = ChatDevAdapter(
        config=test_config,
        run_id=run_id,
        workspace_path=test_workspace
    )
    return adapter


def test_chatdev_initialization(chatdev_adapter):
    """
    Test ChatDev adapter initialization.
    
    Verifies:
    - Repository cloning
    - Commit verification
    - Virtual environment creation
    - Dependency installation
    """
    # Start adapter (clone + setup)
    chatdev_adapter.start()
    
    # Verify framework directory exists
    assert chatdev_adapter.framework_dir.exists(), "Framework directory not created"
    
    # Verify run.py exists
    run_py = chatdev_adapter.framework_dir / "run.py"
    assert run_py.exists(), "run.py not found"
    
    # Verify virtual environment created
    assert chatdev_adapter.venv_path.exists(), "Virtual environment not created"
    
    # Verify Python is accessible
    assert chatdev_adapter.python_path.exists(), "Python executable not found"
    
    print(f"✓ ChatDev initialized successfully")
    print(f"  Framework dir: {chatdev_adapter.framework_dir}")
    print(f"  Python path: {chatdev_adapter.python_path}")


def test_chatdev_health_check(chatdev_adapter):
    """
    Test ChatDev health check.
    
    Verifies that health_check() returns True after initialization.
    """
    chatdev_adapter.start()
    
    health = chatdev_adapter.health_check()
    assert health is True, "Health check failed after initialization"
    
    print("✓ Health check passed")


@pytest.mark.slow  # This test takes ~10 minutes
@pytest.mark.skipif(
    not os.getenv('OPENAI_API_KEY_CHATDEV'),
    reason="OPENAI_API_KEY_CHATDEV not set"
)
def test_chatdev_single_step_execution(chatdev_adapter):
    """
    Test single step execution with ChatDev.
    
    Executes a simple software generation task and verifies:
    - Command completes without timeout
    - Exit code is 0 (success)
    - Output directory created in WareHouse/
    - Metrics returned (even if tokens are 0, will be verified by Usage API)
    
    WARNING: This test makes real OpenAI API calls and may take 10+ minutes.
    """
    # Initialize adapter
    chatdev_adapter.start()
    
    # Simple test task (should complete quickly)
    test_task = "Create a simple Python calculator with add and subtract functions"
    
    # Execute step 1
    result = chatdev_adapter.execute_step(
        step_num=1,
        command_text=test_task
    )
    
    # Verify execution completed
    assert result is not None, "execute_step returned None"
    assert 'success' in result, "Result missing 'success' key"
    assert 'duration_seconds' in result, "Result missing 'duration_seconds' key"
    assert 'tokens_in' in result, "Result missing 'tokens_in' key"
    assert 'tokens_out' in result, "Result missing 'tokens_out' key"
    assert 'hitl_count' in result, "Result missing 'hitl_count' key"
    
    # Verify success
    assert result['success'] is True, f"Execution failed: {result.get('error', 'Unknown error')}"
    
    # Verify timing
    assert result['duration_seconds'] > 0, "Duration should be > 0"
    assert result['duration_seconds'] < 600, "Duration exceeded 10-minute timeout"
    
    # Verify HITL count (should be 0 for Default config)
    assert result['hitl_count'] == 0, "HITL count should be 0 for Default config"
    
    # Token counts may be 0 (no direct logging), will be verified by Usage API
    # Just verify they are non-negative integers
    assert isinstance(result['tokens_in'], int) and result['tokens_in'] >= 0
    assert isinstance(result['tokens_out'], int) and result['tokens_out'] >= 0
    
    # Verify output directory created in WareHouse/
    warehouse_dir = chatdev_adapter.framework_dir / "WareHouse"
    assert warehouse_dir.exists(), "WareHouse directory not created"
    
    # Find generated project directory
    project_dirs = list(warehouse_dir.glob("BAEs_Step1_*"))
    assert len(project_dirs) > 0, "No project directory created in WareHouse"
    
    project_dir = project_dirs[0]
    print(f"✓ ChatDev execution successful")
    print(f"  Duration: {result['duration_seconds']:.2f}s")
    print(f"  Tokens: {result['tokens_in']} in, {result['tokens_out']} out")
    print(f"  HITL: {result['hitl_count']}")
    print(f"  Output: {project_dir}")
    
    # Verify key files exist in output
    assert (project_dir / "meta.txt").exists(), "meta.txt not found in output"
    
    # Cleanup
    chatdev_adapter.stop()


def test_chatdev_graceful_shutdown(chatdev_adapter):
    """
    Test ChatDev graceful shutdown.
    
    Verifies that stop() method executes without errors.
    """
    chatdev_adapter.start()
    
    # Should not raise exception
    chatdev_adapter.stop()
    
    print("✓ Graceful shutdown completed")


if __name__ == "__main__":
    """
    Run tests with pytest.
    
    Quick tests (< 1 minute):
        pytest tests/integration/test_chatdev_single_step.py -v
    
    Include slow tests (with API calls, ~10 minutes):
        pytest tests/integration/test_chatdev_single_step.py -v --run-slow
        
    With API key check:
        OPENAI_API_KEY_CHATDEV=sk-... pytest tests/integration/test_chatdev_single_step.py -v --run-slow
    """
    pytest.main([__file__, "-v", "-s"])
