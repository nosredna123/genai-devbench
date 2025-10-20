"""Setup framework repositories for experiment."""

import subprocess
from pathlib import Path
import yaml
import sys


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
