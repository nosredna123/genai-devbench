"""
Unit tests for StepConfig and get_enabled_steps.

Tests step configuration loading, validation, and declaration-order execution.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import yaml

from src.config.step_config import StepConfig, StepsCollection, get_enabled_steps


@pytest.fixture
def temp_experiment_dir():
    """Create temporary experiment directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def config_dir(temp_experiment_dir):
    """Create config directory structure."""
    config_dir = temp_experiment_dir / "config"
    config_dir.mkdir()
    
    prompts_dir = config_dir / "prompts"
    prompts_dir.mkdir()
    
    return config_dir


def create_config_yaml(config_dir: Path, steps: list) -> Path:
    """Helper to create config.yaml with given steps."""
    config_path = config_dir.parent / "config.yaml"
    config = {"steps": steps}
    config_path.write_text(yaml.dump(config))
    return config_path


class TestStepConfig:
    """Test StepConfig dataclass."""
    
    def test_step_config_creation(self):
        """Test creating StepConfig instance."""
        step = StepConfig(
            id=1,
            name="Test Step",
            enabled=True,
            prompt_file="config/prompts/01_test.txt"
        )
        
        assert step.id == 1
        assert step.name == "Test Step"
        assert step.enabled is True
        assert step.prompt_file == "config/prompts/01_test.txt"
    
    def test_step_config_disabled(self):
        """Test StepConfig with disabled step."""
        step = StepConfig(
            id=2,
            name="Disabled Step",
            enabled=False,
            prompt_file="config/prompts/02_disabled.txt"
        )
        
        assert step.enabled is False


class TestStepsCollection:
    """Test StepsCollection functionality."""
    
    def test_get_enabled_steps_all_enabled(self, temp_experiment_dir):
        """Test getting enabled steps when all are enabled."""
        # Create prompt files
        prompts_dir = temp_experiment_dir / "config" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "01.txt").write_text("Prompt 1")
        (prompts_dir / "02.txt").write_text("Prompt 2")
        (prompts_dir / "03.txt").write_text("Prompt 3")
        
        steps = [
            StepConfig(1, True, "Step 1", "config/prompts/01.txt"),
            StepConfig(2, True, "Step 2", "config/prompts/02.txt"),
            StepConfig(3, True, "Step 3", "config/prompts/03.txt")
        ]
        
        collection = StepsCollection(steps, temp_experiment_dir)
        enabled = collection.get_enabled_steps()
        
        assert len(enabled) == 3
        assert enabled[0].id == 1
        assert enabled[1].id == 2
        assert enabled[2].id == 3
    
    def test_get_enabled_steps_some_disabled(self, temp_experiment_dir):
        """Test getting enabled steps when some are disabled."""
        # Create prompt files
        prompts_dir = temp_experiment_dir / "config" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "01.txt").write_text("Prompt 1")
        (prompts_dir / "02.txt").write_text("Prompt 2")
        (prompts_dir / "03.txt").write_text("Prompt 3")
        
        steps = [
            StepConfig(1, True, "Step 1", "config/prompts/01.txt"),
            StepConfig(2, False, "Step 2", "config/prompts/02.txt"),  # Disabled
            StepConfig(3, True, "Step 3", "config/prompts/03.txt")
        ]
        
        collection = StepsCollection(steps, temp_experiment_dir)
        enabled = collection.get_enabled_steps()
        
        assert len(enabled) == 2
        assert enabled[0].id == 1
        assert enabled[1].id == 3  # Skip disabled step 2
    
    def test_get_enabled_steps_none_enabled(self, temp_experiment_dir):
        """Test getting enabled steps when all are disabled."""
        # Create prompt files
        prompts_dir = temp_experiment_dir / "config" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "01.txt").write_text("Prompt 1")
        (prompts_dir / "02.txt").write_text("Prompt 2")
        (prompts_dir / "03.txt").write_text("Prompt 3")
        
        steps = [
            StepConfig(1, False, "Step 1", "config/prompts/01.txt"),
            StepConfig(2, False, "Step 2", "config/prompts/02.txt"),
            StepConfig(3, False, "Step 3", "config/prompts/03.txt")
        ]
        
        collection = StepsCollection(steps, temp_experiment_dir)
        enabled = collection.get_enabled_steps()
        
        assert len(enabled) == 0
    
    def test_get_enabled_steps_preserves_declaration_order(self, temp_experiment_dir):
        """Test that enabled steps preserve declaration order."""
        # Create prompt files
        prompts_dir = temp_experiment_dir / "config" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "01.txt").write_text("Prompt 1")
        (prompts_dir / "02.txt").write_text("Prompt 2")
        (prompts_dir / "03.txt").write_text("Prompt 3")
        (prompts_dir / "05.txt").write_text("Prompt 5")
        (prompts_dir / "99.txt").write_text("Prompt 99")
        
        # Non-sequential IDs in specific order
        steps = [
            StepConfig(5, True, "Step 5", "config/prompts/05.txt"),
            StepConfig(1, True, "Step 1", "config/prompts/01.txt"),
            StepConfig(99, True, "Step 99", "config/prompts/99.txt"),
            StepConfig(2, True, "Step 2", "config/prompts/02.txt")
        ]
        
        collection = StepsCollection(steps, temp_experiment_dir)
        enabled = collection.get_enabled_steps()
        
        # Should preserve declaration order, not sort by ID
        assert len(enabled) == 4
        assert enabled[0].id == 5
        assert enabled[1].id == 1
        assert enabled[2].id == 99
        assert enabled[3].id == 2
    
    def test_declaration_order_with_disabled_steps(self, temp_experiment_dir):
        """Test declaration order with some steps disabled."""
        # Create prompt files
        prompts_dir = temp_experiment_dir / "config" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "01.txt").write_text("Prompt 1")
        (prompts_dir / "02.txt").write_text("Prompt 2")
        (prompts_dir / "03.txt").write_text("Prompt 3")
        (prompts_dir / "04.txt").write_text("Prompt 4")
        (prompts_dir / "07.txt").write_text("Prompt 7")
        (prompts_dir / "99.txt").write_text("Prompt 99")
        
        steps = [
            StepConfig(3, True, "Step 3", "config/prompts/03.txt"),
            StepConfig(1, False, "Step 1", "config/prompts/01.txt"),  # Disabled
            StepConfig(2, True, "Step 2", "config/prompts/02.txt"),
            StepConfig(4, False, "Step 4", "config/prompts/04.txt")   # Disabled
        ]
        
        collection = StepsCollection(steps, temp_experiment_dir)
        enabled = collection.get_enabled_steps()
        
        # Should maintain order: 3, 2 (skip disabled 1 and 4)
        assert len(enabled) == 2
        assert enabled[0].id == 3
        assert enabled[1].id == 2


