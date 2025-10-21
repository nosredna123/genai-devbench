"""
Orchestrator runner for managing single and multi-framework executions.

Handles timeouts, retries, and full run lifecycle with per-run, per-step logging.
"""

import signal
import time
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import subprocess
from src.utils.logger import get_logger, LogContext
from src.utils.log_summary import LogSummarizer
from src.utils.isolation import create_isolated_workspace, cleanup_workspace
from src.utils.api_client import OpenAIAPIClient
from src.orchestrator.config_loader import load_config, set_deterministic_seeds
from src.orchestrator.metrics_collector import MetricsCollector
from src.orchestrator.validator import Validator
from src.orchestrator.archiver import Archiver
from src.adapters.baes_adapter import BAeSAdapter
from src.adapters.chatdev_adapter import ChatDevAdapter
from src.adapters.ghspec_adapter import GHSpecAdapter
from src.analysis.stopping_rule import check_convergence, get_convergence_summary

logger = get_logger(__name__, component="orchestrator")

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
    
    def __init__(
        self,
        framework_name: str,
        config_path: str = "config/experiment.yaml",
        experiment_name: Optional[str] = None,
        run_id: Optional[str] = None
    ):
        """
        Initialize orchestrator runner.
        
        Args:
            framework_name: Name of framework (baes, chatdev, ghspec)
            config_path: Path to experiment configuration
            experiment_name: Name of experiment (optional, for multi-experiment support)
            run_id: Pre-generated run ID (optional, will generate if not provided)
        """
        self.framework_name = framework_name
        self.config_path = config_path
        self.experiment_name = experiment_name
        self.config = None
        self.adapter = None
        self.metrics_collector = None
        self.validator = None
        self.archiver = None
        self.workspace_path = None
        self.run_id = run_id  # Use provided run_id or generate later
        self.step_timeout_occurred = False
        self.hitl_log_path = None
        
    def _log_hitl_event(
        self,
        step_num: int,
        query: str,
        response: str,
        timestamp: Optional[str] = None
    ) -> None:
        """
        Log HITL event with SHA-1 hash for reproducibility verification.
        
        Appends to hitl_events.jsonl in the run directory.
        
        Args:
            step_num: Current step number
            query: Framework's clarification question
            response: Fixed response text provided
            timestamp: ISO 8601 timestamp (uses current time if None)
        """
        if not self.hitl_log_path:
            return
        
        if timestamp is None:
            timestamp = datetime.utcnow().isoformat() + 'Z'
        
        # Compute SHA-1 hash of response text
        response_hash = hashlib.sha1(response.encode('utf-8')).hexdigest()
        
        event = {
            'timestamp': timestamp,
            'run_id': self.run_id,
            'step': step_num,
            'query': query,
            'response': response,
            'response_sha1': response_hash,
            'query_length': len(query),
            'response_length': len(response)
        }
        
        # Append to JSONL file
        with open(self.hitl_log_path, 'a', encoding='utf-8') as f:
            f.write(json.dumps(event) + '\n')
        
        logger.info(
            "HITL event logged",
            extra={
                'run_id': self.run_id,
                'step': step_num,
                'metadata': {
                    'response_hash': response_hash,
                    'query_length': len(query)
                }
            }
        )
        
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
            
            # Set deterministic seeds for reproducibility (T037)
            set_deterministic_seeds(self.config['random_seed'])
            
            # Generate run ID if not provided, and create isolated workspace
            from src.utils.isolation import generate_run_id
            if self.run_id is None:
                self.run_id = generate_run_id()
            run_dir, workspace_dir = create_isolated_workspace(
                self.framework_name,
                self.run_id,
                self.experiment_name
            )
            self.workspace_path = str(workspace_dir)
            
            # Initialize logging context for per-run, per-step logging
            logs_dir = run_dir / "logs"
            log_context = LogContext.get_instance()
            log_context.set_run_context(
                run_id=self.run_id,
                framework=self.framework_name,
                logs_dir=logs_dir
            )
            
            # Initialize HITL event log (T039)
            self.hitl_log_path = run_dir / "hitl_events.jsonl"
            
            # Track run start time for summary
            run_start_time = datetime.utcnow()
            
            logger.info("Starting framework run",
                       extra={'run_id': self.run_id, 'framework': self.framework_name,
                             'event': 'run_start'})
            
            # Initialize components
            self.metrics_collector = MetricsCollector(self.run_id, model=self.config['model'])
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
            # Get framework configuration and add global model config
            framework_config = self.config['frameworks'][self.framework_name]
            framework_config['model'] = self.config.get('model')  # Add global model to framework config
            
            # Initialize appropriate adapter based on framework
            if self.framework_name == 'baes':
                self.adapter = BAeSAdapter(framework_config, self.run_id, 
                                          self.workspace_path)
            elif self.framework_name == 'chatdev':
                self.adapter = ChatDevAdapter(framework_config, self.run_id,
                                             self.workspace_path)
            elif self.framework_name == 'ghspec':
                self.adapter = GHSpecAdapter(framework_config, self.run_id,
                                            self.workspace_path)
            else:
                raise ValueError(f"Unsupported framework: {self.framework_name}")
                
            # Start framework
            self.adapter.start()
            
            # Start metrics collection and downtime monitoring
            self.metrics_collector.start_run()
            self.validator.start_downtime_monitoring()
            
            # Track step summaries for log summary
            step_summaries = []
            errors_and_warnings = []
            
            # Execute 6 steps sequentially
            # TODO: #3 The number of steps must be loaded from config
            for step_num in range(1, 7):
                # Set logging context for this step
                log_context.set_step_context(step_num)
                
                # Load step prompt
                prompt_path = Path(f"config/prompts/step_{step_num}.txt")
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    command_text = f.read().strip()
                    
                step_start_time = datetime.utcnow()
                step_status = "success"
                step_error = None
                retries = 0
                
                try:
                    # Execute step with timeout and retry
                    result = self._execute_step_with_retry(step_num, command_text)
                    retries = result.get('retry_count', 0)
                    
                    # Record metrics
                    self.metrics_collector.record_step(
                        step_num=step_num,
                        command=command_text,
                        duration_seconds=result.get('duration_seconds', 0),
                        success=result.get('success', True),
                        retry_count=retries,
                        hitl_count=result.get('hitl_count', 0),
                        tokens_in=result.get('tokens_in', 0),
                        tokens_out=result.get('tokens_out', 0),
                        api_calls=result.get('api_calls', 0),
                        cached_tokens=result.get('cached_tokens', 0),
                        start_timestamp=result.get('start_timestamp'),
                        end_timestamp=result.get('end_timestamp')
                    )
                    
                    logger.info("Step completed successfully",
                               extra={'run_id': self.run_id, 'step': step_num,
                                     'event': 'step_complete'})
                    
                    # Add a sleep time between steps to avoid overlap usage data
                    time.sleep(1)
                                     
                except StepTimeoutError as e:
                    step_status = "timeout"
                    step_error = str(e)
                    errors_and_warnings.append({
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'level': 'TIMEOUT',
                        'message': f"Step {step_num}: {step_error}"
                    })
                    logger.error("Step timed out",
                               extra={'run_id': self.run_id, 'step': step_num,
                                     'metadata': {'error': step_error}})
                    raise
                except Exception as e:
                    step_status = "error"
                    step_error = str(e)
                    errors_and_warnings.append({
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'level': 'ERROR',
                        'message': f"Step {step_num}: {step_error}"
                    })
                    logger.error("Step failed permanently",
                               extra={'run_id': self.run_id, 'step': step_num,
                                     'metadata': {'error': step_error}})
                    raise
                finally:
                    # Calculate step duration
                    step_end_time = datetime.utcnow()
                    step_duration = (step_end_time - step_start_time).total_seconds()
                    
                    # Build step summary
                    step_summary = {
                        'step_num': step_num,
                        'status': step_status,
                        'duration_seconds': step_duration,
                        'retries': retries,
                        'api_calls': result.get('api_calls', 0) if 'result' in locals() else 0,
                        'tokens': {
                            'prompt': result.get('tokens_in', 0) if 'result' in locals() else 0,
                            'completion': result.get('tokens_out', 0) if 'result' in locals() else 0,
                            'total': (result.get('tokens_in', 0) + result.get('tokens_out', 0)) if 'result' in locals() else 0
                        },
                        'llm_requests': result.get('api_calls', 0) if 'result' in locals() else 0,
                    }
                    
                    if step_error:
                        step_summary['error'] = step_error
                    
                    # Add note for zero-token steps (template-based)
                    if step_summary['tokens']['total'] == 0 and step_status == "success":
                        step_summary['note'] = "Template-based generation (no LLM calls)"
                    
                    step_summaries.append(step_summary)
                    
                    # Clear step context
                    log_context.clear_step_context()
                    
            # End metrics collection
            self.metrics_collector.end_run()
            
            # Stop downtime monitoring
            zdi = self.validator.stop_downtime_monitoring()
            
            # Run final validation
            logger.info("Running final validation",
                       extra={'run_id': self.run_id, 'event': 'validation_start'})
                       
            crude_score, esr = self.validator.test_crud_endpoints()
            mc = self.validator.compute_migration_continuity()
            
            # Compute all metrics (including quality metrics)
            metrics = self.metrics_collector.get_aggregate_metrics(
                crude_score=crude_score,
                esr=esr,
                mc=mc,
                zdi=zdi
            )
            
            # LAZY EVALUATION: Skip Usage API verification during execution
            # Token metrics are 0 initially and will be backfilled by reconciliation script
            # Set verification_status to 'pending' to indicate reconciliation is needed
            logger.info("Skipping Usage API verification (lazy evaluation - reconciliation required)",
                       extra={'run_id': self.run_id, 'event': 'lazy_evaluation'})
            metrics['usage_api_verification'] = {
                'verified': False, 
                'error': 'Lazy evaluation - metrics will be backfilled by reconciliation script'
            }
            metrics['verification_status'] = 'pending'
            
            # Save metrics
            metrics_file = Path(run_dir) / "metrics.json"
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(metrics, f, indent=2)
            
            # Update manifest with run information
            from src.orchestrator.manifest_manager import update_manifest
            run_data = {
                'run_id': self.run_id,
                'framework': self.framework_name,
                'start_time': metrics.get('start_timestamp'),
                'end_time': metrics.get('end_timestamp'),
                'verification_status': metrics.get('verification_status', 'pending'),
                'total_tokens_in': metrics['aggregate_metrics'].get('TOK_IN', 0),
                'total_tokens_out': metrics['aggregate_metrics'].get('TOK_OUT', 0)
            }
            update_manifest(run_data, self.experiment_name)
            logger.info("Updated runs manifest",
                       extra={'run_id': self.run_id, 'event': 'manifest_updated'})
            
            # Load HITL events if they exist
            hitl_events = []
            if self.hitl_log_path and self.hitl_log_path.exists():
                with open(self.hitl_log_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            hitl_events.append(json.loads(line.strip()))
                        except json.JSONDecodeError:
                            pass
            
            # Track run end time for summary
            run_end_time = datetime.utcnow()
                
            # Create archive (including logs directory)
            logs_dir = Path(run_dir) / "logs"
            self.archiver.save_commit_info(framework_config['commit_hash'])
            archive_path = self.archiver.create_archive(
                workspace_dir=workspace_dir,
                metrics_file=metrics_file,
                logs={'logs': logs_dir} if logs_dir.exists() else {}
            )
            
            # Compute and save archive hash
            archive_hash = self.archiver.compute_hash(archive_path)
            archive_size = archive_path.stat().st_size if archive_path.exists() else 0
            
            self.archiver.create_metadata(
                archive_path=archive_path,
                archive_hash=archive_hash,
                framework=self.framework_name,
                commit_hash=framework_config['commit_hash']
            )
            
            # Generate log summary for git tracking
            summarizer = LogSummarizer(
                run_id=self.run_id,
                framework=self.framework_name,
                run_dir=run_dir
            )
            
            summary_config = {
                'model': self.config.get('model'),
                'step_timeout': STEP_TIMEOUT,
                'max_retries': MAX_RETRIES,
                'random_seed': self.config.get('random_seed')
            }
            
            archive_info = {
                'filename': archive_path.name,
                'hash': archive_hash,
                'size': archive_size,
                'contents': 'workspace/ + logs/ + metrics.json + artifacts/'
            }
            
            summary_text = summarizer.generate_summary(
                config=summary_config,
                start_time=run_start_time,
                end_time=run_end_time,
                steps=step_summaries,
                reconciliation=None,  # Will be filled by reconciliation script
                errors=errors_and_warnings,
                hitl_events=hitl_events,
                archive_info=archive_info
            )
            
            summary_path = summarizer.write_summary(summary_text)
            logger.info("Generated log summary",
                       extra={'run_id': self.run_id, 'event': 'summary_generated',
                             'metadata': {'path': str(summary_path)}})
            
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
            import traceback
            tb_str = traceback.format_exc()
            logger.error("Run failed",
                        extra={'run_id': self.run_id, 'event': 'run_failed',
                              'metadata': {'error': str(e), 'traceback': tb_str}})
            # Also print to console for debugging
            print(f"\n{'='*60}\nFULL TRACEBACK:\n{tb_str}{'='*60}\n", flush=True)
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
    
    def execute_multi_framework(
        self,
        frameworks: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Execute experiments across multiple frameworks with stopping rule.
        
        Runs each framework until convergence is achieved (5-25 runs per framework).
        Uses bootstrap confidence intervals to determine convergence.
        
        Args:
            frameworks: List of framework names to execute. 
                       If None, executes all frameworks from config.
        
        Returns:
            Dictionary with results for all frameworks:
            {
                'frameworks': {
                    'baes': {
                        'runs': [list of run results],
                        'convergence': convergence result dict,
                        'aggregate_metrics': aggregate statistics
                    },
                    ...
                },
                'summary': {
                    'total_runs': int,
                    'successful_runs': int,
                    'failed_runs': int
                }
            }
        """
        # Load config if not already loaded
        if not self.config:
            self.config = load_config(self.config_path)
        
        # Determine frameworks to execute
        if frameworks is None:
            frameworks = list(self.config['frameworks'].keys())
        
        logger.info("Starting multi-framework experiment",
                   extra={'metadata': {'frameworks': frameworks}})
        
        all_results = {}
        total_runs = 0
        successful_runs = 0
        failed_runs = 0
        
        for framework in frameworks:
            logger.info(f"Starting experiments for framework: {framework}",
                       extra={'metadata': {'framework': framework}})
            
            framework_runs = []
            framework_metrics = []
            run_count = 0
            
            # Execute runs until stopping rule satisfied
            # TODO: #2 review MAX_RUNS and MIN_RUNS rules
            while run_count < 25:  # MAX_RUNS
                run_count += 1
                total_runs += 1
                
                logger.info(f"Executing run {run_count} for {framework}",
                           extra={'metadata': {'framework': framework, 'run': run_count}})
                
                # Create new runner for this run
                runner = OrchestratorRunner(framework, self.config_path)
                result = runner.execute_single_run()
                
                framework_runs.append(result)
                
                if result['status'] == 'success':
                    successful_runs += 1
                    # Extract aggregate metrics for convergence check
                    metrics = result['metrics']['aggregate_metrics']
                    framework_metrics.append(metrics)
                else:
                    failed_runs += 1
                    logger.warning(f"Run {run_count} failed for {framework}",
                                 extra={'metadata': {
                                     'framework': framework,
                                     'error': result.get('error')
                                 }})
                
                # Check stopping rule (only if we have enough successful runs)
                if len(framework_metrics) >= 5:  # MIN_RUNS
                    convergence = check_convergence(
                        framework_metrics,
                        framework
                    )
                    
                    logger.info(f"Convergence check for {framework}",
                               extra={'metadata': {
                                   'framework': framework,
                                   'runs': len(framework_metrics),
                                   'should_stop': convergence['should_stop']
                               }})
                    
                    if convergence['should_stop']:
                        logger.info(f"Stopping rule satisfied for {framework}",
                                   extra={'metadata': {
                                       'framework': framework,
                                       'runs': len(framework_metrics),
                                       'reason': convergence['reason']
                                   }})
                        
                        print(f"\n{framework.upper()} Convergence:")
                        print(get_convergence_summary(convergence))
                        break
            
            # Compute aggregate statistics for this framework
            from src.analysis.report_generator import bootstrap_aggregate_metrics
            aggregate_stats = bootstrap_aggregate_metrics(framework_metrics)
            
            all_results[framework] = {
                'runs': framework_runs,
                'convergence': convergence if len(framework_metrics) >= 5 else None,
                'aggregate_metrics': aggregate_stats,
                'n_successful': len(framework_metrics),
                'n_failed': run_count - len(framework_metrics)
            }
            
            logger.info(f"Completed all runs for {framework}",
                       extra={'metadata': {
                           'framework': framework,
                           'successful': len(framework_metrics),
                           'failed': run_count - len(framework_metrics)
                       }})
        
        # Save multi-framework results
        results_path = Path("runs/multi_framework_results.json")
        results_path.parent.mkdir(parents=True, exist_ok=True)
        
        final_results = {
            'frameworks': all_results,
            'summary': {
                'total_runs': total_runs,
                'successful_runs': successful_runs,
                'failed_runs': failed_runs,
                'frameworks_tested': len(frameworks)
            }
        }
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(final_results, f, indent=2)
        
        logger.info("Multi-framework experiment completed",
                   extra={'metadata': {
                       'total_runs': total_runs,
                       'successful': successful_runs,
                       'failed': failed_runs
                   }})
        
        return final_results
