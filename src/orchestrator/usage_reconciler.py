"""
Usage API Reconciliation for token counts.

Updates metrics.json files with accurate token counts from OpenAI Usage API
after the API reporting delay (5-60 minutes).

Supports double-check verification to ensure data stability.
"""

import json
import math
import time
import os
import subprocess
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from src.utils.logger import get_logger
from src.orchestrator.manifest_manager import find_runs

logger = get_logger(__name__, component="reconciliation")

# Minimum wait time (in minutes) before attempting reconciliation:
# - Minimum age of runs before first reconciliation attempt
# - Minimum interval between subsequent verification attempts
# Set to 0 for testing/development (immediate reconciliation)
# Set to 30+ for production (typical OpenAI Usage API delay is 5-60 minutes)
DEFAULT_VERIFICATION_INTERVAL_MIN = int(os.getenv('RECONCILIATION_VERIFICATION_INTERVAL_MIN', '0'))

# Minimum number of consecutive stable verifications required
# Default: 2 (double-check verification)
DEFAULT_MIN_STABLE_VERIFICATIONS = int(os.getenv('RECONCILIATION_MIN_STABLE_VERIFICATIONS', '2'))


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
    
    def _fetch_usage_from_openai(
        self,
        start_timestamp: int,
        end_timestamp: int,
        framework: Optional[str] = None
    ) -> tuple[int, int, int, int]:
        """
        Fetch usage data from OpenAI Usage API with minute-level granularity.
        
        BREAKING CHANGE (v2.0.0): Uses bucket_width="1m" for minute-level buckets
        instead of "1d" daily buckets. This eliminates the zero-token bug caused
        by all sprints on the same day seeing identical daily totals.
        
        API KEY FILTERING (v2.0.0): When framework is specified, filters results
        by framework-specific API key ID to prevent cross-contamination when
        multiple frameworks run simultaneously.
        
        Uses OPEN_AI_KEY_ADM (which has api.usage.read permission) to query the Usage API.
        Attribution to specific frameworks is achieved through api_key_ids filtering.
        
        Args:
            start_timestamp: Unix timestamp for start of window
            end_timestamp: Unix timestamp for end of window
            framework: Framework name (baes, chatdev, ghspec) - required for filtering
            
        Returns:
            Tuple of (input_tokens, output_tokens, api_calls, cached_tokens)
            
        Raises:
            KeyError: If framework specified but OPENAI_API_KEY_{FRAMEWORK}_ID not found
            
        Note:
            - bucket_width="1m" provides minute-level granularity (finest available)
            - limit=1440 allows up to 24 hours of minute buckets per query
            - Tokens are attributed by completion time (not request time)
            - api_key_ids parameter filters to framework-specific usage
        """
        # Use OPEN_AI_KEY_ADM for authorization (it has api.usage.read permission)
        # Framework-specific keys (OPENAI_API_KEY_{FRAMEWORK}) are used during generation,
        # but the admin key is needed to QUERY usage data
        api_key = os.getenv('OPEN_AI_KEY_ADM')
        if not api_key:
            logger.warning("OPEN_AI_KEY_ADM not found in environment")
            return 0, 0, 0, 0
        
        # Get framework-specific API key ID for filtering (FR-010)
        # This prevents cross-contamination when multiple frameworks run simultaneously
        if framework:
            framework_upper = framework.upper()
            api_key_id = os.getenv(f'OPENAI_API_KEY_{framework_upper}_ID')
            if not api_key_id:
                raise KeyError(
                    f"OPENAI_API_KEY_{framework_upper}_ID environment variable required for "
                    f"Usage API filtering. Find your API key ID in OpenAI Dashboard > Usage > API Keys."
                )
        else:
            # Legacy path (no framework specified) - no filtering
            api_key_id = None
        
        url = "https://api.openai.com/v1/organization/usage/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        # Convert to integer timestamps (seconds only, no microseconds)
        # OpenAI Usage API requires integer Unix timestamps
        params = {
            "start_time": int(start_timestamp),
            "end_time": int(end_timestamp),
            "bucket_width": "1m",  # Changed from "1d" - minute-level granularity (FR-005)
            "limit": 1440  # 24 hours of minute buckets (max for 1m bucket_width)
        }
        
        # Add API key filtering if framework specified (FR-010)
        if api_key_id:
            params["api_key_ids"] = [api_key_id]
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            # Check for permission errors
            if response.status_code == 401:
                error_data = response.json()
                if "api.usage.read" in error_data.get("error", {}).get("message", ""):
                    logger.error("API key lacks 'api.usage.read' scope")
                    return 0, 0, 0, 0
            
            response.raise_for_status()
            usage_data = response.json()
            
            # Aggregate tokens from all buckets. The Usage API (Oct 2025) returns
            # input_tokens/output_tokens, but we fall back to legacy field names
            # to remain compatible with earlier API responses.
            def _extract_tokens(result: Dict[str, Any]) -> tuple[int, int, int, int]:
                input_fields = (
                    "input_tokens",
                    "n_context_tokens_total",
                    "n_input_tokens_total",
                    "n_context_tokens",
                )
                output_fields = (
                    "output_tokens",
                    "n_generated_tokens_total",
                    "n_output_tokens_total",
                    "n_generated_tokens",
                )
                tokens_in = next((int(result.get(field, 0) or 0) for field in input_fields if field in result), 0)
                tokens_out = next((int(result.get(field, 0) or 0) for field in output_fields if field in result), 0)
                num_requests = int(result.get("num_model_requests", 0) or 0)
                cached_tokens = int(result.get("input_cached_tokens", 0) or 0)
                return tokens_in, tokens_out, num_requests, cached_tokens

            total_input_tokens = 0
            total_output_tokens = 0
            total_api_calls = 0
            total_cached_tokens = 0
            
            for bucket in usage_data.get("data", []):
                for result in bucket.get("results", []):
                    tokens_in, tokens_out, api_calls, cached_tokens = _extract_tokens(result)
                    total_input_tokens += tokens_in
                    total_output_tokens += tokens_out
                    total_api_calls += api_calls
                    total_cached_tokens += cached_tokens
            
            return total_input_tokens, total_output_tokens, total_api_calls, total_cached_tokens
            
        except Exception as e:
            logger.error(f"Failed to fetch usage from OpenAI API: {e}")
            return 0, 0, 0, 0
    
    def reconcile_run(
        self,
        run_id: str,
        framework: str,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Update a single run's metrics with Usage API data.
        
        Implements double-check verification: data is marked as "verified" 
        only when two consecutive reconciliation attempts return identical 
        token counts with at least VERIFICATION_INTERVAL_MIN minutes between them.
        
        Args:
            run_id: Run identifier
            framework: Framework name (baes, chatdev, ghspec)
            force: Force reconciliation even if already verified
            
        Returns:
            Reconciliation report with updated counts and verification status
            
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
        
        # Check if already verified (not just reconciled)
        reconciliation = metrics.get('usage_api_reconciliation', {})
        verification_status = reconciliation.get('verification_status', 'pending')
        
        if verification_status == 'verified' and not force:
            logger.info(
                f"Run already verified: {framework}/{run_id}",
                extra={'run_id': run_id, 'framework': framework}
            )
            return {
                'run_id': run_id,
                'framework': framework,
                'status': 'already_verified',
                'verified_at': reconciliation.get('verified_at')
            }
        
        # 2. Query Usage API for run-level token counts (BREAKING CHANGE v2.0.0)
        # Changed from per-step reconciliation to per-run reconciliation
        # This eliminates the 36-50% zero-token error caused by bucket misalignment
        
        # Get run time window from metrics
        start_timestamp = None
        end_timestamp = None
        
        # Try to get from steps (use earliest start and latest end)
        if metrics.get('steps'):
            timestamps = [
                (step.get('start_timestamp'), step.get('end_timestamp'))
                for step in metrics['steps']
                if step.get('start_timestamp') and step.get('end_timestamp')
            ]
            if timestamps:
                start_timestamp = min(t[0] for t in timestamps)
                end_timestamp = max(t[1] for t in timestamps)
        
        # Fallback to aggregate metrics timestamps
        if not start_timestamp:
            start_ts_str = metrics.get('start_timestamp')
            end_ts_str = metrics.get('end_timestamp')
            if start_ts_str and end_ts_str:
                from dateutil import parser
                start_timestamp = int(parser.parse(start_ts_str).timestamp())
                end_timestamp = int(parser.parse(end_ts_str).timestamp())
        
        if not start_timestamp or not end_timestamp:
            raise ValueError(f"Cannot determine run time window for {framework}/{run_id}")
        
        # Extend query window by 5 minutes on each end (FR-013)
        # This accounts for OpenAI Usage API's async processing delay
        BUFFER_SECONDS = 300  # 5 minutes
        query_start = start_timestamp - BUFFER_SECONDS
        query_end = end_timestamp + BUFFER_SECONDS
        
        # Query Usage API once for entire run
        tokens_in, tokens_out, api_calls, cached_tokens = self._fetch_usage_from_openai(
            start_timestamp=query_start,
            end_timestamp=query_end,
            framework=framework
        )
        
        # Create current attempt record
        current_attempt = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'total_tokens_in': tokens_in,
            'total_tokens_out': tokens_out,
            'total_api_calls': api_calls,
            'total_cached_tokens': cached_tokens,
            'query_window': {
                'start': query_start,
                'end': query_end,
                'buffer_seconds': BUFFER_SECONDS
            }
        }
        
        # 3. Check verification status against previous attempts
        verification_result = self._check_verification_status(
            metrics, 
            current_attempt,
            framework,
            run_id
        )
        
        # 4. Update reconciliation data structure
        if 'usage_api_reconciliation' not in metrics:
            metrics['usage_api_reconciliation'] = {
                'verification_status': 'pending',
                'attempts': []
            }
        
        # Store this attempt
        metrics['usage_api_reconciliation']['attempts'].append(current_attempt)
        metrics['usage_api_reconciliation']['verification_status'] = verification_result['status']
        metrics['usage_api_reconciliation']['verification_message'] = verification_result['message']
        
        if verification_result['status'] == 'verified':
            metrics['usage_api_reconciliation']['verified_at'] = current_attempt['timestamp']
        
        # 5. Update aggregate metrics
        total_tokens_in = current_attempt['total_tokens_in']
        total_tokens_out = current_attempt['total_tokens_out']
        total_api_calls = current_attempt.get('total_api_calls', 0)
        total_cached_tokens = current_attempt.get('total_cached_tokens', 0)
        
        metrics['aggregate_metrics']['TOK_IN'] = total_tokens_in
        metrics['aggregate_metrics']['TOK_OUT'] = total_tokens_out
        metrics['aggregate_metrics']['API_CALLS'] = total_api_calls
        metrics['aggregate_metrics']['CACHED_TOKENS'] = total_cached_tokens
        
        # Recompute AEI (Autonomy Efficiency Index)
        autr = metrics['aggregate_metrics'].get('AUTR', 0)
        aei = autr / math.log(1 + total_tokens_in) if total_tokens_in > 0 else 0.0
        metrics['aggregate_metrics']['AEI'] = aei
        
        # 6. Save updated metrics
        with open(metrics_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        
        # 7. Update manifest with latest verification status
        from src.orchestrator.manifest_manager import update_manifest
        run_data = {
            'run_id': run_id,
            'framework': framework,
            'start_time': metrics.get('start_timestamp'),
            'end_time': metrics.get('end_timestamp'),
            'verification_status': verification_result['status'],
            'total_tokens_in': total_tokens_in,
            'total_tokens_out': total_tokens_out
        }
        update_manifest(run_data)
        
        # 8. Build response report
        report = {
            'run_id': run_id,
            'framework': framework,
            'status': verification_result['status'],
            'total_tokens_in': total_tokens_in,
            'total_tokens_out': total_tokens_out,
            'verification_message': verification_result['message'],
            'attempt_number': len(metrics['usage_api_reconciliation']['attempts'])
        }
        
        if verification_result['status'] == 'verified':
            report['verified_at'] = current_attempt['timestamp']
            
            # Trigger analysis regeneration when data is verified
            logger.info(
                "Data verified - triggering analysis regeneration",
                extra={
                    'run_id': run_id,
                    'framework': framework,
                    'event': 'analysis_triggered'
                }
            )
            self._trigger_analysis()
        
        logger.info(
            f"Reconciliation attempt for {framework}/{run_id}: {verification_result['status']}",
            extra={
                'run_id': run_id,
                'framework': framework,
                'event': 'reconciliation_attempt',
                'metadata': {
                    'status': verification_result['status'],
                    'total_tokens_in': total_tokens_in,
                    'total_tokens_out': total_tokens_out,
                    'message': verification_result['message']
                }
            }
        )
        
        return report
    
    def _count_stable_verifications(
        self,
        attempts: List[Dict[str, Any]],
        current_attempt: Dict[str, Any]
    ) -> int:
        """
        Count consecutive stable verifications.
        
        A verification is "stable" if:
        1. Token counts are identical to previous attempt
        2. Time gap >= VERIFICATION_INTERVAL_MIN between attempts
        
        Args:
            attempts: List of previous reconciliation attempts
            current_attempt: Current reconciliation attempt
            
        Returns:
            Number of consecutive stable verifications (0 if none)
        """
        if len(attempts) == 0:
            return 0  # First attempt, no stability yet
        
        # Read verification interval from environment at runtime
        verification_interval_min = int(os.getenv('RECONCILIATION_VERIFICATION_INTERVAL_MIN', '0'))
        
        stable_count = 0
        prev = current_attempt
        
        # Walk backwards through attempts, counting consecutive stable checks
        for attempt in reversed(attempts):
            # Check time gap
            try:
                current_time = datetime.fromisoformat(prev['timestamp'])
                prev_time = datetime.fromisoformat(attempt['timestamp'])
                time_diff_minutes = (current_time - prev_time).total_seconds() / 60
            except (KeyError, ValueError):
                break  # Invalid timestamp, stop counting
            
            if time_diff_minutes < verification_interval_min:
                break  # Gap too small, stop counting
            
            # Check if token counts are identical
            prev_in = prev.get('total_tokens_in', 0)
            prev_out = prev.get('total_tokens_out', 0)
            attempt_in = attempt.get('total_tokens_in', 0)
            attempt_out = attempt.get('total_tokens_out', 0)
            
            if prev_in == attempt_in and prev_out == attempt_out:
                stable_count += 1
                prev = attempt
            else:
                break  # Not identical, stop counting
        
        return stable_count
    
    def _check_verification_status(
        self,
        metrics: Dict[str, Any],
        current_attempt: Dict[str, Any],
        framework: str,
        run_id: str
    ) -> Dict[str, str]:
        """
        Check if reconciliation can be verified based on N-check stability criteria.
        
        Verification requires:
        1. N consecutive stable verifications (configurable via RECONCILIATION_MIN_STABLE_VERIFICATIONS)
        2. Time gap >= VERIFICATION_INTERVAL_MIN between each verification
        3. Identical token counts across all N verifications
        
        Also detects anomalies (decreasing token counts) and accepts partial token coverage
        (some steps may not use LLM, which is normal for efficient frameworks like BAeS).
        
        Returns:
            Dict with 'status' and 'message' keys
        """
        reconciliation = metrics.get('usage_api_reconciliation', {})
        attempts = reconciliation.get('attempts', [])
        
        current_in = current_attempt['total_tokens_in']
        current_out = current_attempt['total_tokens_out']
        
        # BREAKING CHANGE v2.0.0: Removed steps_with_tokens/total_steps tracking
        # We now only track aggregate run-level tokens, not per-step tokens
        # Coverage analysis is no longer possible with the new schema
        
        # No previous attempts - this is the first
        if len(attempts) == 0:
            if current_in == 0 and current_out == 0:
                return {
                    'status': 'data_not_available',
                    'message': 'No token data available from Usage API yet (first attempt)'
                }
            return {
                'status': 'pending',
                'message': 'First reconciliation attempt successful, awaiting verification'
            }
        
        # Get previous attempt for comparison
        previous_attempt = attempts[-1]
        previous_in = previous_attempt['total_tokens_in']
        previous_out = previous_attempt['total_tokens_out']
        
        # Check for data availability
        if current_in == 0 and current_out == 0:
            return {
                'status': 'data_not_available',
                'message': f'No token data available yet (attempt {len(attempts) + 1})'
            }
        
        # ANOMALY DETECTION: Token count decreased
        if current_in < previous_in or current_out < previous_out:
            decrease_in = previous_in - current_in
            decrease_out = previous_out - current_out
            return {
                'status': 'warning',
                'message': f'⚠️ Token count DECREASED (in: -{decrease_in}, out: -{decrease_out}) - possible API issue!'
            }
        
        # Check if data is still changing
        data_identical = (current_in == previous_in and current_out == previous_out)
        
        if not data_identical:
            # Data still arriving - normal during propagation delay
            return {
                'status': 'pending',
                'message': f'⏳ Data still arriving: {previous_in:,} → {current_in:,} tokens_in (attempt {len(attempts) + 1})'
            }
        
        # Data is stable - count consecutive stable verifications
        stable_count = self._count_stable_verifications(attempts, current_attempt)
        
        # Read minimum stable verifications from environment at runtime
        min_stable_verifications = int(os.getenv('RECONCILIATION_MIN_STABLE_VERIFICATIONS', '2'))
        
        # Check if we have enough stable verifications
        if stable_count >= min_stable_verifications:
            # ✅ VERIFIED - data is stable after N checks
            return {
                'status': 'verified',
                'message': f'✅ Verified after {stable_count} stable checks: {current_in:,} in, {current_out:,} out'
            }
        else:
            # Need more stable verifications
            return {
                'status': 'pending',
                'message': f'⏳ Awaiting verification: {stable_count}/{min_stable_verifications} stable checks completed'
            }
    
    def reconcile_all_pending(
        self,
        framework: Optional[str] = None,
        min_age_minutes: Optional[int] = None,
        max_age_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Find and reconcile all runs with missing token data.
        
        Args:
            framework: Specific framework to reconcile (None = all frameworks)
            min_age_minutes: Only reconcile runs older than this (wait for Usage API delay).
                           If None, uses RECONCILIATION_VERIFICATION_INTERVAL_MIN env var
            max_age_hours: Don't reconcile runs older than this (likely won't get data)
            
        Returns:
            List of reconciliation reports
        """
        # Read env var at runtime if not explicitly provided
        if min_age_minutes is None:
            min_age_minutes = int(os.getenv('RECONCILIATION_VERIFICATION_INTERVAL_MIN', '0'))
        
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
        
        # Get all runs from manifest (standalone experiment)
        manifest_path = Path("runs/manifest.json")
        if not manifest_path.exists():
            logger.warning("No manifest found")
            return results
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            all_runs = manifest.get("runs", [])
            
            # Apply framework filter if specified
            if framework:
                all_runs = [r for r in all_runs if r.get("framework") == framework]
        except Exception as e:
            logger.error(f"Failed to load manifest: {e}")
            return results
        
        if not all_runs:
            logger.warning("No runs found in manifest")
            return results
        
        # Process each run
        for run_entry in all_runs:
            run_id = run_entry['run_id']
            framework_name = run_entry['framework']
            
            # Build path to metrics file
            run_dir = self.runs_dir / framework_name / run_id
            metrics_file = run_dir / "metrics.json"
            
            if not metrics_file.exists():
                logger.debug(f"Metrics file not found: {framework_name}/{run_id}")
                continue
            
            # Check run age using start_time from manifest (not file mtime)
            start_time_str = run_entry.get('start_time')
            if start_time_str:
                # Parse ISO timestamp from manifest
                try:
                    start_time_dt = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
                    start_timestamp = start_time_dt.timestamp()
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Could not parse start_time for {framework_name}/{run_id}: {e}")
                    continue
            else:
                logger.warning(f"No start_time in manifest for {framework_name}/{run_id}")
                continue
            
            if start_timestamp > min_cutoff:
                logger.debug(
                    f"Run too recent: {framework_name}/{run_id} "
                    f"({(current_time - start_timestamp) / 60:.1f} minutes old)"
                )
                continue
            
            if start_timestamp < max_cutoff:
                logger.debug(
                    f"Run too old: {framework_name}/{run_id} "
                    f"({(current_time - start_timestamp) / 3600:.1f} hours old)"
                )
                continue
            
            # Check if already reconciled or has token data
            try:
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
                
                # Skip if already verified (not just reconciled)
                reconciliation = metrics.get('usage_api_reconciliation', {})
                verification_status = reconciliation.get('verification_status', 'pending')
                
                if verification_status == 'verified':
                    logger.debug(f"Already verified: {framework_name}/{run_id}")
                    continue
                
                # This run needs reconciliation/verification!
                logger.info(f"Reconciling: {framework_name}/{run_id} (status: {verification_status})")
                
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
        List all runs that need reconciliation/verification (without reconciling them).
        
        A run is pending if:
        - Not yet verified (verification_status != 'verified')
        - Old enough (> min_age_minutes)
        
        Args:
            framework: Specific framework to check (None = all frameworks)
            min_age_minutes: Only list runs older than this
            
        Returns:
            List of pending runs with metadata
        """
        pending = []
        current_time = time.time()
        min_cutoff = current_time - (min_age_minutes * 60)
        
        # Get all runs from manifest
        try:
            all_runs = find_runs(framework=framework)
        except Exception as e:
            logger.error("Failed to query manifest: %s", e)
            return pending
        
        for run_entry in all_runs:
            run_id = run_entry['run_id']
            framework_name = run_entry['framework']
            
            # Build path to metrics file
            run_dir = self.runs_dir / framework_name / run_id
            metrics_file = run_dir / "metrics.json"
            
            if not metrics_file.exists():
                logger.warning("Metrics file not found for run %s: %s", run_id, metrics_file)
                continue
            
            file_mtime = metrics_file.stat().st_mtime
            
            # Skip if too recent
            if file_mtime > min_cutoff:
                continue
            
            try:
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    metrics = json.load(f)
                
                # Check verification status
                reconciliation = metrics.get('usage_api_reconciliation', {})
                verification_status = reconciliation.get('verification_status', 'pending')
                
                # Skip if already verified
                if verification_status == 'verified':
                    continue
                
                age_minutes = (current_time - file_mtime) / 60
                attempts = reconciliation.get('attempts', [])
                
                pending.append({
                    'run_id': run_id,
                    'framework': framework_name,
                    'age_minutes': age_minutes,
                    'metrics_file': str(metrics_file),
                    'end_timestamp': metrics.get('end_timestamp'),
                    'verification_status': verification_status,
                    'attempts': len(attempts),
                    'message': reconciliation.get('verification_message', 'Not yet reconciled')
                })
                    
            except Exception as e:
                logger.warning(f"Error checking {framework_name}/{run_id}: {e}")
        
        return pending
    
    def _trigger_analysis(self) -> None:
        """
        Trigger analysis regeneration after data verification.
        
        Runs the analyze_results.sh script to regenerate visualizations
        and statistical reports with verified token data.
        """
        try:
            # Get project root (parent of src/)
            project_root = Path(__file__).parent.parent.parent
            analysis_script = project_root / "runners" / "analyze_results.sh"
            
            if not analysis_script.exists():
                logger.warning(f"Analysis script not found: {analysis_script}")
                return
            
            logger.info("Starting analysis regeneration...")
            
            # Run analysis script
            result = subprocess.run(
                [str(analysis_script)],
                cwd=str(project_root),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                check=False  # Don't raise exception on non-zero exit
            )
            
            if result.returncode == 0:
                logger.info(
                    "Analysis regeneration completed successfully",
                    extra={
                        'event': 'analysis_completed',
                        'metadata': {'exit_code': 0}
                    }
                )
            else:
                logger.error(
                    f"Analysis regeneration failed with exit code {result.returncode}",
                    extra={
                        'event': 'analysis_failed',
                        'metadata': {
                            'exit_code': result.returncode,
                            'stderr': result.stderr[:500]  # First 500 chars
                        }
                    }
                )
                
        except subprocess.TimeoutExpired:
            logger.error("Analysis regeneration timed out (5 minutes)")
        except Exception as e:
            logger.error(f"Failed to trigger analysis: {e}")
