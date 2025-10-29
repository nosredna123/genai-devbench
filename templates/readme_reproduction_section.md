## Reproduction Guide

This section provides step-by-step instructions to reproduce the experiment results reported in the associated research paper.

**Estimated Time**: ≤30 minutes  
**Prerequisites**: Linux/macOS system with Python {python_version}+

---

### 1. Environment Requirements

**System Requirements:**
- Python {python_version} or higher
- 8GB+ RAM (16GB recommended)
- 10GB+ free disk space
- Internet connection (for framework installations and API calls)

**Required Software:**
- Git (for cloning repositories)
- pip (Python package manager)
- virtualenv or venv (Python virtual environment)

**API Access:**
- OpenAI API key (required for frameworks: {frameworks_list})
- Set `OPENAI_API_KEY` environment variable before running

---

### 2. Dependency Installation

**Step 1: Clone or navigate to this experiment directory**

```bash
cd {experiment_dir}
```

**Step 2: Create a Python virtual environment**

```bash
python{python_major_version} -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

**Step 3: Install base dependencies**

```bash
pip install --upgrade pip
pip install pyyaml requests pytest
```

**Step 4: Install framework-specific dependencies**

The experiment uses the following frameworks: {frameworks_list}

Each framework will be installed automatically during the first run, or you can install them manually:

```bash
# Framework installations are handled by the experiment runner
# See config/experiment.yaml for framework configurations
```

---

### 3. Running the Experiment

**Step 1: Configure API credentials**

```bash
# Set OpenAI API key (required)
export OPENAI_API_KEY="your-api-key-here"

# Verify the key is set
echo $OPENAI_API_KEY
```

**Step 2: Review experiment configuration**

The experiment configuration is in `config/experiment.yaml`. Key parameters:
- **Frameworks tested**: {frameworks_list}
- **Number of runs per framework**: {num_runs}
- **Task specification**: See `config/experiment.yaml` for details

**Step 3: Execute the experiment**

```bash
# Run the complete experiment (estimated time: {estimated_runtime})
python ../../src/runner/run_experiment.py config/experiment.yaml

# Monitor progress in real-time
tail -f logs/experiment.log
```

**Note**: The experiment will:
1. Initialize each framework ({frameworks_list})
2. Execute {num_runs} runs per framework
3. Collect metrics (execution time, cost, quality scores)
4. Generate raw data in `analysis/` directory

---

### 4. Regenerating Analysis Reports

After the experiment completes, regenerate the statistical analysis and visualizations:

**Step 1: Run statistical analysis**

```bash
# Generate statistical report with Mann-Whitney U tests
python ../../src/analysis/statistical_analyzer.py analysis/metrics.json

# Output: analysis/statistical_report.md
```

**Step 2: Generate visualizations**

```bash
# Create publication-quality figures
python ../../scripts/export_figures.py . --output-dir analysis/figures

# Output: analysis/figures/*.pdf and *.png
```

**Step 3: (Optional) Regenerate the research paper**

```bash
# Generate camera-ready paper with AI-assisted prose
python ../../scripts/generate_paper.py . --output-dir paper

# Output: paper/main.pdf
```

---

### 5. Expected Outputs

After successful reproduction, you should have:

**Data Files:**
- `analysis/metrics.json` - Raw experimental data ({num_runs} runs × {num_frameworks} frameworks)
- `analysis/statistical_report.md` - Statistical analysis with p-values and effect sizes

**Figures (if generated):**
- `analysis/figures/metric_comparison_*.pdf` - Comparison plots for each metric
- `analysis/figures/metric_comparison_*.png` - Raster versions (300 DPI)
- `analysis/figures/statistical_significance.pdf` - Statistical test results visualization

**Paper (if generated):**
- `paper/main.tex` - LaTeX source with AI-generated prose
- `paper/main.pdf` - Compiled camera-ready PDF (if pdflatex available)
- `paper/figures/` - Embedded figures directory

**Verification:**
- Metric values should match those reported in the paper (within ±5% due to randomness)
- Statistical significance results (p-values) should be consistent
- Figures should visually match those in the published paper

---

### Troubleshooting

**Issue: API rate limits**
- Solution: Reduce `num_runs` in `config/experiment.yaml` or add delays between runs

**Issue: Framework installation failures**
- Solution: Check framework-specific requirements in their documentation
- Verify Python version compatibility

**Issue: Statistical tests show different p-values**
- Expected: Minor variations due to randomness in framework execution
- Acceptable range: ±0.05 for p-values (statistical tests are approximate)

**Issue: Missing dependencies**
- Solution: Ensure virtual environment is activated
- Run: `pip install -r requirements.txt` (if available)

**Issue: Out of memory errors**
- Solution: Reduce concurrent runs or increase system RAM
- Monitor memory usage: `htop` or `top`

---

### Contact & Support

For questions about reproducing this experiment:
1. Check experiment logs in `logs/` directory
2. Review configuration in `config/experiment.yaml`
3. Consult the main project README for general setup instructions

**Citation**: If you use this experiment in your research, please cite the associated paper.

---

*This reproduction guide was automatically generated by genai-devbench paper generation tools.*
*Last updated: {generation_date}*
