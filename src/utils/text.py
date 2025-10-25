"""
Text processing utilities for adapter output parsing.

Provides robust helpers for cleaning and extracting JSON from CLI outputs
that may contain ANSI escape sequences, color codes, progress messages, etc.
"""

import re
import json
from typing import Optional, Tuple


# ANSI escape sequence pattern
# Matches: ESC [ ... m (SGR - colors, styles)
#          ESC [ ... J (clear screen)
#          ESC [ ... K (clear line)
#          ESC [ ... H (cursor position)
#          and other common ANSI control sequences
ANSI_ESCAPE_RE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences from text.
    
    Args:
        text: Input text potentially containing ANSI codes
        
    Returns:
        Text with all ANSI escape sequences removed
        
    Examples:
        >>> strip_ansi("\\x1b[94m\\x1b[1mHello\\x1b[0m")
        'Hello'
        >>> strip_ansi("Plain text")
        'Plain text'
    """
    if not text:
        return text
    return ANSI_ESCAPE_RE.sub('', text)


def extract_json_block(text: str) -> Optional[str]:
    """Extract the first complete JSON object or array from text.
    
    Searches for valid JSON blocks by trying each occurrence of '{' or '['
    and attempting to find matching closing delimiters with proper nesting.
    Returns the first valid JSON block found (object or array).
    
    Args:
        text: Input text potentially containing a JSON block
        
    Returns:
        The extracted JSON text, or None if no valid JSON block found
        
    Examples:
        >>> extract_json_block('Log message\\n{"key": "value"}\\nMore text')
        '{"key": "value"}'
        >>> extract_json_block('No JSON here')
        None
    """
    if not text:
        return None
    
    def find_matching_delimiter(text: str, start_pos: int, open_char: str, close_char: str) -> Optional[int]:
        """Find the position of the matching closing delimiter."""
        depth = 0
        in_string = False
        escape_next = False
        
        for i in range(start_pos, len(text)):
            char = text[i]
            
            # Handle string literals (ignore delimiters inside strings)
            if escape_next:
                escape_next = False
                continue
            
            if char == '\\':
                escape_next = True
                continue
            
            if char == '"':
                in_string = not in_string
                continue
            
            if in_string:
                continue
            
            # Track nesting depth
            if char == open_char:
                depth += 1
            elif char == close_char:
                depth -= 1
                if depth == 0:
                    return i
        
        return None
    
    # Search for both { and [ and return whichever valid JSON comes first
    best_candidate = None
    best_pos = len(text)
    
    # Try to find JSON objects
    pos = 0
    while pos < len(text):
        brace_pos = text.find('{', pos)
        if brace_pos == -1 or brace_pos >= best_pos:
            break
        
        end_pos = find_matching_delimiter(text, brace_pos, '{', '}')
        if end_pos is not None:
            candidate = text[brace_pos:end_pos + 1]
            # Quick validation: try to parse it
            try:
                json.loads(candidate)
                if brace_pos < best_pos:
                    best_candidate = candidate
                    best_pos = brace_pos
                break  # Found the first valid object
            except json.JSONDecodeError:
                # Not valid JSON, continue searching
                pos = brace_pos + 1
                continue
        else:
            pos = brace_pos + 1
    
    # Try to find JSON arrays
    pos = 0
    while pos < len(text):
        bracket_pos = text.find('[', pos)
        if bracket_pos == -1 or bracket_pos >= best_pos:
            break
        
        end_pos = find_matching_delimiter(text, bracket_pos, '[', ']')
        if end_pos is not None:
            candidate = text[bracket_pos:end_pos + 1]
            # Quick validation: try to parse it
            try:
                json.loads(candidate)
                if bracket_pos < best_pos:
                    best_candidate = candidate
                    best_pos = bracket_pos
                break  # Found the first valid array
            except json.JSONDecodeError:
                # Not valid JSON, continue searching
                pos = bracket_pos + 1
                continue
        else:
            pos = bracket_pos + 1
    
    return best_candidate


def parse_json_from_output(
    raw_output: str,
    clean_ansi: bool = True
) -> Tuple[Optional[dict], Optional[str]]:
    """Robustly parse JSON from CLI output that may contain ANSI codes and preamble text.
    
    This is the main helper for adapter CLI output parsing. It:
    1. Optionally strips ANSI escape sequences
    2. Attempts to extract the JSON block boundaries
    3. Tries to parse the JSON
    4. Falls back to parsing the entire cleaned output if block extraction fails
    5. Returns both the parsed result and any error message
    
    Args:
        raw_output: Raw CLI output text
        clean_ansi: Whether to strip ANSI codes (default: True)
        
    Returns:
        Tuple of (parsed_dict, error_message)
        - On success: (dict, None)
        - On failure: (None, error_string)
        
    Examples:
        >>> output = '\\x1b[94mStarting...\\x1b[0m\\n{"success": true}'
        >>> result, error = parse_json_from_output(output)
        >>> result
        {'success': True}
        >>> error is None
        True
    """
    if not raw_output:
        return None, "Empty output"
    
    # Step 1: Strip ANSI if requested
    cleaned = strip_ansi(raw_output).strip() if clean_ansi else raw_output.strip()
    
    # Step 2: Try to extract JSON block
    json_block = extract_json_block(cleaned)
    parse_target = json_block if json_block is not None else cleaned
    
    # Step 3: Attempt to parse
    try:
        result = json.loads(parse_target)
        return result, None
    except json.JSONDecodeError as e:
        # Return detailed error with snippets for debugging
        error_msg = (
            f"JSONDecodeError: {e}\n"
            f"Cleaned output snippet (first 500 chars): {cleaned[:500]}\n"
            f"Raw output snippet (first 500 chars): {raw_output[:500]}"
        )
        return None, error_msg
