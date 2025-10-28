#!/usr/bin/env python3
"""
Create new experiment from template or scratch.

Interactive wizard or CLI mode for experiment creation.
Validates inputs, generates directory structure, registers experiment.

Generated experiments are created in the parent directory of the generator
by default (as sibling directories), making them completely independent.

Usage:
    # Interactive wizard
    python scripts/new_experiment.py
    
    # CLI mode (creates ../my_experiment/)
    python scripts/new_experiment.py --name my_experiment --model gpt-4o \\
        --frameworks baes,chatdev --runs 50
    
    # From template
    python scripts/new_experiment.py --template experiments/baseline
    
    # Custom experiments directory
    python scripts/new_experiment.py --name test --model gpt-4o \\
        --frameworks baes --runs 10 --experiments-dir /path/to/custom/location
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

# Generator imports (new)
from generator.standalone_generator import StandaloneGenerator

# Config sets imports
from src.config_sets import ConfigSetLoader

# Utility imports
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
    template_config: Optional[Dict[str, Any]] = None,
    config_set_obj: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Generate experiment configuration.
    
    Args:
        model: Model name
        frameworks: List of enabled frameworks
        max_runs: Maximum runs per framework
        template_config: Optional template to base on
        config_set_obj: Optional ConfigSet object to use for base template
        
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
        # Generate from config set's experiment_template.yaml
        if not config_set_obj:
            raise ExperimentCreationError(
                "Config set object is required when not using a template"
            )
        
        if not config_set_obj.template_path.exists():
            raise ExperimentCreationError(
                f"Experiment template not found: {config_set_obj.template_path}"
            )
        
        # Load from config set's experiment_template.yaml
        with open(config_set_obj.template_path, 'r', encoding='utf-8') as f:
            base_config = yaml.safe_load(f)
        
        # Start with a copy of the base config
        config = base_config.copy()
        
        # Override with user-specified values
        config['model'] = model
        
        # Update stopping rule with new max_runs
        if 'stopping_rule' not in config:
            config['stopping_rule'] = {}
        config['stopping_rule']['max_runs'] = max_runs
        
        # Always update min_runs to ensure it's <= max_runs
        # Use the smaller of: current min_runs, 5, or max_runs
        current_min = config['stopping_rule'].get('min_runs', 5)
        config['stopping_rule']['min_runs'] = min(current_min, 5, max_runs)
        
        # Update framework enabled status based on requested frameworks
        if 'frameworks' in config:
            for fw_name in config['frameworks']:
                config['frameworks'][fw_name]['enabled'] = fw_name in frameworks
        
        # Ensure required paths are set (use base config defaults)
        if 'prompts_dir' not in config:
            config['prompts_dir'] = 'config/prompts'
        if 'hitl_path' not in config:
            config['hitl_path'] = 'config/hitl/expanded_spec.txt'
    
    return config


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
            
            # Check if directory already exists in parent directory
            generator_root = Path(__file__).parent.parent
            parent_dir = generator_root.parent
            existing_path = parent_dir / name
            
            if existing_path.exists():
                print(f"ℹ️  Note: Directory '{name}' already exists at {existing_path}")
                print(f"   You'll be asked how to handle this next.")
            
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
        experiments_dir = Path('experiments')
        
        if not experiments_dir.exists() or not list(experiments_dir.iterdir()):
            print("⚠ No existing experiments to use as template")
        else:
            # List available experiment directories
            exp_dirs = [d for d in experiments_dir.iterdir() if d.is_dir() and not d.name.startswith('.')]
            
            if not exp_dirs:
                print("⚠ No existing experiments to use as template")
            else:
                print("\nAvailable experiments:")
                for i, exp_dir in enumerate(sorted(exp_dirs), 1):
                    print(f"  {i}. {exp_dir.name}")
                
                while True:
                    template_choice = input("Select template [number or name]: ").strip()
                    
                    # Try as number
                    try:
                        idx = int(template_choice) - 1
                        if 0 <= idx < len(exp_dirs):
                            template_path = sorted(exp_dirs)[idx]
                            break
                    except ValueError:
                        pass
                    
                    # Try as name
                    template_candidate = experiments_dir / template_choice
                    if template_candidate.exists() and template_candidate.is_dir():
                        template_path = template_candidate
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

def _merge_experiment_updates(temp_dir: Path, target_dir: Path) -> None:
    """
    Merge updates from temporary generated experiment into existing experiment.
    
    Updates:
    - src/ (source code)
    - config/ (configuration and prompts)
    - analysis/ (analysis notebooks and visualizations)
    - setup.sh, run.sh, reconcile_usage.sh (scripts)
    - requirements.txt (dependencies)
    - README.md (documentation)
    - .gitignore (git configuration)
    
    Preserves:
    - runs/ (experiment results)
    - logs/ (log files)
    - venv/ (virtual environment)
    - .git/ (git repository)
    - .env (user API keys)
    - frameworks/ (cloned framework repos)
    
    Args:
        temp_dir: Temporary directory with newly generated experiment
        target_dir: Existing experiment directory to update
    """
    import subprocess
    
    print(f"📦 Merging updates into {target_dir.name}...")
    
    # Directories and files to update (overwrite)
    items_to_update = [
        'src',
        'config',
        'analysis',  # Analysis notebooks and visualizations
        'config.yaml',  # Main configuration file with experiment settings
        'setup.sh',
        'run.sh',
        'reconcile_usage.sh',  # Usage reconciliation script
        'requirements.txt',
        'README.md',
        '.gitignore',
        '.env.example',
    ]
    
    # Use rsync if available (better), otherwise use cp
    try:
        # Check if rsync is available
        subprocess.run(['rsync', '--version'], 
                      capture_output=True, check=True)
        use_rsync = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        use_rsync = False
    
    for item in items_to_update:
        source = temp_dir / item
        if not source.exists():
            continue
        
        target = target_dir / item
        
        if use_rsync:
            # Use rsync for better merging
            if source.is_dir():
                # For directories, sync contents
                cmd = [
                    'rsync', '-a', '--delete',
                    str(source) + '/',  # Trailing slash = sync contents
                    str(target) + '/'
                ]
            else:
                # For files, just copy
                cmd = ['rsync', '-a', str(source), str(target)]
            
            subprocess.run(cmd, check=True, capture_output=True)
        else:
            # Fallback to cp
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)
        
        print(f"  ✓ Updated {item}")
    
    print(f"✓ Merge complete")


def create_experiment(
    name: str,
    model: str,
    frameworks: List[str],
    max_runs: int,
    template_path: Optional[Path] = None,
    experiments_base_dir: Optional[Path] = None,
    config_set: str = 'default',
    force: bool = False
) -> None:
    """
    Create new experiment.
    
    Steps:
    1. Validate inputs
    2. Load config set
    3. Generate configuration
    4. Create directory structure
    5. Write config.yaml
    6. Generate README.md
    7. Register in .experiments.json
    
    Args:
        name: Experiment name
        model: Model name
        frameworks: List of enabled frameworks
        max_runs: Maximum runs per framework
        template_path: Optional template experiment directory
        experiments_base_dir: Optional base directory (defaults to parent of generator)
        config_set: Config set name to use (default: 'default')
        force: If True, overwrite existing directory without asking
        
    Raises:
        ExperimentCreationError: If creation fails
    """
    # Validate inputs
    validate_experiment_name(name)
    validate_model(model)
    validate_frameworks(frameworks)
    
    logger.info(f"Creating standalone experiment: {name}")
    logger.info(f"Using config set: {config_set}")
    
    # Load config set
    generator_root = Path(__file__).parent.parent
    loader = ConfigSetLoader(generator_root / 'config_sets')
    
    try:
        config_set_obj = loader.load(config_set)
        logger.info(f"Loaded config set '{config_set}' ({config_set_obj.get_step_count()} steps)")
    except Exception as e:
        raise ExperimentCreationError(f"Failed to load config set '{config_set}': {e}")
    
    # Load template config if provided
    template_config = None
    if template_path:
        logger.info(f"Loading template: {template_path}")
        template_config = load_template_config(template_path)
    
    # Generate configuration
    config = generate_config(model, frameworks, max_runs, template_config, config_set_obj)
    config['experiment_name'] = name  # Add experiment name to config
    
    # Determine output directory
    if experiments_base_dir:
        output_dir = experiments_base_dir / name
    else:
        # Default: create in parent directory of the generator project
        output_dir = generator_root.parent / name
    
    # Check if already exists
    if output_dir.exists():
        logger.warning(f"Directory already exists: {output_dir}")
        
        # Force flag: remove without asking
        if force:
            # Check if user is currently inside the directory to be deleted
            try:
                current_dir = Path.cwd().resolve()
                target_dir = output_dir.resolve()
                
                if current_dir == target_dir or target_dir in current_dir.parents:
                    raise ExperimentCreationError(
                        f"Cannot delete directory: You are currently inside it!\n"
                        f"Current directory: {current_dir}\n"
                        f"Please change to a different directory first:\n"
                        f"  cd {target_dir.parent}"
                    )
            except OSError:
                # Current directory might already be deleted, continue
                pass
            
            logger.info(f"Force flag set: Removing existing directory: {output_dir}")
            print(f"🗑️  Removing existing directory (--force)...")
            shutil.rmtree(output_dir)
            print(f"✓ Removed {output_dir}")
            print()
        
        # In non-interactive mode without force, fail with error
        elif not sys.stdout.isatty():
            raise ExperimentCreationError(
                f"Experiment directory already exists: {output_dir}\n"
                f"Use --force to overwrite, --experiments-dir to specify a different location,\n"
                f"or delete the existing directory manually."
            )
        
        # Interactive mode: ask what to do
        else:
            print()
            print(f"⚠️  Warning: Directory '{name}' already exists at {output_dir}")
            print()
            print("What would you like to do?")
            print("  1. Update/merge - Keep user data (runs, logs, venv, .git), update code/config")
            print("  2. Delete and replace - Remove everything and start fresh")
            print("  3. Cancel - Choose a different name")
            print()
            
            while True:
                choice = input("Select option [1-3] (default: 1): ").strip() or '1'
                if choice in ['1', '2', '3']:
                    break
                print("❌ Invalid choice. Enter 1, 2, or 3.")
            
            print()
            
            if choice == '3':
                print("❌ Cancelled. Please choose a different name or location.")
                sys.exit(0)
            
            elif choice == '2':
                # Delete everything
                # Check if user is currently inside the directory to be deleted
                try:
                    current_dir = Path.cwd().resolve()
                    target_dir = output_dir.resolve()
                    
                    # Check if current directory is the target or inside it
                    if current_dir == target_dir or target_dir in current_dir.parents:
                        print(f"⚠️  WARNING: You are currently inside the directory to be deleted!")
                        print(f"   Current directory: {current_dir}")
                        print(f"   This will cause your shell to become invalid.")
                        print()
                        print(f"   Please change to a different directory first:")
                        print(f"   cd {target_dir.parent}")
                        print()
                        confirm = input("Continue anyway? [y/N]: ").strip().lower()
                        if confirm != 'y':
                            print("❌ Cancelled. Please cd to a different directory and try again.")
                            sys.exit(0)
                        print()
                except OSError:
                    # Current directory might already be deleted, continue
                    pass
                
                logger.info(f"Removing existing directory: {output_dir}")
                print(f"🗑️  Removing existing directory...")
                shutil.rmtree(output_dir)
                print(f"✓ Removed {output_dir}")
                print()
            
            elif choice == '1':
                # Merge mode - generate to temp dir and merge
                logger.info(f"Merge mode: generating to temporary directory")
                print(f"🔄 Merge mode: Updating experiment with new code/config...")
                print(f"   Preserving: runs/, logs/, venv/, .git/, .env")
                print()
                
                # Generate to temp directory
                temp_dir = output_dir.parent / f"{name}_temp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                logger.info(f"Temporary directory: {temp_dir}")
                
                try:
                    generator = StandaloneGenerator()
                    generator.generate(name, config, temp_dir, config_set_obj)
                    
                    # Merge from temp to existing
                    _merge_experiment_updates(temp_dir, output_dir)
                    
                    # Clean up temp directory
                    logger.info(f"Cleaning up temporary directory: {temp_dir}")
                    shutil.rmtree(temp_dir)
                    print(f"✓ Cleaned up temporary files")
                    print()
                    
                    # Success message for merge
                    print("=" * 70)
                    print("✅ Experiment updated successfully!")
                    print("=" * 70)
                    print()
                    print(f"📁 Location: {output_dir.absolute()}")
                    print(f"🔄 Updated: src/, config/, scripts, requirements.txt")
                    print(f"✓ Preserved: runs/, logs/, venv/, .git/, .env")
                    print()
                    print("=" * 70)
                    print("Next steps:")
                    print("=" * 70)
                    print(f"  cd {output_dir}")
                    print("  # Review changes: git status")
                    print("  # Update dependencies if needed: pip install -r requirements.txt")
                    print("  ./run.sh")
                    print()
                    return  # Exit early for merge mode
                    
                except Exception as e:
                    # Clean up temp directory on failure
                    if temp_dir.exists():
                        logger.warning(f"Cleaning up temporary directory after failure: {temp_dir}")
                        shutil.rmtree(temp_dir)
                    raise ExperimentCreationError(f"Merge failed: {e}")

    
    logger.info(f"Output directory: {output_dir}")
    
    # Generate standalone experiment using the new generator
    try:
        generator = StandaloneGenerator()
        generator.generate(name, config, output_dir, config_set_obj)
    except Exception as e:
        # Clean up on failure
        if output_dir.exists():
            logger.warning(f"Cleaning up failed generation: {output_dir}")
            shutil.rmtree(output_dir)
        raise ExperimentCreationError(f"Generation failed: {e}")
    
    # Success
    print("=" * 70)
    print("✅ Standalone experiment created successfully!")
    print("=" * 70)
    print()
    print(f"📁 Location: {output_dir.absolute()}")
    print(f"🎯 Type: Fully independent git repository")
    print(f"📦 Model: {model}")
    print(f"🔧 Frameworks: {', '.join(frameworks)}")
    print(f"🔢 Max runs: {max_runs} per framework ({max_runs * len(frameworks)} total)")
    print()
    print("=" * 70)
    print("Quick start:")
    print("=" * 70)
    print(f"  cd {output_dir}")
    print("  ./setup.sh")
    print("  # Edit .env with your API keys")
    print("  ./run.sh")
    print()
    print("The experiment is now a standalone project with:")
    print("  ✓ Complete source code")
    print("  ✓ Configuration and prompts")
    print("  ✓ Setup and run scripts")
    print("  ✓ Git repository initialized")
    print("  ✓ No dependencies on this generator")
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
  
  # Force overwrite existing directory
  python scripts/new_experiment.py --name baseline --model gpt-4o \\
      --frameworks baes --runs 10 --force
  
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
    
    parser.add_argument(
        '--config-set',
        default='default',
        help='Config set name to use (default: default). Use --list-config-sets to see available options'
    )
    
    parser.add_argument(
        '--list-config-sets',
        action='store_true',
        help='List available config sets and exit'
    )
    
    parser.add_argument(
        '--experiments-dir',
        type=Path,
        help='Custom base directory for experiments (default: parent directory of generator)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing experiment directory without asking'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    args = parse_args()
    
    try:
        # Handle --list-config-sets
        if args.list_config_sets:
            project_root = Path(__file__).parent.parent
            loader = ConfigSetLoader(project_root / 'config_sets')
            available = loader.list_available()
            
            print("Available config sets:")
            print()
            for name in sorted(available):
                details = loader.get_details(name)
                print(f"  {name}")
                print(f"    Description: {details['description']}")
                print(f"    Version: {details['version']}")
                print(f"    Steps: {details['steps_count']}")
                print()
            
            return
        
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
                'template_path': template_path,
                'experiments_base_dir': args.experiments_dir,
                'config_set': args.config_set,
                'force': args.force
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
