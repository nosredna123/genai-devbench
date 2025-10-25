"""
Unit tests for text processing utilities.

Tests ANSI stripping and JSON extraction from CLI outputs.
"""

from src.utils.text import strip_ansi, extract_json_block, parse_json_from_output


class TestStripAnsi:
    """Test ANSI escape sequence removal."""
    
    def test_strip_basic_color_codes(self):
        """Should remove basic SGR color codes."""
        input_text = "\x1b[94m\x1b[1mHello\x1b[0m World"
        expected = "Hello World"
        assert strip_ansi(input_text) == expected
    
    def test_strip_complex_ansi_sequences(self):
        """Should remove various ANSI control sequences."""
        # Color, bold, clear line, cursor position
        input_text = "\x1b[31mRed\x1b[0m \x1b[2KCleared\x1b[H\x1b[J"
        result = strip_ansi(input_text)
        assert "\x1b" not in result
        assert "Red" in result
        assert "Cleared" in result
    
    def test_strip_ansi_with_emoji(self):
        """Should preserve emoji while removing ANSI codes."""
        input_text = "\x1b[94m\x1b[1m🚀 Starting\x1b[0m"
        result = strip_ansi(input_text)
        assert result == "🚀 Starting"
    
    def test_plain_text_unchanged(self):
        """Should return plain text unchanged."""
        plain = "No ANSI codes here"
        assert strip_ansi(plain) == plain
    
    def test_empty_string(self):
        """Should handle empty string."""
        assert strip_ansi("") == ""
    
    def test_none_input(self):
        """Should handle None input."""
        assert strip_ansi(None) is None


class TestExtractJsonBlock:
    """Test JSON block extraction from mixed text."""
    
    def test_extract_simple_object(self):
        """Should extract simple JSON object."""
        text = 'Preamble text\n{"key": "value"}\nTrailing text'
        result = extract_json_block(text)
        assert result == '{"key": "value"}'
    
    def test_extract_nested_object(self):
        """Should extract nested JSON object."""
        text = 'Log: Starting\n{"outer": {"inner": "value"}}\nDone'
        result = extract_json_block(text)
        assert result == '{"outer": {"inner": "value"}}'
    
    def test_extract_array(self):
        """Should extract JSON array."""
        text = 'Info: [1, 2, 3]\nMore text'
        result = extract_json_block(text)
        assert result == '[1, 2, 3]'
    
    def test_prefer_object_over_array(self):
        """Should prefer object when both present and object comes first."""
        text = '{"obj": true} and [1, 2]'
        result = extract_json_block(text)
        assert result == '{"obj": true}'
    
    def test_prefer_array_when_first(self):
        """Should extract array when it appears before object."""
        text = '[1, 2] and {"obj": true}'
        result = extract_json_block(text)
        assert result == '[1, 2]'
    
    def test_no_json_returns_none(self):
        """Should return None when no JSON boundaries found."""
        text = "No JSON here at all"
        assert extract_json_block(text) is None
    
    def test_unmatched_braces_returns_none(self):
        """Should return None when braces/brackets don't match."""
        text = "{ incomplete"
        assert extract_json_block(text) is None
    
    def test_empty_input(self):
        """Should handle empty input."""
        assert extract_json_block("") is None
        assert extract_json_block(None) is None


