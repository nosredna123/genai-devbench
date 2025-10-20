#!/usr/bin/env python3
"""
Create new experiment from template or scratch.

Interactive wizard or CLI mode for experiment creation.
Validates inputs, generates directory structure, registers experiment.

Usage:
    # Interactive wizard
    python scripts/new_experiment.py
    
    # CLI mode
    python scripts/new_experiment.py --name baseline --model gpt-4o \\
        --frameworks baes,chatdev --runs 50
    
    # From template
    python scripts/new_experiment.py --template experiments/baseline
"""

import sys
import argparse
from pathlib import Path
from typing import Optional, List, Dict, Any
import yaml
import shutil
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.experiment_paths import ExperimentPaths
from src.utils.experiment_registry import get_registry, ExperimentAlreadyExistsError
from src.utils.logger import get_logger

logger = get_logger(__name__, component="new_experiment")


class ExperimentCreationError(Exception):
    """Raised when experiment creation fails."""
    pass


# =============================================================================
# Validation
# =============================================================================

def validate_experiment_name(name: str) -> None:
    """
    Validate experiment name.
    
    Rules:
    - Only alphanumeric, hyphens, underscores
    - No spaces
    - Not empty
    - Max 50 characters
    
    Args:
        name: Experiment name to validate
        
    Raises:
        ExperimentCreationError: If name is invalid
    """
    if not name:
        raise ExperimentCreationError("Experiment name cannot be empty")
    
    if len(name) > 50:
        raise ExperimentCreationError(
            f"Experiment name too long: {len(name)} characters (max 50)"
        )
    
    if not all(c.isalnum() or c in '-_' for c in name):
        raise ExperimentCreationError(
            f"Invalid experiment name: '{name}'\n"
            f"Only alphanumeric characters, hyphens, and underscores allowed"
        )
    
    if name.startswith('-') or name.startswith('_'):
        raise ExperimentCreationError(
            f"Experiment name cannot start with '-' or '_': '{name}'"
        )


def validate_model(model: str) -> None:
    """
    Validate model name.
    
    Args:
        model: Model name to validate
        
    Raises:
        ExperimentCreationError: If model is invalid
    """
    valid_models = [
        'gpt-4o',
        'gpt-4o-mini',
        'gpt-4-turbo',
        'gpt-4',
        'gpt-3.5-turbo'
    ]
    
    if model not in valid_models:
        raise ExperimentCreationError(
            f"Invalid model: '{model}'\n"
            f"Valid models: {', '.join(valid_models)}"
        )


def validate_frameworks(frameworks: List[str]) -> None:
    """
    Validate framework list.
    
    Args:
        frameworks: List of framework names
        
    Raises:
        ExperimentCreationError: If frameworks invalid
    """
    valid_frameworks = ['baes', 'chatdev', 'ghspec']
    
    if not frameworks:
        raise ExperimentCreationError("At least one framework must be specified")
    
    for fw in frameworks:
        if fw not in valid_frameworks:
            raise ExperimentCreationError(
                f"Invalid framework: '{fw}'\n"
                f"Valid frameworks: {', '.join(valid_frameworks)}"
            )


# =============================================================================
# Configuration Generation
# =============================================================================

def load_template_config(template_path: Path) -> Dict[str, Any]:
    """
    Load configuration from template experiment.
    
    Args:
        template_path: Path to template experiment directory
        
    Returns:
        Template configuration
        
    Raises:
        ExperimentCreationError: If template invalid
    """
    config_path = template_path / "config.yaml"
    
    if not config_path.exists():
        raise ExperimentCreationError(
            f"Template has no config.yaml: {template_path}"
        )
    
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    except yaml.YAMLError as e:
        raise ExperimentCreationError(
            f"Template config.yaml is invalid: {e}"
        )