class TestGetEnabledSteps:
    """Test get_enabled_steps helper function."""
    
    def test_get_enabled_steps_basic(self, config_dir):
        """Test basic get_enabled_steps functionality."""
        # Create prompt files
        (config_dir / "prompts" / "01.txt").write_text("Prompt 1")
        (config_dir / "prompts" / "02.txt").write_text("Prompt 2")
        
        steps = [
            {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01.txt"},
            {"id": 2, "name": "Step 2", "enabled": True, "prompt_file": "config/prompts/02.txt"}
        ]
        config_path = create_config_yaml(config_dir, steps)
        
        # Load config dict and pass to get_enabled_steps
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, config_dir.parent)
        
        assert len(enabled) == 2
        assert enabled[0].id == 1
        assert enabled[1].id == 2
    
    def test_get_enabled_steps_with_disabled(self, config_dir):
        """Test get_enabled_steps with disabled steps."""
        # Create prompt files
        (config_dir / "prompts" / "01.txt").write_text("Prompt 1")
        (config_dir / "prompts" / "02.txt").write_text("Prompt 2")
        (config_dir / "prompts" / "03.txt").write_text("Prompt 3")
        
        steps = [
            {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01.txt"},
            {"id": 2, "name": "Step 2", "enabled": False, "prompt_file": "config/prompts/02.txt"},
            {"id": 3, "name": "Step 3", "enabled": True, "prompt_file": "config/prompts/03.txt"}
        ]
        config_path = create_config_yaml(config_dir, steps)
        
        # Load config dict and pass to get_enabled_steps
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, config_dir.parent)
        
        assert len(enabled) == 2
        assert enabled[0].id == 1
        assert enabled[1].id == 3
    
    def test_get_enabled_steps_declaration_order(self, config_dir):
        """Test that get_enabled_steps preserves declaration order."""
        # Create prompt files
        (config_dir / "prompts" / "02.txt").write_text("Prompt 2")
        (config_dir / "prompts" / "05.txt").write_text("Prompt 5")
        (config_dir / "prompts" / "10.txt").write_text("Prompt 10")
        
        steps = [
            {"id": 10, "name": "Step 10", "enabled": True, "prompt_file": "config/prompts/10.txt"},
            {"id": 2, "name": "Step 2", "enabled": True, "prompt_file": "config/prompts/02.txt"},
            {"id": 5, "name": "Step 5", "enabled": True, "prompt_file": "config/prompts/05.txt"}
        ]
        config_path = create_config_yaml(config_dir, steps)
        
        # Load config dict and pass to get_enabled_steps
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, config_dir.parent)
        
        # Should be in declaration order: 10, 2, 5
        assert len(enabled) == 3
        assert enabled[0].id == 10
        assert enabled[1].id == 2
        assert enabled[2].id == 5
    
    def test_get_enabled_steps_empty_list(self, config_dir):
        """Test get_enabled_steps with empty steps list raises error."""
        from src.config.exceptions import StepValidationError
        
        steps = []
        config_path = create_config_yaml(config_dir, steps)
        
        # Load config dict and pass to get_enabled_steps
        loaded_config = yaml.safe_load(config_path.read_text())
        
        # Empty list should raise validation error
        with pytest.raises(StepValidationError, match="'steps' list cannot be empty"):
            get_enabled_steps(loaded_config, config_dir.parent)
    
    def test_get_enabled_steps_all_disabled(self, config_dir):
        """Test get_enabled_steps when all steps are disabled."""
        # Create prompt files (even though disabled, they must exist for validation)
        (config_dir / "prompts" / "01.txt").write_text("Prompt 1")
        (config_dir / "prompts" / "02.txt").write_text("Prompt 2")
        
        steps = [
            {"id": 1, "name": "Step 1", "enabled": False, "prompt_file": "config/prompts/01.txt"},
            {"id": 2, "name": "Step 2", "enabled": False, "prompt_file": "config/prompts/02.txt"}
        ]
        config_path = create_config_yaml(config_dir, steps)
        
        # Load config dict and pass to get_enabled_steps
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, config_dir.parent)
        
        assert len(enabled) == 0
    
    def test_step_name_preservation(self, config_dir):
        """Test that step names are preserved."""
        # Create prompt files
        (config_dir / "prompts" / "01.txt").write_text("Prompt 1")
        (config_dir / "prompts" / "02.txt").write_text("Prompt 2")
        
        steps = [
            {"id": 1, "name": "Create User API", "enabled": True, "prompt_file": "config/prompts/01.txt"},
            {"id": 2, "name": "Add Authentication", "enabled": True, "prompt_file": "config/prompts/02.txt"}
        ]
        config_path = create_config_yaml(config_dir, steps)
        
        # Load config dict and pass to get_enabled_steps
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, config_dir.parent)
        
        assert enabled[0].name == "Create User API"
        assert enabled[1].name == "Add Authentication"
    
    def test_prompt_file_paths(self, config_dir):
        """Test that prompt file paths are correctly loaded."""
        # Create prompt file
        (config_dir / "prompts" / "01_custom.txt").write_text("Custom prompt")
        
        steps = [
            {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01_custom.txt"}
        ]
        config_path = create_config_yaml(config_dir, steps)
        
        # Load config dict and pass to get_enabled_steps
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, config_dir.parent)
        
        assert enabled[0].prompt_file == "config/prompts/01_custom.txt"
    
    def test_reordered_steps_execution(self, config_dir):
        """Test researcher can reorder steps by moving YAML entries."""
        # Create prompt files
        (config_dir / "prompts" / "01.txt").write_text("Prompt 1")
        (config_dir / "prompts" / "02.txt").write_text("Prompt 2")
        (config_dir / "prompts" / "03.txt").write_text("Prompt 3")
        
        # Original order: 1, 2, 3
        # Researcher reorders to: 3, 1, 2
        steps = [
            {"id": 3, "name": "Step 3", "enabled": True, "prompt_file": "config/prompts/03.txt"},
            {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01.txt"},
            {"id": 2, "name": "Step 2", "enabled": True, "prompt_file": "config/prompts/02.txt"}
        ]
        config_path = create_config_yaml(config_dir, steps)
        
        # Load config dict and pass to get_enabled_steps
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, config_dir.parent)
        
        # Execution order should be: 3, 1, 2
        assert len(enabled) == 3
        assert enabled[0].id == 3
        assert enabled[1].id == 1
        assert enabled[2].id == 2
    
    def test_complex_reordering_with_gaps(self, config_dir):
        """Test complex reordering scenario with disabled steps."""
        # Create prompt files
        (config_dir / "prompts" / "01.txt").write_text("Prompt 1")
        (config_dir / "prompts" / "02.txt").write_text("Prompt 2")
        (config_dir / "prompts" / "03.txt").write_text("Prompt 3")
        (config_dir / "prompts" / "05.txt").write_text("Prompt 5")
        (config_dir / "prompts" / "07.txt").write_text("Prompt 7")
        
        # Researcher's custom order with gaps
        steps = [
            {"id": 5, "name": "Step 5", "enabled": True, "prompt_file": "config/prompts/05.txt"},
            {"id": 2, "name": "Step 2", "enabled": False, "prompt_file": "config/prompts/02.txt"},
            {"id": 7, "name": "Step 7", "enabled": True, "prompt_file": "config/prompts/07.txt"},
            {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01.txt"},
            {"id": 3, "name": "Step 3", "enabled": False, "prompt_file": "config/prompts/03.txt"}
        ]
        config_path = create_config_yaml(config_dir, steps)
        
        # Load config dict and pass to get_enabled_steps
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, config_dir.parent)
        
        # Should execute: 5, 7, 1 (skip disabled 2 and 3)
        assert len(enabled) == 3
        assert enabled[0].id == 5
        assert enabled[1].id == 7
        assert enabled[2].id == 1
