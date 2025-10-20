"""
Manifest manager for tracking experiment runs.

This module provides a quick-lookup index for all experiment runs
without needing to scan the entire runs/ directory structure.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from src.utils.logger import get_logger
from src.utils.experiment_paths import ExperimentPaths

logger = get_logger(__name__, component="orchestrator")

MANIFEST_VERSION = "1.0"


def _get_empty_manifest() -> Dict[str, Any]:
    """Create an empty manifest structure."""
    return {
        "version": MANIFEST_VERSION,
        "last_updated": datetime.utcnow().isoformat() + "Z",
        "total_runs": 0,
        "frameworks": {
            "chatdev": 0,
            "baes": 0,
            "ghspec": 0
        },
        "runs": []
    }


def get_manifest(experiment_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the current runs manifest.
    
    Args:
        experiment_name: Name of experiment (optional, for backward compatibility)
    
    Returns:
        Dictionary with manifest data, or empty manifest if not found
    """
    # Get manifest path
    if experiment_name:
        exp_paths = ExperimentPaths(experiment_name)
        manifest_path = exp_paths.manifest_path
    else:
        # Standalone experiment: use runs/manifest.json
        manifest_path = Path("runs/manifest.json")
    
    if not manifest_path.exists():
        logger.info("No manifest found, creating empty one")
        return _get_empty_manifest()
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
            logger.debug(f"Loaded manifest with {manifest['total_runs']} runs")
            return manifest
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading manifest: {e}")
        logger.info("Returning empty manifest")
        return _get_empty_manifest()


