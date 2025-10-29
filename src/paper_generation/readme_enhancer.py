"""
ReadmeEnhancer: Enhance experiment README with comprehensive reproduction instructions.

This module appends a detailed Reproduction Guide to the experiment's README.md,
enabling independent researchers to reproduce the experiment in ≤30 minutes.
"""

import logging
from pathlib import Path
from datetime import datetime
import sys
import re

logger = logging.getLogger(__name__)


class ReadmeEnhancer:
    """
    Enhances experiment README.md with reproduction instructions.
    
    Loads a template, injects experiment-specific values (frameworks, Python version,
    runtime estimates), and appends to the existing README.md file.
    """
    
    def __init__(self, template_path: Path | None = None):
        """
        Initialize ReadmeEnhancer.
        
        Args:
            template_path: Path to README reproduction template.
                          If None, uses default template in templates/
        """
        if template_path is None:
            # Default to bundled template
            repo_root = Path(__file__).parent.parent.parent
            template_path = repo_root / "templates" / "readme_reproduction_section.md"
        
        self.template_path = template_path
        
        if not self.template_path.exists():
            raise FileNotFoundError(
                f"README template not found: {self.template_path}\n"
                f"Expected template at: {self.template_path}"
            )
        
        # Load template
        self.template = self.template_path.read_text(encoding='utf-8')
        logger.info("Loaded README template from %s", self.template_path)
    
    def enhance_readme(
        self,
        experiment_dir: Path,
        frameworks: list[str],
        num_runs: int,
        python_version: str | None = None
    ) -> Path:
        """
        Enhance experiment README.md with reproduction instructions.
        
        Args:
            experiment_dir: Path to experiment directory
            frameworks: List of framework names tested
            num_runs: Number of runs per framework
            python_version: Python version requirement (e.g., "3.11")
                           If None, detects from current Python version
        
        Returns:
            Path to updated README.md file
            
        Raises:
            FileNotFoundError: If experiment directory doesn't exist
        """
        if not experiment_dir.exists():
            raise FileNotFoundError(f"Experiment directory not found: {experiment_dir}")
        
        readme_path = experiment_dir / "README.md"
        
        # Detect Python version if not provided
        if python_version is None:
            python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
        
        python_major = python_version.split('.')[0]
        
        # Calculate estimated runtime (rough heuristic: 30 seconds per run)
        total_runs = len(frameworks) * num_runs
        estimated_minutes = (total_runs * 30) // 60
        if estimated_minutes < 5:
            estimated_runtime = "5-10 minutes"
        elif estimated_minutes < 15:
            estimated_runtime = "10-15 minutes"
        elif estimated_minutes < 30:
            estimated_runtime = "15-30 minutes"
        else:
            estimated_runtime = f"{estimated_minutes}-{estimated_minutes + 10} minutes"
        
        # Prepare template values
        values = {
            'python_version': python_version,
            'python_major_version': python_major,
            'frameworks_list': ', '.join(frameworks),
            'num_frameworks': str(len(frameworks)),
            'num_runs': str(num_runs),
            'estimated_runtime': estimated_runtime,
            'experiment_dir': str(experiment_dir),
            'generation_date': datetime.now().strftime('%Y-%m-%d')
        }
        
        # Inject values into template
        enhanced_content = self._inject_values(self.template, values)
        
        # Check if README already has a Reproduction Guide
        if readme_path.exists():
            existing_content = readme_path.read_text(encoding='utf-8')
            
            # Check if Reproduction Guide already exists
            if '## Reproduction Guide' in existing_content:
                logger.warning("README already contains Reproduction Guide - replacing")
                # Remove existing reproduction section
                existing_content = re.sub(
                    r'## Reproduction Guide.*?(?=##|\Z)',
                    '',
                    existing_content,
                    flags=re.DOTALL
                ).rstrip() + '\n\n'
            
            # Append new reproduction section
            updated_content = existing_content + '\n---\n\n' + enhanced_content
        else:
            # Create new README with reproduction section
            logger.info("Creating new README.md with Reproduction Guide")
            updated_content = f"# Experiment: {experiment_dir.name}\n\n{enhanced_content}"
        
        # Write updated README
        readme_path.write_text(updated_content, encoding='utf-8')
        logger.info("Enhanced README.md at %s", readme_path)
        
        return readme_path
    
    def _inject_values(self, template: str, values: dict[str, str]) -> str:
        """
        Inject experiment-specific values into template.
        
        Replaces placeholders like {python_version} with actual values.
        
        Args:
            template: Template string with {placeholders}
            values: Dictionary of placeholder -> value mappings
        
        Returns:
            Template with all placeholders replaced
        """
        result = template
        for key, value in values.items():
            placeholder = '{' + key + '}'
            result = result.replace(placeholder, value)
        
        # Check for any remaining unreplaced placeholders
        remaining = re.findall(r'\{(\w+)\}', result)
        if remaining:
            logger.warning(
                "Template has unreplaced placeholders: %s",
                ', '.join(set(remaining))
            )
        
        return result
