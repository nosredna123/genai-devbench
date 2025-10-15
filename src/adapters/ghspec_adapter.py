"""
GitHub Spec-kit framework adapter implementation.

Integrates with GitHub Spec-kit (ghspec) framework for experiment execution.
"""

import subprocess
import time
from pathlib import Path
from typing import Any, Dict
import requests
from src.adapters.base_adapter import BaseAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class GHSpecAdapter(BaseAdapter):
    """Adapter for GitHub Spec-kit framework."""
    
    def __init__(self, config: Dict[str, Any], run_id: str, workspace_path: str):
        """
        Initialize GitHub Spec-kit adapter.
        
        Args:
            config: Framework configuration from experiment.yaml
            run_id: Unique run identifier
            workspace_path: Isolated workspace directory
        """
        super().__init__(config, run_id, workspace_path)
        self.process = None
        self.framework_dir = None
        self.hitl_text = None
        
    def start(self) -> None:
        """
        Clone GitHub Spec-kit repository and setup workspace structure.
        
        Phase 2 Implementation:
        - Clone spec-kit repository from configured URL
        - Checkout and verify specific commit hash
        - Setup workspace directory structure for artifacts
        - Initialize feature directory (specs/001-baes-experiment/)
        - GHSpec is CLI-based (bash scripts), no services to start
        
        The workspace will have this structure:
            workspace_path/
                ghspec_framework/        # Cloned spec-kit repo
                specs/                   # Artifact storage
                    001-baes-experiment/ # Feature directory
                        spec.md          # Generated specification
                        plan.md          # Generated technical plan
                        tasks.md         # Generated task list
                        src/             # Generated code files
        """
        logger.info("Starting GitHub Spec-kit framework",
                   extra={'run_id': self.run_id, 'event': 'framework_start'})
        
        repo_url = self.config['repo_url']
        commit_hash = self.config['commit_hash']
        
        # Create framework directory for cloned repo
        self.framework_dir = Path(self.workspace_path) / "ghspec_framework"
        
        try:
            # Clone repository
            logger.info("Cloning GitHub Spec-kit repository",
                       extra={'run_id': self.run_id,
                             'metadata': {'repo': repo_url, 'commit': commit_hash}})
            
            subprocess.run(
                ['git', 'clone', repo_url, str(self.framework_dir)],
                check=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=120
            )
            
            # Checkout specific commit
            subprocess.run(
                ['git', 'checkout', commit_hash],
                cwd=self.framework_dir,
                check=True,
                capture_output=True,
                stdin=subprocess.DEVNULL,
                timeout=60
            )
            
            # Verify commit hash matches config (reproducibility requirement)
            self.verify_commit_hash(self.framework_dir, commit_hash)
            
            logger.info("GitHub Spec-kit repository cloned and verified",
                       extra={'run_id': self.run_id,
                             'metadata': {'commit': commit_hash}})
            
            # Setup workspace directory structure for artifacts
            self._setup_workspace_structure()
            
            # GHSpec is CLI-based (bash scripts + direct OpenAI API calls)
            # No virtual environment needed - we call OpenAI API directly
            # No persistent services to start - we invoke bash scripts per phase
            
            logger.info("GitHub Spec-kit framework ready",
                       extra={'run_id': self.run_id,
                             'metadata': {
                                 'framework_dir': str(self.framework_dir),
                                 'specs_dir': str(self.specs_dir),
                                 'feature_dir': str(self.feature_dir)
                             }})
            
        except subprocess.CalledProcessError as e:
            logger.error("Failed to initialize GitHub Spec-kit",
                        extra={'run_id': self.run_id,
                              'metadata': {'error': str(e),
                                         'stderr': e.stderr.decode() if e.stderr else ''}})
            raise RuntimeError("GitHub Spec-kit initialization failed") from e
        except subprocess.TimeoutExpired as e:
            logger.error("GitHub Spec-kit initialization timed out",
                        extra={'run_id': self.run_id})
            raise RuntimeError("GitHub Spec-kit initialization timed out") from e
    
    def _setup_workspace_structure(self) -> None:
        """
        Create workspace directory structure for GHSpec artifacts.
        
        Creates:
            workspace_path/
                specs/                      # Root for all feature specifications
                    001-baes-experiment/    # Feature directory (fixed name for experiment)
                        spec.md             # Will be generated in Phase 3
                        plan.md             # Will be generated in Phase 3
                        tasks.md            # Will be generated in Phase 3
                        src/                # Will contain generated code (Phase 4)
        
        The feature number and name follow spec-kit conventions:
        - NNN format for feature numbers (001, 002, etc.)
        - Kebab-case for feature names
        - For this experiment, we use "001-baes-experiment" consistently
        """
        # Create specs root directory
        self.specs_dir = Path(self.workspace_path) / "specs"
        self.specs_dir.mkdir(parents=True, exist_ok=True)
        
        # Create feature directory with fixed name for reproducibility
        # Using "baes-experiment" as the feature name for all runs
        self.feature_dir = self.specs_dir / "001-baes-experiment"
        self.feature_dir.mkdir(parents=True, exist_ok=True)
        
        # Create src directory for generated code (used in Phase 4)
        self.src_dir = self.feature_dir / "src"
        self.src_dir.mkdir(parents=True, exist_ok=True)
        
        # Store artifact paths for easy access in later phases
        self.spec_md_path = self.feature_dir / "spec.md"
        self.plan_md_path = self.feature_dir / "plan.md"
        self.tasks_md_path = self.feature_dir / "tasks.md"
        
        logger.info("Workspace structure created",
                   extra={'run_id': self.run_id,
                         'metadata': {
                             'specs_dir': str(self.specs_dir),
                             'feature_dir': str(self.feature_dir),
                             'src_dir': str(self.src_dir)
                         }})

            
    def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
        """
        Execute a step by sending command to GitHub Spec-kit framework.
        
        Args:
            step_num: Step number (1-6)
            command_text: Natural language command
            
        Returns:
            Dictionary with execution results
        """
        self.current_step = step_num
        start_time = time.time()
        
        logger.info("Executing step",
                   extra={'run_id': self.run_id, 'step': step_num, 
                         'event': 'step_start', 
                         'metadata': {'framework': 'ghspec'}})
        
        # TODO: Implement actual GitHub Spec-kit command execution
        # This is a placeholder implementation
        
        hitl_count = 0
        tokens_in = 0
        tokens_out = 0
        
        # Simulate step execution
        # In real implementation, this would:
        # 1. Send command to GitHub Spec-kit CLI/API
        # 2. Monitor for HITL requests
        # 3. Track token usage
        # 4. Wait for completion
        
        duration = time.time() - start_time
        
        return {
            'success': True,  # Placeholder
            'duration_seconds': duration,
            'hitl_count': hitl_count,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'retry_count': 0
        }
        
    def health_check(self) -> bool:
        """
        Check if GitHub Spec-kit framework services are responding.
        
        Returns:
            True if healthy, False otherwise
        """
        api_port = self.config['api_port']
        ui_port = self.config['ui_port']
        
        try:
            api_response = requests.get(f"http://localhost:{api_port}/health", 
                                       timeout=5)
            ui_response = requests.get(f"http://localhost:{ui_port}/", 
                                      timeout=5)
            return api_response.status_code == 200 and ui_response.status_code == 200
        except requests.RequestException:
            return False
            
    def handle_hitl(self, query: str) -> str:
        """
        Return fixed HITL response for deterministic execution.
        
        Note: GHSpec uses different HITL content than ChatDev/BAEs because it
        generates specifications incrementally. This returns meta-guidelines
        for handling ambiguous requirements, not a concrete specification.
        
        Args:
            query: Framework's clarification question
            
        Returns:
            Fixed clarification guidelines text
        """
        if self.hitl_text is None:
            # Load GHSpec-specific clarification guidelines
            hitl_path = Path("config/hitl/ghspec_clarification_guidelines.txt")
            with open(hitl_path, 'r', encoding='utf-8') as f:
                self.hitl_text = f.read().strip()
                
        logger.info("HITL intervention",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'event': 'hitl', 
                         'metadata': {'query_length': len(query), 'framework': 'ghspec'}})
                         
        return self.hitl_text
        
    def stop(self) -> None:
        """
        Gracefully shutdown GitHub Spec-kit framework.
        
        Stops services and cleans up resources.
        """
        logger.info("Stopping GitHub Spec-kit framework",
                   extra={'run_id': self.run_id, 'event': 'framework_stop'})
        
        # TODO: Implement graceful shutdown
        # - Stop API/UI services
        # - Terminate framework processes
        # - Clean up temporary files (keep workspace)
        
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                self.process.kill()
                
        logger.info("GitHub Spec-kit framework stopped",
                   extra={'run_id': self.run_id, 'event': 'framework_stopped'})
