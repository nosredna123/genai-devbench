"""
Integration tests for Config Sets end-to-end workflow.

Tests the complete workflow from generation to execution.
"""

import pytest
from pathlib import Path
import tempfile
import shutil
import yaml
import subprocess

from src.config_sets.loader import ConfigSetLoader
from src.config.step_config import get_enabled_steps


@pytest.fixture
def temp_workspace():
    """Create temporary workspace for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


class TestEndToEndWorkflow:
    """Test complete workflow from generation to execution."""
    
    def test_list_available_config_sets(self):
        """Test listing available config sets from real config_sets/ directory."""
        config_sets_dir = Path(__file__).parent.parent.parent / "config_sets"
        loader = ConfigSetLoader(config_sets_dir)
        
        config_set_names = loader.list_available()
        
        # Should have at least default and minimal
        assert len(config_set_names) >= 2
        assert "default" in config_set_names
        assert "minimal" in config_set_names
    
    def test_load_default_config_set(self):
        """Test loading the default config set."""
        config_sets_dir = Path(__file__).parent.parent.parent / "config_sets"
        loader = ConfigSetLoader(config_sets_dir)
        
        config_set = loader.load("default")
        
        assert config_set.name == "default"
        assert len(config_set.available_steps) == 6  # Default has 6 steps
        assert all(step.id in range(1, 7) for step in config_set.available_steps)
    
    def test_load_minimal_config_set(self):
        """Test loading the minimal config set."""
        config_sets_dir = Path(__file__).parent.parent.parent / "config_sets"
        loader = ConfigSetLoader(config_sets_dir)
        
        config_set = loader.load("minimal")
        
        assert config_set.name == "minimal"
        assert len(config_set.available_steps) == 1  # Minimal has 1 step
        assert config_set.available_steps[0].id == 1
    
    def test_generate_experiment_structure(self, temp_workspace):
        """Test generating experiment creates correct structure."""
        # Simulate generator creating experiment
        exp_dir = temp_workspace / "test_experiment"
        exp_dir.mkdir()
        
        config_dir = exp_dir / "config"
        config_dir.mkdir()
        
        prompts_dir = config_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "01_test.txt").write_text("Test prompt")
        
        hitl_dir = config_dir / "hitl"
        hitl_dir.mkdir()
        (hitl_dir / "expanded_spec.txt").write_text("Test spec")
        
        # Create config.yaml
        config = {
            "steps": [
                {
                    "id": 1,
                    "name": "Test Step",
                    "enabled": True,
                    "prompt_file": "config/prompts/01_test.txt"
                }
            ],
            "timeout": {"per_step": 600, "total": 3600}
        }
        (exp_dir / "config.yaml").write_text(yaml.dump(config))
        
        # Verify structure
        assert (exp_dir / "config.yaml").exists()
        assert (config_dir / "prompts").exists()
        assert (config_dir / "hitl").exists()
        assert (prompts_dir / "01_test.txt").exists()
    
    def test_load_generated_config(self, temp_workspace):
        """Test loading config from generated experiment."""
        # Create generated experiment
        exp_dir = temp_workspace / "test_experiment"
        exp_dir.mkdir()
        
        config_dir = exp_dir / "config"
        config_dir.mkdir()
        
        # Create prompts directory and prompt files
        prompts_dir = config_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "01.txt").write_text("Prompt 1")
        (prompts_dir / "02.txt").write_text("Prompt 2")
        (prompts_dir / "03.txt").write_text("Prompt 3")
        
        # Create config.yaml with steps
        config = {
            "steps": [
                {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01.txt"},
                {"id": 2, "name": "Step 2", "enabled": True, "prompt_file": "config/prompts/02.txt"},
                {"id": 3, "name": "Step 3", "enabled": True, "prompt_file": "config/prompts/03.txt"}
            ]
        }
        config_path = exp_dir / "config.yaml"
        config_path.write_text(yaml.dump(config))
        
        # Load enabled steps - pass config dict, not path
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, exp_dir)
        
        assert len(enabled) == 3
        assert all(step.enabled for step in enabled)
    
    def test_customize_disable_step(self, temp_workspace):
        """Test researcher customization: disable a step."""
        exp_dir = temp_workspace / "test_experiment"
        exp_dir.mkdir()
        
        # Create prompts directory and prompt files
        prompts_dir = exp_dir / "config" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "01.txt").write_text("Prompt 1")
        (prompts_dir / "02.txt").write_text("Prompt 2")
        (prompts_dir / "03.txt").write_text("Prompt 3")
        
        # Config with 3 steps
        config = {
            "steps": [
                {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01.txt"},
                {"id": 2, "name": "Step 2", "enabled": True, "prompt_file": "config/prompts/02.txt"},
                {"id": 3, "name": "Step 3", "enabled": True, "prompt_file": "config/prompts/03.txt"}
            ]
        }
        config_path = exp_dir / "config.yaml"
        config_path.write_text(yaml.dump(config))
        
        # Researcher disables step 2
        config["steps"][1]["enabled"] = False
        config_path.write_text(yaml.dump(config))
        
        # Load enabled steps
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, exp_dir)
        
        # Should only have steps 1 and 3
        assert len(enabled) == 2
        assert enabled[0].id == 1
        assert enabled[1].id == 3
    
    def test_customize_reorder_steps(self, temp_workspace):
        """Test researcher customization: reorder steps."""
        exp_dir = temp_workspace / "test_experiment"
        exp_dir.mkdir()
        
        # Create prompts directory and prompt files
        prompts_dir = exp_dir / "config" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "01.txt").write_text("Prompt 1")
        (prompts_dir / "02.txt").write_text("Prompt 2")
        (prompts_dir / "03.txt").write_text("Prompt 3")
        
        # Researcher reorders steps: 3, 1, 2
        config = {
            "steps": [
                {"id": 3, "name": "Step 3", "enabled": True, "prompt_file": "config/prompts/03.txt"},
                {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01.txt"},
                {"id": 2, "name": "Step 2", "enabled": True, "prompt_file": "config/prompts/02.txt"}
            ]
        }
        config_path = exp_dir / "config.yaml"
        config_path.write_text(yaml.dump(config))
        
        # Load enabled steps
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, exp_dir)
        
        # Execution order should match declaration order
        assert len(enabled) == 3
        assert enabled[0].id == 3
        assert enabled[1].id == 1
        assert enabled[2].id == 2
    
    def test_customize_complex_scenario(self, temp_workspace):
        """Test complex customization: reorder + disable."""
        exp_dir = temp_workspace / "test_experiment"
        exp_dir.mkdir()
        
        # Create prompts directory and prompt files
        prompts_dir = exp_dir / "config" / "prompts"
        prompts_dir.mkdir(parents=True)
        for i in range(1, 6):
            (prompts_dir / f"0{i}.txt").write_text(f"Prompt {i}")
        
        # Researcher:
        # 1. Moves step 5 to first position
        # 2. Disables step 2
        # 3. Keeps others in modified order
        config = {
            "steps": [
                {"id": 5, "name": "Step 5", "enabled": True, "prompt_file": "config/prompts/05.txt"},
                {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01.txt"},
                {"id": 2, "name": "Step 2", "enabled": False, "prompt_file": "config/prompts/02.txt"},
                {"id": 3, "name": "Step 3", "enabled": True, "prompt_file": "config/prompts/03.txt"},
                {"id": 4, "name": "Step 4", "enabled": True, "prompt_file": "config/prompts/04.txt"}
            ]
        }
        config_path = exp_dir / "config.yaml"
        config_path.write_text(yaml.dump(config))
        
        # Load enabled steps
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, exp_dir)
        
        # Should execute: 5, 1, 3, 4 (skip disabled 2)
        assert len(enabled) == 4
        assert enabled[0].id == 5
        assert enabled[1].id == 1
        assert enabled[2].id == 3
        assert enabled[3].id == 4
    
    def test_verify_step_ids_preserved(self, temp_workspace):
        """Test that original step IDs are preserved for metrics."""
        exp_dir = temp_workspace / "test_experiment"
        exp_dir.mkdir()
        
        # Create prompts directory and prompt files
        prompts_dir = exp_dir / "config" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "10.txt").write_text("Prompt 10")
        (prompts_dir / "05.txt").write_text("Prompt 5")
        (prompts_dir / "99.txt").write_text("Prompt 99")
        
        # Non-sequential IDs
        config = {
            "steps": [
                {"id": 10, "name": "Step 10", "enabled": True, "prompt_file": "config/prompts/10.txt"},
                {"id": 5, "name": "Step 5", "enabled": True, "prompt_file": "config/prompts/05.txt"},
                {"id": 99, "name": "Step 99", "enabled": True, "prompt_file": "config/prompts/99.txt"}
            ]
        }
        config_path = exp_dir / "config.yaml"
        config_path.write_text(yaml.dump(config))
        
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, exp_dir)
        
        # IDs should be preserved exactly
        assert enabled[0].id == 10
        assert enabled[1].id == 5
        assert enabled[2].id == 99
    
    def test_self_contained_experiment(self, temp_workspace):
        """Test that generated experiment is self-contained."""
        exp_dir = temp_workspace / "test_experiment"
        exp_dir.mkdir()
        
        config_dir = exp_dir / "config"
        config_dir.mkdir()
        
        # Create all necessary files
        prompts_dir = config_dir / "prompts"
        prompts_dir.mkdir()
        (prompts_dir / "01_test.txt").write_text("Test prompt")
        
        hitl_dir = config_dir / "hitl"
        hitl_dir.mkdir()
        (hitl_dir / "expanded_spec.txt").write_text("Test spec")
        
        config = {
            "steps": [
                {"id": 1, "name": "Test", "enabled": True, "prompt_file": "config/prompts/01_test.txt"}
            ]
        }
        (exp_dir / "config.yaml").write_text(yaml.dump(config))
        
        # Verify all files exist locally
        assert (exp_dir / "config.yaml").exists()
        assert (prompts_dir / "01_test.txt").exists()
        assert (hitl_dir / "expanded_spec.txt").exists()
        
        # No references to config_sets/ needed
        config_content = (exp_dir / "config.yaml").read_text()
        assert "config_sets" not in config_content


class TestFailFastValidation:
    """Test fail-fast validation behavior."""
    
    def test_missing_config_yaml(self, temp_workspace):
        """Test that missing config.yaml is detected."""
        exp_dir = temp_workspace / "test_experiment"
        exp_dir.mkdir()
        
        config_path = exp_dir / "config.yaml"
        
        # Attempt to load from non-existent config - must try to read it first
        with pytest.raises(FileNotFoundError):
            loaded_config = yaml.safe_load(config_path.read_text())
            get_enabled_steps(loaded_config, exp_dir)
    
    def test_invalid_yaml_syntax(self, temp_workspace):
        """Test that invalid YAML syntax is detected."""
        exp_dir = temp_workspace / "test_experiment"
        exp_dir.mkdir()
        
        config_path = exp_dir / "config.yaml"
        config_path.write_text("invalid: yaml: syntax:")
        
        # Should fail to parse
        with pytest.raises(yaml.YAMLError):
            loaded_config = yaml.safe_load(config_path.read_text())
            get_enabled_steps(loaded_config, exp_dir)
    
    def test_missing_steps_field(self, temp_workspace):
        """Test that missing 'steps' field is detected."""
        exp_dir = temp_workspace / "test_experiment"
        exp_dir.mkdir()
        
        config = {"timeout": 600}  # Missing 'steps'
        config_path = exp_dir / "config.yaml"
        config_path.write_text(yaml.dump(config))
        
        # Should fail with appropriate error
        with pytest.raises((KeyError, TypeError)):
            get_enabled_steps(config_path, exp_dir)


class TestDeclarationOrderExecution:
    """Test declaration-order execution behavior."""
    
    def test_declaration_order_not_sorted(self, temp_workspace):
        """Test that steps are NOT sorted by ID."""
        exp_dir = temp_workspace / "test_experiment"
        exp_dir.mkdir()
        
        # Create prompts directory and prompt files
        prompts_dir = exp_dir / "config" / "prompts"
        prompts_dir.mkdir(parents=True)
        for i in range(1, 7):
            (prompts_dir / f"0{i}.txt").write_text(f"Prompt {i}")
        
        # IDs in reverse order
        config = {
            "steps": [
                {"id": 6, "name": "Step 6", "enabled": True, "prompt_file": "config/prompts/06.txt"},
                {"id": 5, "name": "Step 5", "enabled": True, "prompt_file": "config/prompts/05.txt"},
                {"id": 4, "name": "Step 4", "enabled": True, "prompt_file": "config/prompts/04.txt"},
                {"id": 3, "name": "Step 3", "enabled": True, "prompt_file": "config/prompts/03.txt"},
                {"id": 2, "name": "Step 2", "enabled": True, "prompt_file": "config/prompts/02.txt"},
                {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01.txt"}
            ]
        }
        config_path = exp_dir / "config.yaml"
        config_path.write_text(yaml.dump(config))
        
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, exp_dir)
        
        # Should be in declaration order (6, 5, 4, 3, 2, 1)
        assert [s.id for s in enabled] == [6, 5, 4, 3, 2, 1]
    
    def test_arbitrary_order(self, temp_workspace):
        """Test arbitrary declaration order."""
        exp_dir = temp_workspace / "test_experiment"
        exp_dir.mkdir()
        
        # Create prompts directory and prompt files
        prompts_dir = exp_dir / "config" / "prompts"
        prompts_dir.mkdir(parents=True)
        (prompts_dir / "01.txt").write_text("Prompt 1")
        (prompts_dir / "02.txt").write_text("Prompt 2")
        (prompts_dir / "03.txt").write_text("Prompt 3")
        (prompts_dir / "05.txt").write_text("Prompt 5")
        (prompts_dir / "07.txt").write_text("Prompt 7")
        
        # Random order
        config = {
            "steps": [
                {"id": 3, "name": "Step 3", "enabled": True, "prompt_file": "config/prompts/03.txt"},
                {"id": 7, "name": "Step 7", "enabled": True, "prompt_file": "config/prompts/07.txt"},
                {"id": 1, "name": "Step 1", "enabled": True, "prompt_file": "config/prompts/01.txt"},
                {"id": 5, "name": "Step 5", "enabled": True, "prompt_file": "config/prompts/05.txt"},
                {"id": 2, "name": "Step 2", "enabled": True, "prompt_file": "config/prompts/02.txt"}
            ]
        }
        config_path = exp_dir / "config.yaml"
        config_path.write_text(yaml.dump(config))
        
        loaded_config = yaml.safe_load(config_path.read_text())
        enabled = get_enabled_steps(loaded_config, exp_dir)
        
        # Should preserve exact order: 3, 7, 1, 5, 2
        assert [s.id for s in enabled] == [3, 7, 1, 5, 2]


class TestMinimalEndToEnd:
    """
    Simple end-to-end integration test using minimal config set.
    
    Tests the complete generation flow: load config set → generate experiment → verify structure.
    This validates that cost calculation, report generation, and statistical analysis 
    utilities are correctly included in generated experiments.
    """
    
    def test_generate_minimal_experiment_end_to_end(self, temp_workspace):
        """
        Test complete experiment generation from minimal config set.
        
        This test verifies:
        1. Config set loads correctly
        2. Experiment generates with correct structure
        3. All required files are present (config, utils, templates)
        4. Cost calculator utility is included
        5. Report generation utility is included
        6. Statistical analysis utility is included
        """
        from generator.standalone_generator import StandaloneGenerator
        
        # Load minimal config set
        config_sets_dir = Path(__file__).parent.parent.parent / "config_sets"
        loader = ConfigSetLoader(config_sets_dir)
        config_set = loader.load("minimal")
        
        assert config_set.name == "minimal"
        assert len(config_set.available_steps) == 1
        
        # Generate experiment configuration
        exp_name = "test_minimal_e2e"
        exp_dir = temp_workspace / exp_name
        
        config = {
            "experiment_name": exp_name,
            "model": "gpt-4o-mini",
            "frameworks": {
                "baes": {
                    "enabled": True,
                    "repo_url": "https://github.com/example/baes",
                    "commit_hash": "abc123"
                }
            },
            "stopping_rule": {
                "max_runs": 1
            }
        }
        
        # Generate experiment using StandaloneGenerator
        generator = StandaloneGenerator()
        generator.generate(
            name=exp_name,
            config=config,
            output_dir=exp_dir,
            config_set=config_set
        )
        
        # Verify basic structure
        assert exp_dir.exists()
        assert (exp_dir / "config.yaml").exists()
        assert (exp_dir / "run.sh").exists()
        assert (exp_dir / "setup.sh").exists()
        assert (exp_dir / "README.md").exists()
        
        # Verify config directory
        config_dir = exp_dir / "config"
        assert config_dir.exists()
        assert (config_dir / "prompts").exists()
        assert (config_dir / "hitl").exists()
        
        # Verify prompts from minimal config set
        prompts_dir = config_dir / "prompts"
        assert (prompts_dir / "01_hello_world.txt").exists()
        
        # Verify src directory structure
        src_dir = exp_dir / "src"
        assert src_dir.exists()
        assert (src_dir / "main.py").exists()
        
        # Verify utils directory (contains cost calculator)
        utils_dir = src_dir / "utils"
        assert utils_dir.exists()
        assert (utils_dir / "cost_calculator.py").exists(), "Cost calculator utility should be included"
        assert (utils_dir / "metrics_config.py").exists(), "Metrics config utility should be included"
        
        # Verify analysis directory (contains report generation)
        analysis_dir = src_dir / "analysis"
        assert analysis_dir.exists()
        assert (analysis_dir / "report_generator.py").exists(), "Report generator should be included"
        assert (analysis_dir / "visualizations.py").exists(), "Visualizations (stats) should be included"
        assert (analysis_dir / "visualization_factory.py").exists(), "Visualization factory should be included"
        
        # Verify config.yaml has correct structure
        config_yaml = yaml.safe_load((exp_dir / "config.yaml").read_text())
        assert config_yaml["experiment_name"] == exp_name
        assert config_yaml["model"] == "gpt-4o-mini"
        assert "steps" in config_yaml
        assert len(config_yaml["steps"]) == 1
        assert config_yaml["steps"][0]["id"] == 1
        assert config_yaml["steps"][0]["enabled"] is True
        
        # Verify experiment is self-contained (no references to generator)
        config_content = (exp_dir / "config.yaml").read_text()
        assert "config_sets" not in config_content
        assert "generator" not in config_content
