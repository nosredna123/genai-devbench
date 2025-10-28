"""
Metrics collection for BAEs experiment framework.

Collects interaction, efficiency, quality, and cost metrics for each run.
"""

import time
from datetime import datetime
from typing import Any, Dict, Optional
import math
from src.utils.cost_calculator import CostCalculator
from src.utils.metrics_config import get_metrics_config
from src.utils.logger import get_logger

logger = get_logger(__name__, component="metrics")


class MetricsCollector:
    """Collects and computes experiment metrics."""
    
    def __init__(self, run_id: str, model: str = 'gpt-4o-mini'):
        """
        Initialize metrics collector for a run.
        
        Args:
            run_id: Unique run identifier
            model: OpenAI model name for cost calculation (default: 'gpt-4o-mini')
        """
        self.run_id = run_id
        self.model = model
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.steps_data: Dict[int, Dict[str, Any]] = {}
        
        # Initialize cost calculator
        self.cost_calculator = CostCalculator(model)
        self.metrics_config = get_metrics_config()
        
    def start_run(self) -> None:
        """Record run start time."""
        self.start_time = time.time()
        
    def end_run(self) -> None:
        """Record run end time."""
        self.end_time = time.time()
        
    def record_step(
        self,
        step_num: int,
        duration_seconds: float,
        start_timestamp: int,
        end_timestamp: int,
        hitl_count: int = 0,
        retry_count: int = 0,
        success: bool = True
    ) -> None:
        """
        Record metrics for a single step.
        
        BREAKING CHANGE (v2.0.0): Token fields removed from step records.
        Token metrics are now collected only at run level via post-run reconciliation.
        This eliminates the 36-50% zero-token error caused by OpenAI Usage API's
        bucket-based attribution system.
        
        Args:
            step_num: Step number (1-indexed)
            duration_seconds: Step execution time in seconds
            start_timestamp: Unix timestamp (seconds) when step started
            end_timestamp: Unix timestamp (seconds) when step ended
            hitl_count: Number of HITL interventions (default: 0)
            retry_count: Number of retries attempted (default: 0)
            success: Whether step completed successfully (default: True)
            
        Note:
            Token metrics (TOK_IN, TOK_OUT, API_CALLS, CACHED_TOKENS) are now
            stored only in aggregate_metrics and populated by UsageReconciler
            after the run completes.
        """
        self.steps_data[step_num] = {
            'step': step_num,
            'duration_seconds': duration_seconds,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp,
            'hitl_count': hitl_count,
            'retry_count': retry_count,
            'success': success
        }

        
    def compute_interaction_metrics(self) -> Dict[str, float]:
        """
        Compute interaction metrics: UTT, HIT, AUTR, HEU.
        
        Returns:
            Dictionary with interaction metrics
        """
        # UTT: Total utterance count (steps)
        utt = len(self.steps_data)
        
        # HIT: Total human interventions
        hit = sum(step['hitl_count'] for step in self.steps_data.values())
        
        # AUTR: Autonomy rate = 1 - HIT/6
        # Using 6 as the fixed scenario length
        autr = 1.0 - (hit / 6.0) if utt > 0 else 0.0
        
        # HEU: Human effort units (weighted by intervention difficulty)
        # Each HITL intervention weighted as 3 units
        heu = hit * 3
        
        return {
            'UTT': utt,
            'HIT': hit,
            'AUTR': autr,
            'HEU': heu
        }
        
    def compute_efficiency_metrics(self) -> Dict[str, Any]:
        """
        Compute efficiency metrics: TOK_IN, TOK_OUT, API_CALLS, CACHED_TOKENS, T_WALL.
        
        BREAKING CHANGE (v2.0.0): Token metrics are initialized to zero and populated
        by post-run reconciliation. Step-level token aggregation removed.
        
        Returns:
            Dictionary with efficiency metrics (tokens will be 0 until reconciliation)
        """
        # BREAKING CHANGE: Tokens no longer aggregated from steps
        # Token metrics initialized to 0 (reconciled post-run)
        tok_in = 0  # Reconciled post-run
        tok_out = 0  # Reconciled post-run
        api_calls = 0  # Reconciled post-run
        cached_tokens = 0  # Reconciled post-run
        
        # Wall-clock time
        if self.start_time and self.end_time:
            t_wall_seconds = self.end_time - self.start_time
            start_timestamp = datetime.utcfromtimestamp(self.start_time).isoformat() + 'Z'
            end_timestamp = datetime.utcfromtimestamp(self.end_time).isoformat() + 'Z'
        else:
            t_wall_seconds = 0
            start_timestamp = None
            end_timestamp = None
            
        return {
            'TOK_IN': tok_in,
            'TOK_OUT': tok_out,
            'API_CALLS': api_calls,
            'CACHED_TOKENS': cached_tokens,
            'T_WALL_seconds': t_wall_seconds,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp
        }
        
    def compute_quality_metrics(
        self,
        crude_score: int,
        esr: float,
        mc: float,
        zdi: int
    ) -> Dict[str, float]:
        """
        Compute quality metrics: CRUDe, ESR, MC, ZDI, Q*, AEI.
        
        Args:
            crude_score: CRUD coverage (0-12 scale)
            esr: Endpoint success rate (0-1)
            mc: Migration continuity (0-1)
            zdi: Zero-downtime incidents count
            
        Returns:
            Dictionary with quality metrics
        """
        # Q*: Composite quality score
        # Q* = 0.4·ESR + 0.3·(CRUDe/12) + 0.3·MC
        q_star = 0.4 * esr + 0.3 * (crude_score / 12.0) + 0.3 * mc
        
        # AEI: Autonomy Efficiency Index
        # AEI = AUTR / log(1 + TOK_IN)
        interaction = self.compute_interaction_metrics()
        efficiency = self.compute_efficiency_metrics()
        
        autr = interaction['AUTR']
        tok_in = efficiency['TOK_IN']
        
        aei = autr / math.log(1 + tok_in) if tok_in > 0 else 0.0
        
        return {
            'CRUDe': crude_score,
            'ESR': esr,
            'MC': mc,
            'ZDI': zdi,
            'Q_star': q_star,
            'AEI': aei
        }
    
    def compute_cost_metrics(self) -> Dict[str, Any]:
        """
        Compute cost metrics: COST_USD and breakdown.
        
        Returns:
            Dictionary with cost metrics and breakdown
        """
        # Get token totals from efficiency metrics
        efficiency = self.compute_efficiency_metrics()
        tok_in = efficiency['TOK_IN']
        tok_out = efficiency['TOK_OUT']
        cached_tokens = efficiency['CACHED_TOKENS']
        
        # Calculate cost using CostCalculator
        cost_breakdown = self.cost_calculator.calculate_cost(
            tokens_in=tok_in,
            tokens_out=tok_out,
            cached_tokens=cached_tokens
        )
        
        return {
            'COST_USD': cost_breakdown['total_cost'],
            'COST_BREAKDOWN': {
                'uncached_input_cost': cost_breakdown['uncached_input_cost'],
                'cached_input_cost': cost_breakdown['cached_input_cost'],
                'output_cost': cost_breakdown['output_cost'],
                'cache_savings': cost_breakdown['cache_savings'],
                'model': cost_breakdown['model']
            }
        }
        
    def get_aggregate_metrics(
        self,
        crude_score: int,
        esr: float,
        mc: float,
        zdi: int
    ) -> Dict[str, Any]:
        """
        Get all aggregate metrics for the run.
        
        Args:
            crude_score: CRUD coverage score
            esr: Endpoint success rate
            mc: Migration continuity
            zdi: Zero-downtime incidents
            
        Returns:
            Complete metrics dictionary
        """
        interaction = self.compute_interaction_metrics()
        efficiency = self.compute_efficiency_metrics()
        quality = self.compute_quality_metrics(crude_score, esr, mc, zdi)
        cost = self.compute_cost_metrics()
        
        return {
            'run_id': self.run_id,
            'model': self.model,
            'start_timestamp': efficiency['start_timestamp'],
            'end_timestamp': efficiency['end_timestamp'],
            'steps': list(self.steps_data.values()),
            'aggregate_metrics': {
                **interaction,
                'TOK_IN': efficiency['TOK_IN'],
                'TOK_OUT': efficiency['TOK_OUT'],
                'API_CALLS': efficiency['API_CALLS'],
                'CACHED_TOKENS': efficiency['CACHED_TOKENS'],
                'T_WALL_seconds': efficiency['T_WALL_seconds'],
                **quality,
                'COST_USD': cost['COST_USD']
            },
            'cost_breakdown': cost['COST_BREAKDOWN']
        }
    
    def save_metrics(
        self,
        output_path,
        run_id: str,
        framework: str,
        start_timestamp: int,
        end_timestamp: int,
        crude_score: int = 0,
        esr: float = 0.0,
        mc: float = 0.0,
        zdi: int = 0
    ) -> None:
        """
        Save metrics to JSON file with schema validation.
        
        BREAKING CHANGE (v2.0.0): Enforces clean schema with fail-fast validation.
        Steps array MUST NOT contain token fields. Token metrics are stored only
        in aggregate_metrics and populated by UsageReconciler post-run.
        
        Args:
            output_path: Path to save metrics.json file
            run_id: Unique run identifier
            framework: Framework name (baes, chatdev, ghspec)
            start_timestamp: Run start Unix timestamp
            end_timestamp: Run end Unix timestamp
            crude_score: CRUD coverage score (default: 0)
            esr: Endpoint success rate (default: 0.0)
            mc: Migration continuity (default: 0.0)
            zdi: Zero-downtime incidents (default: 0)
            
        Raises:
            ValueError: If steps array contains forbidden token fields
            
        Note:
            Validation runs BEFORE file write (fail-fast principle).
            No partial writes on validation failure.
        """
        import json
        from pathlib import Path
        
        # Get metrics with quality scores
        metrics = self.get_aggregate_metrics(crude_score, esr, mc, zdi)
        
        # Validate schema (fail-fast on violations)
        forbidden_fields = {'tokens_in', 'tokens_out', 'api_calls', 'cached_tokens'}
        for step in metrics['steps']:
            violations = forbidden_fields & step.keys()
            if violations:
                raise ValueError(
                    f"Step {step.get('step', '?')} contains forbidden token fields: {violations}. "
                    f"Token metrics must be stored only in aggregate_metrics (not in steps array). "
                    f"This is enforced to prevent the 36-50% zero-token error caused by "
                    f"OpenAI Usage API's bucket-based attribution system."
                )
        
        # Validation passed - safe to write
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(
            "Metrics saved with clean schema validation",
            extra={
                'run_id': run_id,
                'framework': framework,
                'metadata': {
                    'output_path': str(output_path),
                    'steps_count': len(metrics['steps']),
                    'schema_version': '2.0.0'
                }
            }
        )

