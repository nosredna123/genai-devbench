# CLI JSON Parsing Fix - Implementation Summary

## Problem
The BAEs adapter was failing to parse CLI output when it contained:
- ANSI color codes and escape sequences (e.g., `\x1b[94m`, `\x1b[1m`)
- Emojis and Unicode characters (e.g., 🚀, ✓)
- Human-readable progress messages before the JSON block
- Log prefixes like `[INFO]` that contain brackets

This caused `json.loads(result.stdout)` to fail with:
```
JSONDecodeError: Expecting value: line 2 column 1 (char 1)
```

The adapter would then return zero metrics and rely on lazy reconciliation fallback.

## Solution
Created robust text parsing utilities that:
1. **Strip ANSI codes** - Remove all escape sequences before parsing
2. **Extract JSON blocks** - Find valid JSON boundaries using proper nesting logic
3. **Validate candidates** - Verify extracted text is valid JSON before returning

## Files Changed

### New Files
1. **`src/utils/text.py`** - Text processing utilities
   - `strip_ansi()` - Removes ANSI escape sequences
   - `extract_json_block()` - Finds and extracts valid JSON from mixed text
   - `parse_json_from_output()` - Main helper combining both functions

2. **`tests/test_text_utils.py`** - Comprehensive unit tests (27 tests)
   - Tests for ANSI stripping
   - Tests for JSON extraction from various formats
   - Real-world scenario tests

3. **`tests/test_cli_parsing_fix.py`** - Integration tests (3 tests)
   - Tests with actual BAEs CLI output patterns from bug report
   - Validates the fix handles the original failure case

### Modified Files
1. **`src/adapters/baes_adapter.py`**
   - Import `parse_json_from_output` from `src.utils.text`
   - Replaced direct `json.loads(result.stdout)` calls with robust parsing
   - Improved error logging with cleaned output snippets
   - Removed unused `json` import

## Key Features

### ANSI Stripping
Comprehensive regex pattern that removes all ANSI control sequences:
- SGR codes (colors, bold, italic, etc.)
- Cursor positioning
- Screen clearing commands
- Other terminal control sequences

### JSON Extraction
Smart extraction algorithm that:
- Searches for both `{` (objects) and `[` (arrays)
- Uses proper bracket matching with nesting depth tracking
- Handles escaped quotes and string literals correctly
- Validates candidates by attempting to parse them
- Returns the first valid JSON block found
- Ignores non-JSON brackets in log messages like `[INFO]`

### Error Handling
Enhanced error messages include:
- Parsed error details from both success and error outputs
- Cleaned stdout snippets (first 1000 chars) for debugging
- Raw stdout snippets for comparison
- Clear indication when ANSI cleaning and extraction were applied

## Test Coverage
- **27 unit tests** covering edge cases, ANSI handling, JSON extraction
- **3 integration tests** demonstrating real-world scenarios
- **100% pass rate** on all new tests

## Acceptance Criteria ✓
- [x] Successfully parses BAEs output with ANSI codes and preamble text
- [x] Enhanced logging includes cleaned stdout snippets
- [x] No more false "Failed to parse CLI output" errors for valid JSON
- [x] Maintains backward compatibility with clean JSON output
- [x] Comprehensive test coverage validates all scenarios

## Usage Example
```python
from src.utils.text import parse_json_from_output

cli_output = """
\x1b[94m\x1b[1m🚀 Starting Generation\x1b[0m
{"success": true, "result": "data"}
"""

result, error = parse_json_from_output(cli_output)
# result = {"success": True, "result": "data"}
# error = None
```

## Next Steps (Optional)
1. Consider applying this utility to other adapters (ChatDev, GHSpec) if they face similar issues
2. If BAEs CLI supports `--no-color` or `--json-only` flags, optionally add those to CLI commands
3. Monitor adapter logs to confirm the fix resolves the parsing errors in production runs
