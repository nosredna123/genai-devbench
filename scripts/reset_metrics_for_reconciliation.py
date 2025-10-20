#!/usr/bin/env python3
"""
Reset verification status to 'pending' to allow reconciliation to re-run.

This script marks metrics.json files and runs_manifest.json as needing reconciliation by:
- Setting verification_status to 'pending' in all metrics.json files
- Removing existing usage_api_reconciliation data from metrics.json files
- Updating verification_status to 'pending' in runs_manifest.json

This allows the reconciliation script to re-collect and update token data
from the OpenAI Usage API without changing the existing token values.

Usage:
    python scripts/reset_metrics_for_reconciliation.py                    # Reset all runs
    python scripts/reset_metrics_for_reconciliation.py chatdev            # Reset specific framework
    python scripts/reset_metrics_for_reconciliation.py chatdev run-id     # Reset specific run
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def reset_metrics_file(metrics_path: Path, dry_run: bool = False) -> bool:
    """
    Reset verification status in a metrics.json file to 'pending'.
    
    Args:
        metrics_path: Path to metrics.json file
        dry_run: If True, only show what would be changed
        
    Returns:
        True if file was updated, False otherwise
    """
    try:
        with open(metrics_path, 'r', encoding='utf-8') as f:
            metrics = json.load(f)
        
        # Track if any changes were made
        changed = False
        
        # Set verification status to 'pending'
        if metrics.get('verification_status') != 'pending':
            metrics['verification_status'] = 'pending'
            changed = True
        
        # Remove reconciliation data if it exists (to allow fresh reconciliation)
        if 'usage_api_reconciliation' in metrics:
            del metrics['usage_api_reconciliation']
            changed = True
        
        if changed:
            if dry_run:
                print(f"  Would reset: {metrics_path}")
            else:
                # Write back to file
                with open(metrics_path, 'w', encoding='utf-8') as f:
                    json.dump(metrics, f, indent=2)
                print(f"  ✓ Reset: {metrics_path}")
        else:
            if not dry_run:
                print(f"  ⊘ Already pending: {metrics_path}")
        
        return changed
        
    except Exception as e:
        print(f"  ✗ Error processing {metrics_path}: {e}")
        return False


def find_metrics_files(
    framework: Optional[str] = None, 
    run_id: Optional[str] = None
) -> list[Path]:
    """
    Find metrics.json files to reset.
    
    Args:
        framework: Optional framework filter (chatdev, baes, ghspec)
        run_id: Optional run ID filter
        
    Returns:
        List of paths to metrics.json files
    """
    runs_dir = Path("runs")
    
    if not runs_dir.exists():
        print("Error: runs/ directory not found")
        return []
    
    metrics_files = []
    
    if framework and run_id:
        # Specific run
        specific_path = runs_dir / framework / run_id / "metrics.json"
        if specific_path.exists():
            metrics_files.append(specific_path)
        else:
            print(f"Error: metrics.json not found at {specific_path}")
    elif framework:
        # All runs for framework
        framework_dir = runs_dir / framework
        if framework_dir.exists():
            metrics_files.extend(framework_dir.glob("*/metrics.json"))
        else:
            print(f"Error: framework directory not found: {framework_dir}")
    else:
        # All runs for all frameworks
        for fw_dir in runs_dir.iterdir():
            if fw_dir.is_dir() and fw_dir.name in ['chatdev', 'baes', 'ghspec']:
                metrics_files.extend(fw_dir.glob("*/metrics.json"))
    
    return sorted(metrics_files)


def update_manifest_status(
    framework: Optional[str] = None,
    run_id: Optional[str] = None,
    dry_run: bool = False
) -> int:
    """
    Update verification_status to 'pending' in runs_manifest.json.
    
    Args:
        framework: Optional framework filter
        run_id: Optional run ID filter
        dry_run: If True, only show what would be changed
        
    Returns:
        Number of runs updated
    """
    manifest_path = Path("runs") / "runs_manifest.json"
    
    if not manifest_path.exists():
        print(f"Warning: Manifest not found: {manifest_path}")
        return 0
    
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    except Exception as e:
        print(f"Error reading manifest: {e}")
        return 0
    
    # Update runs to pending based on filters
    updated_count = 0
    for run in manifest.get('runs', []):
        # Apply filters
        if framework and run.get('framework') != framework:
            continue
        if run_id and run.get('run_id') != run_id:
            continue
        
        # Update status if needed
        if run.get('verification_status') != 'pending':
            if dry_run:
                print(f"  Would update manifest: {run.get('run_id')}")
            else:
                run['verification_status'] = 'pending'
            updated_count += 1
    
    if updated_count > 0 and not dry_run:
        # Update metadata
        manifest['last_updated'] = datetime.now(timezone.utc).isoformat()
        
        # Save updated manifest
        try:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2)
            print(f"  ✓ Updated {updated_count} run(s) in manifest")
        except Exception as e:
            print(f"  ✗ Error writing manifest: {e}")
            return 0
    
    return updated_count


def main():
    """Main entry point."""
    # Parse arguments
    framework = None
    run_id = None
    dry_run = False
    
    args = sys.argv[1:]
    
    # Check for flags
    if '--dry-run' in args:
        dry_run = True
        args.remove('--dry-run')
    
    if '-n' in args:
        dry_run = True
        args.remove('-n')
    
    if '--help' in args or '-h' in args:
        print(__doc__)
        sys.exit(0)
    
    # Parse positional arguments
    if len(args) >= 1:
        framework = args[0]
        if framework not in ['chatdev', 'baes', 'ghspec']:
            print(f"Error: Invalid framework '{framework}'. Must be one of: chatdev, baes, ghspec")
            sys.exit(1)
    
    if len(args) >= 2:
        run_id = args[1]
    
    # Find metrics files
    print("Searching for metrics.json files...")
    metrics_files = find_metrics_files(framework, run_id)
    
    if not metrics_files:
        print("No metrics.json files found.")
        sys.exit(0)
    
    print(f"Found {len(metrics_files)} metrics.json file(s)")
    print()
    
    if dry_run:
        print("DRY RUN MODE - no files will be modified")
        print()
    
    # Reset each file
    reset_count = 0
    for metrics_path in metrics_files:
        if reset_metrics_file(metrics_path, dry_run=dry_run):
            reset_count += 1
    
    print()
    
    # Update manifest
    print("Updating runs_manifest.json...")
    manifest_count = update_manifest_status(framework, run_id, dry_run=dry_run)
    
    print()
    print("=" * 60)
    if dry_run:
        print(f"Would reset:")
        print(f"  - {reset_count} / {len(metrics_files)} metrics.json file(s)")
        print(f"  - {manifest_count} run(s) in manifest")
        print("Run without --dry-run to apply changes")
    else:
        print(f"Successfully reset:")
        print(f"  - {reset_count} / {len(metrics_files)} metrics.json file(s)")
        print(f"  - {manifest_count} run(s) in manifest")
        print()
        print("Next steps:")
        print("  1. Run: ./runners/reconcile_usage.sh")
        print("     (The script will wait for Usage API propagation if needed)")
    print("=" * 60)


if __name__ == '__main__':
    main()
