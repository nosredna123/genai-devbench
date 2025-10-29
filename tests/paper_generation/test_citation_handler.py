"""Unit tests for CitationHandler.

Tests placeholder insertion patterns and LaTeX rendering.
"""

from src.paper_generation.citation_handler import CitationHandler


class TestCitationHandler:
    """Test citation placeholder handling."""
    
    def test_framework_detection(self):
        """Test framework names are detected and get placeholders."""
        handler = CitationHandler()
        
        text = "ChatDev is a framework for multi-agent development."
        result = handler.insert_placeholders(text)
        
        assert "**[CITE: ChatDev framework]**" in result
    
    def test_multiple_frameworks(self):
        """Test multiple frameworks get placeholders."""
        handler = CitationHandler()
        
        text = "We compared ChatDev, MetaGPT, and AutoGen."
        result = handler.insert_placeholders(text)
        
        assert "**[CITE: ChatDev framework]**" in result
        assert "**[CITE: MetaGPT framework]**" in result
        assert "**[CITE: AutoGen framework]**" in result
    
    def test_claim_detection(self):
        """Test research claims get citation placeholders."""
        handler = CitationHandler()
        
        text = "Studies have shown that multi-agent systems improve code quality."
        result = handler.insert_placeholders(text)
        
        assert "**[CITE: studies have shown]**" in result or "**[CITE:" in result
    
    def test_case_insensitive_matching(self):
        """Test framework matching is case-insensitive."""
        handler = CitationHandler()
        
        text = "chatdev and METAGPT are popular frameworks."
        result = handler.insert_placeholders(text)
        
        # Should detect both despite different casing
        assert result.count("**[CITE:") >= 2
    
    def test_no_duplicate_placeholders(self):
        """Test same framework doesn't get multiple placeholders at same position."""
        handler = CitationHandler()
        
        text = "ChatDev is great. ChatDev works well."
        result = handler.insert_placeholders(text)
        
        # Should have 2 placeholders (one per mention)
        assert result.count("**[CITE: ChatDev") == 2
    
    def test_render_latex(self):
        """Test Markdown placeholders converted to LaTeX."""
        handler = CitationHandler()
        
        text = "Some text **[CITE: ChatDev framework]** more text."
        result = handler.render_latex(text)
        
        assert r"\textbf{[CITE: ChatDev framework]}" in result
        assert "**[CITE:" not in result  # Markdown syntax removed
    
    def test_count_placeholders(self):
        """Test counting citation placeholders."""
        handler = CitationHandler()
        
        text = "Text **[CITE: one]** more **[CITE: two]** end."
        count = handler.count_placeholders(text)
        
        assert count == 2
    
    def test_count_placeholders_none(self):
        """Test counting when no placeholders present."""
        handler = CitationHandler()
        
        text = "Plain text with no citations."
        count = handler.count_placeholders(text)
        
        assert count == 0
    
    def test_extract_placeholders(self):
        """Test extracting placeholder descriptions."""
        handler = CitationHandler()
        
        text = "Text **[CITE: ChatDev]** and **[CITE: research claim]** end."
        descriptions = handler.extract_placeholders(text)
        
        assert len(descriptions) == 2
        assert "ChatDev" in descriptions
        assert "research claim" in descriptions
    
    def test_framework_patterns_comprehensive(self):
        """Test all framework patterns are detected."""
        handler = CitationHandler()
        
        frameworks = [
            "ChatDev",
            "MetaGPT",
            "AutoGen",
            "LangChain",
            "LangGraph",
            "CrewAI",
            "OpenAI Swarm",
            "GPT-Engineer",
            "DevOpsGPT",
            "Devika"
        ]
        
        for fw in frameworks:
            text = f"We used {fw} for this experiment."
            result = handler.insert_placeholders(text)
            assert "**[CITE:" in result, f"Failed to detect {fw}"
    
    def test_preserve_original_text(self):
        """Test original text is preserved around placeholders."""
        handler = CitationHandler()
        
        text = "We used ChatDev to build applications."
        result = handler.insert_placeholders(text)
        
        # Original words should still be present
        assert "We used ChatDev" in result
        assert "to build applications" in result
    
    def test_empty_text(self):
        """Test handling of empty text."""
        handler = CitationHandler()
        
        result = handler.insert_placeholders("")
        assert result == ""
        
        count = handler.count_placeholders("")
        assert count == 0
