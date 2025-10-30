# genai-devbench Development Guidelines

Auto-generated from all feature plans. Last updated: 2025-10-27

## Active Technologies
- Python 3.11+ + requests (OpenAI API calls), PyYAML (config), pytest (testing) (008-fix-zero-tokens)
- Python 3.11+ + PyYAML (config), pytest (testing), existing codebase (no new external deps) (009-refactor-analysis-module)
- File-based (YAML configs, JSON run data) (009-refactor-analysis-module)
- Python 3.11+ (matching existing genai-devbench codebase) (010-paper-generation)
- File-based (YAML configs, JSON run data, generated LaTeX/Markdown files, PDF/PNG figures) (010-paper-generation)
- File-based (YAML configs, JSON run data, Markdown reports, SVG/PNG figures) (011-enhance-statistical-report)
- Python 3.11+ + SciPy ≥1.11.0, statsmodels ≥0.14.0, NumPy ≥1.24.0, pytest (012-fix-statistical-report)
- File-based (YAML configs, JSON run data, generated Markdown/LaTeX reports) (012-fix-statistical-report)

## Project Structure
```
src/
tests/
```

## Commands
cd src [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] pytest [ONLY COMMANDS FOR ACTIVE TECHNOLOGIES][ONLY COMMANDS FOR ACTIVE TECHNOLOGIES] ruff check .

## Code Style
Python 3.11+: Follow standard conventions

## Recent Changes
- 012-fix-statistical-report: Added Python 3.11+ + SciPy ≥1.11.0, statsmodels ≥0.14.0, NumPy ≥1.24.0, pytest
- 011-enhance-statistical-report: Added Python 3.11+ (matching existing genai-devbench codebase)
- 010-paper-generation: Added Python 3.11+ (matching existing genai-devbench codebase)

<!-- MANUAL ADDITIONS START -->
<!-- MANUAL ADDITIONS END -->
