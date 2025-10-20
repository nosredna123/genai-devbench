"""
Dependency Analyzer

Analyzes experiment configuration and generates minimal requirements.txt
including only dependencies needed for enabled frameworks and metrics.
"""

from typing import Dict, List, Set, Any


class DependencyAnalyzer:
    """Analyzes and generates minimal dependency list."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize dependency analyzer.
        
        Args:
            config: Experiment configuration dictionary
        """
        self.config = config
        self.enabled_frameworks = self._get_enabled_frameworks()
        self.enabled_metrics = self._get_enabled_metrics()
    
    def _get_enabled_frameworks(self) -> List[str]:
        """Get list of enabled framework names."""
        frameworks = self.config.get('frameworks', {})
        return [
            name for name, fw_config in frameworks.items()
            if fw_config.get('enabled', False)
        ]
    
    def _get_enabled_metrics(self) -> List[str]:
        """Get list of enabled metric names."""
        metrics_config = self.config.get('metrics', {})
        return metrics_config.get('enabled', [])
    
    def generate_requirements(self) -> List[str]:
        """
        Generate minimal requirements list.
        
        Returns:
            List of dependency strings (e.g., ['pyyaml>=6.0', ...])
        """
        dependencies = set()
        
        # Base requirements (always needed)
        dependencies.update(self._get_base_requirements())
        
        # Analysis and metrics (always included for now)
        dependencies.update(self._get_analysis_requirements())
        
        # Utilities
        dependencies.update(self._get_utility_requirements())
        
        # Framework-specific dependencies
        dependencies.update(self._get_framework_requirements())
        
        # Metric-specific dependencies
        dependencies.update(self._get_metric_requirements())
        
        # Sort for consistent output
        return sorted(list(dependencies))
    
    def _get_base_requirements(self) -> Set[str]:
        """Get base dependencies always needed."""
        return {
            'pyyaml>=6.0',
            'requests>=2.31.0',
            'python-dotenv>=1.0.0',
            'openai>=1.0.0',
        }
    
    def _get_analysis_requirements(self) -> Set[str]:
        """Get dependencies for analysis and visualization."""
        return {
            'matplotlib>=3.7.0',
            'numpy>=1.24.0',
            'pandas>=2.0.0',
            'scipy>=1.10.0',
        }
    
    def _get_utility_requirements(self) -> Set[str]:
        """Get utility dependencies."""
        return {
            'tqdm>=4.65.0',
            'colorlog>=6.7.0',
        }
    
    def _get_framework_requirements(self) -> Set[str]:
        """
        Get framework-specific dependencies.
        
        Currently frameworks are git clones, so no extra Python packages needed.
        This method exists for future extensibility.
        """
        dependencies = set()
        
        # Framework-specific dependencies can be added here
        # For example:
        # if 'baes' in self.enabled_frameworks:
        #     dependencies.add('some-baes-dependency>=1.0')
        
        return dependencies
    
    def _get_metric_requirements(self) -> Set[str]:
        """
        Get metric-specific dependencies.
        
        Different metrics may require different packages.
        """
        dependencies = set()
        
        # All current metrics use the analysis packages already included
        # This method exists for future extensibility
        
        # Example:
        # if 'code_quality' in self.enabled_metrics:
        #     dependencies.add('pylint>=2.17.0')
        
        return dependencies
    
    def get_python_version_requirement(self) -> str:
        """
        Return required Python version.
        
        Returns:
            Version string (e.g., '>=3.9')
        """
        return ">=3.9"
    
    def generate_requirements_file_content(self) -> str:
        """
        Generate complete requirements.txt file content with comments.
        
        Returns:
            Complete requirements.txt content
        """
        requirements = self.generate_requirements()
        
        # Group dependencies by category
        base = [r for r in requirements if any(pkg in r for pkg in ['pyyaml', 'requests', 'python-dotenv', 'openai'])]
        analysis = [r for r in requirements if any(pkg in r for pkg in ['matplotlib', 'numpy', 'pandas', 'scipy'])]
        utils = [r for r in requirements if r not in base and r not in analysis]
        
        content = f"""# Python {self.get_python_version_requirement()}
# Generated for experiment: {self.config.get('experiment_name', 'unknown')}

# Core Dependencies
{chr(10).join(base)}

# Analysis and Metrics
{chr(10).join(analysis)}

# Utilities
{chr(10).join(utils) if utils else '# (none)'}
"""
        return content
