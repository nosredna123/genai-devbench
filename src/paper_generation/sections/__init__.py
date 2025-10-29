"""
Section Generators for Academic Paper Generation

This package contains individual section generators that create specific
sections of the academic paper (Abstract, Introduction, Related Work, etc.).

All generators extend BaseSectionGenerator and use ProseEngine for AI-powered
text generation.
"""

from .abstract_generator import AbstractGenerator
from .introduction_generator import IntroductionGenerator
from .related_work_generator import RelatedWorkGenerator
from .methodology_generator import MethodologyGenerator
from .results_generator import ResultsGenerator
from .discussion_generator import DiscussionGenerator
from .conclusion_generator import ConclusionGenerator


__all__ = [
    'AbstractGenerator',
    'IntroductionGenerator',
    'RelatedWorkGenerator',
    'MethodologyGenerator',
    'ResultsGenerator',
    'DiscussionGenerator',
    'ConclusionGenerator',
]

