"""
Log summary generation for experiment runs.

Creates human-readable summaries of run logs for git tracking.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class LogSummarizer:
    """Generates comprehensive log summaries for experiment runs."""
    
    def __init__(self, run_id: str, framework: str, run_dir: Path):
        """
        Initialize log summarizer.
        
        Args:
            run_id: Run identifier
            framework: Framework name
            run_dir: Run directory path
        """
        self.run_id = run_id
        self.framework = framework
        self.run_dir = run_dir
        
    def generate_summary(
        self,
        config: Dict[str, Any],
        start_time: datetime,
        end_time: datetime,
        steps: List[Dict[str, Any]],
        reconciliation: Optional[Dict[str, Any]],
        errors: List[Dict[str, Any]],
        hitl_events: List[Dict[str, Any]],
        archive_info: Dict[str, Any]
    ) -> str:
        """
        Generate comprehensive log summary.
        
        Args:
            config: Experiment configuration
            start_time: Run start timestamp
            end_time: Run end timestamp
            steps: List of step execution summaries
            reconciliation: Reconciliation results (if performed)
            errors: List of errors and warnings
            hitl_events: HITL interaction events
            archive_info: Archive metadata
            
        Returns:
            Formatted summary text
        """
        duration = end_time - start_time
        
        lines = [
            "=" * 80,
            "EXPERIMENT RUN SUMMARY",
            "=" * 80,
            f"Run ID: {self.run_id}",
            f"Framework: {self.framework}",
            f"Model: {config.get('model', 'N/A')}",
            f"Started: {start_time.isoformat()}Z",
            f"Completed: {end_time.isoformat()}Z",
            f"Duration: {self._format_duration(duration.total_seconds())}",
            "",
            "=" * 80,
            "CONFIGURATION",
            "=" * 80,
            f"Steps Configured: {len(steps)}",
            f"Timeout per Step: {config.get('step_timeout', 600)}s",
            f"Max Retries: {config.get('max_retries', 2)}",
            f"Random Seed: {config.get('random_seed', 'N/A')}",
            "",
            "=" * 80,
            "STEP EXECUTION SUMMARY",
            "=" * 80,
        ]
        
        # Step summaries
        for step in steps:
            lines.extend(self._format_step_summary(step))
            lines.append("")
        
        # Reconciliation summary
        if reconciliation:
            lines.extend([
                "=" * 80,
                "RECONCILIATION SUMMARY",
                "=" * 80,
            ])
            lines.extend(self._format_reconciliation_summary(reconciliation))
            lines.append("")
        
        # Final metrics
        lines.extend([
            "=" * 80,
            "FINAL METRICS",
            "=" * 80,
        ])
        lines.extend(self._format_metrics_summary(steps))
        lines.append("")
        
        # Errors and warnings
        if errors:
            lines.extend([
                "=" * 80,
                "ERRORS AND WARNINGS",
                "=" * 80,
            ])
            for error in errors:
                timestamp = error.get('timestamp', 'N/A')
                level = error.get('level', 'ERROR')
                message = error.get('message', 'N/A')
                lines.append(f"[{timestamp}] {level} {message}")
            lines.append("")
        
        # HITL interactions
        if hitl_events:
            lines.extend([
                "=" * 80,
                "HITL INTERACTIONS",
                "=" * 80,
                f"Total HITL Events: {len(hitl_events)}",
            ])
            for event in hitl_events:
                step = event.get('step', 'N/A')
                hash_val = event.get('response_sha1', 'N/A')[:10]
                lines.append(f"Step {step:03d}: Clarification requested (response hash: {hash_val}...)")
            lines.append("")
        
        # Archive integrity
        lines.extend([
            "=" * 80,
            "ARCHIVE INTEGRITY",
            "=" * 80,
            f"Archive: {archive_info.get('filename', 'N/A')}",
            f"SHA-256: {archive_info.get('hash', 'N/A')}",
            f"Size: {self._format_size(archive_info.get('size', 0))}",
            f"Contents: {archive_info.get('contents', 'N/A')}",
            "=" * 80,
        ])
        
        return "\n".join(lines)
    
    def _format_step_summary(self, step: Dict[str, Any]) -> List[str]:
        """Format a single step summary."""
        step_num = step.get('step_num', 'N/A')
        status = step.get('status', 'UNKNOWN').upper()
        duration = step.get('duration_seconds', 0)
        retries = step.get('retries', 0)
        
        lines = [
            f"Step {step_num:03d}: {status} (duration: {self._format_duration(duration)}, retries: {retries})"
        ]
        
        # Token metrics
        tokens = step.get('tokens', {})
        prompt = tokens.get('prompt', 0)
        completion = tokens.get('completion', 0)
        total = tokens.get('total', 0)
        
        lines.append(f"  - API Calls: {step.get('api_calls', 0)}")
        lines.append(f"  - Tokens (prompt/completion/total): {prompt} / {completion} / {total}")
        lines.append(f"  - LLM Requests: {step.get('llm_requests', 0)}")
        
        # Special notes (e.g., template-based generation)
        note = step.get('note')
        if note:
            lines.append(f"  - Note: {note}")
        
        # Error information for failed steps
        error = step.get('error')
        if error:
            lines.append(f"  - Last error: {error}")
        
        return lines
    
    def _format_reconciliation_summary(self, reconciliation: Dict[str, Any]) -> List[str]:
        """Format reconciliation summary."""
        status = reconciliation.get('status', 'UNKNOWN').upper()
        attempts = reconciliation.get('attempts', 0)
        stable_count = reconciliation.get('stable_verifications', 0)
        required = reconciliation.get('required_stable', 2)
        first_stable = reconciliation.get('first_stable_attempt', 'N/A')
        steps_with_tokens = reconciliation.get('steps_with_tokens', 0)
        total_steps = reconciliation.get('total_steps', 0)
        interval = reconciliation.get('interval_minutes', 0)
        
        lines = [
            f"Status: {status}",
            f"Verification Attempts: {attempts}",
            f"Stable Verifications: {stable_count} (required: {required})",
            f"First Stable At: Attempt {first_stable}",
            f"Steps with Tokens: {steps_with_tokens} / {total_steps}",
            f"Verification Interval: {interval} minutes",
            "",
        ]
        
        # Token reconciliation details
        cached = reconciliation.get('cached_tokens', 0)
        usage_api = reconciliation.get('usage_api_tokens', 0)
        diff = usage_api - cached
        diff_pct = (abs(diff) / cached * 100) if cached > 0 else 0
        within_threshold = reconciliation.get('within_threshold', False)
        
        lines.extend([
            "Token Reconciliation:",
            f"  - Total Cached Tokens: {cached:,}",
            f"  - Total Usage API Tokens: {usage_api:,}",
            f"  - Difference: {diff:,} tokens ({diff_pct:.2f}%)",
            f"  - Within Threshold: {'YES' if within_threshold else 'NO'}",
        ])
        
        return lines
    
    def _format_metrics_summary(self, steps: List[Dict[str, Any]]) -> List[str]:
        """Format final metrics summary."""
        total_api_calls = sum(s.get('api_calls', 0) for s in steps)
        total_tokens = sum(s.get('tokens', {}).get('total', 0) for s in steps)
        total_duration = sum(s.get('duration_seconds', 0) for s in steps)
        
        successful_steps = sum(1 for s in steps if s.get('status') == 'success')
        total_steps = len(steps)
        success_rate = (successful_steps / total_steps * 100) if total_steps > 0 else 0
        
        failed_steps = total_steps - successful_steps
        
        lines = [
            f"Total API Calls: {total_api_calls}",
            f"Total Tokens: {total_tokens:,}",
            f"Total Duration: {self._format_duration(total_duration)}",
            f"Steps Completed: {total_steps} / {total_steps}",
            f"Success Rate: {success_rate:.0f}% ({successful_steps} successful, {failed_steps} failed/timeout)",
        ]
        
        return lines
    
    def _format_duration(self, seconds: float) -> str:
        """Format duration as human-readable string."""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:.0f}m {secs:.0f}s"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}h {minutes:.0f}m"
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size as human-readable string."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
    
    def write_summary(self, summary_text: str) -> Path:
        """
        Write summary to file.
        
        Args:
            summary_text: Formatted summary text
            
        Returns:
            Path to summary file
        """
        summary_dir = self.run_dir / "summary"
        summary_dir.mkdir(parents=True, exist_ok=True)
        summary_path = summary_dir / "logs_summary.txt"
        summary_path.write_text(summary_text, encoding='utf-8')
        return summary_path
