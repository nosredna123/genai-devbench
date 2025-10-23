"""
Experiment path management.

All paths are derived from experiment directory. No legacy modes, no fallbacks.
Raises explicit errors for missing experiments or invalid configurations.

Design Principles:
- No silent fallbacks (fail fast with clear errors)
- DRY: Single source of truth for all paths
- Explicit: Every path derived from experiment name + config
"""

from pathlib import Path
from typing import Dict, Any, Optional
import hashlib
import json
import yaml


class ExperimentNotFoundError(Exception):
    """Raised when experiment directory doesn't exist."""
    pass


class ConfigNotFoundError(Exception):
    """Raised when experiment config file is missing."""
    pass


class ConfigHashMismatchError(Exception):
    """Raised when config hash validation fails."""
    pass


class ExperimentPaths:
    """
    Manages all paths for an experiment.
    
    Design:
    - All paths derived from experiment_dir
    - No hardcoded paths
    - No fallback mechanisms
    - Config hash validation enforced
    
    Example:
        >>> paths = ExperimentPaths("baseline_gpt4o_mini")
        >>> paths.validate_config_hash()  # Raises if config changed
        >>> run_dir = paths.get_run_dir("baes", "run-123")
    """
    
    def __init__(
        self,
        experiment_name: str,
        project_root: Optional[Path] = None,
        experiments_base_dir: Optional[Path] = None,
        auto_create_structure: bool = False,
        validate_exists: bool = True
    ):
        """
        Initialize experiment paths.
        
        Args:
            experiment_name: Name of the experiment
            project_root: Project root directory (auto-detected if not provided)
            experiments_base_dir: Base directory for experiments (default: project_root/experiments)
            auto_create_structure: If True, create missing directories
            validate_exists: If True, validate experiment exists (set False for new experiments)
            
        Raises:
            ExperimentNotFoundError: If experiment directory doesn't exist (when validate_exists=True)
            ConfigNotFoundError: If config.yaml is missing (when validate_exists=True)
        """
        self.experiment_name = experiment_name
        self.project_root = project_root or self._detect_project_root()
        
        # Check if this is a standalone experiment (config.yaml at project root, no experiments/ dir)
        is_standalone = (
            (self.project_root / "config.yaml").exists() and
            not (self.project_root / "experiments").exists()
        )
        
        if is_standalone:
            # Standalone experiment: project root IS the experiment directory
            self.experiments_base_dir = self.project_root.parent
            self.experiment_dir = self.project_root
        else:
            # Multi-experiment structure: experiments/<name>/
            self.experiments_base_dir = experiments_base_dir or (self.project_root / "experiments")
            self.experiment_dir = self.experiments_base_dir / experiment_name
        
        # For new experiments, skip validation
        if not validate_exists:
            self.config_path = self.experiment_dir / "config.yaml"
            self.config = None  # Will be set after config is written
            
            # Create directory structure
            if auto_create_structure:
                self.ensure_structure()
            
            return
        
        # Validate experiment exists (fail fast)
        if not self.experiment_dir.exists():
            raise ExperimentNotFoundError(
                f"Experiment '{experiment_name}' not found.\n"
                f"Expected directory: {self.experiment_dir}\n"
                f"Available experiments:\n"
                f"{self._list_available_experiments()}\n"
                f"Create new experiment: python scripts/new_experiment.py"
            )
        
        # Load config (fail fast if missing)
        self.config_path = self.experiment_dir / "config.yaml"
        if not self.config_path.exists():
            raise ConfigNotFoundError(
                f"Config not found: {self.config_path}\n"
                f"Experiment directory exists but config.yaml is missing.\n"
                f"This indicates a corrupted experiment."
            )
        
        # Load config into memory
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # Create directory structure if requested
        if auto_create_structure:
            self.ensure_structure()
    
    @staticmethod
    def _detect_project_root() -> Path:
        """
        Auto-detect project root directory.
        
        Returns:
            Path to project root
            
        Raises:
            ValueError: If project root cannot be detected
        """
        current = Path.cwd()
        
        # Walk up looking for indicators
        while current != current.parent:
            # Look for experiments/ or .git/ directory
            if (current / "experiments").exists() or (current / ".git").exists():
                return current
            current = current.parent
        
        # No indicators found
        raise ValueError(
            "Could not detect project root.\n"
            "Make sure you're running from within the baes_experiment project,\n"
            "or pass project_root explicitly to ExperimentPaths()."
        )
    
    def _list_available_experiments(self) -> str:
        """
        List available experiments for error messages.
        
        Returns:
            Formatted string of available experiments
        """
        if not self.experiments_base_dir.exists():
            return f"  (experiments directory not found: {self.experiments_base_dir})"
        
        experiments = [
            d.name for d in self.experiments_base_dir.iterdir()
            if d.is_dir() and (d / "config.yaml").exists()
        ]
        
        if not experiments:
            return "  (no experiments found)"
        
        return "\n".join(f"  - {name}" for name in sorted(experiments))
    
    # =============================================================================
    # Directory Paths (DRY: All derived from experiment_dir)
    # =============================================================================
    
    @property
    def runs_dir(self) -> Path:
        """Get runs directory path."""
        return self.experiment_dir / "runs"
    
    @property
    def analysis_dir(self) -> Path:
        """Get analysis directory path."""
        return self.experiment_dir / "analysis"
    
    @property
    def visualizations_dir(self) -> Path:
        """Get visualizations directory path."""
        return self.analysis_dir / "visualizations"
    
    @property
    def meta_dir(self) -> Path:
        """Get metadata directory path (hidden)."""
        return self.experiment_dir / ".meta"
    
    # =============================================================================
    # File Paths (DRY: All derived from directory properties)
    # =============================================================================
    
    @property
    def manifest_path(self) -> Path:
        """Get manifest file path."""
        return self.runs_dir / "manifest.json"
    
    @property
    def config_hash_path(self) -> Path:
        """Get config hash file path."""
        return self.meta_dir / "config_hash.txt"
    
    @property
    def status_path(self) -> Path:
        """Get status file path."""
        return self.meta_dir / "status.txt"
    
    @property
    def created_at_path(self) -> Path:
        """Get creation timestamp file path."""
        return self.meta_dir / "created_at.txt"
    
    @property
    def updated_at_path(self) -> Path:
        """Get last update timestamp file path."""
        return self.meta_dir / "updated_at.txt"
    
    @property
    def report_path(self) -> Path:
        """Get report file path."""
        return self.analysis_dir / "report.md"
    
    @property
    def readme_path(self) -> Path:
        """Get README file path."""
        return self.experiment_dir / "README.md"
    
    # =============================================================================
    # Shared Resource Paths (from config, in project root)
    # =============================================================================
    
    @property
    def prompts_dir(self) -> Path:
        """
        Get prompts directory (shared across experiments).
        
        Raises:
            ValueError: If prompts_dir not in config or doesn't exist
        """
        if 'prompts_dir' not in self.config:
            raise ValueError(
                f"'prompts_dir' not found in config: {self.config_path}\n"
                f"Add: prompts_dir: 'config/prompts'"
            )
        
        prompts_path = self.project_root / self.config['prompts_dir']
        
        if not prompts_path.exists():
            raise ValueError(
                f"Prompts directory not found: {prompts_path}\n"
                f"Configured in: {self.config_path}\n"
                f"Value: prompts_dir: '{self.config['prompts_dir']}'"
            )
        
        return prompts_path
    
    @property
    def hitl_path(self) -> Path:
        """
        Get HITL file path (shared across experiments).
        
        Raises:
            ValueError: If hitl_path not in config or doesn't exist
        """
        if 'hitl_path' not in self.config:
            raise ValueError(
                f"'hitl_path' not found in config: {self.config_path}\n"
                f"Add: hitl_path: 'config/hitl/expanded_spec.txt'"
            )
        
        hitl_file = self.project_root / self.config['hitl_path']
        
        if not hitl_file.exists():
            raise ValueError(
                f"HITL file not found: {hitl_file}\n"
                f"Configured in: {self.config_path}\n"
                f"Value: hitl_path: '{self.config['hitl_path']}'"
            )
        
        return hitl_file
    
    # =============================================================================
    # Run-Specific Paths
    # =============================================================================
    
    def get_run_dir(self, framework: str, run_id: str) -> Path:
        """
        Get path for a specific run.
        
        Args:
            framework: Framework name (baes, chatdev, ghspec)
            run_id: Run identifier (UUID)
            
        Returns:
            Path to run directory
        """
        return self.runs_dir / framework / run_id
    
    def get_run_logs_dir(self, framework: str, run_id: str) -> Path:
        """Get logs directory for a specific run."""
        return self.get_run_dir(framework, run_id) / "logs"
    
    def get_run_workspace_dir(self, framework: str, run_id: str) -> Path:
        """Get workspace directory for a specific run."""
        return self.get_run_dir(framework, run_id) / "workspace"
    
    def get_run_metrics_path(self, framework: str, run_id: str) -> Path:
        """Get metrics.json path for a specific run."""
        return self.get_run_dir(framework, run_id) / "metrics.json"
    
    def get_run_step_metrics_path(self, framework: str, run_id: str) -> Path:
        """Get step_metrics.json path for a specific run."""
        return self.get_run_dir(framework, run_id) / "step_metrics.json"
    
    # =============================================================================
    # Sprint-Specific Paths (US1: Sprint Architecture)
    # =============================================================================
    
    def get_sprint_dir(self, run_dir: Path, sprint_num: int) -> Path:
        """
        Get path for a specific sprint within a run.
        
        Args:
            run_dir: Run directory path (e.g., experiments/my_exp/runs/baes/abc123)
            sprint_num: Sprint number (1-indexed)
            
        Returns:
            Path to sprint directory (e.g., run_dir/sprint_001)
        """
        return run_dir / f"sprint_{sprint_num:03d}"
    
    def get_summary_dir(self, run_dir: Path) -> Path:
        """
        Get path for run-level summary directory.
        
        Args:
            run_dir: Run directory path
            
        Returns:
            Path to summary directory (e.g., run_dir/summary)
        """
        return run_dir / "summary"
    
    # =============================================================================
    # Config Hash Computation & Validation
    # =============================================================================
    
    def compute_config_hash(self, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Compute SHA-256 hash of canonical config fields.
        
        Only hashes fields that affect experimental validity.
        Changes to comments, formatting, or non-critical fields won't change hash.
        
        Args:
            config: Configuration dict (uses self.config if not provided)
        
        Returns:
            Full SHA-256 hex digest (64 chars)
        """
        # Use provided config or self.config
        cfg = config if config is not None else self.config
        
        if cfg is None:
            raise ValueError(
                "No configuration available. "
                "Either pass config parameter or ensure experiment is loaded."
            )
        
        # Fields that invalidate results if changed
        canonical_fields = {
            'model': cfg.get('model'),
            'random_seed': cfg.get('random_seed'),
            'frameworks': {
                k: {
                    'enabled': v.get('enabled'),
                    'commit_hash': v.get('commit_hash'),
                    'repo_url': v.get('repo_url')
                }
                for k, v in cfg.get('frameworks', {}).items()
                if v.get('enabled', False)
            },
            'stopping_rule': cfg.get('stopping_rule'),
            'metrics': {
                'reliable_metrics': cfg.get('metrics', {}).get('reliable_metrics'),
                'derived_metrics': cfg.get('metrics', {}).get('derived_metrics'),
            },
            'pricing': cfg.get('pricing'),
        }
        
        # Canonical JSON (sorted keys for determinism)
        config_str = json.dumps(canonical_fields, sort_keys=True)
        
        # Compute SHA-256
        return hashlib.sha256(config_str.encode('utf-8')).hexdigest()
    
    def validate_config_hash(self) -> None:
        """
        Validate that config hasn't changed since experiment started.
        
        On first run: Saves current hash to .meta/config_hash.txt
        On subsequent runs: Compares current hash with stored hash
        
        Raises:
            ConfigHashMismatchError: If hash mismatch detected
        """
        current_hash = self.compute_config_hash()
        
        # First run: save hash
        if not self.config_hash_path.exists():
            self.meta_dir.mkdir(parents=True, exist_ok=True)
            self.config_hash_path.write_text(current_hash, encoding='utf-8')
            return
        
        # Subsequent runs: validate hash
        stored_hash = self.config_hash_path.read_text(encoding='utf-8').strip()
        
        if stored_hash != current_hash:
            raise ConfigHashMismatchError(
                f"❌ Configuration has changed since experiment started!\n\n"
                f"Experiment: {self.experiment_name}\n"
                f"Config: {self.config_path}\n\n"
                f"Stored hash (when experiment started):\n  {stored_hash}\n\n"
                f"Current hash (now):\n  {current_hash}\n\n"
                f"This could invalidate your results.\n\n"
                f"Options:\n"
                f"  1. Revert config changes and try again\n"
                f"  2. Create a new experiment with the new config:\n"
                f"     python scripts/new_experiment.py --name '{self.experiment_name}_v2'\n"
                f"  3. Force update hash (NOT recommended - breaks reproducibility):\n"
                f"     rm {self.config_hash_path}"
            )
    
    # =============================================================================
    # Directory Structure Management
    # =============================================================================
    
    def ensure_structure(self) -> None:
        """
        Create experiment directory structure if missing.
        
        Creates:
        - runs/
        - analysis/
        - analysis/visualizations/
        - .meta/
        
        Safe to call multiple times (idempotent).
        """
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        self.visualizations_dir.mkdir(parents=True, exist_ok=True)
        self.meta_dir.mkdir(parents=True, exist_ok=True)
    
    # =============================================================================
    # Utility Methods
    # =============================================================================
    
    def __repr__(self) -> str:
        """String representation."""
        return f"ExperimentPaths('{self.experiment_name}')"
    
    def __str__(self) -> str:
        """Human-readable string."""
        return (
            f"Experiment: {self.experiment_name}\n"
            f"Directory: {self.experiment_dir}\n"
            f"Config: {self.config_path}\n"
            f"Runs: {self.runs_dir}\n"
            f"Analysis: {self.analysis_dir}"
        )


# =============================================================================
# Factory Function (Convenience)
# =============================================================================

def get_experiment_paths(
    experiment_name: str,
    project_root: Optional[Path] = None,
    experiments_base_dir: Optional[Path] = None,
    auto_create_structure: bool = False,
    validate_exists: bool = True
) -> ExperimentPaths:
    """
    Get ExperimentPaths instance for an experiment.
    
    Convenience factory function for common use case.
    
    Args:
        experiment_name: Name of the experiment
        project_root: Project root directory (auto-detected if None)
        experiments_base_dir: Base directory for experiments (default: project_root/experiments)
        auto_create_structure: If True, create missing directories
        validate_exists: If True, validate experiment exists (set False for new experiments)
        
    Returns:
        ExperimentPaths instance
        
    Raises:
        ExperimentNotFoundError: If experiment doesn't exist (when validate_exists=True)
        ConfigNotFoundError: If config.yaml is missing (when validate_exists=True)
    """
    return ExperimentPaths(
        experiment_name=experiment_name,
        project_root=project_root,
        experiments_base_dir=experiments_base_dir,
        auto_create_structure=auto_create_structure,
        validate_exists=validate_exists
    )
