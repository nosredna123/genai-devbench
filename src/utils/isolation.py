"""
Workspace isolation utilities for experiment runs.

Provides functions to create and manage isolated workspaces per run.
"""

import shutil
import uuid
from pathlib import Path
from typing import Tuple
from src.utils.logger import get_logger

logger = get_logger(__name__)


def generate_run_id() -> str:
    """
    Generate a unique run identifier.
    
    Returns:
        UUID string for run identification
    """
    return str(uuid.uuid4())


def create_isolated_workspace(framework: str, run_id: str) -> Tuple[Path, Path]:
    """
    Create isolated workspace directory for a run.
    
    Args:
        framework: Framework name (baes, chatdev, ghspec)
        run_id: Unique run identifier
        
    Returns:
        Tuple of (run_dir, workspace_dir) Path objects
        
    Example:
        run_dir: runs/baes/550e8400-e29b-41d4-a716-446655440000/
        workspace_dir: runs/baes/550e8400-e29b-41d4-a716-446655440000/workspace/
    """
    run_dir = Path("runs") / framework / run_id
    workspace_dir = run_dir / "workspace"
    
    # Check for collision (should be astronomically rare with UUIDs)
    if run_dir.exists():
        logger.warning(
            f"Run directory already exists: {run_dir}. Appending suffix.",
            extra={'run_id': run_id, 'framework': framework}
        )
        # Append a suffix to avoid collision
        collision_id = str(uuid.uuid4())[:8]
        run_dir = Path("runs") / framework / f"{run_id}-{collision_id}"
        workspace_dir = run_dir / "workspace"
    
    # Create directories
    workspace_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(
        f"Created isolated workspace: {workspace_dir}",
        extra={'run_id': run_id, 'framework': framework}
    )
    
    return run_dir, workspace_dir


def cleanup_workspace(workspace_dir: Path, run_id: str) -> None:
    """
    Remove workspace directory after successful archival.
    
    This conserves disk space by deleting the original workspace
    after it has been safely archived in run.tar.gz.
    
    Args:
        workspace_dir: Path to workspace directory
        run_id: Run identifier for logging
        
    Raises:
        FileNotFoundError: If workspace doesn't exist
    """
    if not workspace_dir.exists():
        raise FileNotFoundError(f"Workspace not found: {workspace_dir}")
    
    shutil.rmtree(workspace_dir)
    
    logger.info(
        f"Cleaned up workspace: {workspace_dir}",
        extra={'run_id': run_id}
    )


def get_run_directory(framework: str, run_id: str) -> Path:
    """
    Get the run directory path for a given framework and run ID.
    
    Args:
        framework: Framework name
        run_id: Run identifier
        
    Returns:
        Path to run directory
    """
    return Path("runs") / framework / run_id


def ensure_runs_directory() -> None:
    """
    Ensure the top-level runs directory exists.
    
    Creates runs/ if it doesn't exist.
    """
    runs_dir = Path("runs")
    runs_dir.mkdir(exist_ok=True)
    logger.debug("Ensured runs directory exists")
