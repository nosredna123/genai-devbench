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
        output_dir: Path
    ) -> None:
        """
        Generate complete standalone experiment project.
        
        Args:
            name: Experiment name
            config: Experiment configuration dictionary
            output_dir: Output directory for generated project
        """
        print(f"🚀 Generating standalone experiment: {name}")
        print(f"📁 Output directory: {output_dir}")
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
        
        # Step 4: Copy configuration files
        print("⚙️  Copying configuration files...")
        self._copy_config_files(artifacts['config_files'], output_dir)
        
        # Step 5: Generate template files
        print("📝 Generating template files...")
        self._copy_template_files(output_dir)
        
        # Step 6: Generate scripts
        print("🔧 Generating execution scripts...")
        self._generate_all_scripts(script_generator, output_dir)
        
        # Step 7: Generate configuration
        print("⚙️  Generating configuration...")
        self._generate_config_yaml(config, output_dir)
        
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
    
    def _copy_config_files(
        self, 
        config_files: Dict[str, list[Path]], 
        output_dir: Path
    ) -> None:
        """Copy configuration files (no modification needed)."""
        for category, files in config_files.items():
            for source_file in files:
                # Determine destination path
                relative_path = source_file.relative_to(self.project_root / 'config')
                dest_file = output_dir / 'config' / relative_path
                
                # Ensure parent directory exists
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(source_file, dest_file)
                
                print(f"  ✓ config/{relative_path}")
    
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
            logger.error("config.yaml not found")
            return 1
        
        config = load_config(config_path)
        
        experiment_name = config.get('experiment_name', 'unnamed')
        model = config.get('model', 'unknown')
        
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
        
        # Get max runs
        max_runs = config.get('max_runs_per_framework', 1)
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
        logger.warning("Experiment interrupted by user")
        return 130
        
    except Exception as e:
        logger.exception("Experiment failed")
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
        
        # README.md
        readme = script_generator.generate_readme()
        (output_dir / 'README.md').write_text(readme, encoding='utf-8')
        print("  ✓ README.md")
        
        # .env.example
        env_example = script_generator.generate_env_example()
        (output_dir / '.env.example').write_text(env_example, encoding='utf-8')
        print("  ✓ .env.example")
    
    def _generate_config_yaml(self, config: Dict[str, Any], output_dir: Path) -> None:
        """Generate standalone config.yaml."""
        # Make paths relative to experiment root
        standalone_config = config.copy()
        
        # Update paths
        if 'prompts_dir' in standalone_config:
            standalone_config['prompts_dir'] = 'config/prompts'
        if 'hitl_path' in standalone_config:
            standalone_config['hitl_path'] = 'config/hitl/expanded_spec.txt'
        
        # Keep only enabled frameworks
        if 'frameworks' in standalone_config:
            enabled_frameworks = {
                name: fw_config 
                for name, fw_config in standalone_config['frameworks'].items()
                if fw_config.get('enabled', False)
            }
            standalone_config['frameworks'] = enabled_frameworks
        
        # Write config
        config_path = output_dir / 'config.yaml'
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(standalone_config, f, default_flow_style=False, sort_keys=False, indent=2)
        
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
        for script in ['setup.sh', 'run.sh']:
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
