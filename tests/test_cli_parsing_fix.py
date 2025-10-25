"""
Integration test demonstrating the CLI JSON parsing fix for BAEs adapter.

This test simulates the exact scenario from the bug report where BAEs CLI
output contains ANSI color codes, emojis, and progress messages before the
final JSON block.
"""

from src.utils.text import parse_json_from_output


def test_baes_cli_output_from_bug_report():
    """
    Test parsing the exact type of output that was failing in production.
    
    This reproduces the scenario from the bug report where:
    - BAEs CLI outputs ANSI color codes and emoji
    - Progress messages appear before JSON
    - The JSON block is buried in the output
    - Previously this would fail with: "Expecting value: line 2 column 1 (char 1)"
    """
    # Simulated output from BAEs CLI (from the bug report)
    cli_output = """
\x1b[94m\x1b[1m🚀 Starting Student System Generation\x1b[0m

\x1b[32m✓\x1b[0m Phase 1: Analyzing requirements...
\x1b[32m✓\x1b[0m Phase 1: Generating domain model...
\x1b[32m✓\x1b[0m Phase 1: Creating artifacts...

{
  "success": true,
  "result": {
    "success": true,
    "message": "Phase 1 artifact generation completed (Phase 2 test generation temporarily disabled)",
    "artifacts_generated": true
  },
  "metadata": {
    "phase": 1,
    "timestamp": "2025-10-25T10:45:56Z"
  }
}
"""
    
    # This should now succeed (previously would fail with JSONDecodeError)
    result, error = parse_json_from_output(cli_output)
    
    # Assertions
    assert error is None, f"Parsing should succeed but got error: {error}"
    assert result is not None, "Result should not be None"
    assert result["success"] is True, "Should extract success field correctly"
    assert result["result"]["message"].startswith("Phase 1 artifact")
    assert result["metadata"]["phase"] == 1
    
    print("✓ Successfully parsed BAEs CLI output that previously failed!")
    print(f"  - Extracted success: {result['success']}")
    print(f"  - Message: {result['result']['message'][:50]}...")
    print(f"  - Phase: {result['metadata']['phase']}")


def test_baes_error_output_with_ansi():
    """
    Test parsing BAEs error output which also contains ANSI codes.
    """
    error_output = """
\x1b[94m\x1b[1m🚀 Starting Request Processing\x1b[0m

\x1b[31m✗\x1b[0m Error: Validation failed
\x1b[31m✗\x1b[0m Configuration incomplete

{
  "success": false,
  "error": "Configuration validation failed: missing required field 'entity_name'",
  "error_type": "ValidationError",
  "traceback": null
}
"""
    
    result, error = parse_json_from_output(error_output)
    
    assert error is None, f"Parsing should succeed but got error: {error}"
    assert result is not None
    assert result["success"] is False
    assert "Configuration validation failed" in result["error"]
    assert result["error_type"] == "ValidationError"
    
    print("✓ Successfully parsed BAEs error output with ANSI codes!")


def test_multiple_json_like_structures():
    """
    Test that we extract the first valid JSON block even when there are
    non-JSON brackets/braces in log messages.
    """
    output = """
[INFO] Initializing system...
[INFO] Loading configuration from {config_dir}
[DEBUG] Array processing complete

{
  "status": "initialized",
  "config_loaded": true
}

[INFO] Done
"""
    
    result, error = parse_json_from_output(output)
    
    assert error is None, f"Should extract valid JSON despite [INFO] brackets: {error}"
    assert result is not None
    assert result["status"] == "initialized"
    assert result["config_loaded"] is True
    
    print("✓ Correctly extracted JSON from output with log brackets!")


if __name__ == "__main__":
    test_baes_cli_output_from_bug_report()
    test_baes_error_output_with_ansi()
    test_multiple_json_like_structures()
    print("\n✅ All integration tests passed!")
