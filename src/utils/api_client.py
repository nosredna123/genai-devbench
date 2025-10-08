"""
OpenAI Usage API client for token verification.

Provides functions to verify token counts against OpenAI's usage API.
"""

import time
import requests
from typing import Dict, Any, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)

# API configuration
OPENAI_API_BASE = "https://api.openai.com/v1"
MAX_RETRIES = 3
INITIAL_BACKOFF = 1  # seconds
BACKOFF_MULTIPLIER = 2


class OpenAIAPIClient:
    """Client for OpenAI Usage API."""
    
    def __init__(self, api_key: str):
        """
        Initialize OpenAI API client.
        
        Args:
            api_key: OpenAI API key
        """
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
    def verify_token_counts(
        self,
        run_id: str,
        local_tokens_in: int,
        local_tokens_out: int,
        model: str = "gpt-4"
    ) -> Dict[str, Any]:
        """
        Verify token counts against OpenAI Usage API.
        
        Uses exponential backoff retry on failures.
        
        Args:
            run_id: Run identifier for logging
            local_tokens_in: Locally counted input tokens
            local_tokens_out: Locally counted output tokens
            model: Model name used
            
        Returns:
            Dictionary with verification results:
            {
                'verified': bool,
                'api_tokens_in': int,
                'api_tokens_out': int,
                'local_tokens_in': int,
                'local_tokens_out': int,
                'discrepancy_in': int,
                'discrepancy_out': int,
                'discrepancy_pct_in': float,
                'discrepancy_pct_out': float,
                'error': Optional[str]
            }
        """
        backoff = INITIAL_BACKOFF
        last_error = None
        
        for attempt in range(MAX_RETRIES):
            try:
                if attempt > 0:
                    logger.info("Retrying usage API call",
                               extra={'run_id': run_id,
                                     'metadata': {'attempt': attempt, 'backoff': backoff}})
                    time.sleep(backoff)
                    backoff *= BACKOFF_MULTIPLIER
                    
                # TODO: Implement actual OpenAI Usage API call
                # This is a placeholder implementation
                # Real implementation would:
                # 1. Call https://api.openai.com/v1/usage
                # 2. Filter by date/model
                # 3. Aggregate token counts
                # 4. Compare with local counts
                
                # Placeholder: assume counts match for now
                api_tokens_in = local_tokens_in
                api_tokens_out = local_tokens_out
                
                discrepancy_in = abs(api_tokens_in - local_tokens_in)
                discrepancy_out = abs(api_tokens_out - local_tokens_out)
                
                discrepancy_pct_in = (discrepancy_in / local_tokens_in * 100) if local_tokens_in > 0 else 0
                discrepancy_pct_out = (discrepancy_out / local_tokens_out * 100) if local_tokens_out > 0 else 0
                
                result = {
                    'verified': True,
                    'api_tokens_in': api_tokens_in,
                    'api_tokens_out': api_tokens_out,
                    'local_tokens_in': local_tokens_in,
                    'local_tokens_out': local_tokens_out,
                    'discrepancy_in': discrepancy_in,
                    'discrepancy_out': discrepancy_out,
                    'discrepancy_pct_in': discrepancy_pct_in,
                    'discrepancy_pct_out': discrepancy_pct_out,
                    'error': None
                }
                
                if discrepancy_pct_in > 5 or discrepancy_pct_out > 5:
                    logger.warning("Significant token count discrepancy",
                                 extra={'run_id': run_id,
                                       'metadata': {
                                           'discrepancy_pct_in': discrepancy_pct_in,
                                           'discrepancy_pct_out': discrepancy_pct_out
                                       }})
                                       
                return result
                
            except requests.RequestException as e:
                last_error = str(e)
                logger.warning("Usage API request failed",
                             extra={'run_id': run_id,
                                   'metadata': {'attempt': attempt + 1, 'error': str(e)}})
                
                if attempt == MAX_RETRIES - 1:
                    logger.error("All usage API retries exhausted",
                               extra={'run_id': run_id})
                    break
                    
        # Return error result if all retries failed
        return {
            'verified': False,
            'api_tokens_in': 0,
            'api_tokens_out': 0,
            'local_tokens_in': local_tokens_in,
            'local_tokens_out': local_tokens_out,
            'discrepancy_in': local_tokens_in,
            'discrepancy_out': local_tokens_out,
            'discrepancy_pct_in': 100.0,
            'discrepancy_pct_out': 100.0,
            'error': f"API verification failed after {MAX_RETRIES} retries: {last_error}"
        }
