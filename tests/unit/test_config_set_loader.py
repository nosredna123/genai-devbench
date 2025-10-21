"""
Unit tests for ConfigSetLoader.

Tests config set discovery, loading, and validation.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import yaml

from src.config_sets.loader import ConfigSetLoader
from src.config_sets.exceptions import ConfigSetNotFoundError, ConfigSetValidationError


@pytest.fixture
def temp_config_sets_dir():
    """Create temporary config sets directory."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture
def valid_config_set(temp_config_sets_dir):
    """Create a valid config set."""
    config_set_dir = temp_config_sets_dir / "test_set"
    config_set_dir.mkdir()
    
    # Create prompts directory
    prompts_dir = config_set_dir / "prompts"
    prompts_dir.mkdir()
    (prompts_dir / "01_test_step.txt").write_text("Test prompt")
    
    # Create hitl directory
    hitl_dir = config_set_dir / "hitl"
    hitl_dir.mkdir()
    (hitl_dir / "expanded_spec.txt").write_text("Test spec")
    
    # Create metadata.yaml
    metadata = {
        "name": "test_set",
        "version": "1.0.0",
        "description": "Test config set",
        "available_steps": [
            {
                "id": 1,
                "name": "Test Step",
                "prompt_file": "prompts/01_test_step.txt",
                "description": "A test step"
            }
        ]
    }
    (config_set_dir / "metadata.yaml").write_text(yaml.dump(metadata))
    
    # Create experiment_template.yaml
    template = {
        "steps": [
            {
                "id": 1,
                "name": "Test Step",
                "enabled": True,
                "prompt_file": "config/prompts/01_test_step.txt"
            }
        ],
        "timeout": {
            "per_step": 600,
            "total": 3600
        }
    }
    (config_set_dir / "experiment_template.yaml").write_text(yaml.dump(template))
    
    return config_set_dir


