"""
BAEs framework adapter implementation.

Integrates with BAEs framework for experiment execution.
"""

import subprocess
import time
from pathlib import Path
from typing import Any, Dict
import requests
from src.adapters.base_adapter import BaseAdapter
from src.utils.logger import get_logger

logger = get_logger(__name__)


class BAeSAdapter(BaseAdapter):
    """Adapter for BAEs framework."""
    
    def __init__(self, config: Dict[str, Any], run_id: str, workspace_path: str):
        """
        Initialize BAEs adapter.
        
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
        Initialize BAEs framework environment.
        
        Clones repository, sets up environment, starts services.
        """
        logger.info("Starting BAEs framework",
                   extra={'run_id': self.run_id, 'event': 'framework_start'})
        
        # Clone repository
        repo_url = self.config['repo_url']
        commit_hash = self.config['commit_hash']
        self.framework_dir = Path(self.workspace_path) / "baes_framework"
        
        try:
            # Clone repository
            subprocess.run(
                ['git', 'clone', repo_url, str(self.framework_dir)],
                check=True,
                capture_output=True,
                timeout=300
            )
            
            # Checkout specific commit
            subprocess.run(
                ['git', 'checkout', commit_hash],
                cwd=self.framework_dir,
                check=True,
                capture_output=True,
                timeout=60
            )
            
            logger.info(f"BAEs repository cloned at commit {commit_hash}",
                       extra={'run_id': self.run_id})
            
            # TODO: Set up virtual environment and install dependencies
            # TODO: Start framework services (API, UI)
            # This will be framework-specific implementation
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone BAEs repository: {e}",
                        extra={'run_id': self.run_id})
            raise RuntimeError(f"BAEs initialization failed: {e}")
        except subprocess.TimeoutExpired:
            logger.error("Repository clone timed out",
                        extra={'run_id': self.run_id})
            raise RuntimeError("BAEs initialization timed out")
            
    def execute_step(self, step_num: int, command_text: str) -> Dict[str, Any]:
        """
        Execute a step by sending command to BAEs framework.
        
        Args:
            step_num: Step number (1-6)
            command_text: Natural language command
            
        Returns:
            Dictionary with execution results
        """
        self.current_step = step_num
        start_time = time.time()
        
        logger.info(f"Executing step {step_num}",
                   extra={'run_id': self.run_id, 'step': step_num, 
                         'event': 'step_start'})
        
        # TODO: Implement actual BAEs command execution
        # This is a placeholder implementation
        
        hitl_count = 0
        tokens_in = 0
        tokens_out = 0
        
        # Simulate step execution
        # In real implementation, this would:
        # 1. Send command to BAEs API
        # 2. Monitor for HITL requests
        # 3. Track token usage
        # 4. Wait for completion
        
        duration = time.time() - start_time
        
        return {
            'success': True,  # Placeholder
            'duration_seconds': duration,
            'hitl_count': hitl_count,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out
        }
        
    def health_check(self) -> bool:
        """
        Check if BAEs framework services are responding.
        
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
        except Exception:
            return False
            
    def handle_hitl(self, query: str) -> str:
        """
        Return fixed HITL response for deterministic execution.
        
        Args:
            query: Framework's clarification question
            
        Returns:
            Fixed clarification text
        """
        if self.hitl_text is None:
            # Load HITL text from config (should be done once)
            hitl_path = Path("config/hitl/expanded_spec.txt")
            with open(hitl_path, 'r') as f:
                self.hitl_text = f.read().strip()
                
        logger.info("HITL intervention",
                   extra={'run_id': self.run_id, 'step': self.current_step,
                         'event': 'hitl', 'metadata': {'query_length': len(query)}})
                         
        return self.hitl_text
        
    def stop(self) -> None:
        """
        Gracefully shutdown BAEs framework.
        
        Stops services and cleans up resources.
        """
        logger.info("Stopping BAEs framework",
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
                
        logger.info("BAEs framework stopped",
                   extra={'run_id': self.run_id, 'event': 'framework_stopped'})
