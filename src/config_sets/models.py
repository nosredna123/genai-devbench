"""
Data models for Config Set Management.

A Config Set is a curated experiment scenario template containing:
- Metadata (name, description, available steps)
- Experiment template (default config.yaml structure)
- Prompts directory (prompt files for each step)
- HITL directory (human-in-the-loop files)
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any
import yaml


@dataclass
class StepMetadata:
    """Metadata about a step in a config set."""
    id: int
    name: str
    prompt_file: str
    description: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StepMetadata':
        """Load from metadata.yaml entry."""
        return cls(
            id=data['id'],
            name=data['name'],
            prompt_file=data['prompt_file'],
            description=data['description']
        )


@dataclass
class ConfigSet:
    """A curated experiment scenario template."""
    
    name: str
    description: str
    version: str
    available_steps: List[StepMetadata]
    defaults: Dict[str, Any]
    
    # Paths
    base_path: Path
    template_path: Path
    prompts_dir: Path
    hitl_dir: Path
    
    @classmethod
    def load(cls, config_set_dir: Path) -> 'ConfigSet':
        """
        Load config set from directory.
        
        Args:
            config_set_dir: Path to config set (e.g., config_sets/default/)
            
        Returns:
            Loaded ConfigSet object
            
        Raises:
            FileNotFoundError: If metadata.yaml missing
            ValueError: If metadata is invalid
        """
        metadata_path = config_set_dir / "metadata.yaml"
        if not metadata_path.exists():
            raise FileNotFoundError(f"metadata.yaml not found in {config_set_dir}")
        
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f)
        
        # Load available steps
        steps = [
            StepMetadata.from_dict(step_data)
            for step_data in metadata.get('available_steps', [])
        ]
        
        return cls(
            name=metadata['name'],
            description=metadata['description'],
            version=metadata.get('version', '1.0.0'),
            available_steps=steps,
            defaults=metadata.get('defaults', {}),
            base_path=config_set_dir,
            template_path=config_set_dir / "experiment_template.yaml",
            prompts_dir=config_set_dir / "prompts",
            hitl_dir=config_set_dir / "hitl"
        )
    
    def validate(self) -> List[str]:
        """
        Validate config set structure.
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        # Check template exists
        if not self.template_path.exists():
            errors.append(f"experiment_template.yaml not found at {self.template_path}")
        
        # Check directories exist
        if not self.prompts_dir.exists():
            errors.append(f"prompts/ directory not found at {self.prompts_dir}")
        if not self.hitl_dir.exists():
            errors.append(f"hitl/ directory not found at {self.hitl_dir}")
        
        # Check prompt files exist
        for step in self.available_steps:
            prompt_path = self.base_path / step.prompt_file
            if not prompt_path.exists():
                errors.append(f"Prompt file not found: {step.prompt_file}")
            elif prompt_path.stat().st_size == 0:
                errors.append(f"Prompt file is empty: {step.prompt_file}")
        
        # Check for duplicate step IDs
        step_ids = [s.id for s in self.available_steps]
        if len(step_ids) != len(set(step_ids)):
            errors.append("Duplicate step IDs found in available_steps")
        
        return errors
    
    def get_step_count(self) -> int:
        """Get total number of steps in this config set."""
        return len(self.available_steps)
