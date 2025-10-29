"""Citation placeholder insertion and rendering.

Handles insertion of citation placeholders to avoid AI hallucinations
of non-existent references. Detects framework names and research claims,
inserts bold placeholders for manual citation filling.

Constitution Principle II: Clarity & Transparency - explicit placeholders
Constitution Principle VII: Fail-Fast Philosophy - prevent hallucinations
"""

import re


class CitationHandler:
    """Manages citation placeholders in AI-generated prose.
    
    Prevents hallucinations by inserting clear placeholders instead of
    allowing AI to generate fake references. Placeholders are visually
    distinct in PDF output and include guidance for manual filling.
    """
    
    # Framework name patterns (case-insensitive)
    FRAMEWORK_PATTERNS = [
        r'\bChatDev\b',
        r'\bMetaGPT\b',
        r'\bAutoGen\b',
        r'\bLangChain\b',
        r'\bLangGraph\b',
        r'\bCrewAI\b',
        r'\bOpenAI\s+Swarm\b',
        r'\bGPT-?Engineer\b',
        r'\bDevOpsGPT\b',
        r'\bDevika\b'
    ]
    
    # Research claim patterns that need citations
    CLAIM_PATTERNS = [
        # Comparative claims
        r'studies have shown',
        r'research has demonstrated',
        r'previous work',
        r'prior research',
        r'recent studies',
        r'empirical evidence',
        
        # Performance claims
        r'has been shown to',
        r'is known to',
        r'is widely used',
        r'is commonly employed',
        
        # Framework capabilities
        r'supports multi-agent',
        r'enables autonomous',
        r'provides',
        r'implements',
        r'utilizes',
        r'leverages'
    ]
    
    def __init__(self):
        """Initialize citation handler with compiled regex patterns."""
        # Compile framework patterns (case-insensitive)
        self.framework_regexes = [
            re.compile(pattern, re.IGNORECASE) 
            for pattern in self.FRAMEWORK_PATTERNS
        ]
        
        # Compile claim patterns (case-insensitive)
        self.claim_regexes = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.CLAIM_PATTERNS
        ]
    
    def insert_placeholders(self, text: str) -> str:
        """Insert citation placeholders in prose text.
        
        Detects framework mentions and research claims, inserts
        **[CITE: description]** placeholders for manual filling.
        
        Args:
            text: Input prose text (Markdown or plain text)
        
        Returns:
            Text with citation placeholders inserted
        
        Example:
            Input: "ChatDev supports multi-agent collaboration."
            Output: "ChatDev **[CITE: ChatDev framework]** supports 
                    multi-agent collaboration **[CITE: multi-agent claim]**."
        """
        result = text
        
        # Track positions we've already inserted citations
        # (avoid duplicate placeholders for same match)
        inserted_positions = set()
        
        # Insert framework citations
        for pattern in self.framework_regexes:
            matches = list(pattern.finditer(result))
            
            # Process matches in reverse order to preserve positions
            for match in reversed(matches):
                start, end = match.span()
                
                # Skip if we already inserted at this position
                if start in inserted_positions:
                    continue
                
                framework_name = match.group(0)
                placeholder = f" **[CITE: {framework_name} framework]**"
                
                # Insert after the framework name
                result = result[:end] + placeholder + result[end:]
                inserted_positions.add(start)
        
        # Insert claim citations
        for pattern in self.claim_regexes:
            matches = list(pattern.finditer(result))
            
            for match in reversed(matches):
                start, end = match.span()
                
                # Skip if we already inserted nearby
                if any(abs(start - pos) < 50 for pos in inserted_positions):
                    continue
                
                claim_text = match.group(0)
                placeholder = f" **[CITE: {claim_text}]**"
                
                # Insert after the claim phrase
                result = result[:end] + placeholder + result[end:]
                inserted_positions.add(start)
        
        return result
    
    def render_latex(self, text: str) -> str:
        """Render citation placeholders in LaTeX format with bold styling.
        
        Converts **[CITE: description]** to LaTeX \textbf{[CITE: description]}
        for visual distinction in compiled PDF.
        
        Args:
            text: Text with Markdown-style placeholders
        
        Returns:
            Text with LaTeX-formatted citation placeholders
        """
        # Pattern matches: **[CITE: anything]**
        pattern = re.compile(r'\*\*\[CITE:(.*?)\]\*\*')
        
        # Replace with LaTeX bold command
        result = pattern.sub(r'\\textbf{[CITE:\1]}', text)
        
        return result
    
    def count_placeholders(self, text: str) -> int:
        """Count citation placeholders in text.
        
        Args:
            text: Text to analyze
        
        Returns:
            Number of citation placeholders found
        """
        pattern = re.compile(r'\*\*\[CITE:.*?\]\*\*')
        matches = pattern.findall(text)
        return len(matches)
    
    def extract_placeholders(self, text: str) -> list[str]:
        """Extract all citation placeholder descriptions.
        
        Args:
            text: Text to analyze
        
        Returns:
            List of citation descriptions (without markup)
        
        Example:
            Input: "Text **[CITE: ChatDev]** more **[CITE: claim]**"
            Output: ["ChatDev", "claim"]
        """
        pattern = re.compile(r'\*\*\[CITE:(.*?)\]\*\*')
        matches = pattern.findall(text)
        
        # Strip whitespace from descriptions
        return [match.strip() for match in matches]