def update_manifest(run_data: Dict[str, Any], experiment_name: Optional[str] = None) -> None:
    """
    Update the manifest with new run information.
    
    Args:
        run_data: Dictionary with run information containing:
            - run_id: Unique identifier
            - framework: Framework name (chatdev, baes, ghspec)
            - start_time: ISO format timestamp
            - end_time: ISO format timestamp (optional)
            - verification_status: Reconciliation status (optional)
            - total_tokens_in: Input tokens (optional)
            - total_tokens_out: Output tokens (optional)
        experiment_name: Name of experiment (optional, for backward compatibility)
    """
    manifest = get_manifest(experiment_name)
    
    # Get manifest path
    if experiment_name:
        exp_paths = ExperimentPaths(experiment_name)
        manifest_path = exp_paths.manifest_path
    else:
        # Standalone experiment: use runs/manifest.json
        manifest_path = Path("runs/manifest.json")
    
    # Ensure directory exists
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Extract key fields
    run_id = run_data.get("run_id")
    framework = run_data.get("framework")
    
    if not run_id or not framework:
        logger.error("run_id and framework are required in run_data")
        return
    
    # Check if run already exists
    existing_idx = None
    for idx, run in enumerate(manifest["runs"]):
        if run["run_id"] == run_id:
            existing_idx = idx
            break
    
    # Build run entry
    run_entry = {
        "run_id": run_id,
        "framework": framework,
        "path": f"{framework}/{run_id}",
        "start_time": run_data.get("start_time"),
        "end_time": run_data.get("end_time"),
        "verification_status": run_data.get("verification_status", "pending"),
        "total_tokens_in": run_data.get("total_tokens_in", 0),
        "total_tokens_out": run_data.get("total_tokens_out", 0)
    }
    
    if existing_idx is not None:
        # Update existing run
        manifest["runs"][existing_idx] = run_entry
        logger.info(f"Updated run {run_id} in manifest")
    else:
        # Add new run
        manifest["runs"].append(run_entry)
        manifest["total_runs"] += 1
        manifest["frameworks"][framework] = manifest["frameworks"].get(framework, 0) + 1
        logger.info(f"Added run {run_id} to manifest")
    
    # Update timestamp
    manifest["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    # Save manifest
    try:
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        logger.debug(f"Manifest saved to {manifest_path}")
    except (OSError, IOError) as e:
        logger.error(f"Error saving manifest: {e}")


def find_runs(
    framework: Optional[str] = None,
    verification_status: Optional[str] = None,
    min_tokens: Optional[int] = None,
    experiment_name: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query runs from the manifest with optional filters.
    
    Args:
        framework: Filter by framework name
        verification_status: Filter by verification status
        min_tokens: Filter by minimum total tokens (in + out)
        experiment_name: Name of experiment (optional, for backward compatibility)
    
    Returns:
        List of matching run entries
    """
    manifest = get_manifest(experiment_name)
    runs = manifest["runs"]
    
    # Apply filters
    if framework:
        runs = [r for r in runs if r.get("framework") == framework]
    
    if verification_status:
        runs = [r for r in runs if r.get("verification_status") == verification_status]
    
    if min_tokens:
        runs = [
            r for r in runs 
            if (r.get("total_tokens_in", 0) + r.get("total_tokens_out", 0)) >= min_tokens
        ]
    
    logger.debug(f"Found {len(runs)} runs matching filters")
    return runs


def rebuild_manifest(experiment_name: Optional[str] = None) -> None:
    """
    Rebuild the manifest by scanning the runs/ directory.
    
    This is useful if the manifest gets out of sync with actual files.
    
    Args:
        experiment_name: Name of experiment (optional, for backward compatibility)
    """
    logger.info("Rebuilding manifest from runs/ directory")
    
    manifest = _get_empty_manifest()
    
    # Get runs directory
    if experiment_name:
        exp_paths = ExperimentPaths(experiment_name)
        runs_dir = exp_paths.runs_dir
        manifest_path = exp_paths.manifest_path
    else:
        # Backward compatibility: use old path
        runs_dir = Path("runs")
        manifest_path = Path("runs/runs_manifest.json")
    
    if not runs_dir.exists():
        logger.warning("runs/ directory does not exist")
        return
    
    # Scan for all metadata.json files
    for metadata_file in runs_dir.glob("*/*/metadata.json"):
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # Extract run info
            run_id = metadata.get("run_id")
            framework = metadata_file.parent.parent.name
            
            # Try to load metrics if available
            metrics_file = metadata_file.parent / "metrics.json"
            metrics = {}
            if metrics_file.exists():
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
            
            # Build run data
            run_data = {
                "run_id": run_id,
                "framework": framework,
                "start_time": metadata.get("start_time"),
                "end_time": metadata.get("end_time"),
                "verification_status": metrics.get("verification_status", "pending"),
                "total_tokens_in": metrics.get("total_tokens_in", 0),
                "total_tokens_out": metrics.get("total_tokens_out", 0)
            }
            
            # Add to manifest
            manifest["runs"].append({
                "run_id": run_id,
                "framework": framework,
                "path": f"{framework}/{run_id}",
                **run_data
            })
            manifest["total_runs"] += 1
            manifest["frameworks"][framework] = manifest["frameworks"].get(framework, 0) + 1
            
            logger.debug(f"Added run {run_id} during rebuild")
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error processing {metadata_file}: {e}")
    
    # Save rebuilt manifest
    manifest["last_updated"] = datetime.utcnow().isoformat() + "Z"
    
    try:
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Rebuilt manifest with {manifest['total_runs']} runs")
    except (OSError, IOError) as e:
        logger.error(f"Error saving rebuilt manifest: {e}")


def remove_run(run_id: str, experiment_name: Optional[str] = None) -> None:
    """
    Remove a run from the manifest.
    
    Args:
        run_id: The run ID to remove
        experiment_name: Name of experiment (optional, for backward compatibility)
    """
    manifest = get_manifest(experiment_name)
    
    # Get manifest path
    if experiment_name:
        exp_paths = ExperimentPaths(experiment_name)
        manifest_path = exp_paths.manifest_path
    else:
        # Backward compatibility: use old path
        manifest_path = Path("runs/runs_manifest.json")
    
    # Find and remove the run
    for idx, run in enumerate(manifest["runs"]):
        if run["run_id"] == run_id:
            framework = run["framework"]
            manifest["runs"].pop(idx)
            manifest["total_runs"] -= 1
            manifest["frameworks"][framework] = max(0, manifest["frameworks"].get(framework, 1) - 1)
            manifest["last_updated"] = datetime.utcnow().isoformat() + "Z"
            
            # Save
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Removed run {run_id} from manifest")
            return
    
    logger.warning(f"Run {run_id} not found in manifest")
