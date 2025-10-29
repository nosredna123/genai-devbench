"""Unit tests for DocumentFormatter.

Tests LaTeX special character escaping and math mode preservation.
"""

from pathlib import Path
from src.paper_generation.document_formatter import DocumentFormatter


class TestDocumentFormatter:
    """Test LaTeX document formatting."""
    
    def test_escape_basic_characters(self):
        """Test basic special character escaping."""
        formatter = DocumentFormatter()
        
        text = "Cost is $100 & efficiency is 80%"
        result = formatter.escape_latex(text, preserve_math=False)
        
        assert r"\$" in result
        assert r"\&" in result
        assert r"\%" in result
        assert "$" not in result or r"\$" in result
    
    def test_escape_all_special_chars(self):
        """Test all special characters are escaped."""
        formatter = DocumentFormatter()
        
        special_chars = "& % $ # _ { } ~ ^"
        result = formatter.escape_latex(special_chars, preserve_math=False)
        
        # Should not contain unescaped specials
        assert "&" not in result or r"\&" in result
        assert "%" not in result or r"\%" in result
        assert "$" not in result or r"\$" in result
    
    def test_preserve_inline_math(self):
        """Test inline math mode is preserved."""
        formatter = DocumentFormatter()
        
        text = "The cost function is $f(x) = x^2$ where x is input."
        result = formatter.escape_latex(text, preserve_math=True)
        
        # Math content should be preserved
        assert "$f(x) = x^2$" in result
        # Non-math text should be escaped if needed
    
    def test_preserve_display_math(self):
        """Test display math mode is preserved."""
        formatter = DocumentFormatter()
        
        text = "The equation is: $$E = mc^2$$"
        result = formatter.escape_latex(text, preserve_math=True)
        
        assert "$$E = mc^2$$" in result
    
    def test_preserve_equation_environment(self):
        """Test equation environment is preserved."""
        formatter = DocumentFormatter()
        
        text = r"\begin{equation} y = mx + b \end{equation}"
        result = formatter.escape_latex(text, preserve_math=True)
        
        assert r"\begin{equation}" in result
        assert r"\end{equation}" in result
    
    def test_mixed_math_and_text(self):
        """Test escaping with both math and regular text."""
        formatter = DocumentFormatter()
        
        text = "Cost is $100 but the formula is $C = 100$ dollars."
        result = formatter.escape_latex(text, preserve_math=True)
        
        # First $100 should be escaped
        assert r"\$100" in result
        # Math formula should be preserved
        assert "$C = 100$" in result
    
    def test_format_table(self):
        """Test LaTeX table formatting."""
        formatter = DocumentFormatter()
        
        result = formatter.format_table(
            headers=["Framework", "Cost"],
            rows=[["ChatDev", "$10"], ["MetaGPT", "$20"]],
            caption="Comparison table",
            label="tab:comparison"
        )
        
        assert r"\begin{table}" in result
        assert r"\caption{Comparison table}" in result
        assert r"\label{tab:comparison}" in result
        assert r"\toprule" in result
        assert r"\midrule" in result
        assert r"\bottomrule" in result
        assert "Framework" in result
        assert "ChatDev" in result
    
    def test_format_figure(self):
        """Test LaTeX figure formatting."""
        formatter = DocumentFormatter()
        
        img_path = Path("figures/plot.pdf")
        result = formatter.format_figure(
            image_path=img_path,
            caption="Test figure",
            label="fig:test",
            width="0.8\\columnwidth"
        )
        
        assert r"\begin{figure}" in result
        assert r"\includegraphics" in result
        assert "figures/plot.pdf" in result
        assert r"\caption{Test figure}" in result
        assert r"\label{fig:test}" in result
    
    def test_wrap_section(self):
        """Test section heading wrapping."""
        formatter = DocumentFormatter()
        
        result = formatter.wrap_section(
            title="Introduction",
            content="This is the intro.",
            level=1
        )
        
        assert r"\section{Introduction}" in result
        assert "This is the intro." in result
    
    def test_wrap_subsection(self):
        """Test subsection heading."""
        formatter = DocumentFormatter()
        
        result = formatter.wrap_section(
            title="Background",
            content="Content here.",
            level=2
        )
        
        assert r"\subsection{Background}" in result
    
    def test_format_complete_document(self):
        """Test complete LaTeX document formatting."""
        formatter = DocumentFormatter()
        
        result = formatter.format_latex_document(
            title="Test Paper",
            authors=["Alice", "Bob"],
            abstract="This is the abstract.",
            sections={
                "introduction": "Intro content",
                "conclusion": "Conclusion content"
            }
        )
        
        assert r"\documentclass[sigconf]{acmart}" in result
        assert r"\title{Test Paper}" in result
        assert r"\author{Alice}" in result
        assert r"\author{Bob}" in result
        assert r"\begin{abstract}" in result
        assert "This is the abstract." in result
        assert r"\section{Introduction}" in result
        assert r"\section{Conclusion}" in result
    
    def test_empty_text_escaping(self):
        """Test escaping empty string."""
        formatter = DocumentFormatter()
        
        result = formatter.escape_latex("", preserve_math=False)
        assert result == ""
    
    def test_no_special_chars(self):
        """Test text without special characters passes through."""
        formatter = DocumentFormatter()
        
        text = "This is plain text with no special characters."
        result = formatter.escape_latex(text, preserve_math=False)
        
        assert result == text
    
    def test_backslash_handling(self):
        """Test backslash is properly escaped."""
        formatter = DocumentFormatter()
        
        text = "Path is C:\\Users\\test"
        result = formatter.escape_latex(text, preserve_math=False)
        
        # Backslashes should be escaped
        assert r"\textbackslash" in result or "\\\\" in result
