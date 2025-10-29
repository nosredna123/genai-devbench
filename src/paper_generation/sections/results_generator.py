"""
ResultsGenerator: Generate results section.

Presents descriptive statistics tables, comparative analysis with effect sizes,
and AI-generated interpretations embedded with p-values (≥800 words).
"""

import logging
from dataclasses import replace
from ..section_generator import BaseSectionGenerator
from ..models import SectionContext


logger = logging.getLogger(__name__)


class ResultsGenerator(BaseSectionGenerator):
    """
    Generate results section (≥800 words).
    
    Includes statistical tables, comparisons, and interpretations.
    """
    
    def generate(self, context: SectionContext) -> str:
        """
        Generate results prose with statistical tables.
        
        Args:
            context: SectionContext with experiment data
            
        Returns:
            Results prose (≥800 words) with embedded tables
        """
        logger.info("Generating results section")
        
        # Prepare context for results (includes metric filtering)
        results_context = self._prepare_context(context, "results")
        
        # Generate using prose engine
        prose = self.prose_engine.generate_prose(results_context)
        
        # Optionally: Add statistical tables formatting
        # (For now, AI generates them as part of prose)
        
        # Validate word count
        self._validate_word_count(prose)
        
        logger.info("Results generated: %d words", len(prose.split()))
        
        return prose
    
    def _prepare_context(self, context: SectionContext, section_name: str) -> SectionContext:
        """
        Prepare SectionContext for results section.
        
        Applies metric filtering if config.metrics_filter is specified.
        Handles single-framework experiments (no comparative analysis).
        
        Args:
            context: Original context
            section_name: Name of section to generate
            
        Returns:
            New SectionContext with section_name set and metrics filtered
        """
        # Start with base preparation (sets section_name)
        prepared_context = super()._prepare_context(context, section_name)
        
        # Check if single framework (no comparative analysis needed)
        if len(context.frameworks) == 1:
            logger.info("Single framework experiment detected - focusing on descriptive analysis")
            # Note: AI prompt will be adjusted automatically based on context
        
        # Apply metric filtering if specified
        if self.config.metrics_filter is not None:
            filtered_metrics = {}
            metrics_filter_set = set(self.config.metrics_filter)
            
            for framework, framework_metrics in context.metrics.items():
                # Filter metrics for this framework
                filtered_framework_metrics = {
                    metric_name: metric_data
                    for metric_name, metric_data in framework_metrics.items()
                    if metric_name in metrics_filter_set
                }
                filtered_metrics[framework] = filtered_framework_metrics
            
            # Replace metrics in context
            prepared_context = replace(prepared_context, metrics=filtered_metrics)
            logger.info("Filtered metrics to: %s", list(metrics_filter_set))
        
        return prepared_context
