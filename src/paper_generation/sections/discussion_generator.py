"""
DiscussionGenerator: Generate discussion section.

Interprets results, discusses implications for practitioners,
analyzes trade-offs, and acknowledges threats to validity (≥800 words).
"""

import logging
from ..section_generator import BaseSectionGenerator
from ..models import SectionContext


logger = logging.getLogger(__name__)


class DiscussionGenerator(BaseSectionGenerator):
    """
    Generate discussion section (≥800 words).
    
    Covers interpretation, implications, and threats to validity.
    """
    
    def generate(self, context: SectionContext) -> str:
        """
        Generate discussion prose.
        
        Args:
            context: SectionContext with experiment data
            
        Returns:
            Discussion prose (≥800 words)
        """
        logger.info("Generating discussion section")
        
        # Prepare context for discussion
        discussion_context = self._prepare_context(context, "discussion")
        
        # Generate using prose engine
        prose = self.prose_engine.generate_prose(discussion_context)
        
        # Validate word count
        self._validate_word_count(prose)
        
        logger.info("Discussion generated: %d words", len(prose.split()))
        
        return prose
