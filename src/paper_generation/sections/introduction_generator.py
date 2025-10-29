"""
IntroductionGenerator: Generate introduction section.

Provides research motivation, problem statement, key contributions, 
and paper organization (≥800 words).
"""

import logging
from ..section_generator import BaseSectionGenerator
from ..models import SectionContext


logger = logging.getLogger(__name__)


class IntroductionGenerator(BaseSectionGenerator):
    """
    Generate introduction section (≥800 words).
    
    Covers motivation, problem statement, contributions, and structure.
    """
    
    def generate(self, context: SectionContext) -> str:
        """
        Generate introduction prose.
        
        Args:
            context: SectionContext with experiment data
            
        Returns:
            Introduction prose (≥800 words)
        """
        logger.info("Generating introduction section")
        
        # Prepare context for introduction
        intro_context = self._prepare_context(context, "introduction")
        
        # Generate using prose engine
        prose = self.prose_engine.generate_prose(intro_context)
        
        # Validate word count
        self._validate_word_count(prose)
        
        logger.info("Introduction generated: %d words", len(prose.split()))
        
        return prose
