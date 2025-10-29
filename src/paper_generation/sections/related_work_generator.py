"""
RelatedWorkGenerator: Generate related work section.

Surveys framework landscape, compares approaches, and positions this work.
Inserts citation placeholders to prevent hallucinations (≥800 words).
"""

import logging
from ..section_generator import BaseSectionGenerator
from ..models import SectionContext


logger = logging.getLogger(__name__)


class RelatedWorkGenerator(BaseSectionGenerator):
    """
    Generate related work section (≥800 words).
    
    Includes framework landscape and citation placeholders.
    """
    
    def generate(self, context: SectionContext) -> str:
        """
        Generate related work prose with citation placeholders.
        
        Args:
            context: SectionContext with experiment data
            
        Returns:
            Related work prose (≥800 words) with citation placeholders
        """
        logger.info("Generating related work section")
        
        # Prepare context for related work
        related_context = self._prepare_context(context, "related_work")
        
        # Generate using prose engine
        prose = self.prose_engine.generate_prose(related_context)
        
        # Insert citation placeholders using CitationHandler
        from ..citation_handler import CitationHandler
        citation_handler = CitationHandler()
        prose_with_citations = citation_handler.insert_placeholders(prose)
        
        # Validate word count
        self._validate_word_count(prose_with_citations)
        
        placeholder_count = citation_handler.count_placeholders(prose_with_citations)
        logger.info("Related work generated: %d words, %d citation placeholders", 
                   len(prose_with_citations.split()), placeholder_count)
        
        return prose_with_citations
