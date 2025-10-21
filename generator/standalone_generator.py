"""
Standalone Generator

Main orchestrator that coordinates all generation components to create
fully independent, self-contained experiment projects.
"""

import shutil
import subprocess
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from generator.artifact_collector import ArtifactCollector
from generator.import_rewriter import ImportRewriter
from generator.script_generator import ScriptGenerator
from generator.dependency_analyzer import DependencyAnalyzer
from src.config_sets.models import ConfigSet


class StandaloneGenerator:
    """Main generator creating standalone experiment projects."""
    
    def __init__(self, project_root: Optional[Path] = None):
        """
        Initialize standalone generator.
        
        Args:
            project_root: Path to generator project root (auto-detected if None)
        """
        self.project_root = project_root or Path(__file__).parent.parent
        self.import_rewriter = ImportRewriter()
    
    def generate(
        self, 
        name: str, 
        config: Dict[str, Any], 
        output_dir: Path,
        config_set: ConfigSet
    ) -> None:
        """
        Generate complete standalone experiment project.
        
        Args:
            name: Experiment name
            config: Experiment configuration dictionary
            output_dir: Output directory for generated project
            config_set: ConfigSet object containing prompts, HITL, and metadata
        """
        print(f"🚀 Generating standalone experiment: {name}")
        print(f"📁 Output directory: {output_dir}")
        print(f"📦 Config set: {config_set.name} ({config_set.get_step_count()} steps)")
        print()
        
        # Ensure experiment_name is in config
        config['experiment_name'] = name
        
        # Get enabled frameworks for import rewriting
        enabled_frameworks = [
            name for name, fw_config in config.get('frameworks', {}).items()
            if fw_config.get('enabled', False)
        ]
        
        # Initialize import rewriter with framework info
        self.import_rewriter = ImportRewriter(enabled_frameworks)
        
        # Initialize components
        artifact_collector = ArtifactCollector(config, self.project_root)
        script_generator = ScriptGenerator(config)
        dependency_analyzer = DependencyAnalyzer(config)
        
        # Step 1: Create directory structure
        print("📂 Creating directory structure...")
        self._create_directory_structure(output_dir)
        
        # Step 2: Collect artifacts
        print("📦 Collecting artifacts...")
        artifacts = artifact_collector.get_all_artifacts()
        
        # Step 3: Copy source files
        print("📄 Copying source files...")
        self._copy_source_files(artifacts['source_files'], output_dir)
        
        # Step 4: Copy configuration files from config set
        print("⚙️  Copying configuration files from config set...")
        self._copy_config_set_files(config_set, output_dir)
        
        # Step 4.5: Copy documentation files
        print("📚 Copying documentation files...")
        self._copy_docs_files(artifacts['docs_files'], output_dir)
        
        # Step 5: Generate template files
        print("📝 Generating template files...")
        self._copy_template_files(output_dir)
        
        # Step 6: Generate scripts
        print("🔧 Generating execution scripts...")
        self._generate_all_scripts(script_generator, output_dir)
        
        # Step 7: Generate configuration
        print("⚙️  Generating configuration...")
        self._generate_config_yaml(config, output_dir, config_set)
        
        # Step 8: Generate requirements.txt
        print("📋 Generating requirements.txt...")
        self._generate_requirements(dependency_analyzer, output_dir)
        
        # Step 9: Generate .gitignore
        print("🚫 Generating .gitignore...")
        self._generate_gitignore(script_generator, output_dir)
        
        # Step 10: Copy .env file if it exists
        print("🔑 Checking for .env file...")
        self._copy_env_file(output_dir)
        
        # Step 11: Initialize git repository
        print("🔄 Initializing git repository...")
        self._initialize_git_repo(output_dir, name)
        
        # Step 12: Validate generated project
        print("✅ Validating generated project...")
        self._validate_generated_project(output_dir)
        
        print()
        print("✅ Generation complete!")
        print()
    
    def _create_directory_structure(self, output_dir: Path) -> None:
        """Create experiment directory structure."""
        directories = [
            output_dir / 'src' / 'adapters',
            output_dir / 'src' / 'analysis',
            output_dir / 'src' / 'orchestrator',
            output_dir / 'src' / 'utils',
            output_dir / 'config' / 'prompts',
            output_dir / 'config' / 'hitl',
            output_dir / 'runs',
            output_dir / 'analysis' / 'visualizations',
            output_dir / 'frameworks',
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _copy_source_files(
        self, 
        source_files: Dict[str, list[Path]], 
        output_dir: Path
    ) -> None:
        """Copy source files with import rewriting."""
        for category, files in source_files.items():
            for source_file in files:
                # Determine destination path
                relative_path = source_file.relative_to(self.project_root / 'src')
                dest_file = output_dir / 'src' / relative_path
                
                # Copy with rewriting
                self.import_rewriter.rewrite_file(source_file, dest_file)
                
                print(f"  ✓ {relative_path}")
    
    def _copy_config_set_files(
        self, 
        config_set: ConfigSet, 
        output_dir: Path
    ) -> None:
        """
        Copy ALL files from config set to experiment (always copy all, no filtering).
        
        Args:
            config_set: ConfigSet object with paths to prompts and HITL files
            output_dir: Destination directory for generated experiment
        """
        # Copy ALL prompt files (no filtering based on enabled steps)
        prompts_dest = output_dir / 'config' / 'prompts'
        prompts_dest.mkdir(parents=True, exist_ok=True)
        
        for step_metadata in config_set.available_steps:
            # prompt_file already contains "prompts/" prefix, remove it
            prompt_filename = Path(step_metadata.prompt_file).name
            prompt_source = config_set.prompts_dir / prompt_filename
            prompt_dest = prompts_dest / prompt_filename
            
            shutil.copy2(prompt_source, prompt_dest)
            print(f"  ✓ config/prompts/{prompt_filename}")
        
        # Copy ALL HITL files
        hitl_dest = output_dir / 'config' / 'hitl'
        hitl_dest.mkdir(parents=True, exist_ok=True)
        
        for hitl_file in config_set.hitl_dir.glob('*'):
            if hitl_file.is_file():
                dest_file = hitl_dest / hitl_file.name
                shutil.copy2(hitl_file, dest_file)
                print(f"  ✓ config/hitl/{hitl_file.name}")
    
    def _copy_docs_files(
        self,
        docs_files: Dict[str, list[Path]],
        output_dir: Path
    ) -> None:
        """Copy documentation files (e.g., framework-specific prompts)."""
        for framework, files in docs_files.items():
            for source_file in files:
                # Determine destination path
                relative_path = source_file.relative_to(self.project_root / 'docs')
                dest_file = output_dir / 'docs' / relative_path
                
                # Ensure parent directory exists
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(source_file, dest_file)
                
                print(f"  ✓ docs/{relative_path}")
    
    def _copy_template_files(self, output_dir: Path) -> None:
        """Copy template files (main.py, setup_frameworks.py)."""
        templates_dir = self.project_root / 'templates'
        
        if not templates_dir.exists():
            # Templates will be created in Phase 2
            # For now, create placeholder files
            self._create_placeholder_main(output_dir)
            self._create_placeholder_setup_frameworks(output_dir)
        else:
            # Copy from templates directory
            for template_file in templates_dir.glob('*.py'):
                dest_file = output_dir / 'src' / template_file.name
                shutil.copy2(template_file, dest_file)
                print(f"  ✓ src/{template_file.name}")
    
    def _create_placeholder_main(self, output_dir: Path) -> None:
        """Create placeholder main.py."""
        main_content = '''"""Main entry point for experiment execution."""

import sys
from pathlib import Path

from src.orchestrator.runner import OrchestratorRunner
from src.orchestrator.config_loader import load_config
from src.utils.logger import get_logger

logger = get_logger(__name__)


def main():
    """Execute experiment."""
    try:
        # Load configuration
        config_path = Path('config.yaml')
        if not config_path.exists():
            print("❌ ERROR: config.yaml not found", file=sys.stderr)
            logger.error("config.yaml not found")
            return 1
        
        config = load_config(config_path)
        
        # Validate required configuration fields
        experiment_name = config.get('experiment_name')
        if not experiment_name:
            logger.error("Missing 'experiment_name' in config.yaml")
            return 1
        
        model = config.get('model')
        if not model:
            logger.error("Missing 'model' in config.yaml")
            return 1
        
        print("=" * 41)
        print(f"Running experiment: {experiment_name}")
        print("=" * 41)
        print()
        print("Configuration:")
        print(f"  Model: {model}")
        
        # Get enabled frameworks
        enabled_frameworks = [
            name for name, fw_config in config.get('frameworks', {}).items()
            if fw_config.get('enabled', False)
        ]
        
        if not enabled_frameworks:
            logger.error("No frameworks enabled in configuration")
            return 1
        
        print(f"  Frameworks: {', '.join(enabled_frameworks)}")
        
        # Get max runs from stopping_rule (required)
        stopping_rule = config.get('stopping_rule')
        if not stopping_rule:
            logger.error("Missing 'stopping_rule' section in config.yaml")
            return 1
        
        max_runs = stopping_rule.get('max_runs')
        if max_runs is None:
            logger.error("Missing 'stopping_rule.max_runs' in config.yaml")
            return 1
        
        total_runs = len(enabled_frameworks) * max_runs
        print(f"  Max runs per framework: {max_runs}")
        print()
        print("This may take a while...")
        print()
        
        # Run each framework
        all_results = {}
        for framework_name in enabled_frameworks:
            logger.info(f"Starting {framework_name} runs")
            framework_results = []
            
            for run_num in range(1, max_runs + 1):
                logger.info(f"Running {framework_name} - run {run_num}/{max_runs}")
                
                runner = OrchestratorRunner(
                    framework_name=framework_name,
                    config_path=str(config_path),
                    experiment_name=experiment_name
                )
                
                result = runner.run()
                framework_results.append(result)
            
            all_results[framework_name] = framework_results
        
        logger.info("Experiment completed successfully")
        logger.info(f"Results saved to: {Path('runs').absolute()}")
        
        # Print summary
        print()
        print("=" * 41)
        print("✅ Experiment completed!")
        print("=" * 41)
        print(f"Results directory: {Path('runs').absolute()}")
        print()
        
        return 0
        
    except KeyboardInterrupt:
        print("\\n❌ Experiment interrupted by user", file=sys.stderr)
        logger.warning("Experiment interrupted by user")
        return 130
        
    except Exception as e:
        print(f"\\n❌ EXPERIMENT FAILED: {e}", file=sys.stderr)
        logger.exception("Experiment failed")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
'''
        (output_dir / 'src' / 'main.py').write_text(main_content, encoding='utf-8')
        print("  ✓ src/main.py")
    
    def _create_placeholder_setup_frameworks(self, output_dir: Path) -> None:
        """Create placeholder setup_frameworks.py."""
        setup_content = '''"""Setup framework repositories for experiment."""

import subprocess
from pathlib import Path
import yaml
import sys

def load_config():
    """Load experiment configuration."""
    with open('config.yaml', 'r') as f:
        return yaml.safe_load(f)

def clone_framework(name: str, repo_url: str, commit_hash: str):
    """Clone and checkout framework repository."""
    frameworks_dir = Path('frameworks')
    frameworks_dir.mkdir(exist_ok=True)
    
    target_dir = frameworks_dir / name
    
    if target_dir.exists():
        print(f"✓ {name} already exists")
        return
        
    print(f"Cloning {name}...")
    try:
        subprocess.run(['git', 'clone', repo_url, str(target_dir)], 
                      check=True, capture_output=True)
        subprocess.run(['git', 'checkout', commit_hash], 
                      cwd=target_dir, check=True, capture_output=True)
        print(f"✓ {name} cloned successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to clone {name}: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    try:
        config = load_config()
        
        print("Setting up framework repositories...")
        print()
        
        for name, fw_config in config['frameworks'].items():
            if fw_config.get('enabled', False):
                clone_framework(
                    name,
                    fw_config['repo_url'],
                    fw_config['commit_hash']
                )
        
        print()
        print("✅ All frameworks ready!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
'''
        (output_dir / 'src' / 'setup_frameworks.py').write_text(setup_content, encoding='utf-8')
        print("  ✓ src/setup_frameworks.py")
    
    def _generate_all_scripts(
        self, 
        script_generator: ScriptGenerator, 
        output_dir: Path
    ) -> None:
        """Generate all execution scripts."""
        # setup.sh
        setup_script = script_generator.generate_setup_script()
        setup_path = output_dir / 'setup.sh'
        setup_path.write_text(setup_script, encoding='utf-8')
        setup_path.chmod(0o755)  # Make executable
        print("  ✓ setup.sh")
        
        # run.sh
        run_script = script_generator.generate_run_script()
        run_path = output_dir / 'run.sh'
        run_path.write_text(run_script, encoding='utf-8')
        run_path.chmod(0o755)  # Make executable
        print("  ✓ run.sh")
        
        # reconcile_usage.sh
        reconcile_script = script_generator.generate_reconcile_usage_script()
        reconcile_path = output_dir / 'reconcile_usage.sh'
        reconcile_path.write_text(reconcile_script, encoding='utf-8')
        reconcile_path.chmod(0o755)  # Make executable
        print("  ✓ reconcile_usage.sh")
        
        # README.md
        readme = script_generator.generate_readme()
        (output_dir / 'README.md').write_text(readme, encoding='utf-8')
        print("  ✓ README.md")
        
        # .env.example
        env_example = script_generator.generate_env_example()
        (output_dir / '.env.example').write_text(env_example, encoding='utf-8')
        print("  ✓ .env.example")
    
    def _generate_config_yaml(
        self, 
        config: Dict[str, Any], 
        output_dir: Path,
        config_set: ConfigSet
    ) -> None:
        """
        Generate standalone config.yaml from config set template.
        
        Args:
            config: Experiment configuration dictionary
            output_dir: Output directory for generated project
            config_set: ConfigSet object with template and metadata
        """
        # Load the template from config set
        template_path = config_set.template_path
        with open(template_path, 'r', encoding='utf-8') as f:
            full_config = yaml.safe_load(f)
        
        # Override with experiment-specific settings
        full_config['experiment_name'] = config.get('experiment_name')
        full_config['model'] = config.get('model')
        full_config['random_seed'] = config.get('random_seed', 42)
        
        # Update paths to be relative to experiment root
        full_config['prompts_dir'] = 'config/prompts'
        full_config['hitl_path'] = 'config/hitl/expanded_spec.txt'
        
        # Update frameworks - merge config into full_config
        if 'frameworks' in config:
            # Ensure frameworks dict exists in full_config
            if 'frameworks' not in full_config:
                full_config['frameworks'] = {}
            
            for fw_name, fw_config in config['frameworks'].items():
                # If framework doesn't exist in full_config, add it entirely
                if fw_name not in full_config['frameworks']:
                    full_config['frameworks'][fw_name] = fw_config.copy()
                else:
                    # Framework exists - merge the config
                    if not isinstance(full_config['frameworks'][fw_name], dict):
                        full_config['frameworks'][fw_name] = {}
                    # Update/merge all fields from fw_config into full_config
                    full_config['frameworks'][fw_name].update(fw_config)
        
        # Convert repo_url to file:// paths pointing to local frameworks directory
        # This avoids cloning the repository for every run (huge performance improvement!)
        # The frameworks are already cloned in <experiment>/frameworks/ by setup.sh
        if 'frameworks' in full_config:
            for fw_name in full_config['frameworks']:
                # Use absolute path to frameworks directory
                # At runtime, this will be resolved relative to where the experiment runs
                frameworks_abs_path = (output_dir / 'frameworks' / fw_name).absolute()
                full_config['frameworks'][fw_name]['repo_url'] = f'file://{frameworks_abs_path}'
        
        # Update stopping rule
        if 'stopping_rule' in config:
            full_config['stopping_rule'] = config['stopping_rule']
        
        # Update timeouts if specified
        if 'timeouts' in config:
            full_config['timeouts'] = config['timeouts']
        
        # Write complete config with header comments
        config_path = output_dir / 'config.yaml'
        with open(config_path, 'w', encoding='utf-8') as f:
            # Write header with explanatory comments
            f.write("# ============================================================\n")
            f.write("# Experiment Configuration\n")
            f.write("# ============================================================\n")
            f.write(f"# Generated from config set: {config_set.name} (v{config_set.version})\n")
            f.write(f"# Description: {config_set.description}\n")
            f.write("#\n")
            f.write("# This file configures your experiment run.\n")
            f.write("#\n")
            f.write("# Key sections:\n")
            f.write("#   - steps: Configure which steps to run (enable/disable)\n")
            f.write("#       * All prompt files are copied, you control execution here\n")
            f.write("#       * Steps execute in declaration order (not sorted by ID)\n")
            f.write("#   - experiment_name: Unique identifier for this experiment\n")
            f.write("#   - model: OpenAI model to use (gpt-4o, gpt-4o-mini, etc.)\n")
            f.write("#   - random_seed: For reproducibility (keeps runs deterministic)\n")
            f.write("#   - stopping_rule: Controls when execution stops\n")
            f.write("#       * max_runs: Maximum runs per framework (hard limit)\n")
            f.write("#       * min_runs: Minimum before checking convergence\n")
            f.write("#       * confidence_level: Statistical confidence (0.95 = 95%)\n")
            f.write("#       * metrics: Which metrics to monitor for convergence\n")
            f.write("#   - timeouts: Prevents infinite hangs (step timeout, health checks)\n")
            f.write("#   - frameworks: Which AI dev tools to benchmark (enabled: true/false)\n")
            f.write("#   - metrics: Quality measurements to compute\n")
            f.write("#       * functional_correctness: CRUD endpoints validation\n")
            f.write("#       * design_quality: Architecture and design patterns\n")
            f.write("#       * code_maintainability: Code complexity and readability\n")
            f.write("#       * api_calls: Token usage and API efficiency\n")
            f.write("#   - analysis: Convergence detection and statistical analysis settings\n")
            f.write("#   - visualizations: Chart generation configuration\n")
            f.write("#   - report: Markdown report generation settings\n")
            f.write("#   - pricing: Cost per 1K tokens for each model\n")
            f.write("# ============================================================\n\n")
            
            # Write actual config using standard YAML dump
            yaml.dump(full_config, f, default_flow_style=False, sort_keys=False, indent=2)
        
        print("  ✓ config.yaml")
    
    def _generate_requirements(
        self, 
        dependency_analyzer: DependencyAnalyzer, 
        output_dir: Path
    ) -> None:
        """Generate requirements.txt."""
        requirements_content = dependency_analyzer.generate_requirements_file_content()
        (output_dir / 'requirements.txt').write_text(requirements_content, encoding='utf-8')
        print("  ✓ requirements.txt")
    
    def _generate_gitignore(
        self, 
        script_generator: ScriptGenerator, 
        output_dir: Path
    ) -> None:
        """Generate .gitignore."""
        gitignore_content = script_generator.generate_gitignore()
        (output_dir / '.gitignore').write_text(gitignore_content, encoding='utf-8')
        print("  ✓ .gitignore")
    
    def _copy_env_file(self, output_dir: Path) -> None:
        """
        Copy .env file from generator directory if it exists.
        
        This preserves API keys and configuration from the generator,
        saving users time in setting up the new experiment.
        
        Args:
            output_dir: Output directory for generated project
        """
        source_env = self.project_root / '.env'
        
        if source_env.exists():
            dest_env = output_dir / '.env'
            shutil.copy2(source_env, dest_env)
            print("  ✓ Copied .env file from generator")
            print("  ℹ️  API keys and configuration preserved")
        else:
            print("  ℹ️  No .env file found in generator (will use .env.example)")
    
    def _initialize_git_repo(self, output_dir: Path, name: str) -> None:
        """Initialize git repository."""
        try:
            # Initialize repo
            subprocess.run(['git', 'init'], cwd=output_dir, check=True, capture_output=True)
            
            # Add all files
            subprocess.run(['git', 'add', '.'], cwd=output_dir, check=True, capture_output=True)
            
            # Create initial commit
            commit_message = f"Initial commit: {name} experiment"
            subprocess.run(
                ['git', 'commit', '-m', commit_message],
                cwd=output_dir,
                check=True,
                capture_output=True
            )
            
            print("  ✓ Git repository initialized")
            print(f"  ✓ Initial commit created")
            
        except subprocess.CalledProcessError as e:
            print(f"  ⚠️  Warning: Git initialization failed: {e}")
            print("  → You can initialize git manually later")
    
    def _validate_generated_project(self, output_dir: Path) -> None:
        """Validate generated project."""
        required_files = [
            'setup.sh',
            'run.sh',
            'reconcile_usage.sh',
            'README.md',
            'config.yaml',
            'requirements.txt',
            '.gitignore',
            '.env.example',
            'src/main.py',
            'src/setup_frameworks.py',
        ]
        
        missing_files = []
        for file_path in required_files:
            if not (output_dir / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"  ⚠️  Warning: Missing files: {', '.join(missing_files)}")
        else:
            print("  ✓ All required files present")
        
        # Check scripts are executable
        for script in ['setup.sh', 'run.sh', 'reconcile_usage.sh']:
            script_path = output_dir / script
            if script_path.exists() and not script_path.stat().st_mode & 0o111:
                print(f"  ⚠️  Warning: {script} is not executable")
        
        # Validate Python syntax
        python_files = list((output_dir / 'src').rglob('*.py'))
        syntax_errors = []
        
        for py_file in python_files:
            if not self.import_rewriter.validate_syntax(py_file):
                syntax_errors.append(py_file.relative_to(output_dir))
        
        if syntax_errors:
            print(f"  ⚠️  Warning: Syntax errors in: {', '.join(map(str, syntax_errors))}")
        else:
            print(f"  ✓ All {len(python_files)} Python files have valid syntax")
