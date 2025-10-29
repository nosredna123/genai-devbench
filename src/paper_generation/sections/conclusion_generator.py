"""
ConclusionGenerator: Generate conclusion section.

Summarizes contributions, restates key findings, discusses limitations,
and suggests future work (≥800 words).
"""

import logging
from ..section_generator import BaseSectionGenerator
from ..models import SectionContext


logger = logging.getLogger(__name__)


class ConclusionGenerator(BaseSectionGenerator):
    """
    Generate conclusion section (≥800 words).
    
    Covers contributions, findings, limitations, and future work.
    """
    
    def generate(self, context: SectionContext) -> str:
        """
        Generate conclusion prose.
        
        Args:
            context: SectionContext with experiment data
            
        Returns:
            Conclusion prose (≥800 words)
        """
        logger.info("Generating conclusion section")
        
        # Prepare context for conclusion
        conclusion_context = self._prepare_context(context, "conclusion")
        
        # Generate using prose engine
        prose = self.prose_engine.generate_prose(conclusion_context)
        
        # Validate word count
        self._validate_word_count(prose)
        
        logger.info("Conclusion generated: %d words", len(prose.split()))
        
        return prose
