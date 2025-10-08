"""
Orchestrator runner for managing single framework executions.

Handles timeouts, retries, and full run lifecycle.
"""

import signal
import time
import os
from pathlib import Path
from typing import Dict, Any, Optional
import subprocess
from src.utils.logger import get_logger
from src.utils.isolation import create_isolated_workspace, cleanup_workspace
from src.utils.api_client import OpenAIAPIClient
from src.orchestrator.config_loader import load_config
from src.orchestrator.metrics_collector import MetricsCollector
from src.orchestrator.validator import Validator
from src.orchestrator.archiver import Archiver
from src.adapters.baes_adapter import BAeSAdapter

logger = get_logger(__name__)

# Constants
STEP_TIMEOUT = 600  # 10 minutes per step
SHUTDOWN_GRACE_PERIOD = 30  # seconds
MAX_RETRIES = 2
BACKOFF_MULTIPLIER = 2
INITIAL_BACKOFF = 5  # seconds


class StepTimeoutError(Exception):
    """Raised when a step execution times out."""


class OrchestratorRunner:
    """Manages the execution of a single framework run."""
    
    def __init__(self, framework_name: str, config_path: str = "config/experiment.yaml"):
        """
        Initialize orchestrator runner.
        
        Args:
            framework_name: Name of framework (baes, chatdev, ghspec)
            config_path: Path to experiment configuration
        """
        self.framework_name = framework_name
        self.config_path = config_path
        self.config = None
        self.adapter = None
        self.metrics_collector = None
        self.validator = None
        self.archiver = None
        self.workspace_path = None
        self.run_id = None
        self.step_timeout_occurred = False
        
    def _timeout_handler(self, _signum, _frame):
        """Signal handler for step timeout."""
        self.step_timeout_occurred = True
        logger.error("Step timeout occurred",
                    extra={'run_id': self.run_id, 'event': 'step_timeout'})
        raise StepTimeoutError("Step execution exceeded timeout")
        
    def _execute_step_with_timeout(self, step_num: int, command_text: str) -> Dict[str, Any]:
        """
        Execute a step with timeout enforcement.
        
        Args:
            step_num: Step number
            command_text: Command to execute
            
        Returns:
            Step execution results
            
        Raises:
            StepTimeoutError: If step exceeds timeout
        """
        # Set up timeout alarm
        signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(STEP_TIMEOUT)
        
        try:
            result = self.adapter.execute_step(step_num, command_text)
            signal.alarm(0)  # Cancel alarm
            return result
        except StepTimeoutError:
            # Attempt graceful shutdown
            logger.warning("Attempting graceful shutdown after timeout",
                          extra={'run_id': self.run_id})
            try:
                if self.adapter.process:
                    self.adapter.process.terminate()
                    time.sleep(SHUTDOWN_GRACE_PERIOD)
                    
                    # Force kill if still running
                    if self.adapter.process.poll() is None:
                        logger.warning("Force killing timed out process",
                                      extra={'run_id': self.run_id})
                        self.adapter.process.kill()
            except Exception as e:
                logger.error("Error during timeout cleanup",
                           extra={'run_id': self.run_id, 
                                 'metadata': {'error': str(e)}})
            raise
        finally:
            signal.alarm(0)  # Ensure alarm is cancelled
            
    def _execute_step_with_retry(self, step_num: int, command_text: str) -> Dict[str, Any]:
        """
        Execute a step with automatic retries.
        
        Args:
            step_num: Step number
            command_text: Command to execute
            
        Returns:
            Step execution results
            
        Raises:
            Exception: If all retries are exhausted
        """
        last_exception = None
        backoff = INITIAL_BACKOFF
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                if attempt > 0:
                    logger.info("Retrying step",
                               extra={'run_id': self.run_id, 'step': step_num,
                                     'metadata': {'attempt': attempt, 'backoff': backoff}})
                    time.sleep(backoff)
                    backoff *= BACKOFF_MULTIPLIER
                    
                result = self._execute_step_with_timeout(step_num, command_text)
                
                if attempt > 0:
                    logger.info("Step succeeded after retry",
                               extra={'run_id': self.run_id, 'step': step_num,
                                     'metadata': {'attempts': attempt + 1}})
                                     
                return result
                
            except Exception as e:
                last_exception = e
                logger.warning("Step failed",
                             extra={'run_id': self.run_id, 'step': step_num,
                                   'metadata': {'attempt': attempt + 1, 
                                              'error': str(e)}})
                
                if attempt == MAX_RETRIES:
                    logger.error("All retries exhausted",
                               extra={'run_id': self.run_id, 'step': step_num})
                    break
                    
        raise last_exception
        
    def execute_single_run(self) -> Dict[str, Any]:
        """
        Execute a complete framework run.
        
        Returns:
            Dictionary with run results and metadata
        """
        try:
            # Load configuration
            self.config = load_config(self.config_path)
            framework_config = self.config['frameworks'][self.framework_name]
            
            # Generate run ID and create isolated workspace
            from src.utils.isolation import generate_run_id
            self.run_id = generate_run_id()
            run_dir, workspace_dir = create_isolated_workspace(self.framework_name, self.run_id)
            self.workspace_path = str(workspace_dir)
            
            logger.info("Starting framework run",
                       extra={'run_id': self.run_id, 'framework': self.framework_name,
                             'event': 'run_start'})
            
            # Initialize components
            self.metrics_collector = MetricsCollector(self.run_id)
            self.validator = Validator(
                api_base_url=f"http://localhost:{framework_config['api_port']}",
                ui_base_url=f"http://localhost:{framework_config['ui_port']}",
                run_id=self.run_id
            )
            self.archiver = Archiver(
                run_id=self.run_id,
                run_dir=run_dir
            )
            
            # Initialize framework adapter
            if self.framework_name == 'baes':
                self.adapter = BAeSAdapter(framework_config, self.run_id, 
                                          self.workspace_path)
            else:
                raise ValueError(f"Unsupported framework: {self.framework_name}")
                
            # Start framework
            self.adapter.start()
            
            # Start metrics collection and downtime monitoring
            self.metrics_collector.start_run()
            self.validator.start_downtime_monitoring()
            
            # Execute 6 steps sequentially
            for step_num in range(1, 7):
                # Load step prompt
                prompt_path = Path(f"config/prompts/step_{step_num}.txt")
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    command_text = f.read().strip()
                    
                try:
                    # Execute step with timeout and retry
                    result = self._execute_step_with_retry(step_num, command_text)
                    
                    # Record metrics
                    self.metrics_collector.record_step(
                        step_num=step_num,
                        command=command_text,
                        duration_seconds=result.get('duration_seconds', 0),
                        success=result.get('success', True),
                        retry_count=result.get('retry_count', 0),
                        hitl_count=result.get('hitl_count', 0),
                        tokens_in=result.get('tokens_in', 0),
                        tokens_out=result.get('tokens_out', 0)
                    )
                    
                    logger.info("Step completed successfully",
                               extra={'run_id': self.run_id, 'step': step_num,
                                     'event': 'step_complete'})
                                     
                except Exception as e:
                    logger.error("Step failed permanently",
                               extra={'run_id': self.run_id, 'step': step_num,
                                     'metadata': {'error': str(e)}})
                    raise
                    
            # End metrics collection
            self.metrics_collector.end_run()
            
            # Stop downtime monitoring
            zdi = self.validator.stop_downtime_monitoring()
            
            # Run final validation
            logger.info("Running final validation",
                       extra={'run_id': self.run_id, 'event': 'validation_start'})
                       
            crude_score, esr = self.validator.test_crud_endpoints()
            mc = self.validator.compute_migration_continuity()
            
            # Compute all metrics
            metrics = self.metrics_collector.get_aggregate_metrics()
            
            # Add quality metrics
            quality_metrics = self.metrics_collector.compute_quality_metrics(
                crude_score=crude_score,
                esr=esr,
                mc=mc,
                zdi=zdi
            )
            metrics['aggregate_metrics'].update(quality_metrics)
            
            # Verify token counts with OpenAI API (T026)
            api_key_env = framework_config.get('api_key_env')
            if api_key_env and os.getenv(api_key_env):
                logger.info("Verifying token counts with OpenAI API",
                           extra={'run_id': self.run_id, 'event': 'usage_api_verification'})
                try:
                    api_client = OpenAIAPIClient(os.getenv(api_key_env))
                    usage_verification = api_client.verify_token_counts(
                        run_id=self.run_id,
                        local_tokens_in=metrics['aggregate_metrics'].get('TOK_IN', 0),
                        local_tokens_out=metrics['aggregate_metrics'].get('TOK_OUT', 0)
                    )
                    metrics['usage_api_verification'] = usage_verification
                    
                    if not usage_verification['verified']:
                        logger.warning("Token count verification failed",
                                     extra={'run_id': self.run_id,
                                           'metadata': {'error': usage_verification.get('error')}})
                except Exception as e:
                    logger.error("Usage API verification error",
                               extra={'run_id': self.run_id,
                                     'metadata': {'error': str(e)}})
                    metrics['usage_api_verification'] = {'verified': False, 'error': str(e)}
            else:
                logger.info("Skipping usage API verification (no API key)",
                           extra={'run_id': self.run_id})
                metrics['usage_api_verification'] = {'verified': False, 'error': 'No API key configured'}
            
            # Save metrics
            metrics_file = Path(run_dir) / "metrics.json"
            import json
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2)
                
            # Create archive
            logs_dir = Path(run_dir) / "logs"
            self.archiver.save_commit_info(framework_config['commit_hash'])
            archive_path = self.archiver.create_archive(
                workspace_dir=workspace_dir,
                metrics_file=metrics_file,
                logs={} if not logs_dir.exists() else {}
            )
            
            # Compute and save archive hash
            archive_hash = self.archiver.compute_hash(archive_path)
            self.archiver.create_metadata(
                archive_path=archive_path,
                hash_value=archive_hash,
                framework_name=self.framework_name,
                commit_hash=framework_config['commit_hash']
            )
            
            # Verify archive
            self.archiver.verify_archive(archive_path, archive_hash)
            
            logger.info("Run completed successfully",
                       extra={'run_id': self.run_id, 'event': 'run_complete'})
                       
            return {
                'status': 'success',
                'run_id': self.run_id,
                'metrics': metrics,
                'archive_path': archive_path
            }
            
        except StepTimeoutError:
            logger.error("Run failed due to timeout",
                        extra={'run_id': self.run_id, 'event': 'run_timeout'})
            return {
                'status': 'timeout_failure',
                'run_id': self.run_id,
                'error': 'Step execution timeout'
            }
            
        except Exception as e:
            logger.error("Run failed",
                        extra={'run_id': self.run_id, 'event': 'run_failed',
                              'metadata': {'error': str(e)}})
            return {
                'status': 'failed',
                'run_id': self.run_id,
                'error': str(e)
            }
            
        finally:
            # Cleanup
            if self.adapter:
                try:
                    self.adapter.stop()
                except Exception as e:
                    logger.warning("Error during adapter shutdown",
                                 extra={'run_id': self.run_id,
                                       'metadata': {'error': str(e)}})
