"""
Step configuration data structures for generated experiments.

This module handles steps in generated experiment config.yaml files.
For config set management (curated templates), see src/config_sets/.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any
from .exceptions import StepValidationError


@dataclass
class StepConfig:
    """
    Represents a single step in an experiment configuration.
    
    Attributes:
        id: Step identifier (e.g., 1, 2, 3)
        enabled: Whether the step should be executed
        name: Human-readable step name
        prompt_file: Path to prompt file relative to experiment directory
    """
    id: int
    enabled: bool
    name: str
    prompt_file: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StepConfig':
        """
        Create StepConfig from dictionary (from YAML).
        
        Args:
            data: Dictionary with id, enabled, name, prompt_file keys
            
        Returns:
            StepConfig instance
            
        Raises:
            StepValidationError: If required fields are missing or invalid
        """
        required_fields = ['id', 'enabled', 'name', 'prompt_file']
        missing = [f for f in required_fields if f not in data]
        
        if missing:
            raise StepValidationError(
                f"Step configuration missing required fields: {', '.join(missing)}"
            )
        
        # Validate types
        if not isinstance(data['id'], int):
            raise StepValidationError(f"Step id must be integer, got: {type(data['id']).__name__}")
        
        if not isinstance(data['enabled'], bool):
            raise StepValidationError(f"Step enabled must be boolean, got: {type(data['enabled']).__name__}")
        
        if not isinstance(data['name'], str):
            raise StepValidationError(f"Step name must be string, got: {type(data['name']).__name__}")
        
        if not isinstance(data['prompt_file'], str):
            raise StepValidationError(f"Step prompt_file must be string, got: {type(data['prompt_file']).__name__}")
        
        return cls(
            id=data['id'],
            enabled=data['enabled'],
            name=data['name'],
            prompt_file=data['prompt_file']
        )


class StepsCollection:
    """
    Manages a collection of steps with validation.
    
    Provides methods to:
    - Load steps from config dictionary
    - Validate step IDs (no duplicates)
    - Validate prompt files exist
    - Get enabled steps in declaration order
    """
    
    def __init__(self, steps: List[StepConfig], experiment_dir: Path):
        """
        Initialize steps collection.
        
        Args:
            steps: List of StepConfig instances
            experiment_dir: Path to experiment directory (for validating prompt paths)
        """
        self.steps = steps
        self.experiment_dir = experiment_dir
        self._validate()
    
    @classmethod
    def from_config(cls, config: Dict[str, Any], experiment_dir: Path) -> 'StepsCollection':
        """
        Create StepsCollection from config dictionary.
        
        Args:
            config: Configuration dictionary with 'steps' key
            experiment_dir: Path to experiment directory
            
        Returns:
            StepsCollection instance
            
        Raises:
            StepValidationError: If steps configuration is invalid
        """
        if 'steps' not in config:
            raise StepValidationError("Configuration missing 'steps' key")
        
        steps_data = config['steps']
        
        if not isinstance(steps_data, list):
            raise StepValidationError("'steps' must be a list")
        
        if len(steps_data) == 0:
            raise StepValidationError("'steps' list cannot be empty")
        
        steps = [StepConfig.from_dict(step_data) for step_data in steps_data]
        
        return cls(steps, experiment_dir)
    
    def _validate(self) -> None:
        """
        Validate steps collection (fail-fast).
        
        Checks:
        - No duplicate step IDs
        - All prompt files exist
        
        Raises:
            StepValidationError: If validation fails
        """
        # Check for duplicate IDs
        step_ids = [step.id for step in self.steps]
        duplicates = [id for id in step_ids if step_ids.count(id) > 1]
        
        if duplicates:
            unique_dups = sorted(set(duplicates))
            raise StepValidationError(
                f"Duplicate step IDs found: {unique_dups}"
            )
        
        # Check prompt files exist (fail-fast)
        for step in self.steps:
            prompt_path = self.experiment_dir / step.prompt_file
            
            if not prompt_path.exists():
                raise StepValidationError(
                    f"Step {step.id} ({step.name}): Prompt file not found: {step.prompt_file}"
                )
            
            if not prompt_path.is_file():
                raise StepValidationError(
                    f"Step {step.id} ({step.name}): Prompt path is not a file: {step.prompt_file}"
                )
            
            # Check file is not empty
            if prompt_path.stat().st_size == 0:
                raise StepValidationError(
                    f"Step {step.id} ({step.name}): Prompt file is empty: {step.prompt_file}"
                )
    
    def get_enabled_steps(self) -> List[StepConfig]:
        """
        Get enabled steps in declaration order (not sorted by ID).
        
        Returns:
            List of enabled StepConfig instances in the order they appear in config
        """
        return [step for step in self.steps if step.enabled]
    
    def get_all_steps(self) -> List[StepConfig]:
        """
        Get all steps in declaration order.
        
        Returns:
            List of all StepConfig instances
        """
        return self.steps.copy()
    
    def get_step_by_id(self, step_id: int) -> StepConfig:
        """
        Get step by ID.
        
        Args:
            step_id: Step identifier
            
        Returns:
            StepConfig instance
            
        Raises:
            StepValidationError: If step ID not found
        """
        for step in self.steps:
            if step.id == step_id:
                return step
        
        raise StepValidationError(f"Step ID {step_id} not found in configuration")
    
    def __len__(self) -> int:
        """Return number of steps."""
        return len(self.steps)
    
    def __iter__(self):
        """Iterate over steps."""
        return iter(self.steps)


def get_enabled_steps(config: Dict[str, Any], experiment_dir: Path) -> List[StepConfig]:
    """
    Helper function to get enabled steps from config.
    
    Args:
        config: Configuration dictionary with 'steps' key
        experiment_dir: Path to experiment directory
        
    Returns:
        List of enabled StepConfig instances in declaration order
        
    Raises:
        StepValidationError: If configuration is invalid
        
    Example:
        config = yaml.safe_load(Path('config.yaml').read_text())
        enabled_steps = get_enabled_steps(config, Path.cwd())
        
        for step in enabled_steps:
            print(f"Step {step.id}: {step.name}")
    """
    collection = StepsCollection.from_config(config, experiment_dir)
    return collection.get_enabled_steps()
