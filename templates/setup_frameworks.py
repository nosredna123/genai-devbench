"""Setup framework repositories for experiment."""

import subprocess
from pathlib import Path
import yaml
import sys
import os


def load_config():
    """Load experiment configuration."""
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print("❌ Error: config.yaml not found")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing config.yaml: {e}")
        sys.exit(1)


def clone_framework(name: str, repo_url: str, commit_hash: str):
    """Clone and checkout framework repository."""
    frameworks_dir = Path('frameworks')
    frameworks_dir.mkdir(exist_ok=True)
    
    target_dir = frameworks_dir / name
    
    if target_dir.exists():
        print(f"✓ {name} already exists at {target_dir}")
        # Verify it's on the correct commit
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=target_dir,
                capture_output=True,
                text=True,
                check=True
            )
            current_hash = result.stdout.strip()
            if current_hash.startswith(commit_hash) or commit_hash.startswith(current_hash):
                print(f"  Already on commit {commit_hash[:7]}")
                return
            else:
                print(f"  Updating to commit {commit_hash[:7]}...")
                subprocess.run(
                    ['git', 'fetch'],
                    cwd=target_dir,
                    check=True,
                    capture_output=True
                )
                subprocess.run(
                    ['git', 'checkout', commit_hash],
                    cwd=target_dir,
                    check=True,
                    capture_output=True
                )
                print(f"✓ Updated {name}")
        except subprocess.CalledProcessError:
            print(f"  ⚠️  Could not verify commit, will re-clone")
            import shutil
            shutil.rmtree(target_dir)
    
    if not target_dir.exists():
        print(f"Cloning {name} from {repo_url}...")
        try:
            subprocess.run(
                ['git', 'clone', repo_url, str(target_dir)],
                check=True,
                capture_output=True
            )
            print(f"✓ Cloned {name}")
            
            print(f"  Checking out commit {commit_hash[:7]}...")
            subprocess.run(
                ['git', 'checkout', commit_hash],
                cwd=target_dir,
                check=True,
                capture_output=True
            )
            print(f"✓ {name} ready")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to setup {name}:")
            print(f"   {e}")
            if e.stderr:
                print(f"   {e.stderr.decode('utf-8')}")
            sys.exit(1)


def setup_venv_if_needed(name: str, framework_path: Path, use_venv: bool):
    """
    Create virtual environment for framework if needed.
    
    Args:
        name: Framework name (baes, chatdev, ghspec)
        framework_path: Path to framework directory
        use_venv: Whether framework needs Python venv (from config)
    """
    if not use_venv:
        print(f"  Skipping venv (use_venv=false)")
        return
    
    requirements_file = framework_path / 'requirements.txt'
    if not requirements_file.exists():
        print(f"  ⚠️  requirements.txt not found, skipping venv")
        return
    
    venv_path = framework_path / '.venv'
    python_path = venv_path / 'bin' / 'python'
    
    # Check if venv already exists
    if python_path.exists() and os.access(python_path, os.X_OK):
        print(f"  ✓ Venv already exists")
        return
    
    print(f"  Creating virtual environment...")
    try:
        # Create venv
        subprocess.run(
            ['python3', '-m', 'venv', str(venv_path), '--clear'],
            check=True,
            capture_output=True,
            timeout=60
        )
        
        # Install requirements
        print(f"  Installing dependencies (this may take 3-5 minutes)...")
        subprocess.run(
            [
                str(python_path), '-m', 'pip', 'install',
                '-r', str(requirements_file),
                '--timeout', '300'
            ],
            check=True,
            capture_output=True,
            timeout=300
        )
        
        print(f"  ✓ Venv created successfully")
        
    except subprocess.TimeoutExpired:
        print(f"  ❌ Venv creation timed out")
        # Clean up partial venv
        if venv_path.exists():
            import shutil
            shutil.rmtree(venv_path, ignore_errors=True)
        sys.exit(1)
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Failed to create venv:")
        if e.stderr:
            print(f"     {e.stderr.decode('utf-8')}")
        # Clean up partial venv
        if venv_path.exists():
            import shutil
            shutil.rmtree(venv_path, ignore_errors=True)
        sys.exit(1)


