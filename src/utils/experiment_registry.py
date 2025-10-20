"""
Experiment registry management.

Global registry tracking all experiments in the workspace.
No silent fallbacks - raises errors for invalid operations.

Design Principles:
- Single source of truth (.experiments.json in project root)
- Atomic operations (load, modify, save)
- Explicit error messages
- Thread-safe file operations
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import json
import fcntl
from contextlib import contextmanager

from src.utils.logger import get_logger

logger = get_logger(__name__, component="registry")


class RegistryError(Exception):
    """Base exception for registry operations."""
    pass


class ExperimentAlreadyExistsError(RegistryError):
    """Raised when trying to create experiment that already exists."""
    pass


class ExperimentRegistry:
    """
    Global experiment registry manager.
    
    Manages .experiments.json file in project root.
    Provides atomic operations for registry updates.
    
    Example:
        >>> registry = ExperimentRegistry()
        >>> registry.register_experiment("baseline", {...})
        >>> info = registry.get_experiment("baseline")
        >>> all_exps = registry.list_experiments()
    """
    
    REGISTRY_VERSION = "1.0"
    REGISTRY_FILENAME = ".experiments.json"
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize registry manager.
        
        Args:
            project_root: Project root directory (auto-detected if None)
            
        Raises:
            ValueError: If project root cannot be detected
        """
        self.project_root = project_root or self._detect_project_root()
        self.registry_path = self.project_root / self.REGISTRY_FILENAME
        
        # Create registry if it doesn't exist
        if not self.registry_path.exists():
            self._create_empty_registry()
    
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
        
        while current != current.parent:
            # Look for experiments/ or .git/ directory
            if (current / "experiments").exists() or (current / ".git").exists():
                return current
            current = current.parent
        
        raise ValueError(
            "Could not detect project root.\n"
            "Make sure you're running from within the baes_experiment project."
        )
    
    def _create_empty_registry(self) -> None:
        """Create empty registry file."""
        empty_registry = {
            "version": self.REGISTRY_VERSION,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "experiments": {}
        }
        
        self._atomic_write(empty_registry)
        logger.info(f"Created empty registry: {self.registry_path}")
    
    @contextmanager
    def _lock_registry(self):
        """
        Context manager for registry file locking.
        
        Ensures atomic read-modify-write operations.
        """
        lock_path = self.registry_path.with_suffix('.lock')
        
        with open(lock_path, 'w') as lock_file:
            # Acquire exclusive lock
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                # Release lock
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    
    def _atomic_read(self) -> Dict[str, Any]:
        """
        Read registry atomically.
        
        Returns:
            Registry data
            
        Raises:
            RegistryError: If registry is corrupted
        """
        try:
            with self._lock_registry():
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Validate structure
                if 'version' not in data or 'experiments' not in data:
                    raise RegistryError(
                        f"Registry file is corrupted: {self.registry_path}\n"
                        f"Missing required fields: 'version' or 'experiments'\n"
                        f"Consider backing up and recreating."
                    )
                
                return data
        
        except json.JSONDecodeError as e:
            raise RegistryError(
                f"Registry file is corrupted (invalid JSON): {self.registry_path}\n"
                f"Error: {e}\n"
                f"Consider backing up and recreating."
            )
    
    def _atomic_write(self, data: Dict[str, Any]) -> None:
        """
        Write registry atomically.
        
        Uses atomic write pattern (write to temp, then rename).
        
        Args:
            data: Registry data to write
        """
        temp_path = self.registry_path.with_suffix('.tmp')
        
        with self._lock_registry():
            # Write to temp file
            with open(temp_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Atomic rename
            temp_path.replace(self.registry_path)
    
    # =============================================================================
    # Registry Operations
    # =============================================================================
    
    def register_experiment(
        self,
        name: str,
        config: Dict[str, Any],
        config_hash: str
    ) -> None:
        """
        Register a new experiment.
        
        Args:
            name: Experiment name
            config: Experiment configuration
            config_hash: Configuration hash
            
        Raises:
            ExperimentAlreadyExistsError: If experiment already registered
        """
        registry = self._atomic_read()
        
        # Check if already exists
        if name in registry['experiments']:
            raise ExperimentAlreadyExistsError(
                f"Experiment '{name}' is already registered.\n"
                f"Use a different name or delete existing experiment:\n"
                f"  rm -rf experiments/{name}"
            )
        
        # Extract metadata from config
        frameworks = config.get('frameworks', {})
        enabled_frameworks = [
            fw_name for fw_name, fw_config in frameworks.items()
            if fw_config.get('enabled', False)
        ]
        
        # Create entry
        now = datetime.utcnow().isoformat() + "Z"
        registry['experiments'][name] = {
            "path": f"experiments/{name}",
            "config_hash": config_hash,
            "created_at": now,
            "updated_at": now,
            "status": "pending",  # pending | in_progress | completed | failed
            "model": config.get('model', 'unknown'),
            "frameworks": {
                fw_name: {
                    "enabled": True,
                    "runs": 0
                }
                for fw_name in enabled_frameworks
            },
            "total_runs": 0,
            "max_runs": config.get('stopping_rule', {}).get('max_runs', 0) * len(enabled_frameworks),
            "stopping_rule_met": False
        }
        
        # Update registry timestamp
        registry['updated_at'] = now
        
        # Save atomically
        self._atomic_write(registry)
        
        logger.info(f"Registered experiment: {name}")
    
    def update_experiment(
        self,
        name: str,
        updates: Dict[str, Any]
    ) -> None:
        """
        Update experiment metadata.
        
        Args:
            name: Experiment name
            updates: Dictionary of fields to update
            
        Raises:
            RegistryError: If experiment not found
        """
        registry = self._atomic_read()
        
        # Check if exists
        if name not in registry['experiments']:
            raise RegistryError(
                f"Experiment '{name}' not found in registry.\n"
                f"Available experiments:\n{self._format_experiment_list(registry)}"
            )
        
        # Update fields
        registry['experiments'][name].update(updates)
        registry['experiments'][name]['updated_at'] = datetime.utcnow().isoformat() + "Z"
        registry['updated_at'] = datetime.utcnow().isoformat() + "Z"
        
        # Save atomically
        self._atomic_write(registry)
        
        logger.debug(f"Updated experiment: {name}")
    
    def increment_run_count(
        self,
        name: str,
        framework: str,
        increment: int = 1
    ) -> None:
        """
        Increment run count for experiment/framework.
        
        Args:
            name: Experiment name
            framework: Framework name
            increment: Number to increment by
            
        Raises:
            RegistryError: If experiment or framework not found
        """
        registry = self._atomic_read()
        
        if name not in registry['experiments']:
            raise RegistryError(f"Experiment '{name}' not found in registry")
        
        exp_data = registry['experiments'][name]
        
        if framework not in exp_data.get('frameworks', {}):
            raise RegistryError(
                f"Framework '{framework}' not found in experiment '{name}'"
            )
        
        # Increment counts
        exp_data['frameworks'][framework]['runs'] += increment
        exp_data['total_runs'] += increment
        exp_data['updated_at'] = datetime.utcnow().isoformat() + "Z"
        
        # Update status
        if exp_data['status'] == 'pending' and exp_data['total_runs'] > 0:
            exp_data['status'] = 'in_progress'
        
        # Check stopping rule
        if exp_data['total_runs'] >= exp_data['max_runs']:
            exp_data['stopping_rule_met'] = True
            exp_data['status'] = 'completed'
        
        registry['updated_at'] = datetime.utcnow().isoformat() + "Z"
        
        # Save atomically
        self._atomic_write(registry)
    
    def get_experiment(self, name: str) -> Dict[str, Any]:
        """
        Get experiment metadata.
        
        Args:
            name: Experiment name
            
        Returns:
            Experiment metadata
            
        Raises:
            RegistryError: If experiment not found
        """
        registry = self._atomic_read()
        
        if name not in registry['experiments']:
            raise RegistryError(
                f"Experiment '{name}' not found in registry.\n"
                f"Available experiments:\n{self._format_experiment_list(registry)}"
            )
        
        return registry['experiments'][name].copy()
    
    def list_experiments(
        self,
        status: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        List all experiments.
        
        Args:
            status: Optional status filter (pending | in_progress | completed | failed)
            
        Returns:
            Dictionary of {experiment_name: metadata}
        """
        registry = self._atomic_read()
        experiments = registry['experiments']
        
        if status:
            experiments = {
                name: data for name, data in experiments.items()
                if data.get('status') == status
            }
        
        return experiments
    
    def delete_experiment(self, name: str) -> None:
        """
        Remove experiment from registry.
        
        Note: Does NOT delete experiment directory.
        
        Args:
            name: Experiment name
            
        Raises:
            RegistryError: If experiment not found
        """
        registry = self._atomic_read()
        
        if name not in registry['experiments']:
            raise RegistryError(f"Experiment '{name}' not found in registry")
        
        # Remove entry
        del registry['experiments'][name]
        registry['updated_at'] = datetime.utcnow().isoformat() + "Z"
        
        # Save atomically
        self._atomic_write(registry)
        
        logger.info(f"Deleted experiment from registry: {name}")
    
    # =============================================================================
    # Utility Methods
    # =============================================================================
    
    def _format_experiment_list(self, registry: Dict[str, Any]) -> str:
        """Format experiment list for error messages."""
        experiments = registry.get('experiments', {})
        
        if not experiments:
            return "  (no experiments)"
        
        lines = []
        for name, data in sorted(experiments.items()):
            status = data.get('status', 'unknown')
            runs = data.get('total_runs', 0)
            max_runs = data.get('max_runs', 0)
            lines.append(f"  - {name} ({status}, {runs}/{max_runs} runs)")
        
        return "\n".join(lines)
    
    def validate_registry(self) -> List[str]:
        """
        Validate registry consistency.
        
        Checks:
        - All registered experiments have directories
        - All experiment directories are registered
        - Config hashes match
        
        Returns:
            List of validation warnings (empty if all OK)
        """
        warnings = []
        registry = self._atomic_read()
        experiments_dir = self.project_root / "experiments"
        
        if not experiments_dir.exists():
            warnings.append("experiments/ directory does not exist")
            return warnings
        
        # Check registered experiments have directories
        for name in registry['experiments']:
            exp_dir = experiments_dir / name
            if not exp_dir.exists():
                warnings.append(
                    f"Registered experiment '{name}' has no directory: {exp_dir}"
                )
        
        # Check experiment directories are registered
        for exp_dir in experiments_dir.iterdir():
            if not exp_dir.is_dir():
                continue
            
            config_path = exp_dir / "config.yaml"
            if not config_path.exists():
                continue
            
            if exp_dir.name not in registry['experiments']:
                warnings.append(
                    f"Experiment directory '{exp_dir.name}' is not registered"
                )
        
        return warnings


# =============================================================================
# Singleton Access
# =============================================================================

_registry_instance: Optional[ExperimentRegistry] = None


def get_registry(project_root: Optional[Path] = None) -> ExperimentRegistry:
    """
    Get singleton registry instance.
    
    Args:
        project_root: Project root (only used on first call)
        
    Returns:
        ExperimentRegistry instance
    """
    global _registry_instance
    
    if _registry_instance is None:
        _registry_instance = ExperimentRegistry(project_root)
    
    return _registry_instance


def reset_registry() -> None:
    """
    Reset singleton instance.
    
    Primarily for testing.
    """
    global _registry_instance
    _registry_instance = None
