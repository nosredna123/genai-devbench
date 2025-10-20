"""
Unit tests for custom experiments base directory feature.

Tests that ExperimentPaths correctly handles custom base directories
and that scripts can use non-default experiment locations.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
import yaml

from src.utils.experiment_paths import ExperimentPaths, ExperimentNotFoundError


class TestCustomExperimentsDir:
    """Test custom experiments base directory functionality."""
    
    def test_default_experiments_dir(self, tmp_path):
        """Test that default experiments directory is used when not specified."""
        # Create project structure
        project_root = tmp_path / "project"
        project_root.mkdir()
        experiments_dir = project_root / "experiments"
        experiments_dir.mkdir()
        
        exp_dir = experiments_dir / "test_exp"
        exp_dir.mkdir()
        
        # Create minimal config
        config_path = exp_dir / "config.yaml"
        config_path.write_text("random_seed: 42\nmodel: gpt-4o")
        
        # Test default path resolution
        paths = ExperimentPaths(
            "test_exp",
            project_root=project_root,
            validate_exists=True
        )
        
        assert paths.experiments_base_dir == experiments_dir
        assert paths.experiment_dir == exp_dir
        assert paths.experiment_name == "test_exp"
    
    def test_custom_experiments_dir(self, tmp_path):
        """Test that custom experiments directory is used when specified."""
        # Create custom experiments directory
        custom_dir = tmp_path / "custom_experiments"
        custom_dir.mkdir()
        
        exp_dir = custom_dir / "my_exp"
        exp_dir.mkdir()
        
        # Create minimal config
        config_path = exp_dir / "config.yaml"
        config_path.write_text("random_seed: 42\nmodel: gpt-4o")
        
        # Test custom path resolution
        paths = ExperimentPaths(
            "my_exp",
            experiments_base_dir=custom_dir,
            validate_exists=True
        )
        
        assert paths.experiments_base_dir == custom_dir
        assert paths.experiment_dir == exp_dir
        assert paths.experiment_name == "my_exp"
    
    def test_custom_dir_overrides_default(self, tmp_path):
        """Test that custom directory overrides default."""
        # Create both default and custom directories
        project_root = tmp_path / "project"
        project_root.mkdir()
        default_dir = project_root / "experiments"
        default_dir.mkdir()
        
        custom_dir = tmp_path / "my_custom_experiments"
        custom_dir.mkdir()
        
        # Create experiment in custom location only
        exp_dir = custom_dir / "test_exp"
        exp_dir.mkdir()
        config_path = exp_dir / "config.yaml"
        config_path.write_text("random_seed: 42\nmodel: gpt-4o")
        
        # Should use custom directory
        paths = ExperimentPaths(
            "test_exp",
            project_root=project_root,
            experiments_base_dir=custom_dir,
            validate_exists=True
        )
        
        assert paths.experiments_base_dir == custom_dir
        assert paths.experiment_dir == custom_dir / "test_exp"
    
    def test_experiment_not_found_in_custom_dir(self, tmp_path):
        """Test that proper error is raised when experiment not in custom dir."""
        custom_dir = tmp_path / "custom_experiments"
        custom_dir.mkdir()
        
        # Try to access non-existent experiment
        with pytest.raises(ExperimentNotFoundError) as exc_info:
            ExperimentPaths(
                "nonexistent",
                experiments_base_dir=custom_dir,
                validate_exists=True
            )
        
        assert "nonexistent" in str(exc_info.value)
        assert str(custom_dir) in str(exc_info.value)
    
    def test_create_experiment_in_custom_dir(self, tmp_path):
        """Test creating new experiment in custom directory."""
        custom_dir = tmp_path / "new_custom_experiments"
        custom_dir.mkdir()
        
        # Create new experiment (validate_exists=False)
        paths = ExperimentPaths(
            "new_exp",
            experiments_base_dir=custom_dir,
            auto_create_structure=True,
            validate_exists=False
        )
        
        assert paths.experiments_base_dir == custom_dir
        assert paths.experiment_dir == custom_dir / "new_exp"
        
        # Verify structure is created in custom location
        assert paths.experiment_dir.exists()
        assert paths.runs_dir.exists()
        assert paths.analysis_dir.exists()
        assert paths.meta_dir.exists()
    
    def test_paths_derived_from_custom_base(self, tmp_path):
        """Test that all paths are correctly derived from custom base."""
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        
        exp_dir = custom_dir / "test_exp"
        exp_dir.mkdir()
        config_path = exp_dir / "config.yaml"
        config_path.write_text("random_seed: 42\nmodel: gpt-4o")
        
        paths = ExperimentPaths(
            "test_exp",
            experiments_base_dir=custom_dir,
            validate_exists=True
        )
        
        # Verify all paths use custom base
        assert paths.runs_dir == custom_dir / "test_exp" / "runs"
        assert paths.analysis_dir == custom_dir / "test_exp" / "analysis"
        assert paths.visualizations_dir == custom_dir / "test_exp" / "analysis" / "visualizations"
        assert paths.meta_dir == custom_dir / "test_exp" / ".meta"
        assert paths.manifest_path == custom_dir / "test_exp" / "runs" / "manifest.json"
        assert paths.config_path == custom_dir / "test_exp" / "config.yaml"
    
    def test_relative_vs_absolute_paths(self, tmp_path):
        """Test that both relative and absolute paths work."""
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        
        exp_dir = custom_dir / "test_exp"
        exp_dir.mkdir()
        config_path = exp_dir / "config.yaml"
        config_path.write_text("random_seed: 42\nmodel: gpt-4o")
        
        # Absolute path
        paths_abs = ExperimentPaths(
            "test_exp",
            experiments_base_dir=custom_dir.absolute(),
            validate_exists=True
        )
        
        assert paths_abs.experiments_base_dir.is_absolute()
        assert paths_abs.experiment_dir.exists()
    
    def test_list_experiments_in_custom_dir(self, tmp_path):
        """Test that error messages list experiments from custom directory."""
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        
        # Create some experiments
        for name in ["exp1", "exp2", "exp3"]:
            exp_dir = custom_dir / name
            exp_dir.mkdir()
            (exp_dir / "config.yaml").write_text("random_seed: 42")
        
        # Try to access non-existent experiment
        with pytest.raises(ExperimentNotFoundError) as exc_info:
            ExperimentPaths(
                "nonexistent",
                experiments_base_dir=custom_dir,
                validate_exists=True
            )
        
        error_msg = str(exc_info.value)
        # Should list experiments from custom directory
        assert "exp1" in error_msg
        assert "exp2" in error_msg
        assert "exp3" in error_msg
    
    def test_empty_custom_experiments_dir(self, tmp_path):
        """Test handling of empty custom experiments directory."""
        custom_dir = tmp_path / "empty_custom"
        custom_dir.mkdir()
        
        with pytest.raises(ExperimentNotFoundError) as exc_info:
            ExperimentPaths(
                "any_exp",
                experiments_base_dir=custom_dir,
                validate_exists=True
            )
        
        assert "no experiments found" in str(exc_info.value)
    
    def test_config_loaded_from_custom_dir(self, tmp_path):
        """Test that config is correctly loaded from custom directory."""
        custom_dir = tmp_path / "custom"
        custom_dir.mkdir()
        
        exp_dir = custom_dir / "test_exp"
        exp_dir.mkdir()
        
        # Create config with test data
        config_data = {
            'random_seed': 123,
            'model': 'gpt-4o',
            'prompts_dir': 'config/prompts',
            'hitl_path': 'config/hitl/test.txt'
        }
        config_path = exp_dir / "config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config_data, f)
        
        paths = ExperimentPaths(
            "test_exp",
            experiments_base_dir=custom_dir,
            validate_exists=True
        )
        
        assert paths.config == config_data
        assert paths.config['random_seed'] == 123
        assert paths.config['model'] == 'gpt-4o'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
