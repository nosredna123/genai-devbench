from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Tuple


def sprint_dir(run_dir: Path, sprint_num: int) -> Path:
    return run_dir / f"sprint_{sprint_num:03d}"


def create_sprint_workspace(run_dir: Path, sprint_num: int) -> Tuple[Path, Path]:
    """Create sprint directory structure and return (sprint_dir, artifacts_dir).

    Idempotent: creating an existing sprint dir is a no-op (directory is ensured).
    """
    sd = sprint_dir(run_dir, sprint_num)
    artifacts = sd / "generated_artifacts"
    logs = sd / "logs"
    sd.mkdir(parents=True, exist_ok=True)
    artifacts.mkdir(parents=True, exist_ok=True)
    logs.mkdir(parents=True, exist_ok=True)
    # create placeholders for metadata/validation to indicate creation
    # Note: metrics.json is saved at run level, not sprint level
    for fname in ("metadata.json", "validation.json"):
        fpath = sd / fname
        if not fpath.exists():
            fpath.write_text("{}")
    return sd, artifacts


def get_previous_sprint_artifacts(run_dir: Path, current_sprint_num: int) -> Optional[Path]:
    """Return the Path to previous sprint's generated_artifacts or None if not present."""
    if current_sprint_num <= 1:
        return None
    prev = sprint_dir(run_dir, current_sprint_num - 1) / "generated_artifacts"
    return prev if prev.exists() else None


def create_final_symlink(run_dir: Path, final_sprint_num: int) -> Path:
    """Create or update `final` symlink pointing to the given sprint directory.

    Returns the Path to the symlink.
    """
    target = sprint_dir(run_dir, final_sprint_num)
    link = run_dir / "final"
    # Remove existing symlink or file
    if link.exists() or link.is_symlink():
        try:
            link.unlink()
        except Exception:
            # on some systems unlink may fail; try rmdir for directories
            if link.is_dir():
                import shutil

                shutil.rmtree(link)
    # Create symlink (POSIX)
    try:
        link.symlink_to(target)
    except Exception:
        # fallback: copy (fail-fast principle prefers raising, but keep minimal safety)
        raise
    return link
"""
Workspace isolation utilities for experiment runs.

Provides functions to create and manage isolated workspaces per run.
"""

import shutil
import uuid
from pathlib import Path
from typing import Tuple, Optional
from src.utils.logger import get_logger
from src.utils.experiment_paths import ExperimentPaths

logger = get_logger(__name__)


def generate_run_id() -> str:
    """
    Generate a unique run identifier.
    
    Returns:
        UUID string for run identification
    """
    return str(uuid.uuid4())


def create_isolated_workspace(
    framework: str,
    run_id: str,
    experiment_name: Optional[str] = None
) -> Tuple[Path, Path]:
    """
    Create isolated run directory for sprint-based execution.
    
    Args:
        framework: Framework name (baes, chatdev, ghspec)
        run_id: Unique run identifier
        experiment_name: Name of experiment (optional, for backward compatibility)
        
    Returns:
        Tuple of (run_dir, run_dir) Path objects
        Note: Returns run_dir twice for backward compatibility. In sprint-based
        architecture, there's no single "workspace" - each sprint has its own
        workspace at sprint_NNN/generated_artifacts/
        
    Example:
        run_dir: runs/baes/550e8400-e29b-41d4-a716-446655440000/
        Individual sprint workspaces created by create_sprint_workspace()
    """
    # Get run directory
    if experiment_name:
        exp_paths = ExperimentPaths(experiment_name)
        run_dir = exp_paths.get_run_dir(framework, run_id)
    else:
        # Backward compatibility: use old path
        run_dir = Path("runs") / framework / run_id
    
    # Check for collision (should be astronomically rare with UUIDs)
    if run_dir.exists():
        logger.warning(
            f"Run directory already exists: {run_dir}. Appending suffix.",
            extra={'run_id': run_id, 'framework': framework}
        )
        # Append a suffix to avoid collision
        collision_id = str(uuid.uuid4())[:8]
        
        if experiment_name:
            exp_paths = ExperimentPaths(experiment_name)
            run_dir = exp_paths.runs_dir / framework / f"{run_id}-{collision_id}"
        else:
            run_dir = Path("runs") / framework / f"{run_id}-{collision_id}"
    
    # Create only the run directory (no workspace dir in sprint architecture)
    run_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(
        "Created isolated run directory: %s",
        run_dir,
        extra={'run_id': run_id, 'framework': framework}
    )
    
    # Return run_dir twice for backward compatibility with code expecting (run_dir, workspace_dir)
    # In sprint architecture, workspace_dir is not used - each sprint creates its own workspace
    return run_dir, run_dir


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


def get_run_directory(
    framework: str,
    run_id: str,
    experiment_name: Optional[str] = None
) -> Path:
    """
    Get the run directory path for a given framework and run ID.
    
    Args:
        framework: Framework name
        run_id: Run identifier
        experiment_name: Name of experiment (optional, for backward compatibility)
        
    Returns:
        Path to run directory
    """
    if experiment_name:
        exp_paths = ExperimentPaths(experiment_name)
        return exp_paths.get_run_dir(framework, run_id)
    else:
        # Backward compatibility: use old path
        return Path("runs") / framework / run_id


def ensure_runs_directory(experiment_name: Optional[str] = None) -> None:
    """
    Ensure the top-level runs directory exists.
    
    Creates runs/ if it doesn't exist.
    
    Args:
        experiment_name: Name of experiment (optional, for backward compatibility)
    """
    if experiment_name:
        exp_paths = ExperimentPaths(experiment_name)
        runs_dir = exp_paths.runs_dir
    else:
        # Backward compatibility: use old path
        runs_dir = Path("runs")
    
    runs_dir.mkdir(exist_ok=True, parents=True)
    logger.debug("Ensured runs directory exists")