class TestParseJsonFromOutput:
    """Test end-to-end JSON parsing from CLI output."""
    
    def test_parse_clean_json(self):
        """Should parse clean JSON without any noise."""
        output = '{"success": true, "result": "data"}'
        result, error = parse_json_from_output(output)
        assert error is None
        assert result == {"success": True, "result": "data"}
    
    def test_parse_json_with_ansi(self):
        """Should parse JSON with ANSI color codes."""
        output = '\x1b[94m\x1b[1m🚀 Starting\x1b[0m\n{"success": true}\n'
        result, error = parse_json_from_output(output)
        assert error is None
        assert result == {"success": True}
    
    def test_parse_json_with_preamble(self):
        """Should parse JSON with human-readable preamble."""
        output = """
        [INFO] Initializing system...
        [INFO] Processing request...
        {"success": true, "message": "Complete"}
        [INFO] Done
        """
        result, error = parse_json_from_output(output)
        assert error is None
        assert result["success"] is True
        assert result["message"] == "Complete"
    
    def test_parse_complex_cli_output(self):
        """Should parse realistic BAEs CLI output with ANSI + logs + JSON."""
        output = (
            '\x1b[94m\x1b[1m🚀 Starting Student System Generation\x1b[0m\n'
            '\x1b[32m✓\x1b[0m Phase 1: Generating artifacts...\n'
            '\x1b[32m✓\x1b[0m Phase 2: Running tests...\n'
            '{\n'
            '  "success": true,\n'
            '  "result": {\n'
            '    "success": true,\n'
            '    "message": "Phase 1 artifact generation completed"\n'
            '  }\n'
            '}\n'
        )
        result, error = parse_json_from_output(output)
        assert error is None
        assert result["success"] is True
        assert result["result"]["message"] == "Phase 1 artifact generation completed"
    
    def test_parse_array_output(self):
        """Should parse JSON array output."""
        output = 'Starting...\n[{"id": 1}, {"id": 2}]\nDone'
        result, error = parse_json_from_output(output)
        assert error is None
        assert len(result) == 2
        assert result[0]["id"] == 1
    
    def test_invalid_json_returns_error(self):
        """Should return error for invalid JSON."""
        output = '\x1b[94mStarting\x1b[0m\n{invalid json}\nFailed'
        result, error = parse_json_from_output(output)
        assert result is None
        assert error is not None
        assert "JSONDecodeError" in error
    
    def test_no_json_returns_error(self):
        """Should return error when no JSON found."""
        output = "Just plain text, no JSON"
        result, error = parse_json_from_output(output)
        assert result is None
        assert error is not None
    
    def test_empty_output_returns_error(self):
        """Should return error for empty output."""
        result, error = parse_json_from_output("")
        assert result is None
        assert error == "Empty output"
    
    def test_error_includes_snippets(self):
        """Error message should include output snippets for debugging."""
        output = "Not JSON" * 100  # Make it long
        result, error = parse_json_from_output(output)
        assert result is None
        assert "Cleaned output snippet" in error
        assert "Raw output snippet" in error
    
    def test_disable_ansi_cleaning(self):
        """Should support disabling ANSI cleaning."""
        # With ANSI codes inside the JSON that would break parsing if not cleaned
        output = '{"success": \x1b[94mtrue\x1b[0m}'
        
        # With cleaning (default) - ANSI codes are stripped before parsing
        result_clean, _ = parse_json_from_output(output, clean_ansi=True)
        assert result_clean is not None
        assert result_clean["success"] is True
        
        # Without cleaning (should fail because ANSI codes corrupt the JSON)
        result_no_clean, error = parse_json_from_output(output, clean_ansi=False)
        assert result_no_clean is None
        assert error is not None


class TestRealWorldScenarios:
    """Test with real-world adapter output scenarios."""
    
    def test_baes_successful_output(self):
        """Should parse typical successful BAEs output."""
        output = """
\x1b[94m\x1b[1m🚀 Starting Student System Generation\x1b[0m

\x1b[32m✓\x1b[0m Analyzing requirements...
\x1b[32m✓\x1b[0m Generating domain model...
\x1b[32m✓\x1b[0m Creating artifacts...

{
  "success": true,
  "result": {
    "success": true,
    "message": "Phase 1 artifact generation completed (Phase 2 test generation temporarily disabled)",
    "artifacts": {
      "domain_model": "generated",
      "entity_classes": ["Student", "Course"]
    }
  },
  "metadata": {
    "phase": 1,
    "timestamp": "2025-10-25T10:45:56Z"
  }
}
"""
        result, error = parse_json_from_output(output)
        assert error is None
        assert result["success"] is True
        assert result["result"]["message"].startswith("Phase 1 artifact")
        assert "Student" in result["result"]["artifacts"]["entity_classes"]
    
    def test_baes_error_output(self):
        """Should parse BAEs error output."""
        output = """
\x1b[94m\x1b[1m🚀 Starting Request Processing\x1b[0m

\x1b[31m✗\x1b[0m Error: Invalid configuration

{
  "success": false,
  "error": "Configuration validation failed: missing required field 'entity_name'",
  "error_type": "ValidationError"
}
"""
        result, error = parse_json_from_output(output)
        assert error is None
        assert result["success"] is False
        assert "Configuration validation failed" in result["error"]
    
    def test_multi_line_json_with_unicode(self):
        """Should handle multi-line JSON with unicode characters."""
        output = """
Progress: ▓▓▓▓▓▓▓▓▓▓ 100%

{
  "success": true,
  "message": "Task completed ✓",
  "data": {
    "emoji": "🎉",
    "unicode": "测试"
  }
}
"""
        result, error = parse_json_from_output(output)
        assert error is None
        assert result["success"] is True
        assert result["data"]["emoji"] == "🎉"
        assert result["data"]["unicode"] == "测试"
