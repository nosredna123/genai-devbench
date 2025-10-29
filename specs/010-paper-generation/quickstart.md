# Quickstart: Camera-Ready Paper Generation

**Feature**: 010-paper-generation  
**Audience**: Researchers using genai-devbench  
**Time**: 10 minutes to generate first paper

**Important**: This feature generates scientific papers from completed experiment results. The AI model (`gpt-5-mini`) is used **only for paper prose generation**, not for experiment execution.

---

## Prerequisites

1. **Completed Experiment**: You must have a completed experiment with analysis results
2. **Python 3.11+**: Check with `python --version`
3. **OpenAI API Key**: Set `OPENAI_API_KEY` environment variable (for paper generation only)
4. **Pandoc ≥2.0** (optional, for PDF generation): Install via package manager
5. **LaTeX Distribution** (optional, for PDF generation): TeX Live or MiKTeX

**Note**: Pandoc and LaTeX are only needed for final PDF compilation. You can generate Markdown-only papers without them.

---

## Quick Start (5 minutes)

### Step 1: Set API Key

```bash
export OPENAI_API_KEY="sk-..."  # Your OpenAI API key
```

### Step 2: Generate Paper

```bash
# Navigate to genai-devbench root
cd /path/to/genai-devbench

# Generate camera-ready paper
python scripts/generate_paper.py /path/to/your/experiment
```

This will:
- ✅ Generate AI-powered prose for all sections (≥800 words each)
- ✅ Export publication-quality figures (PDF + PNG 300 DPI)
- ✅ Insert citation placeholders (no hallucinated references)
- ✅ Compile to ACM SIGSOFT format PDF
- ✅ Complete in ~2-3 minutes

### Step 3: Review Output

```bash
# Paper output is in ./paper_output/
cd paper_output

# Check generated files
ls -lh
# main.md         # Markdown source
# main.tex        # LaTeX source
# main.pdf        # Camera-ready PDF ✅
# figures/        # PDF + PNG figures
# acm_template/   # ACM template files
```

### Step 4: Review AI-Generated Content

**IMPORTANT**: All prose is AI-generated and marked for manual review.

Open `main.pdf` and look for bold `[AI-GENERATED - REVIEW REQUIRED]` markers. You MUST:
- ✅ Verify factual accuracy
- ✅ Check scientific validity
- ✅ Fill citation placeholders: `[CITE: description]` → real citations
- ✅ Validate causal claims

**Do NOT submit without manual review!**

---

## Common Use Cases

### Generate Markdown Only (Skip PDF)

```bash
python scripts/generate_paper.py /path/to/experiment --skip-latex
```

**Use when**: Pandoc/LaTeX not installed, or you want to edit Markdown before PDF compilation.

**Output**: `main.md` only (no LaTeX or PDF)

---

### Regenerate Just Figures

```bash
python scripts/generate_paper.py /path/to/experiment --figures-only
```

**Use when**: You've already generated the paper but need higher-quality figures.

**Output**: Updated `figures/` directory (PDF + PNG)

---

### Customize Sections

```bash
python scripts/generate_paper.py /path/to/experiment \
    --sections=methodology,results \
    --prose-level=comprehensive
```

**Options**:
- `--sections`: Comma-separated sections for full prose (others get outlines)
- `--prose-level`: `minimal` | `standard` | `comprehensive`
- `--model`: OpenAI model for prose generation (default: `gpt-5-mini`)

---

### Use Different AI Model

```bash
# Default: gpt-5-mini (latest generation, cost-effective)
python scripts/generate_paper.py /path/to/experiment

# Premium quality (more expensive)
python scripts/generate_paper.py /path/to/experiment --model=gpt-5

# Other options
python scripts/generate_paper.py /path/to/experiment --model=gpt-4o
python scripts/generate_paper.py /path/to/experiment --model=gpt-4-turbo
```

**Model Selection Guide**:
- `gpt-5-mini`: Default, latest generation, best cost/quality balance
- `gpt-5`: Premium quality, best for final submissions
- `gpt-4o`: Previous generation, still excellent quality
- `gpt-4-turbo`: Fast + high quality from GPT-4 series

---

### Filter Metrics

```bash
python scripts/generate_paper.py /path/to/experiment \
    --metrics-filter=efficiency,cost
```

**Use when**: You only want specific metric categories in the paper.

**Result**: Tables and prose focus on filtered metrics only.

---

## Manual PDF Compilation

If you generated Markdown-only (`--skip-latex`), compile manually:

```bash
cd paper_output

# Install Pandoc if needed
sudo apt-get install pandoc  # Ubuntu
brew install pandoc          # macOS

# Convert Markdown → LaTeX
pandoc --from=markdown+tex_math_dollars \
       --to=latex \
       --standalone \
       --template=acm_template/template.tex \
       -o main.tex \
       main.md

# Compile LaTeX → PDF
pdflatex main.tex
bibtex main      # After adding references
pdflatex main.tex
pdflatex main.tex  # Run twice for cross-references
```

---

## Troubleshooting

### Error: "Pandoc not found"

**Problem**: Pandoc not installed

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install pandoc

# macOS
brew install pandoc

