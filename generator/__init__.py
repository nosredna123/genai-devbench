"""
Standalone Experiment Generator

This package contains the core logic for generating fully independent,
self-contained experiment projects.

Components:
- ArtifactCollector: Determines which files to copy based on configuration
- ImportRewriter: Adapts Python imports for standalone operation
- ScriptGenerator: Generates execution scripts (setup.sh, run.sh, README)
- DependencyAnalyzer: Creates minimal requirements.txt
- StandaloneGenerator: Main orchestrator coordinating all components
"""

from .artifact_collector import ArtifactCollector
from .import_rewriter import ImportRewriter
from .script_generator import ScriptGenerator
from .dependency_analyzer import DependencyAnalyzer
from .standalone_generator import StandaloneGenerator

__all__ = [
    'ArtifactCollector',
    'ImportRewriter',
    'ScriptGenerator',
    'DependencyAnalyzer',
    'StandaloneGenerator',
]

__version__ = '2.0.0'
