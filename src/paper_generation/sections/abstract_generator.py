"""
AbstractGenerator: Generate abstract section.

Extracts experiment summary, frameworks, and key findings into concise overview.
"""

import logging
from ..section_generator import BaseSectionGenerator
from ..models import SectionContext


logger = logging.getLogger(__name__)


class AbstractGenerator(BaseSectionGenerator):
    """
    Generate abstract section (150-250 words).
    
    Summarizes motivation, methods, key results, and implications.
    """
    
    def generate(self, context: SectionContext) -> str:
        """
        Generate abstract prose.
        
        Args:
            context: SectionContext with experiment data
            
        Returns:
            Abstract prose (150-250 words)
        """
        logger.info("Generating abstract section")
        
        # Prepare context for abstract
        abstract_context = self._prepare_context(context, "abstract")
        
        # Generate using prose engine
        # Note: Abstract is shorter (150-250 words), not 800+
        prose = self.prose_engine.generate_prose(abstract_context)
        
        logger.info("Abstract generated: %d words", len(prose.split()))
        
        return prose