# Windows
choco install pandoc

# Or skip LaTeX:
python scripts/generate_paper.py /path/to/experiment --skip-latex
```

---

### Error: "OpenAI API key not found"

**Problem**: Missing `OPENAI_API_KEY` environment variable

**Solution**:
```bash
export OPENAI_API_KEY="sk-your-key-here"
# Make persistent (optional):
echo 'export OPENAI_API_KEY="sk-..."' >> ~/.bashrc
```

---

### Error: "Experiment directory missing analysis results"

**Problem**: Experiment not completed or Feature 009 not run

**Solution**:
```bash
# Run experiment analysis first
cd /path/to/experiment
python scripts/generate_reports.py --experiment-dir .

# Then generate paper
python scripts/generate_paper.py .
```

---

### Error: "Prose too short (400 words < 800 minimum)"

**Problem**: AI generated insufficient content (rare)

**Solution**:
- Check `--prose-level` setting (try `comprehensive`)
- Verify experiment has sufficient data (≥30 runs recommended)
- Check OpenAI API status (may be degraded)
- Manually edit `main.md` to expand section

---

### Warning: "Citation placeholders detected"

**Not an error**: This is expected!

**Action**: Fill placeholders before submission:
1. Open `main.md` in text editor
2. Search for `[CITE: `
3. Replace with real BibTeX keys: `[CITE: AutoGPT paper]` → `\cite{autogpt2023}`
4. Add entries to `references.bib`
5. Recompile PDF

---

## Example Workflow

### Full Paper Pipeline (Start to Finish)

```bash
# 1. Set up environment
export OPENAI_API_KEY="sk-..."
cd /path/to/genai-devbench

# 2. Verify experiment is complete
ls /path/to/experiment/analysis/
# Should contain: statistical_report.md, metrics.json, etc.

# 3. Generate paper with custom settings
python scripts/generate_paper.py /path/to/experiment \
    --output-dir ./my_paper \
    --prose-level=comprehensive \
    --sections=introduction,methodology,results,discussion

# 4. Review output
cd my_paper
open main.pdf  # macOS
xdg-open main.pdf  # Linux

# 5. Fill citations
# Edit main.md: Replace [CITE: ...] with real citations
# Add entries to references.bib

# 6. Recompile
pdflatex main.tex
bibtex main
pdflatex main.tex
pdflatex main.tex

# 7. Submit to conference ✅
```

---

## Figure Export Only

If you just need figures (no paper text):

```bash
# Method 1: Use generate_paper.py
python scripts/generate_paper.py /path/to/experiment --figures-only

# Method 2: Use dedicated export script
python scripts/export_figures.py /path/to/experiment \
    --output-dir ./figures \
    --formats=pdf,png \
    --dpi=300
```

**Output**: `figures/` directory with all visualizations in PDF and PNG.

---

## Programmatic Usage (Python API)

```python
from pathlib import Path
from src.paper_generation import PaperGenerator, PaperConfig

# Configure paper generation
config = PaperConfig(
    experiment_dir=Path("/path/to/experiment"),
    output_dir=Path("./paper_output"),
    sections=["methodology", "results"],
    prose_level="comprehensive",
    openai_api_key="sk-..."  # Or use env var
)

# Generate paper
generator = PaperGenerator()
result = generator.generate_paper(config)

# Check results
print(f"PDF: {result.pdf_path}")
print(f"Word count: {result.total_word_count}")
print(f"Figures: {len(result.figure_paths)}")
print(f"Time: {result.generation_time_seconds:.1f}s")
```

---

## Next Steps

1. **Review AI Content**: Carefully validate all generated prose
2. **Fill Citations**: Replace `[CITE: ...]` placeholders with real references
3. **Add References**: Populate `references.bib` with BibTeX entries
4. **Customize**: Edit `main.md` to add your insights and refinements
5. **Recompile**: Run `pdflatex` after edits
6. **Submit**: Upload to conference submission system

**Remember**: This tool automates 80% of boilerplate writing. The remaining 20% (insights, citations, refinement) is your expertise!

---

## Performance Notes

- **Typical runtime**: 2-3 minutes for 50 runs, 3 frameworks
- **AI token usage**: ~15,000-20,000 tokens (cost varies by model: gpt-5-mini is most cost-effective)
- **Output size**: ~5-15MB (PDF + figures)
- **Prose quality**: Publication-ready with manual review

---

## Support

- **Documentation**: See `specs/010-paper-generation/` for detailed design docs
- **API Reference**: `contracts/api.md` for programmatic usage
- **Issues**: File bug reports with experiment directory structure and error logs
- **Constitution**: All design decisions follow `docs/constitution.md` principles

---

**Quick Reference**:

| Task | Command |
|------|---------|
| Full paper | `python scripts/generate_paper.py <exp_dir>` |
| Markdown only | Add `--skip-latex` |
| Figures only | Add `--figures-only` |
| Custom sections | Add `--sections=intro,results` |
| Comprehensive prose | Add `--prose-level=comprehensive` |
| Filter metrics | Add `--metrics-filter=efficiency,cost` |
| Help | Add `--help` |

**First-time users**: Start with the default command (no flags) to see full capabilities!