def generate_config(
    model: str,
    frameworks: List[str],
    max_runs: int,
    template_config: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generate experiment configuration.
    
    Args:
        model: Model name
        frameworks: List of enabled frameworks
        max_runs: Maximum runs per framework
        template_config: Optional template to base on
        
    Returns:
        Complete configuration dictionary
    """
    if template_config:
        # Start from template
        config = template_config.copy()
        
        # Override with new values
        config['model'] = model
        config['stopping_rule']['max_runs'] = max_runs
        
        # Update frameworks
        for fw_name in config['frameworks']:
            config['frameworks'][fw_name]['enabled'] = fw_name in frameworks
    
    else:
        # Generate from scratch
        # Set min_runs intelligently: min(5, max_runs) to avoid validation errors
        min_runs = min(5, max_runs)
        
        config = {
            'random_seed': 42,
            'model': model,
            'prompts_dir': 'config/prompts',
            'hitl_path': 'config/hitl/expanded_spec.txt',
            'stopping_rule': {
                'min_runs': min_runs,
                'max_runs': max_runs,
                'confidence_level': 0.95,
                'max_half_width_pct': 10,
                'metrics': ['TOK_IN', 'T_WALL_seconds', 'COST_USD']
            },
            'timeouts': {
                'step_timeout_seconds': 600,
                'health_check_interval_seconds': 5,
                'api_retry_attempts': 3
            },
            'frameworks': {
                'baes': {
                    'enabled': 'baes' in frameworks,
                    'repo_url': 'https://github.com/gesad-lab/baes_demo',
                    'commit_hash': '1dd573633a98b8baa636c200bc1684cec7a8179f',
                    'api_port': 8100,
                    'ui_port': 8600,
                    'max_retries': 3,
                    'auto_restart_servers': False,
                    'use_venv': True,
                    'api_key_env': 'OPENAI_API_KEY_BAES'
                },
                'chatdev': {
                    'enabled': 'chatdev' in frameworks,
                    'repo_url': 'https://github.com/OpenBMB/ChatDev.git',
                    'commit_hash': '52edb89997b4312ad27d8c54584d0a6c59940135',
                    'api_port': 8001,
                    'ui_port': 3001,
                    'api_key_env': 'OPENAI_API_KEY_CHATDEV'
                },
                'ghspec': {
                    'enabled': 'ghspec' in frameworks,
                    'repo_url': 'https://github.com/github/spec-kit.git',
                    'commit_hash': '89f4b0b38a42996376c0f083d47281a4c9196761',
                    'api_port': 8002,
                    'ui_port': 3002,
                    'api_key_env': 'OPENAI_API_KEY_GHSPEC'
                }
            },
            'metrics': {
                'enabled': [
                    'functional_correctness',
                    'design_quality',
                    'code_maintainability',
                    'api_calls'
                ],
                'config': {}
            },
            'pricing': {
                'gpt-4o': {
                    'input': 0.0025,
                    'output': 0.010
                },
                'gpt-4o-mini': {
                    'input': 0.000150,
                    'output': 0.000600
                },
                'gpt-4-turbo': {
                    'input': 0.01,
                    'output': 0.03
                },
                'gpt-4': {
                    'input': 0.03,
                    'output': 0.06
                },
                'gpt-3.5-turbo': {
                    'input': 0.0005,
                    'output': 0.0015
                }
            }
        }
    
    return config


# =============================================================================
# README Generation
# =============================================================================

def generate_readme(
    name: str,
    model: str,
    frameworks: List[str],
    max_runs: int,
    config_hash: str
) -> str:
    """
    Generate README.md content for experiment.
    
    Args:
        name: Experiment name
        model: Model name
        frameworks: List of enabled frameworks
        max_runs: Maximum runs per framework
        config_hash: Configuration hash
        
    Returns:
        README.md content
    """
    frameworks_str = ', '.join(frameworks)
    total_runs = max_runs * len(frameworks)
    
    return f"""# Experiment: {name}

**Created:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC  
**Config Hash:** `{config_hash}`

## Configuration

- **Model:** `{model}`
- **Frameworks:** {frameworks_str}
- **Max Runs per Framework:** {max_runs}
- **Total Max Runs:** {total_runs}

## Directory Structure

```
{name}/
├── config.yaml          # Experiment configuration
├── README.md            # This file
├── runs/                # Run outputs
│   ├── baes/
│   ├── chatdev/
│   └── ghspec/
├── analysis/            # Analysis results
│   ├── visualizations/
│   └── report.md
└── .meta/               # Metadata
    ├── manifest.json    # Run manifest
    └── config.hash      # Config hash
```

## Usage

### Run Experiment

```bash
# From project root
./runners/run_experiment.sh {name}
```

### Analyze Results

```bash
./runners/analyze_results.sh {name}
```

### Check Status

```bash
python -c "from src.utils.experiment_registry import get_registry; \\
           import json; \\
           print(json.dumps(get_registry().get_experiment('{name}'), indent=2))"
```

## Notes

- Configuration is immutable after first run (hash validation)
- Each run creates isolated workspace under `runs/<framework>/<run_id>/`
- Analysis outputs saved to `analysis/`
- Manifest tracks all completed runs
"""


# =============================================================================
# Interactive Wizard
# =============================================================================

def interactive_wizard() -> Dict[str, Any]:
    """
    Interactive experiment creation wizard.
    
    Returns:
        Dictionary with experiment parameters
    """
    print("=" * 70)
    print("Create New Experiment - Interactive Wizard")
    print("=" * 70)
    print()
    
    # Get experiment name
    while True:
        name = input("Experiment name (alphanumeric, hyphens, underscores): ").strip()
        try:
            validate_experiment_name(name)
            
            # Check if already exists
            registry = get_registry()
            if name in registry.list_experiments():
                print(f"❌ Experiment '{name}' already exists. Choose different name.")
                continue
            
            break
        
        except ExperimentCreationError as e:
            print(f"❌ {e}")
    
    print(f"✓ Experiment name: {name}")
    print()
    
    # Get model
    print("Available models:")
    print("  1. gpt-4o (recommended)")
    print("  2. gpt-4o-mini")
    print("  3. gpt-4-turbo")
    print("  4. gpt-4")
    print("  5. gpt-3.5-turbo")
    
    model_choices = {
        '1': 'gpt-4o',
        '2': 'gpt-4o-mini',
        '3': 'gpt-4-turbo',
        '4': 'gpt-4',
        '5': 'gpt-3.5-turbo'
    }
    
    while True:
        choice = input("Select model [1-5] (default: 1): ").strip() or '1'
        if choice in model_choices:
            model = model_choices[choice]
            break
        print("❌ Invalid choice. Enter 1-5.")
    
    print(f"✓ Model: {model}")
    print()
    
    # Get frameworks
    print("Available frameworks:")
    print("  1. baes")
    print("  2. chatdev")
    print("  3. ghspec")
    
    while True:
        fw_input = input("Select frameworks (comma-separated, e.g. '1,2,3') (default: all): ").strip()
        
        if not fw_input:
            frameworks = ['baes', 'chatdev', 'ghspec']
            break
        
        try:
            fw_numbers = [x.strip() for x in fw_input.split(',')]
            fw_map = {'1': 'baes', '2': 'chatdev', '3': 'ghspec'}
            frameworks = [fw_map[n] for n in fw_numbers if n in fw_map]
            
            if not frameworks:
                print("❌ No valid frameworks selected")
                continue
            
            validate_frameworks(frameworks)
            break
        
        except (KeyError, ExperimentCreationError) as e:
            print(f"❌ {e}")
    
    print(f"✓ Frameworks: {', '.join(frameworks)}")
    print()
    
    # Get max runs
    while True:
        runs_input = input("Max runs per framework (default: 50): ").strip() or '50'
        try:
            max_runs = int(runs_input)
            if max_runs < 1:
                print("❌ Must be at least 1")
                continue
            if max_runs > 1000:
                print("❌ Maximum is 1000 runs")
                continue
            break
        except ValueError:
            print("❌ Must be a number")
    
    print(f"✓ Max runs: {max_runs} per framework ({max_runs * len(frameworks)} total)")
    print()
    
    # Check for template
    use_template = input("Base on existing experiment template? [y/N]: ").strip().lower()
    template_path = None
    
    if use_template in ['y', 'yes']:
        registry = get_registry()
        experiments = registry.list_experiments()
        
        if not experiments:
            print("⚠ No existing experiments to use as template")
        else:
            print("\nAvailable experiments:")
            for i, exp_name in enumerate(sorted(experiments.keys()), 1):
                print(f"  {i}. {exp_name}")
            
            while True:
                template_choice = input("Select template [number or name]: ").strip()
                
                # Try as number
                try:
                    idx = int(template_choice) - 1
                    if 0 <= idx < len(experiments):
                        template_name = sorted(experiments.keys())[idx]
                        template_path = Path(f"experiments/{template_name}")
                        break
                except ValueError:
                    pass
                
                # Try as name
                if template_choice in experiments:
                    template_path = Path(f"experiments/{template_choice}")
                    break
                
                print("❌ Invalid choice")
            
            print(f"✓ Using template: {template_path.name}")
    
    print()
    print("=" * 70)
    print("Summary:")
    print(f"  Name: {name}")
    print(f"  Model: {model}")
    print(f"  Frameworks: {', '.join(frameworks)}")
    print(f"  Max runs: {max_runs} per framework ({max_runs * len(frameworks)} total)")
    if template_path:
        print(f"  Template: {template_path.name}")
    print("=" * 70)
    print()
    
    confirm = input("Create experiment? [Y/n]: ").strip().lower()
    if confirm in ['n', 'no']:
        print("Cancelled.")
        sys.exit(0)
    
    return {
        'name': name,
        'model': model,
        'frameworks': frameworks,
        'max_runs': max_runs,
        'template_path': template_path
    }


# =============================================================================
# Experiment Creation
# =============================================================================

def create_experiment(
    name: str,
    model: str,
    frameworks: List[str],
    max_runs: int,
    template_path: Optional[Path] = None
) -> None:
    """
    Create new experiment.
    
    Steps:
    1. Validate inputs
    2. Generate configuration
    3. Create directory structure
    4. Write config.yaml
    5. Generate README.md
    6. Register in .experiments.json
    
    Args:
        name: Experiment name
        model: Model name
        frameworks: List of enabled frameworks
        max_runs: Maximum runs per framework
        template_path: Optional template experiment directory
        
    Raises:
        ExperimentCreationError: If creation fails
    """
    # Validate inputs
    validate_experiment_name(name)
    validate_model(model)
    validate_frameworks(frameworks)
    
    logger.info(f"Creating experiment: {name}")
    
    # Load template config if provided
    template_config = None
    if template_path:
        logger.info(f"Loading template: {template_path}")
        template_config = load_template_config(template_path)
    
    # Generate configuration
    config = generate_config(model, frameworks, max_runs, template_config)
    
    # Create experiment paths (validate_exists=False for new experiments)
    exp_paths = ExperimentPaths(
        name,
        auto_create_structure=True,
        validate_exists=False
    )
    
    # Compute config hash
    config_hash = exp_paths.compute_config_hash(config)
    
    # Write config.yaml
    config_path = exp_paths.experiment_dir / "config.yaml"
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, indent=2)
    
    logger.info(f"Created config: {config_path}")
    
    # Write config hash
    hash_path = exp_paths.meta_dir / "config.hash"
    hash_path.write_text(config_hash, encoding='utf-8')
    
    logger.info(f"Saved config hash: {config_hash}")
    
    # Generate README.md
    readme_content = generate_readme(name, model, frameworks, max_runs, config_hash)
    readme_path = exp_paths.experiment_dir / "README.md"
    readme_path.write_text(readme_content, encoding='utf-8')
    
    logger.info(f"Created README: {readme_path}")
    
    # Copy prompts and hitl from template if available
    if template_path:
        # Copy prompts
        template_prompts = template_path / "prompts"
        if template_prompts.exists():
            shutil.copytree(template_prompts, exp_paths.prompts_dir, dirs_exist_ok=True)
            logger.info(f"Copied prompts from template")
        
        # Copy hitl
        template_hitl = template_path / "hitl"
        if template_hitl.exists():
            shutil.copytree(template_hitl, exp_paths.hitl_dir, dirs_exist_ok=True)
            logger.info(f"Copied hitl config from template")
    
    # Register in .experiments.json
    try:
        registry = get_registry()
        registry.register_experiment(name, config, config_hash)
        logger.info("Registered in .experiments.json")
    
    except ExperimentAlreadyExistsError as e:
        # Clean up created directory
        shutil.rmtree(exp_paths.experiment_dir)
        raise ExperimentCreationError(str(e))
    
    # Success
    print()
    print("✅ Experiment created successfully!")
    print()
    print(f"📁 Location: {exp_paths.experiment_dir}")
    print(f"🔑 Config hash: {config_hash}")
    print()
    print("Next steps:")
    print(f"  1. Review configuration: {config_path}")
    print(f"  2. Run experiment: ./runners/run_experiment.sh {name}")
    print(f"  3. Analyze results: ./runners/analyze_results.sh {name}")
    print()


# =============================================================================
# CLI
# =============================================================================

def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Create new experiment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive wizard
  python scripts/new_experiment.py
  
  # CLI mode
  python scripts/new_experiment.py --name baseline --model gpt-4o \\
      --frameworks baes,chatdev --runs 50
  
  # From template
  python scripts/new_experiment.py --name variant1 --template baseline
        """
    )
    
    parser.add_argument(
        '--name',
        help='Experiment name (alphanumeric, hyphens, underscores)'
    )
    
    parser.add_argument(
        '--model',
        choices=['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
        help='Model name'
    )
    
    parser.add_argument(
        '--frameworks',
        help='Comma-separated list of frameworks (baes,chatdev,ghspec)'
    )
    
    parser.add_argument(
        '--runs',
        type=int,
        help='Maximum runs per framework'
    )
    
    parser.add_argument(
        '--template',
        help='Template experiment name or path'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        # Interactive mode if no arguments
        if not any([args.name, args.model, args.frameworks, args.runs]):
            params = interactive_wizard()
        
        # CLI mode
        else:
            # Validate required arguments
            if not args.name:
                raise ExperimentCreationError("--name is required in CLI mode")
            if not args.model:
                raise ExperimentCreationError("--model is required in CLI mode")
            if not args.frameworks:
                raise ExperimentCreationError("--frameworks is required in CLI mode")
            if not args.runs:
                raise ExperimentCreationError("--runs is required in CLI mode")
            
            # Parse frameworks
            frameworks = [fw.strip() for fw in args.frameworks.split(',')]
            
            # Parse template
            template_path = None
            if args.template:
                # Try as path first
                template_path = Path(args.template)
                if not template_path.exists():
                    # Try as experiment name
                    template_path = Path(f"experiments/{args.template}")
                
                if not template_path.exists():
                    raise ExperimentCreationError(
                        f"Template not found: {args.template}"
                    )
            
            params = {
                'name': args.name,
                'model': args.model,
                'frameworks': frameworks,
                'max_runs': args.runs,
                'template_path': template_path
            }
        
        # Create experiment
        create_experiment(**params)
    
    except ExperimentCreationError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\nCancelled.")
        sys.exit(0)
    
    except Exception as e:
        logger.exception("Unexpected error during experiment creation")
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
