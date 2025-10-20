"""
Import Rewriter

Rewrites Python imports in source files to work in standalone experiment projects.
Removes parent project references and updates paths.
"""

import re
import ast
from pathlib import Path
from typing import Optional


class ImportRewriter:
    """Rewrites imports in Python files for standalone operation."""
    
    def __init__(self):
        """Initialize import rewriter."""
        # Patterns to detect and remove
        self.parent_reference_patterns = [
            r'from\s+src\.utils\.experiment_registry\s+import.*',
            r'import\s+src\.utils\.experiment_registry.*',
            r'get_registry\(\)',
            r'registry\.register_experiment',
            r'ExperimentAlreadyExistsError',
        ]
        
        # Path replacements
        self.path_replacements = [
            # Replace references to parent experiments directory
            (r"Path\(['\"]experiments['\"]", "Path('runs'"),
            (r"['\"]experiments/", "'runs/"),
            (r'["\']experiments/', '"runs/'),
            
            # Replace references to parent runners directory
            (r"['\"]runners/", "'scripts/"),
            (r'["\']runners/', '"scripts/'),
            
            # Remove parent directory navigation
            (r"Path\(['\"]\.\.\/experiments", "Path('runs'"),
            (r"Path\(['\"]\.\.\/\.\.", "Path('.'"),
        ]
    
    def rewrite_file(self, source_path: Path, dest_path: Path) -> None:
        """
        Read source file, rewrite imports and paths, write to destination.
        
        Args:
            source_path: Path to source file
            dest_path: Path to destination file
        """
        # Read source content
        with open(source_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Rewrite content
        rewritten_content = self.rewrite_content(content, source_path)
        
        # Ensure destination directory exists
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write to destination
        with open(dest_path, 'w', encoding='utf-8') as f:
            f.write(rewritten_content)
    
    def rewrite_content(self, content: str, file_path: Optional[Path] = None) -> str:
        """
        Rewrite content by removing parent references and updating paths.
        
        Args:
            content: Source file content
            file_path: Optional path to source file (for context)
            
        Returns:
            Rewritten content
        """
        # Remove parent project references (registry imports, etc.)
        for pattern in self.parent_reference_patterns:
            content = re.sub(pattern, '# [Generator: removed parent reference]', content)
        
        # Update path references
        for old_pattern, new_value in self.path_replacements:
            content = re.sub(old_pattern, new_value, content)
        
        # Special handling for experiment_paths.py
        if file_path and file_path.name == 'experiment_paths.py':
            content = self._rewrite_experiment_paths(content)
        
        # Special handling for config_loader.py
        if file_path and file_path.name == 'config_loader.py':
            content = self._rewrite_config_loader(content)
        
        return content
    
    def _rewrite_experiment_paths(self, content: str) -> str:
        """
        Special rewriting for experiment_paths.py.
        
        Changes:
        - Remove registry dependencies
        - Make paths relative to experiment root (current dir)
        - Simplify initialization
        """
        # Remove registry imports
        content = re.sub(
            r'from\s+\.experiment_registry.*\n',
            '# [Generator: removed registry import]\n',
            content
        )
        
        # Update experiments_base_dir default to current directory
        content = re.sub(
            r"experiments_base_dir\s*or\s*Path\(['\"]experiments['\"]",
            "experiments_base_dir or Path('.')",
            content
        )
        
        # Remove validate_exists parameter logic if it references registry
        # (Will be handled by actual implementation review)
        
        return content
    
    def _rewrite_config_loader(self, content: str) -> str:
        """
        Special rewriting for config_loader.py.
        
        Changes:
        - Simplify to load from ./config.yaml
        - Remove registry lookups
        - Remove parent path resolution
        """
        # Remove registry imports
        content = re.sub(
            r'from\s+\.\.utils\.experiment_registry.*\n',
            '# [Generator: removed registry import]\n',
            content
        )
        
        # Simplify config path resolution
        # (Specific changes depend on current implementation)
        
        return content
    
    def validate_syntax(self, file_path: Path) -> bool:
        """
        Validate that Python file has valid syntax.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            True if syntax is valid, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
            return True
        except SyntaxError:
            return False
    
    def check_for_parent_references(self, file_path: Path) -> list[str]:
        """
        Check if file contains references to parent project.
        
        Args:
            file_path: Path to Python file
            
        Returns:
            List of lines containing parent references
        """
        problematic_patterns = [
            'experiment_registry',
            'genai-devbench',
            '../experiments',
            '../runners',
            '.experiments.json',
        ]
        
        issues = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                for pattern in problematic_patterns:
                    if pattern in line and '[Generator:' not in line:
                        issues.append(f"Line {line_num}: {line.strip()}")
        
        return issues
