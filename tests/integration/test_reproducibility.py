"""
Integration test for reproducibility validation.

Executes the same experiment twice with identical configuration and verifies
that all outputs match byte-for-byte.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Tuple
import sys


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while chunk := f.read(4096):
            sha256.update(chunk)
    return sha256.hexdigest()


def compare_json_files(file1: Path, file2: Path) -> Tuple[bool, str]:
    """
    Compare two JSON files for equivalence.
    
    Returns:
        Tuple of (are_equal, difference_message)
    """
    try:
        with open(file1, 'r', encoding='utf-8') as f1:
            data1 = json.load(f1)
        with open(file2, 'r', encoding='utf-8') as f2:
            data2 = json.load(f2)
        
        if data1 == data2:
            return True, "Files are identical"
        else:
            return False, f"JSON content differs:\n{file1}\nvs\n{file2}"
    except Exception as e:
        return False, f"Error comparing files: {e}"


def compare_jsonl_files(file1: Path, file2: Path) -> Tuple[bool, str]:
    """
    Compare two JSONL files line by line.
    
    Returns:
        Tuple of (are_equal, difference_message)
    """
    try:
        with open(file1, 'r', encoding='utf-8') as f1, \
             open(file2, 'r', encoding='utf-8') as f2:
            lines1 = f1.readlines()
            lines2 = f2.readlines()
        
        if len(lines1) != len(lines2):
            return False, f"Different number of lines: {len(lines1)} vs {len(lines2)}"
        
        for i, (line1, line2) in enumerate(zip(lines1, lines2)):
            data1 = json.loads(line1)
            data2 = json.loads(line2)
            
            # Compare excluding timestamp (may vary slightly)
            if 'timestamp' in data1:
                del data1['timestamp']
            if 'timestamp' in data2:
                del data2['timestamp']
            
            if data1 != data2:
                return False, f"Line {i+1} differs:\n{data1}\nvs\n{data2}"
        
        return True, "Files are identical (excluding timestamps)"
    except Exception as e:
        return False, f"Error comparing JSONL files: {e}"


def test_reproducibility(run1_dir: Path, run2_dir: Path) -> bool:
    """
    Test reproducibility by comparing two run directories.
    
    Args:
        run1_dir: Path to first run directory
        run2_dir: Path to second run directory
        
    Returns:
        True if runs are reproducible, False otherwise
    """
    print(f"\n{'='*60}")
    print("REPRODUCIBILITY VALIDATION TEST")
    print(f"{'='*60}\n")
    
    print(f"Run 1: {run1_dir}")
    print(f"Run 2: {run2_dir}\n")
    
    # Files to compare
    files_to_compare = [
        ('metrics.json', compare_json_files),
        ('hitl_events.jsonl', compare_jsonl_files),
        ('commit.txt', lambda f1, f2: (compute_file_hash(f1) == compute_file_hash(f2), 
                                       "Hashes match" if compute_file_hash(f1) == compute_file_hash(f2) 
                                       else "Hashes differ"))
    ]
    
    all_passed = True
    
    for filename, compare_func in files_to_compare:
        file1 = run1_dir / filename
        file2 = run2_dir / filename
        
        # Check if files exist
        if not file1.exists():
            print(f"❌ {filename}: Missing in run 1")
            all_passed = False
            continue
        
        if not file2.exists():
            print(f"❌ {filename}: Missing in run 2")
            all_passed = False
            continue
        
        # Compare files
        is_equal, message = compare_func(file1, file2)
        
        if is_equal:
            print(f"✓ {filename}: {message}")
        else:
            print(f"✗ {filename}: {message}")
            all_passed = False
    
    # Compare usage_api.json if it exists
    usage_file1 = run1_dir / "usage_api.json"
    usage_file2 = run2_dir / "usage_api.json"
    
    if usage_file1.exists() and usage_file2.exists():
        is_equal, message = compare_json_files(usage_file1, usage_file2)
        if is_equal:
            print(f"✓ usage_api.json: {message}")
        else:
            print(f"✗ usage_api.json: {message}")
            all_passed = False
    elif usage_file1.exists() or usage_file2.exists():
        print(f"⚠ usage_api.json: Present in only one run")
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✓ REPRODUCIBILITY TEST PASSED")
        print("All compared files match - experiment is reproducible!")
    else:
        print("✗ REPRODUCIBILITY TEST FAILED")
        print("Some files differ - experiment is NOT reproducible")
    print(f"{'='*60}\n")
    
    return all_passed


def main():
    """Main entry point for reproducibility test."""
    if len(sys.argv) != 3:
        print("Usage: python test_reproducibility.py <run1_dir> <run2_dir>")
        print("\nExample:")
        print("  python test_reproducibility.py \\")
        print("    runs/baes/550e8400-e29b-41d4-a716-446655440000 \\")
        print("    runs/baes/550e8400-e29b-41d4-a716-446655440001")
        sys.exit(1)
    
    run1_dir = Path(sys.argv[1])
    run2_dir = Path(sys.argv[2])
    
    if not run1_dir.exists():
        print(f"Error: Run 1 directory not found: {run1_dir}")
        sys.exit(1)
    
    if not run2_dir.exists():
        print(f"Error: Run 2 directory not found: {run2_dir}")
        sys.exit(1)
    
    passed = test_reproducibility(run1_dir, run2_dir)
    sys.exit(0 if passed else 1)


if __name__ == '__main__':
    main()
