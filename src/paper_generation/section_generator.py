"""
BaseSectionGenerator: Abstract base class for all section generators.

Provides common functionality for loading context, orchestrating prose generation,
and inserting AI markers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
import logging

from .models import SectionContext, PaperConfig
from .prose_engine import ProseEngine


logger = logging.getLogger(__name__)


class BaseSectionGenerator(ABC):
    """
    Abstract base class for section generators.
    
    All section generators must implement the generate() method which
    returns prose for their specific section.
    """
    
    def __init__(self, config: PaperConfig, prose_engine: ProseEngine):
        """
        Initialize section generator.
        
        Args:
            config: PaperConfig with generation settings
            prose_engine: ProseEngine instance for AI prose generation
        """
        self.config = config
        self.prose_engine = prose_engine
        
        logger.debug("Initialized %s", self.__class__.__name__)
    
    @abstractmethod
    def generate(self, context: SectionContext) -> str:
        """
        Generate prose for this section.
        
        Args:
            context: SectionContext with experiment data
            
        Returns:
            Generated prose as string (≥800 words with AI marker)
            
        Raises:
            ProseGenerationError: If generation fails
        """
        pass
    
    def _validate_word_count(self, prose: str, min_words: int = 800) -> bool:
        """
        Validate that prose meets minimum word count.
        
        Args:
            prose: Generated prose text
            min_words: Minimum required words
            
        Returns:
            True if valid, False otherwise
        """
        word_count = len(prose.split())
        is_valid = word_count >= min_words
        
        if not is_valid:
            logger.warning("Section has only %d words, expected ≥%d", 
                         word_count, min_words)
        
        return is_valid
    
    def _prepare_context(self, context: SectionContext, section_name: str) -> SectionContext:
        """
        Prepare SectionContext for specific section.
        
        Args:
            context: Original context
            section_name: Name of section to generate
            
        Returns:
            New SectionContext with section_name set
        """
        # Create a copy with the section name set
        from dataclasses import replace
        return replace(context, section_name=section_name)
