"""LaTeX document formatting and special character escaping.

Handles LaTeX special character escaping, math mode preservation,
and ACM template integration. Ensures generated text compiles correctly.

Constitution Principle II: Clarity & Transparency - explicit escaping rules
Constitution Principle VII: Fail-Fast Philosophy - prevent compilation errors
"""

import re
import logging
from pathlib import Path
from typing import Optional


logger = logging.getLogger(__name__)


class DocumentFormatter:
    """Handles LaTeX document formatting and special character escaping.
    
    Provides utilities for:
    - Escaping LaTeX special characters
    - Preserving math mode delimiters
    - Formatting complete documents with ACM template
    - Handling tables and figures in LaTeX syntax
    """
    
    # LaTeX special characters that need escaping
    # Order matters: backslash must be first!
    SPECIAL_CHARS = [
        ('\\', r'\textbackslash{}'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
        ('^', r'\textasciicircum{}'),
    ]
    
    # Patterns for detecting math mode (don't escape inside these)
    MATH_PATTERNS = [
        (re.compile(r'\$\$.*?\$\$', re.DOTALL), 'display_math'),  # $$...$$ 
        (re.compile(r'\$.*?\$'), 'inline_math'),                   # $...$
        (re.compile(r'\\begin\{equation\}.*?\\end\{equation\}', re.DOTALL), 'equation'),
        (re.compile(r'\\begin\{align\}.*?\\end\{align\}', re.DOTALL), 'align'),
    ]
    
    def __init__(self):
        """Initialize document formatter."""
    
    def escape_latex(self, text: str, preserve_math: bool = True) -> str:
        """Escape LaTeX special characters in text.
        
        Args:
            text: Input text that may contain special characters
            preserve_math: If True, don't escape text inside math mode delimiters
        
        Returns:
            Text with special characters escaped for LaTeX
        
        Example:
            Input: "Cost is $100 & efficiency is 80%"
            Output (with escaping): Cost is \\$100 \\& efficiency is 80\\%
        """
        if preserve_math:
            # Extract math regions first
            math_regions = []
            for pattern, _ in self.MATH_PATTERNS:
                for match in pattern.finditer(text):
                    math_regions.append((match.start(), match.end(), match.group(0)))
            
            # Sort by start position
            math_regions.sort(key=lambda x: x[0])
            
            # Process text in chunks, escaping non-math regions
            result = []
            last_pos = 0
            
            for start, end, math_text in math_regions:
                # Escape text before math region
                if start > last_pos:
                    chunk = text[last_pos:start]
                    result.append(self._escape_chunk(chunk))
                
                # Preserve math region as-is
                result.append(math_text)
                last_pos = end
            
            # Escape remaining text after last math region
            if last_pos < len(text):
                chunk = text[last_pos:]
                result.append(self._escape_chunk(chunk))
            
            return ''.join(result)
        
        else:
            # Escape entire text
            return self._escape_chunk(text)
    
    def _escape_chunk(self, text: str) -> str:
        """Escape special characters in a text chunk (no math mode).
        
        Args:
            text: Plain text to escape
        
        Returns:
            Escaped text
        """
        result = text
        for char, escaped in self.SPECIAL_CHARS:
            result = result.replace(char, escaped)
        return result
    
    def format_latex_document(
        self,
        title: str,
        authors: list[str],
        abstract: str,
        sections: dict[str, str],
        references: Optional[str] = None
    ) -> str:
        """Format complete LaTeX document with ACM template.
        
        Args:
            title: Paper title
            authors: List of author names
            abstract: Abstract text
            sections: Dictionary mapping section names to content
            references: Optional bibliography content
        
        Returns:
            Complete LaTeX document source
        """
        # Build author list for ACM format
        author_latex = "\n".join([
            f"\\author{{{name}}}" for name in authors
        ])
        
        # Build section content
        section_latex = []
        for section_name, content in sections.items():
            # Convert section name to title case
            title = section_name.replace('_', ' ').title()
            section_latex.append(f"\\section{{{title}}}\n{content}\n")
        
        # Assemble document
        doc = f"""\\documentclass[sigconf]{{acmart}}

% Packages
\\usepackage{{booktabs}}  % Professional tables
\\usepackage{{graphicx}}  % Figures

% Paper metadata
\\title{{{title}}}

{author_latex}

\\begin{{document}}

\\maketitle

\\begin{{abstract}}
{abstract}
\\end{{abstract}}

{"".join(section_latex)}

"""
        
        # Add references if provided
        if references:
            doc += f"""
\\bibliographystyle{{ACM-Reference-Format}}
\\bibliography{{{references}}}
"""
        
        doc += "\\end{document}\n"
        
        return doc
    
    def format_table(
        self,
        headers: list[str],
        rows: list[list[str]],
        caption: str,
        label: str
    ) -> str:
        """Format table in LaTeX booktabs style.
        
        Args:
            headers: Column headers
            rows: Table data rows
            caption: Table caption
            label: Table label for cross-referencing
        
        Returns:
            LaTeX table code
        """
        num_cols = len(headers)
        col_spec = 'l' * num_cols  # Left-aligned columns
        
        # Build header row
        header_row = ' & '.join(headers) + ' \\\\'
        
        # Build data rows
        data_rows = '\n'.join([
            ' & '.join(row) + ' \\\\' 
            for row in rows
        ])
        
        table = f"""\\begin{{table}}[t]
\\caption{{{caption}}}
\\label{{{label}}}
\\begin{{tabular}}{{{col_spec}}}
\\toprule
{header_row}
\\midrule
{data_rows}
\\bottomrule
\\end{{tabular}}
\\end{{table}}
"""
        return table
    
    def format_figure(
        self,
        image_path: Path,
        caption: str,
        label: str,
        width: str = "0.8\\columnwidth"
    ) -> str:
        """Format figure in LaTeX.
        
        Handles missing figures by generating placeholder text instead of
        \\includegraphics command to prevent LaTeX compilation errors.
        
        Args:
            image_path: Path to figure file (relative to LaTeX source)
            caption: Figure caption
            label: Figure label for cross-referencing
            width: Figure width (LaTeX dimension)
        
        Returns:
            LaTeX figure code
        """
        # Check if figure file exists (handle both absolute and relative paths)
        if not image_path.exists():
            # Generate placeholder for missing figure
            logger.warning("Figure not found: %s - inserting placeholder", image_path)
            figure = f"""\\begin{{figure}}[t]
\\centering
\\fbox{{\\parbox[c][2in]{{0.8\\columnwidth}}{{%
\\centering\\textbf{{[FIGURE MISSING]}}\\\\[0.5em]
Expected file: \\texttt{{{image_path.name}}}\\\\[0.5em]
\\textit{{Caption:}} {caption}
}}}}
\\caption{{{caption}}}
\\label{{{label}}}
\\end{{figure}}
"""
        else:
            # Normal figure with includegraphics
            figure = f"""\\begin{{figure}}[t]
\\centering
\\includegraphics[width={width}]{{{image_path}}}
\\caption{{{caption}}}
\\label{{{label}}}
\\end{{figure}}
"""
        return figure
    
    def wrap_section(self, title: str, content: str, level: int = 1) -> str:
        """Wrap content in LaTeX section heading.
        
        Args:
            title: Section title
            content: Section content
            level: Section level (1=section, 2=subsection, etc.)
        
        Returns:
            LaTeX section code
        """
        section_commands = ['section', 'subsection', 'subsubsection', 'paragraph']
        cmd = section_commands[min(level - 1, len(section_commands) - 1)]
        
        return f"\\{cmd}{{{title}}}\n{content}\n"
