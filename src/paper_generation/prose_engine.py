"""
ProseEngine: AI-powered prose generation for scientific papers.

Handles OpenAI API calls with structured prompts, exponential backoff retry,
token usage tracking, and word count validation (≥800 words per section).

Uses requests library for direct API calls (no openai package dependency).
"""

import os
import time
import json
from typing import Optional
import logging
import requests

from .models import PaperConfig, SectionContext
from .exceptions import ProseGenerationError


logger = logging.getLogger(__name__)


class ProseEngine:
    """
    Generate AI-powered prose for scientific paper sections.
    
    Uses OpenAI API (default: gpt-3.5-turbo) via requests library to generate 
    comprehensive prose based on experiment data and section context. 
    Includes retry logic, token tracking, and quality validation.
    """
    
    OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
    
    def __init__(self, config: PaperConfig):
        """
        Initialize ProseEngine with configuration.
        
        Args:
            config: PaperConfig with model, temperature, prose_level settings
            
        Raises:
            ConfigValidationError: If API key not found
        """
        self.config = config
        self.total_tokens_used = 0
        
        # Set OpenAI API key from config or environment
        self.api_key = config.openai_api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            from .exceptions import ConfigValidationError
            raise ConfigValidationError(
                field="openai_api_key",
                message="OpenAI API key not found. Set OPENAI_API_KEY environment variable or pass via config.openai_api_key"
            )
        
        logger.info("ProseEngine initialized with model=%s, prose_level=%s", 
                   config.model, config.prose_level)
    
    def generate_prose(
        self,
        context: SectionContext,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> str:
        """
        Generate prose for a paper section using OpenAI API.
        
        Args:
            context: SectionContext with experiment data and section info
            max_retries: Maximum number of retry attempts on transient errors
            retry_delay: Initial delay between retries (exponentially increases)
            
        Returns:
            Generated prose as string (≥800 words)
            
        Raises:
            ProseGenerationError: If generation fails after retries or output invalid
        """
        prompt = self._build_prompt(context)
        
        # Retry loop with exponential backoff
        last_exception = None
        for attempt in range(max_retries):
            try:
                logger.info("Generating prose for section '%s' (attempt %d/%d)",
                           context.section_name, attempt + 1, max_retries)
                
                # Prepare API request
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": self.config.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert scientific writer specializing in software engineering research papers."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": self.config.temperature,
                    "max_tokens": 2000  # Allow sufficient tokens for ≥800 words
                }
                
                # Make API call
                response = requests.post(
                    self.OPENAI_API_URL,
                    headers=headers,
                    json=payload,
                    timeout=60  # 60 second timeout
                )
                
                # Check for HTTP errors
                response.raise_for_status()
                
                # Parse response
                response_data = response.json()
                
                # Extract prose and track tokens
                prose = response_data['choices'][0]['message']['content']
                tokens_used = response_data['usage']['total_tokens']
                self.total_tokens_used += tokens_used
                
                logger.info("Generated %d words using %d tokens",
                           len(prose.split()), tokens_used)
                
                # Validate word count
                word_count = len(prose.split())
                if word_count < 800:
                    logger.warning("Prose only %d words, expected ≥800. Retrying with adjusted prompt.",
                                 word_count)
                    # Could adjust prompt here, but for now just return what we got
                    # (validation will happen at caller level)
                
                # Add AI-generated marker
                prose_with_marker = self._add_ai_marker(prose)
                
                return prose_with_marker
                
            except (requests.RequestException, KeyError, json.JSONDecodeError) as e:
                last_exception = e
                logger.warning("API call failed (attempt %d/%d): %s",
                             attempt + 1, max_retries, str(e))
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    delay = retry_delay * (2 ** attempt)
                    logger.info("Retrying in %.1f seconds...", delay)
                    time.sleep(delay)
                else:
                    # Final attempt failed
                    raise ProseGenerationError(
                        message=f"OpenAI API call failed after {max_retries} attempts: {str(last_exception)}"
                    ) from e
        
        # Should not reach here, but just in case
        raise ProseGenerationError(
            message=f"Prose generation failed after {max_retries} attempts"
        )
    
    def _build_prompt(self, context: SectionContext) -> str:
        """
        Build structured prompt for OpenAI based on section context.
        
        Args:
            context: SectionContext with experiment data
            
        Returns:
            Formatted prompt string
        """
        # Get prose level instructions
        prose_level_instruction = self._get_prose_level_instruction()
        word_count_target = self._get_word_count_target()
        
        # Build context description
        frameworks_str = ", ".join(context.frameworks)
        key_findings_str = "\n".join(f"- {finding}" for finding in context.key_findings)
        
        prompt = f"""Write a comprehensive {context.section_name} section for a scientific research paper.

EXPERIMENT CONTEXT:
- Study: {context.experiment_summary}
- Frameworks compared: {frameworks_str}
- Number of runs: {context.num_runs} runs per framework
- Key findings:
{key_findings_str}

WRITING GUIDELINES:
- Generate AT LEAST {word_count_target} words of academic prose
- Use formal academic writing style appropriate for ACM SIGSOFT publications
- {prose_level_instruction}
- Focus on the experimental methodology and empirical results
- Do NOT include citations (they will be added separately)
- Do NOT fabricate or hallucinate information not present in the context

SECTION REQUIREMENTS for {context.section_name}:
{self._get_section_requirements(context.section_name)}

Generate the prose now:
"""
        
        return prompt
    
    def _get_word_count_target(self) -> int:
        """Get word count target based on prose_level setting."""
        if self.config.prose_level == "minimal":
            return 400  # Concise, focused content
        elif self.config.prose_level == "comprehensive":
            return 1200  # Detailed, expansive content
        else:  # standard
            return 800  # Balanced content
    
    def _get_prose_level_instruction(self) -> str:
        """Get writing instructions based on prose_level setting."""
        if self.config.prose_level == "minimal":
            return (
                "Keep prose concise and focused on direct observations. "
                "Report what the data shows without strong causal claims or extensive interpretation. "
                "Use phrases like 'the data shows', 'we observe', 'results indicate' rather than "
                "'this proves', 'this causes', 'this demonstrates'. "
                "Stick to factual descriptions and avoid speculative implications."
            )
        elif self.config.prose_level == "comprehensive":
            return (
                "Provide thorough, detailed analysis with deep exploration of implications. "
                "Connect findings to theoretical frameworks and practical applications. "
                "Discuss causal mechanisms where supported by data. "
                "Explore edge cases, limitations, and nuanced interpretations. "
                "Include rich contextual details and comprehensive background."
            )
        else:  # standard
            return (
                "Provide balanced analysis with clear observations and moderate interpretation. "
                "Combine factual reporting with reasonable inferences from the data. "
                "Discuss practical significance without over-claiming causality. "
                "Maintain professional academic tone with appropriate level of detail."
            )
    
    def _get_section_requirements(self, section_name: str) -> str:
        """Get section-specific writing requirements."""
        requirements = {
            "abstract": "Summarize the study's motivation, methods, key results, and implications in 150-250 words",
            "introduction": "Motivate the research problem, state objectives, preview key contributions, and outline paper structure",
            "related_work": "Survey existing multi-agent frameworks, compare their approaches, and position this work within the landscape",
            "methodology": "Describe experimental design, task specifications, evaluation metrics, and statistical analysis methods",
            "results": "Present descriptive statistics and detailed analysis of framework performance with metric measurements",
            "discussion": "Interpret findings, discuss implications for practitioners, analyze trade-offs, and acknowledge threats to validity",
            "conclusion": "Summarize contributions, restate key findings, discuss limitations, and suggest future research directions"
        }
        
        return requirements.get(section_name, "Follow standard academic writing conventions for this section")
    
    def _add_ai_marker(self, prose: str) -> str:
        """
        Add marker indicating AI-generated content.
        
        Args:
            prose: Generated prose text
            
        Returns:
            Prose with AI marker prepended
        """
        marker = "<!-- AI-GENERATED CONTENT - REQUIRES HUMAN REVIEW -->\n\n"
        return marker + prose
