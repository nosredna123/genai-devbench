"""
Service for discovering and loading config sets.

Discovery mechanism: Distributed metadata (scan directories)
"""

from pathlib import Path
from typing import List, Dict, Any
from .models import ConfigSet
from .exceptions import ConfigSetNotFoundError, ConfigSetValidationError


class ConfigSetLoader:
    """Service for managing config sets in generator."""
    
    def __init__(self, config_sets_dir: Path):
        """
        Initialize loader.
        
        Args:
            config_sets_dir: Path to config_sets/ directory
        """
        self.config_sets_dir = Path(config_sets_dir)
        if not self.config_sets_dir.exists():
            raise FileNotFoundError(f"Config sets directory not found: {config_sets_dir}")
    
    def list_available(self) -> List[str]:
        """
        List all available config set names.
        
        Scans config_sets/ directory for subdirectories containing metadata.yaml
        
        Returns:
            List of config set names (e.g., ["default", "minimal"])
        """
        config_sets = []
        
        for item in self.config_sets_dir.iterdir():
            if item.is_dir():
                metadata_path = item / "metadata.yaml"
                if metadata_path.exists():
                    config_sets.append(item.name)
        
        return sorted(config_sets)
    
    def load(self, name: str) -> ConfigSet:
        """
        Load and validate config set.
        
        Args:
            name: Config set name (e.g., "default")
            
        Returns:
            Validated ConfigSet object
            
        Raises:
            ConfigSetNotFoundError: If config set doesn't exist
            ConfigSetValidationError: If config set is invalid (fail-fast)
        """
        config_set_dir = self.config_sets_dir / name
        
        # Check existence
        if not config_set_dir.exists():
            available = self.list_available()
            raise ConfigSetNotFoundError(
                f"Config set '{name}' not found. Available: {', '.join(available)}"
            )
        
        # Load config set
        try:
            config_set = ConfigSet.load(config_set_dir)
        except Exception as e:
            raise ConfigSetValidationError(f"Failed to load config set '{name}': {e}") from e
        
        # Validate (fail-fast)
        errors = config_set.validate()
        if errors:
            error_msg = f"Config set '{name}' validation failed:\n"
            error_msg += "\n".join(f"  - {err}" for err in errors)
            raise ConfigSetValidationError(error_msg)
        
        return config_set
    
    def get_details(self, name: str) -> Dict[str, Any]:
        """
        Get config set details without full validation.
        
        Args:
            name: Config set name
            
        Returns:
            Dictionary with config set information
            
        Example:
            {
                "name": "default",
                "description": "6-step CRUD application",
                "steps_count": 6,
                "steps": [
                    {"id": 1, "name": "Student CRUD", ...},
                    ...
                ]
            }
        """
        config_set = self.load(name)  # Will validate
        
        return {
            "name": config_set.name,
            "description": config_set.description,
            "version": config_set.version,
            "steps_count": config_set.get_step_count(),
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "description": step.description,
                    "prompt_file": step.prompt_file
                }
                for step in config_set.available_steps
            ]
        }
