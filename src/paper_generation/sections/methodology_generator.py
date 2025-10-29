"""
MethodologyGenerator: Generate methodology section.

Describes experimental design, task specification, metrics definitions,
and statistical methods (≥800 words).
"""

import logging
from ..section_generator import BaseSectionGenerator
from ..models import SectionContext


logger = logging.getLogger(__name__)


class MethodologyGenerator(BaseSectionGenerator):
    """
    Generate methodology section (≥800 words).
    
    Covers experimental design, tasks, metrics, and statistics.
    """
    
    def generate(self, context: SectionContext) -> str:
        """
        Generate methodology prose.
        
        Args:
            context: SectionContext with experiment data
            
        Returns:
            Methodology prose (≥800 words)
        """
        logger.info("Generating methodology section")
        
        # Prepare context for methodology
        methodology_context = self._prepare_context(context, "methodology")
        
        # Generate using prose engine
        prose = self.prose_engine.generate_prose(methodology_context)
        
        # Validate word count
        self._validate_word_count(prose)
        
        logger.info("Methodology generated: %d words", len(prose.split()))
        
        return prose
