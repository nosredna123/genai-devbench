"""
Artifact Collector

Determines which files need to be copied to generated experiment based on configuration.
Only includes what's needed for enabled frameworks and metrics.
"""

from pathlib import Path
from typing import Dict, List, Set, Any
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


class ArtifactCollector:
    """Collects all artifacts needed for a standalone experiment."""
    
    def __init__(self, config: Dict[str, Any], project_root: Path = None):
        """
        Initialize artifact collector.
        
        Args:
            config: Experiment configuration dictionary
            project_root: Path to generator project root (auto-detected if None)
        """
        self.config = config
        self.project_root = project_root or Path(__file__).parent.parent
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
    
    def collect_source_files(self) -> Dict[str, List[Path]]:
        """
        Collect source files needed for experiment.
        
        Returns:
            Dictionary mapping category to list of file paths:
            {
                'adapters': [Path('src/adapters/baes_adapter.py'), ...],
                'analysis': [Path('src/analysis/report_generator.py'), ...],
                'orchestrator': [Path('src/orchestrator/runner.py'), ...],
                'utils': [Path('src/utils/logger.py'), ...]
            }
        """
        artifacts = {
            'adapters': self._collect_adapter_files(),
            'analysis': self._collect_analysis_files(),
            'orchestrator': self._collect_orchestrator_files(),
            'utils': self._collect_util_files(),
            'config': self._collect_config_module_files(),
        }
        
        return artifacts
    
    def _collect_adapter_files(self) -> List[Path]:
        """Collect adapter files for enabled frameworks."""
        adapters_dir = self.project_root / 'src' / 'adapters'
        files = []
        
        # Always include base adapter
        base_adapter = adapters_dir / 'base_adapter.py'
        if base_adapter.exists():
            files.append(base_adapter)
        
        # Include adapters for enabled frameworks
        for framework in self.enabled_frameworks:
            adapter_file = adapters_dir / f'{framework}_adapter.py'
            if adapter_file.exists():
                files.append(adapter_file)
            
            # Include framework-specific helpers (e.g., baes_kernel_wrapper)
            if framework == 'baes':
                wrapper_file = adapters_dir / 'baes_kernel_wrapper.py'
                if wrapper_file.exists():
                    files.append(wrapper_file)
        
        # Always include __init__.py
        init_file = adapters_dir / '__init__.py'
        if init_file.exists():
            files.append(init_file)
        
        return files
    
    def _collect_analysis_files(self) -> List[Path]:
        """Collect analysis files."""
        analysis_dir = self.project_root / 'src' / 'analysis'
        
        # Include all analysis files - they're all lightweight
        files = [
            analysis_dir / 'report_generator.py',
            analysis_dir / 'stopping_rule.py',
            analysis_dir / 'visualizations.py',
            analysis_dir / 'visualization_factory.py',
            analysis_dir / '__init__.py',
        ]
        
        return [f for f in files if f.exists()]
    
    def _collect_orchestrator_files(self) -> List[Path]:
        """Collect orchestrator files."""
        orchestrator_dir = self.project_root / 'src' / 'orchestrator'
        
        # Core orchestrator files always needed
        files = [
            orchestrator_dir / 'runner.py',
            orchestrator_dir / 'config_loader.py',
            orchestrator_dir / 'metrics_collector.py',
            orchestrator_dir / 'manifest_manager.py',
            orchestrator_dir / 'validator.py',
            orchestrator_dir / 'archiver.py',
            orchestrator_dir / 'usage_reconciler.py',
            orchestrator_dir / '__init__.py',
        ]
        
        return [f for f in files if f.exists()]
    
    def _collect_util_files(self) -> List[Path]:
        """Collect utility files."""
        utils_dir = self.project_root / 'src' / 'utils'
        
        # Core utilities always needed
        files = [
            utils_dir / 'logger.py',
            utils_dir / 'api_client.py',
            utils_dir / 'cost_calculator.py',
            utils_dir / 'experiment_paths.py',
            utils_dir / 'isolation.py',
            utils_dir / 'log_summary.py',
            utils_dir / 'metrics_config.py',
            utils_dir / 'text.py',
            utils_dir / '__init__.py',
        ]
        
        # Note: experiment_registry.py will be excluded (removed in cleanup phase)
        
        return [f for f in files if f.exists()]
    
    def _collect_config_module_files(self) -> List[Path]:
        """Collect config module files (step_config.py for configurable steps)."""
        config_dir = self.project_root / 'src' / 'config'
        
        # Config module files needed for runtime
        files = [
            config_dir / 'step_config.py',
            config_dir / 'exceptions.py',
            config_dir / '__init__.py',
        ]
        
        return [f for f in files if f.exists()]
    
    def collect_docs_files(self) -> Dict[str, List[Path]]:
        """
        Collect documentation files needed for frameworks.
        
        Returns:
            Dictionary with framework-specific docs paths
        """
        docs_dir = self.project_root / 'docs'
        artifacts = {}
        
        # Collect framework-specific documentation
        for framework in self.enabled_frameworks:
            framework_docs_dir = docs_dir / framework
            if framework_docs_dir.exists():
                artifacts[framework] = []
                for file_path in framework_docs_dir.rglob('*'):
                    if file_path.is_file():
                        artifacts[framework].append(file_path)
        
        return artifacts
    
    def collect_config_files(self) -> Dict[str, List[Path]]:
        """
        Collect configuration files.
        
        Returns:
            Dictionary with 'prompts' and 'hitl' keys containing file paths
        """
        config_dir = self.project_root / 'config'
        artifacts = {
            'prompts': [],
            'hitl': [],
        }
        
        # Collect prompts - all prompt files are shared across frameworks
        prompts_dir = config_dir / 'prompts'
        if prompts_dir.exists():
            # Collect all .txt files directly in prompts directory
            for file_path in prompts_dir.glob('*.txt'):
                if file_path.is_file():
                    artifacts['prompts'].append(file_path)
            
            # Also check for framework-specific subdirectories if they exist
            for framework in self.enabled_frameworks:
                framework_prompts_dir = prompts_dir / framework
                if framework_prompts_dir.exists() and framework_prompts_dir.is_dir():
                    for file_path in framework_prompts_dir.rglob('*'):
                        if file_path.is_file():
                            artifacts['prompts'].append(file_path)
        
        # Collect HITL configuration
        hitl_dir = config_dir / 'hitl'
        if hitl_dir.exists():
            for file_path in hitl_dir.rglob('*'):
                if file_path.is_file():
                    artifacts['hitl'].append(file_path)
        
        return artifacts
    
    def collect_dependencies(self) -> Set[str]:
        """
        Collect Python dependencies needed for experiment.
        
        Returns:
            Set of dependency strings (e.g., 'pyyaml>=6.0')
        """
        dependencies = set()
        
        # Base dependencies (always)
        dependencies.update([
            'pyyaml>=6.0',
            'requests>=2.31.0',
            'python-dotenv>=1.0.0',
            'openai>=1.0.0',
        ])
        
        # Analysis and metrics (always included for now)
        dependencies.update([
            'matplotlib>=3.7.0',
            'numpy>=1.24.0',
            'pandas>=2.0.0',
            'scipy>=1.10.0',
        ])
        
        # Utilities
        dependencies.update([
            'tqdm>=4.65.0',
            'colorlog>=6.7.0',
        ])
        
        # Framework-specific dependencies
        # (Currently frameworks are git clones, so no extra deps)
        
        # Metric-specific dependencies
        # (Could be extended based on enabled_metrics in future)
        
        return dependencies
    
    def get_all_artifacts(self) -> Dict[str, Any]:
        """
        Get all artifacts in a single call.
        
        Returns:
            Dictionary containing all artifact categories
        """
        return {
            'source_files': self.collect_source_files(),
            'config_files': self.collect_config_files(),
            'docs_files': self.collect_docs_files(),
            'dependencies': self.collect_dependencies(),
        }
