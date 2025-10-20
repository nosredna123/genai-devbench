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
        command: str,
        duration_seconds: float,
        success: bool,
        retry_count: int,
        hitl_count: int,
        tokens_in: int,
        tokens_out: int,
        api_calls: int = 0,
        cached_tokens: int = 0,
        start_timestamp: Optional[int] = None,
        end_timestamp: Optional[int] = None
    ) -> None:
        """
        Record metrics for a single step.
        
        LAZY EVALUATION PATTERN:
        Token metrics (tokens_in, tokens_out, api_calls, cached_tokens) will be 0 initially.
        These are backfilled later by the reconciliation script after OpenAI Usage API
        propagation delay (5-15 minutes). All steps are marked with verification_status='pending'.
        
        Args:
            step_num: Step number (1-6)
            command: Natural language command text
            duration_seconds: Step execution time
            success: Whether step completed successfully
            retry_count: Number of retries attempted
            hitl_count: Number of HITL interventions
            tokens_in: Input tokens consumed (will be 0 initially, backfilled by reconciliation)
            tokens_out: Output tokens generated (will be 0 initially, backfilled by reconciliation)
            api_calls: Number of API calls made to OpenAI (will be 0 initially)
            cached_tokens: Number of cached input tokens (will be 0 initially)
            start_timestamp: Unix timestamp when step started (for Usage API reconciliation)
            end_timestamp: Unix timestamp when step ended (for Usage API reconciliation)
        """
        # LAZY EVALUATION: Accept zeros for token metrics during execution
        # Validation is handled by reconciliation script, not during execution
        
        self.steps_data[step_num] = {
            'step_number': step_num,
            'command': command,
            'duration_seconds': duration_seconds,
            'success': success,
            'retry_count': retry_count,
            'hitl_count': hitl_count,
            'tokens_in': tokens_in,
            'tokens_out': tokens_out,
            'api_calls': api_calls,
            'cached_tokens': cached_tokens,
            'start_timestamp': start_timestamp,
            'end_timestamp': end_timestamp,
            'verification_status': 'pending'  # Will be updated by reconciliation script
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
        
        Returns:
            Dictionary with efficiency metrics
        """
        # Total tokens
        tok_in = sum(step['tokens_in'] for step in self.steps_data.values())
        tok_out = sum(step['tokens_out'] for step in self.steps_data.values())
        api_calls = sum(step.get('api_calls', 0) for step in self.steps_data.values())
        cached_tokens = sum(step.get('cached_tokens', 0) for step in self.steps_data.values())
        
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