class TestConfigSetLoader:
    """Test ConfigSetLoader functionality."""
    
    def test_list_config_sets_empty_directory(self, temp_config_sets_dir):
        """Test listing config sets in empty directory."""
        loader = ConfigSetLoader(temp_config_sets_dir)
        config_sets = loader.list_available()
        assert len(config_sets) == 0
    
    def test_list_config_sets_with_valid_set(self, temp_config_sets_dir, valid_config_set):
        """Test listing config sets with one valid set."""
        loader = ConfigSetLoader(temp_config_sets_dir)
        config_set_names = loader.list_available()
        assert len(config_set_names) == 1
        assert "test_set" in config_set_names
    
    def test_load_valid_config_set(self, temp_config_sets_dir, valid_config_set):
        """Test loading a valid config set."""
        loader = ConfigSetLoader(temp_config_sets_dir)
        config_set = loader.load("test_set")
        
        assert config_set.name == "test_set"
        assert config_set.description == "Test config set"
        assert len(config_set.available_steps) == 1
        assert config_set.available_steps[0].id == 1
        assert config_set.available_steps[0].name == "Test Step"
    
    def test_load_nonexistent_config_set(self, temp_config_sets_dir):
        """Test loading a config set that doesn't exist."""
        loader = ConfigSetLoader(temp_config_sets_dir)
        
        with pytest.raises(ConfigSetNotFoundError) as exc_info:
            loader.load("nonexistent")
        
        assert "nonexistent" in str(exc_info.value)
    
    def test_validation_missing_metadata(self, temp_config_sets_dir):
        """Test validation fails when metadata.yaml is missing."""
        config_set_dir = temp_config_sets_dir / "invalid_set"
        config_set_dir.mkdir()
        
        loader = ConfigSetLoader(temp_config_sets_dir)
        config_set_names = loader.list_available()
        
        # Should not include invalid config set
        assert len(config_set_names) == 0
    
    def test_validation_missing_prompts_dir(self, temp_config_sets_dir):
        """Test validation fails when prompts directory is missing."""
        config_set_dir = temp_config_sets_dir / "no_prompts"
        config_set_dir.mkdir()
        
        # Create metadata only
        metadata = {
            "name": "no_prompts",
            "version": "1.0.0",
            "description": "Missing prompts",
            "available_steps": []
        }
        (config_set_dir / "metadata.yaml").write_text(yaml.dump(metadata))
        
        loader = ConfigSetLoader(temp_config_sets_dir)
        
        # Should be listed (validation happens on load)
        assert "no_prompts" in loader.list_available()
        
        # But loading should fail
        with pytest.raises(ConfigSetValidationError):
            loader.load("no_prompts")
    
    def test_validation_missing_template(self, temp_config_sets_dir):
        """Test validation fails when experiment_template.yaml is missing."""
        config_set_dir = temp_config_sets_dir / "no_template"
        config_set_dir.mkdir()
        (config_set_dir / "prompts").mkdir()
        (config_set_dir / "hitl").mkdir()
        
        metadata = {
            "name": "no_template",
            "version": "1.0.0",
            "description": "Missing template",
            "available_steps": []
        }
        (config_set_dir / "metadata.yaml").write_text(yaml.dump(metadata))
        
        loader = ConfigSetLoader(temp_config_sets_dir)
        
        # Should be listed
        assert "no_template" in loader.list_available()
        
        # But loading should fail
        with pytest.raises(ConfigSetValidationError):
            loader.load("no_template")
    
    def test_load_config_set_with_multiple_steps(self, temp_config_sets_dir):
        """Test loading config set with multiple steps."""
        config_set_dir = temp_config_sets_dir / "multi_step"
        config_set_dir.mkdir()
        
        prompts_dir = config_set_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "01_step1.txt").write_text("Step 1")
        (prompts_dir / "02_step2.txt").write_text("Step 2")
        
        hitl_dir = config_set_dir / "hitl"
        hitl_dir.mkdir()
        (hitl_dir / "expanded_spec.txt").write_text("Spec")
        
        metadata = {
            "name": "multi_step",
            "version": "1.0.0",
            "description": "Multiple steps",
            "available_steps": [
                {"id": 1, "name": "Step 1", "prompt_file": "prompts/01_step1.txt", "description": "First"},
                {"id": 2, "name": "Step 2", "prompt_file": "prompts/02_step2.txt", "description": "Second"}
            ]
        }
        (config_set_dir / "metadata.yaml").write_text(yaml.dump(metadata))
        
        template = {
            "steps": [
                {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01_step1.txt"},
                {"id": 2, "name": "Step 2", "enabled": True, "prompt_file": "config/prompts/02_step2.txt"}
            ]
        }
        (config_set_dir / "experiment_template.yaml").write_text(yaml.dump(template))
        
        loader = ConfigSetLoader(temp_config_sets_dir)
        config_set = loader.load("multi_step")
        
        assert len(config_set.available_steps) == 2
        assert config_set.available_steps[0].id == 1
        assert config_set.available_steps[1].id == 2
    
    def test_config_set_has_path(self, temp_config_sets_dir, valid_config_set):
        """Test that loaded config set has a base_path."""
        loader = ConfigSetLoader(temp_config_sets_dir)
        config_set = loader.load("test_set")
        
        assert config_set.base_path == valid_config_set
        assert config_set.base_path.exists()
        assert config_set.base_path.is_dir()
    
    def test_invalid_metadata_yaml(self, temp_config_sets_dir):
        """Test handling of invalid YAML in metadata."""
        config_set_dir = temp_config_sets_dir / "bad_yaml"
        config_set_dir.mkdir()
        (config_set_dir / "prompts").mkdir()
        (config_set_dir / "hitl").mkdir()
        
        # Write invalid YAML
        (config_set_dir / "metadata.yaml").write_text("invalid: yaml: content:")
        
        template = {"steps": []}
        (config_set_dir / "experiment_template.yaml").write_text(yaml.dump(template))
        
        loader = ConfigSetLoader(temp_config_sets_dir)
        
        # Should be listed (has metadata.yaml)
        assert "bad_yaml" in loader.list_available()
        
        # But loading should fail
        with pytest.raises((ConfigSetValidationError, yaml.YAMLError)):
            loader.load("bad_yaml")


class TestConfigSetValidation:
    """Test config set validation rules."""
    
    def test_required_fields_in_metadata(self, temp_config_sets_dir):
        """Test that all required fields are validated."""
        config_set_dir = temp_config_sets_dir / "incomplete"
        config_set_dir.mkdir()
        (config_set_dir / "prompts").mkdir()
        (config_set_dir / "hitl").mkdir()
        
        # Missing required fields
        metadata = {
            "name": "incomplete"
            # Missing version, description, available_steps
        }
        (config_set_dir / "metadata.yaml").write_text(yaml.dump(metadata))
        
        template = {"steps": []}
        (config_set_dir / "experiment_template.yaml").write_text(yaml.dump(template))
        
        loader = ConfigSetLoader(temp_config_sets_dir)
        
        # Should be listed
        assert "incomplete" in loader.list_available()
        
        # But loading should fail
        with pytest.raises((ConfigSetValidationError, KeyError)):
            loader.load("incomplete")
    
    def test_step_metadata_validation(self, temp_config_sets_dir):
        """Test validation of step metadata fields."""
        config_set_dir = temp_config_sets_dir / "bad_steps"
        config_set_dir.mkdir()
        (config_set_dir / "prompts").mkdir()
        (config_set_dir / "hitl").mkdir()
        
        # Steps with missing fields
        metadata = {
            "name": "bad_steps",
            "version": "1.0.0",
            "description": "Bad step metadata",
            "available_steps": [
                {"id": 1}  # Missing name and description
            ]
        }
        (config_set_dir / "metadata.yaml").write_text(yaml.dump(metadata))
        
        template = {"steps": [{"id": 1}]}
        (config_set_dir / "experiment_template.yaml").write_text(yaml.dump(template))
        
        loader = ConfigSetLoader(temp_config_sets_dir)
        
        # Should be listed
        assert "bad_steps" in loader.list_available()
        
        # But loading should fail
        with pytest.raises((ConfigSetValidationError, KeyError)):
            loader.load("bad_steps")
