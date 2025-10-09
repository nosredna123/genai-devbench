"""
Usage API Reconciliation for token counts.

Updates metrics.json files with accurate token counts from OpenAI Usage API
after the API reporting delay (5-60 minutes).
"""

import json
import math
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from src.utils.logger import get_logger
from src.adapters.base_adapter import BaseAdapter

logger = get_logger(__name__)


class UsageReconciler:
    """
    Reconciles token counts from OpenAI Usage API.
    
    The OpenAI Usage API has a reporting delay of 5-60 minutes. This class
    updates metrics.json files after runs complete, once the API data is available.
    """
    
    def __init__(self, runs_dir: Path = Path("runs")):
        """
        Initialize usage reconciler.
        
        Args:
            runs_dir: Root directory containing framework run directories
        """
        self.runs_dir = runs_dir
        self.base_adapter = BaseAdapter(
            config={},
            run_id="reconciler",
            workspace_path="/tmp/reconciler"
        )
    
    def reconcile_run(
        self,
        run_id: str,
        framework: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Update a single run's metrics with Usage API data.
        
        Args:
            run_id: Run identifier
            framework: Framework name (baes, chatdev, ghspec)
            force: Force reconciliation even if already done
            
        Returns:
            Reconciliation report with updated counts
            
        Raises:
            FileNotFoundError: If metrics.json doesn't exist
            ValueError: If metrics format is invalid
        """
        # 1. Load existing metrics.json
        run_dir = self.runs_dir / framework / run_id
        metrics_file = run_dir / "metrics.json"
        
        if not metrics_file.exists():
            raise FileNotFoundError(f"Metrics file not found: {metrics_file}")
        
        with open(metrics_file, 'r', encoding='utf-8') as f:
            metrics = json.load(f)
        
        # Check if already reconciled
        if metrics.get('usage_api_reconciliation') and not force:
            logger.info(
                f"Run already reconciled: {framework}/{run_id}",
                extra={'run_id': run_id, 'framework': framework}
            )
            return {
                'run_id': run_id,
                'framework': framework,
                'status': 'already_reconciled',
                'reconciled_at': metrics['usage_api_reconciliation']['reconciled_at']
            }
        
        # 2. Prepare reconciliation report
        reconciliation_report = {
            'run_id': run_id,
            'framework': framework,
            'reconciled_at': datetime.now(timezone.utc).isoformat(),
            'steps_updated': [],
            'status': 'success'
        }
        
        # 3. Update each step with Usage API data
        steps_with_tokens = 0
        total_tokens_in = 0
        total_tokens_out = 0
        
        for step in metrics.get('steps', []):
            step_num = step['step_number']
            
            # Skip if already has significant tokens (unless force)
            if not force and (step.get('tokens_in', 0) > 0 or step.get('tokens_out', 0) > 0):
                logger.debug(
                    f"Step {step_num} already has tokens, skipping",
                    extra={'run_id': run_id, 'step': step_num}
                )
                total_tokens_in += step['tokens_in']
                total_tokens_out += step['tokens_out']
                continue
            
            # Get time window from step
            start_timestamp = step.get('start_timestamp')
            end_timestamp = step.get('end_timestamp')
            
            if not start_timestamp or not end_timestamp:
                logger.warning(
                    f"Step {step_num} missing timestamps, cannot reconcile",
                    extra={'run_id': run_id, 'step': step_num}
                )
                reconciliation_report['steps_updated'].append({
                    'step': step_num,
                    'status': 'missing_timestamps',
                    'tokens_in': 0,
                    'tokens_out': 0
                })
                continue
            
            # Query Usage API for this time window
            logger.info(
                f"Querying Usage API for step {step_num}",
                extra={
                    'run_id': run_id,
                    'step': step_num,
                    'metadata': {
                        'start_timestamp': start_timestamp,
                        'end_timestamp': end_timestamp,
                        'duration_seconds': end_timestamp - start_timestamp
                    }
                }
            )
            
            try:
                tokens_in, tokens_out = self.base_adapter.fetch_usage_from_openai(
                    api_key_env_var='OPEN_AI_KEY_ADM',
                    start_timestamp=start_timestamp,
                    end_timestamp=end_timestamp,
                    model=None  # Don't filter by model (unreliable)
                )
                
                # Update step
                step['tokens_in'] = tokens_in
                step['tokens_out'] = tokens_out
                
                total_tokens_in += tokens_in
                total_tokens_out += tokens_out
                
                if tokens_in > 0 or tokens_out > 0:
                    steps_with_tokens += 1
                
                reconciliation_report['steps_updated'].append({
                    'step': step_num,
                    'status': 'success',
                    'tokens_in': tokens_in,
                    'tokens_out': tokens_out
                })
                
                logger.info(
                    f"Step {step_num} updated: {tokens_in:,} input, {tokens_out:,} output tokens",
                    extra={'run_id': run_id, 'step': step_num}
                )
                
            except Exception as e:
                logger.error(
                    f"Failed to fetch usage for step {step_num}: {e}",
                    extra={'run_id': run_id, 'step': step_num, 'metadata': {'error': str(e)}}
                )
                reconciliation_report['steps_updated'].append({
                    'step': step_num,
                    'status': 'error',
                    'error': str(e),
                    'tokens_in': 0,
                    'tokens_out': 0
                })
        
        # 4. Recompute aggregate metrics
        metrics['aggregate_metrics']['TOK_IN'] = total_tokens_in
        metrics['aggregate_metrics']['TOK_OUT'] = total_tokens_out
        
        # Recompute AEI (Autonomy Efficiency Index)
        # AEI = AUTR / log(1 + TOK_IN)
        autr = metrics['aggregate_metrics'].get('AUTR', 0)
        aei = autr / math.log(1 + total_tokens_in) if total_tokens_in > 0 else 0.0
        metrics['aggregate_metrics']['AEI'] = aei
        
        # 5. Add reconciliation metadata
        reconciliation_report['total_tokens_in'] = total_tokens_in
        reconciliation_report['total_tokens_out'] = total_tokens_out
        reconciliation_report['steps_with_tokens'] = steps_with_tokens
        reconciliation_report['total_steps'] = len(metrics.get('steps', []))
        
        metrics['usage_api_reconciliation'] = reconciliation_report
        
        # 6. Save updated metrics
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(
            f"Reconciled {framework}/{run_id}: {total_tokens_in:,} input, {total_tokens_out:,} output tokens",
            extra={
                'run_id': run_id,
                'framework': framework,
                'event': 'reconciliation_complete',
                'metadata': {
                    'total_tokens_in': total_tokens_in,
                    'total_tokens_out': total_tokens_out,
                    'steps_with_tokens': steps_with_tokens,
                    'total_steps': len(metrics.get('steps', []))
                }
            }
        )
        
        return reconciliation_report
    
    def reconcile_all_pending(
        self,
        framework: Optional[str] = None,
        min_age_minutes: int = 30,
        max_age_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Find and reconcile all runs with missing token data.
        
        Args:
            framework: Specific framework to reconcile (None = all frameworks)
            min_age_minutes: Only reconcile runs older than this (wait for Usage API delay)
            max_age_hours: Don't reconcile runs older than this (likely won't get data)
            
        Returns:
            List of reconciliation reports
        """
        results = []
        current_time = time.time()
        min_cutoff = current_time - (min_age_minutes * 60)
        max_cutoff = current_time - (max_age_hours * 3600)
        
        logger.info(
            f"Scanning for pending reconciliations",
            extra={
                'metadata': {
                    'framework_filter': framework or 'all',
                    'min_age_minutes': min_age_minutes,
                    'max_age_hours': max_age_hours
                }
            }
        )
        
        if not self.runs_dir.exists():
            logger.warning(f"Runs directory not found: {self.runs_dir}")
            return results
        
        # Iterate through framework directories
        for framework_dir in self.runs_dir.iterdir():
            if not framework_dir.is_dir():
                continue
            
            framework_name = framework_dir.name
            
            # Apply framework filter
            if framework and framework_name != framework:
                continue
            
            logger.debug(f"Scanning framework: {framework_name}")
            
            # Iterate through run directories
            for run_dir in framework_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                
                run_id = run_dir.name
                metrics_file = run_dir / "metrics.json"
                
                if not metrics_file.exists():
                    logger.debug(f"Metrics file not found: {framework_name}/{run_id}")
                    continue
                
                # Check file age
                file_mtime = metrics_file.stat().st_mtime
                
                if file_mtime > min_cutoff:
                    logger.debug(
                        f"Run too recent: {framework_name}/{run_id} "
                        f"({(current_time - file_mtime) / 60:.1f} minutes old)"
                    )
                    continue
                
                if file_mtime < max_cutoff:
                    logger.debug(
                        f"Run too old: {framework_name}/{run_id} "
                        f"({(current_time - file_mtime) / 3600:.1f} hours old)"
                    )
                    continue
                
                # Check if already reconciled or has token data
                try:
                    with open(metrics_file, 'r', encoding='utf-8') as f:
                        metrics = json.load(f)
                    
                    # Skip if already reconciled
                    if metrics.get('usage_api_reconciliation'):
                        logger.debug(f"Already reconciled: {framework_name}/{run_id}")
                        continue
                    
                    # Check if has token data
                    total_tokens = metrics.get('aggregate_metrics', {}).get('TOK_IN', 0)
                    if total_tokens > 0:
                        logger.debug(f"Already has tokens: {framework_name}/{run_id}")
                        continue
                    
                    # This run needs reconciliation!
                    logger.info(f"Reconciling: {framework_name}/{run_id}")
                    
                    report = self.reconcile_run(run_id, framework_name)
                    results.append(report)
                    
                except Exception as e:
                    logger.error(
                        f"Failed to reconcile {framework_name}/{run_id}: {e}",
                        extra={
                            'framework': framework_name,
                            'run_id': run_id,
                            'metadata': {'error': str(e)}
                        }
                    )
                    results.append({
                        'run_id': run_id,
                        'framework': framework_name,
                        'status': 'error',
                        'error': str(e)
                    })
        
        logger.info(
            f"Reconciliation scan complete: {len(results)} runs processed",
            extra={'metadata': {'runs_reconciled': len(results)}}
        )
        
        return results
    
    def get_pending_runs(
        self,
        framework: Optional[str] = None,
        min_age_minutes: int = 30
    ) -> List[Dict[str, Any]]:
        """
        List all runs that need reconciliation (without reconciling them).
        
        Args:
            framework: Specific framework to check (None = all frameworks)
            min_age_minutes: Only list runs older than this
            
        Returns:
            List of pending runs with metadata
        """
        pending = []
        current_time = time.time()
        min_cutoff = current_time - (min_age_minutes * 60)
        
        if not self.runs_dir.exists():
            return pending
        
        for framework_dir in self.runs_dir.iterdir():
            if not framework_dir.is_dir():
                continue
            
            framework_name = framework_dir.name
            
            if framework and framework_name != framework:
                continue
            
            for run_dir in framework_dir.iterdir():
                if not run_dir.is_dir():
                    continue
                
                run_id = run_dir.name
                metrics_file = run_dir / "metrics.json"
                
                if not metrics_file.exists():
                    continue
                
                file_mtime = metrics_file.stat().st_mtime
                
                if file_mtime > min_cutoff:
                    continue
                
                try:
                    with open(metrics_file, 'r', encoding='utf-8') as f:
                        metrics = json.load(f)
                    
                    if metrics.get('usage_api_reconciliation'):
                        continue
                    
                    total_tokens = metrics.get('aggregate_metrics', {}).get('TOK_IN', 0)
                    if total_tokens > 0:
                        continue
                    
                    age_minutes = (current_time - file_mtime) / 60
                    
                    pending.append({
                        'run_id': run_id,
                        'framework': framework_name,
                        'age_minutes': age_minutes,
                        'metrics_file': str(metrics_file),
                        'end_timestamp': metrics.get('end_timestamp')
                    })
                    
                except Exception as e:
                    logger.warning(f"Error checking {framework_name}/{run_id}: {e}")
        
        return pending