def patch_chatdev_if_needed(framework_path: Path):
    """
    Apply ChatDev patches for O1/GPT-5 support.
    
    Patches are idempotent - safe to run multiple times.
    
    Args:
        framework_path: Path to chatdev framework directory
    """
    print(f"  Applying ChatDev patches...")
    
    # Patch 1: Add O1 and GPT-5 model types to camel/typing.py
    typing_file = framework_path / 'camel' / 'typing.py'
    if typing_file.exists():
        content = typing_file.read_text()
        
        # Check if already patched
        if 'O1_PREVIEW' not in content:
            # Find ModelType enum and add new entries
            if 'class ModelType(Enum):' in content:
                # Add after existing model types
                content = content.replace(
                    'GPT_4O_MINI = "gpt-4o-mini"',
                    'GPT_4O_MINI = "gpt-4o-mini"\n    O1_PREVIEW = "o1-preview"\n    O1_MINI = "o1-mini"\n    GPT_5 = "gpt-5"'
                )
                typing_file.write_text(content)
                print(f"    ✓ Patched camel/typing.py")
            else:
                print(f"    ⚠️  Could not find ModelType enum in camel/typing.py")
        else:
            print(f"    ✓ camel/typing.py already patched")
    else:
        print(f"    ⚠️  camel/typing.py not found")
    
    # Patch 2: Add O1/GPT-5 handling to camel/model_backend.py
    backend_file = framework_path / 'camel' / 'model_backend.py'
    if backend_file.exists():
        content = backend_file.read_text()
        
        if 'o1-preview' not in content:
            # Add O1/GPT-5 models to token limit dictionaries
            # These are dictionaries, so we need to add individual key-value pairs
            content = content.replace(
                '"gpt-4o-mini": 16384',
                '"gpt-4o-mini": 16384,\n                "o1-preview": 16384,\n                "o1-mini": 16384,\n                "gpt-5": 16384'
            )
            backend_file.write_text(content)
            print(f"    ✓ Patched camel/model_backend.py")
        else:
            print(f"    ✓ camel/model_backend.py already patched")
    else:
        print(f"    ⚠️  camel/model_backend.py not found")
    
    # Patch 3: Update statistics tracking for O1/GPT-5
    stats_file = framework_path / 'chatdev' / 'statistics.py'
    if stats_file.exists():
        content = stats_file.read_text()
        
        if 'o1-preview' not in content:
            # Add O1/GPT-5 to cost tracking
            content = content.replace(
                '"gpt-4o": 0.01',
                '"gpt-4o": 0.01,\n        "o1-preview": 0.015,\n        "o1-mini": 0.005,\n        "gpt-5": 0.02'
            )
            stats_file.write_text(content)
            print(f"    ✓ Patched chatdev/statistics.py")
        else:
            print(f"    ✓ chatdev/statistics.py already patched")
    else:
        print(f"    ⚠️  chatdev/statistics.py not found")
    
    print(f"  ✓ ChatDev patches applied")


def main():
    """Main entry point."""
    try:
        config = load_config()
        
        print("========================================")
        print("Setting up framework repositories")
        print("========================================")
        print()
        
        frameworks = config.get('frameworks', {})
        if not frameworks:
            print("⚠️  No frameworks configured")
            return
        
        enabled_frameworks = {
            name: fw_config
            for name, fw_config in frameworks.items()
            if fw_config.get('enabled', False)
        }
        
        if not enabled_frameworks:
            print("⚠️  No frameworks enabled")
            return
        
        print(f"Enabled frameworks: {', '.join(enabled_frameworks.keys())}")
        print()
        
        for name, fw_config in enabled_frameworks.items():
            clone_framework(
                name,
                fw_config['repo_url'],
                fw_config['commit_hash']
            )
            
            # Setup venv if needed
            framework_path = Path('frameworks') / name
            use_venv = fw_config.get('use_venv', False)
            setup_venv_if_needed(name, framework_path, use_venv)
            
            # Apply ChatDev-specific patches
            if name == 'chatdev':
                patch_chatdev_if_needed(framework_path)
            
            print()
        
        print("========================================")
        print("✅ All frameworks ready!")
        print("========================================")
        
    except KeyError as e:
        print(f"❌ Error: Missing required configuration key: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
