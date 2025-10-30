"""
PaperGenerator: Main orchestrator for camera-ready paper generation.

Coordinates the entire pipeline: experiment data loading, section generation,
figure export, citation placeholder insertion, LaTeX conversion, and PDF compilation.
"""

import json
import yaml
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging
import subprocess

from .models import PaperConfig, PaperResult, PaperStructure, SectionContext
from .exceptions import (
    ExperimentDataError,
    DependencyMissingError,
    PdfCompilationError
)
from .prose_engine import ProseEngine
from .figure_exporter import FigureExporter
from .pandoc_converter import PandocConverter
from .citation_handler import CitationHandler
from .document_formatter import DocumentFormatter
from .template_bundle import TemplateBundle
from .readme_enhancer import ReadmeEnhancer
from .experiment_analyzer import ExperimentAnalyzer
from .sections import (
    AbstractGenerator,
    IntroductionGenerator,
    RelatedWorkGenerator,
    MethodologyGenerator,
    ResultsGenerator,
    DiscussionGenerator,
    ConclusionGenerator
)


logger = logging.getLogger(__name__)


class PaperGenerator:
    """
    Main orchestrator for paper generation pipeline.
    
    Coordinates all components to generate a complete camera-ready paper
    from experiment results.
    """
    
    def __init__(self, config: PaperConfig):
        """
        Initialize PaperGenerator with configuration.
        
        Args:
            config: PaperConfig with all generation settings
            
        Raises:
            DependencyMissingError: If Pandoc not available
            ExperimentDataError: If experiment directory invalid
        """
        self.config = config
        
        # Validate experiment directory structure
        self._validate_experiment_directory()
        
        # Detect Pandoc availability (fail-fast) - only if not in figures-only mode
        if not config.skip_latex and not config.figures_only:
            self.pandoc = PandocConverter()
            logger.info("Pandoc detected: version %s", self.pandoc.get_version())
        else:
            self.pandoc = None
            if config.figures_only:
                logger.info("Pandoc skipped (figures_only=True)")
            else:
                logger.info("LaTeX compilation skipped (skip_latex=True)")
        
        # Initialize components
        self.prose_engine = ProseEngine(config)
        self.figure_exporter = FigureExporter(config)
        self.citation_handler = CitationHandler()
        self.document_formatter = DocumentFormatter()
        self.template_bundle = TemplateBundle()
        
        # Initialize section generators
        self.section_generators = {
            'abstract': AbstractGenerator(config, self.prose_engine),
            'introduction': IntroductionGenerator(config, self.prose_engine),
            'related_work': RelatedWorkGenerator(config, self.prose_engine),
            'methodology': MethodologyGenerator(config, self.prose_engine),
            'results': ResultsGenerator(config, self.prose_engine),
            'discussion': DiscussionGenerator(config, self.prose_engine),
            'conclusion': ConclusionGenerator(config, self.prose_engine),
        }
        
        # T036: Initialize statistical data storage
        self.statistical_data = {}
        
        logger.info("PaperGenerator initialized for experiment: %s", config.experiment_dir)
    
    def generate(self) -> PaperResult:
        """
        Execute complete paper generation pipeline.
        
        Returns:
            PaperResult with output paths, metrics, and timing
            
        Raises:
            ExperimentDataError: If data loading fails
            ProseGenerationError: If section generation fails
            FigureExportError: If figure export fails
            LatexConversionError: If Pandoc conversion fails
            PdfCompilationError: If pdflatex compilation fails
        """
        start_time = time.time()
        
        logger.info("=" * 80)
        if self.config.figures_only:
            logger.info("Starting figures-only export")
        else:
            logger.info("Starting paper generation pipeline")
        logger.info("=" * 80)
        
        # Step 1: Analyze raw experiment data (prerequisite)
        logger.info("Step 1: Analyzing raw experiment runs...")
        analyzer = ExperimentAnalyzer(self.config.experiment_dir, self.config.output_dir)
        frameworks_data = analyzer.analyze()
        logger.info("  Analyzed %d frameworks", len(frameworks_data))
        
        # Step 2: Load analyzed data
        logger.info("Step 2: Loading analyzed data...")
        context = self._load_analyzed_data(frameworks_data)
        
        # Validate metrics_filter if specified (after data loaded)
        if self.config.metrics_filter is not None:
            # Extract all unique metric names from loaded data
            available_metrics = set()
            for framework_metrics in context.metrics.values():
                available_metrics.update(framework_metrics.keys())
            self.config.validate_metrics_filter(available_metrics)
        
        # If figures-only mode, skip prose generation and LaTeX compilation
        if self.config.figures_only:
            logger.info("Step 3: Exporting figures (figures-only mode)...")
            figures = self.figure_exporter.export_figures(context)
            
            end_time = time.time()
            
            # Collect figure paths
            figure_paths = []
            for fig in figures:
                if fig.pdf_path:
                    figure_paths.append(fig.pdf_path)
                if fig.png_path:
                    figure_paths.append(fig.png_path)
            
            # Create result with figures only
            result = PaperResult(
                markdown_path=None,
                latex_path=None,
                pdf_path=None,
                figure_paths=figure_paths,
                total_word_count=0,
                generation_time_seconds=end_time - start_time,
                ai_tokens_used=0  # No AI prose generated in figures-only mode
            )
            
            logger.info("=" * 80)
            logger.info("Figure export complete!")
            logger.info("  Figures generated: %d", len(figures))
            logger.info("  Time: %.1f seconds", result.generation_time_seconds)
            logger.info("  Output: %s", self.config.output_dir / "figures")
            logger.info("=" * 80)
            
            return result
        
        # Step 3: Generate all sections
        logger.info("Step 3: Generating sections...")
        sections = self._generate_all_sections(context)
        
        # Step 4: Export figures
        logger.info("Step 4: Exporting figures...")
        figures = self.figure_exporter.export_figures(context)
        
        # Step 5: Assemble paper structure
        logger.info("Step 5: Assembling paper structure...")
        paper_structure = PaperStructure(
            title=f"Empirical Comparison of {len(context.frameworks)} Multi-Agent Frameworks",
            authors=["Author 1", "Author 2"],  # TODO: Extract from config
            abstract=sections.get('abstract', ''),
            introduction=sections.get('introduction', ''),
            related_work=sections.get('related_work', ''),
            methodology=sections.get('methodology', ''),
            results=sections.get('results', ''),
            discussion=sections.get('discussion', ''),
            conclusion=sections.get('conclusion', ''),
            figures=figures,
            tables=[],  # TODO: Extract from results if needed
            references_template=""  # Will be filled manually after citation placeholder review
        )
        
        # Step 6: Insert citation placeholders
        logger.info("Step 6: Inserting citation placeholders...")
        paper_structure = self._insert_citations(paper_structure)
        
        # Step 7: Convert to LaTeX
        logger.info("Step 7: Converting to LaTeX...")
        latex_file = self._convert_to_latex(paper_structure)
        
        # Step 8: Compile to PDF (if not skipped)
        pdf_file = None
        if not self.config.skip_latex:
            logger.info("Step 8: Compiling to PDF...")
            pdf_file = self._compile_to_pdf(latex_file)
        else:
            logger.info("Step 8: Skipped PDF compilation (skip_latex=True)")
        
        # Calculate metrics
        end_time = time.time()
        total_words = sum(len(text.split()) for text in sections.values())
        
        # Collect figure paths
        figure_paths = []
        for fig in figures:
            if fig.pdf_path:
                figure_paths.append(fig.pdf_path)
            if fig.png_path:
                figure_paths.append(fig.png_path)
        
        # Create result
        result = PaperResult(
            markdown_path=self.config.output_dir / "main.md" if not self.config.skip_latex else None,
            latex_path=latex_file if latex_file else None,
            pdf_path=pdf_file if pdf_file else None,
            figure_paths=figure_paths,
            total_word_count=total_words,
            generation_time_seconds=end_time - start_time,
            ai_tokens_used=self.prose_engine.total_tokens_used
        )
        
        # Step 9: Enhance experiment README with reproduction instructions
        logger.info("Step 9: Enhancing experiment README...")
        try:
            readme_enhancer = ReadmeEnhancer()
            readme_path = readme_enhancer.enhance_readme(
                experiment_dir=self.config.experiment_dir,
                frameworks=context.frameworks,
                num_runs=context.num_runs
            )
            result.warnings.append(f"Enhanced README with reproduction guide: {readme_path}")
            logger.info("  README enhanced: %s", readme_path)
        except Exception as e:
            logger.warning("Failed to enhance README: %s", str(e))
            result.warnings.append(f"README enhancement failed: {str(e)}")
        
        logger.info("=" * 80)
        logger.info("Paper generation complete!")
        logger.info("  Total words: %d", total_words)
        logger.info("  Total tokens: %d", result.ai_tokens_used)
        logger.info("  Time: %.1f seconds", result.generation_time_seconds)
        logger.info("  Output: %s", self.config.output_dir)
        if pdf_file:
            logger.info("  PDF: %s", pdf_file)
        logger.info("=" * 80)
        
        return result
    
    def _validate_experiment_directory(self):
        """
        Validate experiment directory structure.
        
        Raises:
            ExperimentDataError: If directory structure invalid
        """
        exp_dir = self.config.experiment_dir
        
        if not exp_dir.exists():
            raise ExperimentDataError(
                message=f"Experiment directory does not exist: {exp_dir}"
            )
        
        # Check for runs subdirectory (required for analysis)
        runs_dir = exp_dir / "runs"
        if not runs_dir.exists():
            raise ExperimentDataError(
                message=f"Experiment directory missing 'runs/' subdirectory: {exp_dir}\n"
                       f"Expected: {runs_dir}",
                remediation="Ensure the experiment directory contains raw run data in runs/{framework}/{run_id}/"
            )
        
        logger.debug("Experiment directory validated: %s", exp_dir)
    
    def _load_analyzed_data(self, frameworks_data: Dict[str, Any]) -> SectionContext:
        """
        Load analyzed experiment data from output directory.
        
        T036: Enhanced to parse statistical reports and extract structured data.
        
        Args:
            frameworks_data: Pre-analyzed framework metrics
            
        Returns:
            SectionContext with loaded data
            
        Raises:
            ExperimentDataError: If required files missing or invalid
        """
        exp_dir = self.config.experiment_dir
        output_dir = self.config.output_dir
        
        try:
            # Load config.yaml from experiment root directory
            config_file = exp_dir / "config.yaml"
            if not config_file.exists():
                raise ExperimentDataError(
                    message=f"config.yaml not found in experiment directory: {exp_dir}\n"
                           f"Expected: {config_file}",
                    remediation="Ensure the experiment directory contains config.yaml with experiment configuration"
                )
            
            with open(config_file, 'r', encoding='utf-8') as f:
                exp_config = yaml.safe_load(f)
            
            # Validate required config fields
            if 'frameworks' not in exp_config or not exp_config['frameworks']:
                raise ExperimentDataError(
                    message=f"'frameworks' key missing or empty in config.yaml: {config_file}",
                    remediation="Ensure config.yaml contains 'frameworks' section with at least one framework"
                )
            
            frameworks = list(exp_config['frameworks'].keys())
            
            # Get num_runs - must be in stopping_rule or direct field
            if 'stopping_rule' in exp_config:
                if 'max_runs' not in exp_config['stopping_rule']:
                    raise ExperimentDataError(
                        message="'stopping_rule' exists but 'max_runs' is missing in config.yaml",
                        remediation="Add 'max_runs' field to 'stopping_rule' section in config.yaml"
                    )
                num_runs = exp_config['stopping_rule']['max_runs']
            elif 'num_runs' in exp_config:
                num_runs = exp_config['num_runs']
            else:
                raise ExperimentDataError(
                    message="Neither 'stopping_rule.max_runs' nor 'num_runs' found in config.yaml",
                    remediation="Add either 'stopping_rule.max_runs' or 'num_runs' to config.yaml"
                )
            
            # Count actual runs from runs/ directory to verify/override
            runs_dir = exp_dir / "runs"
            if runs_dir.exists():
                # Get framework directories (excluding manifest.json)
                framework_dirs = [d for d in runs_dir.iterdir() 
                                if d.is_dir() and d.name != '__pycache__']
                if framework_dirs:
                    # Count runs in first framework directory
                    first_framework = framework_dirs[0]
                    run_dirs = [d for d in first_framework.iterdir() 
                              if d.is_dir() and d.name.startswith('run_')]
                    if run_dirs:
                        actual_runs = len(run_dirs)
                        logger.info(f"Detected {actual_runs} actual runs from {first_framework.name}")
                        num_runs = actual_runs  # Use actual count instead of config
            
            # Use analyzed metrics from output_dir
            metrics = frameworks_data
            
            # Validate frameworks exist in analyzed data
            for framework in frameworks:
                if framework not in metrics:
                    raise ExperimentDataError(
                        message=f"Framework '{framework}' from config not found in analyzed metrics data",
                        remediation=f"Ensure runs exist for framework '{framework}' in runs/ directory"
                    )
            
            # Load statistical_report.md from output_dir (required)
            report_file = output_dir / "statistical_report.md"
            if not report_file.exists():
                raise ExperimentDataError(
                    message=f"statistical_report.md not found in output directory: {output_dir}",
                    remediation="Run statistical analysis before generating paper"
                )
            
            statistical_report = report_file.read_text(encoding='utf-8')
            # Extract key findings from report (simple heuristic)
            key_findings = self._extract_key_findings(statistical_report)
            
            # T036: Parse statistical reports and extract structured data
            self.statistical_data = self._parse_statistical_reports()
            
            # Create context
            context = SectionContext(
                section_name="",  # Will be set by each generator
                experiment_summary=f"Empirical comparison of {len(frameworks)} multi-agent frameworks for software development",
                frameworks=frameworks,
                num_runs=num_runs,
                metrics=metrics,
                statistical_results=self.statistical_data,  # Include statistical data
                key_findings=key_findings
            )
            
            logger.info("Loaded experiment data: %d frameworks, %d runs", 
                       len(frameworks), num_runs)
            
            return context
            
        except Exception as e:
            raise ExperimentDataError(
                message=f"Failed to load analyzed data: {str(e)}"
            ) from e
    
    def _parse_statistical_reports(self) -> Dict[str, Any]:
        """
        Parse statistical_report_summary.md and extract structured data (T036).
        
        Extracts:
        - comparisons: List of {framework1, framework2, effect_size, ci, p_value, test_type}
        - primary_metric: str
        - visualization_paths: Dict[str, str] mapping viz types to relative paths
        - power_warnings: List[str]
        - methodology_text: str
        - key_findings: List[str]
        
        Returns:
            Dict with structured statistical data
        """
        output_dir = self.config.output_dir
        summary_file = output_dir / "statistical_report_summary.md"
        full_file = output_dir / "statistical_report_full.md"
        
        # Validate required files exist
        if not summary_file.exists():
            raise ExperimentDataError(
                message=f"statistical_report_summary.md not found in output directory: {output_dir}",
                remediation="Run statistical analysis before generating paper"
            )
        
        if not full_file.exists():
            raise ExperimentDataError(
                message=f"statistical_report_full.md not found in output directory: {output_dir}",
                remediation="Run statistical analysis before generating paper"
            )
        
        statistical_data = {
            'comparisons': [],
            'primary_metric': None,
            'visualization_paths': {},
            'power_warnings': [],
            'methodology_text': "",
            'key_findings': []
        }
        
        summary_content = summary_file.read_text(encoding='utf-8')
        
        # Extract comparisons from Key Findings section
        in_findings = False
        current_metric = None
        
        for line in summary_content.split('\n'):
            line_stripped = line.strip()
            
            # Detect Key Findings section
            if '## 📊 Key Findings' in line_stripped or '## Key Findings' in line_stripped:
                in_findings = True
                continue
            
            # Detect next section (end of findings)
            if in_findings and line_stripped.startswith('## ') and 'Key Findings' not in line_stripped:
                in_findings = False
                continue
            
            if in_findings:
                # Extract metric name
                if line_stripped.startswith('### '):
                    current_metric = line_stripped[4:].strip()
                    if not statistical_data['primary_metric']:
                        statistical_data['primary_metric'] = current_metric
                
                # Extract test result and p-value
                if '**Result**:' in line_stripped and current_metric:
                    # Extract p-value
                    import re
                    p_match = re.search(r'p=([\d.]+)', line_stripped)
                    p_value = float(p_match.group(1)) if p_match else None
                    test_type = None
                
                # Extract test type
                if '**Test Used**:' in line_stripped:
                    test_type = line_stripped.split('**Test Used**:')[1].strip()
                
                # Extract effect sizes
                if line_stripped.startswith('- ') and ' vs ' in line_stripped and ':' in line_stripped:
                    # Parse effect size line: "- framework1 vs framework2: measure = value (magnitude, 95% CI: [lower, upper])"
                    parts = line_stripped[2:].split(':')
                    if len(parts) >= 2:
                        comparison = parts[0].strip()
                        frameworks = [f.strip() for f in comparison.split(' vs ')]
                        
                        if len(frameworks) == 2:
                            # Extract effect size value and CI
                            effect_str = parts[1].strip()
                            import re
                            value_match = re.search(r'=\s*([-\d.]+)', effect_str)
                            ci_match = re.search(r'\[([-\d.]+),\s*([-\d.]+)\]', effect_str)
                            magnitude_match = re.search(r'\(([^,]+),', effect_str)
                            
                            if value_match:
                                statistical_data['comparisons'].append({
                                    'framework1': frameworks[0],
                                    'framework2': frameworks[1],
                                    'metric': current_metric,
                                    'effect_size': float(value_match.group(1)),
                                    'ci_lower': float(ci_match.group(1)) if ci_match else None,
                                    'ci_upper': float(ci_match.group(2)) if ci_match else None,
                                    'magnitude': magnitude_match.group(1).strip() if magnitude_match else 'unknown',
                                    'p_value': p_value,
                                    'test_type': test_type
                                })
        
        # Extract visualization paths
        in_viz_section = False
        for line in summary_content.split('\n'):
            if '## 📈 Critical Visualizations' in line or '## Critical Visualizations' in line:
                in_viz_section = True
                continue
            
            if in_viz_section and line.strip().startswith('## '):
                in_viz_section = False
                continue
            
            if in_viz_section and line.strip().startswith('!['):
                # Extract image path: ![caption](path)
                import re
                img_match = re.search(r'!\[.*?\]\((.*?)\)', line)
                if img_match:
                    path = img_match.group(1)
                    # Determine viz type from path
                    if 'box_plot' in path:
                        statistical_data['visualization_paths']['box_plot'] = path
                    elif 'forest_plot' in path:
                        statistical_data['visualization_paths']['forest_plot'] = path
                    elif 'violin_plot' in path:
                        statistical_data['visualization_paths']['violin_plot'] = path
                    elif 'qq_plot' in path:
                        statistical_data['visualization_paths']['qq_plot'] = path
        
        # Extract power warnings
        in_power_section = False
        for line in summary_content.split('\n'):
            if '## ⚠️ Power Analysis' in line or '## Power Analysis' in line:
                in_power_section = True
                continue
            
            if in_power_section and line.strip().startswith('## '):
                in_power_section = False
                continue
            
            if in_power_section and line.strip().startswith('- '):
                statistical_data['power_warnings'].append(line.strip()[2:])
        
        # Extract methodology text from full report
        full_content = full_file.read_text(encoding='utf-8')
        
        in_methodology = False
        methodology_lines = []
        for line in full_content.split('\n'):
            if '## 6. Statistical Methodology' in line or '## Statistical Methodology' in line:
                in_methodology = True
                continue
            
            if in_methodology and line.strip().startswith('## '):
                break
            
            if in_methodology and line.strip().startswith('### Reproducibility'):
                break
            
            if in_methodology:
                methodology_lines.append(line)
        
        statistical_data['methodology_text'] = '\n'.join(methodology_lines).strip()
        
        # Extract key findings (simple heuristic - first few comparisons)
        for comp in statistical_data['comparisons'][:3]:
            finding = (
                f"{comp['framework1']} vs {comp['framework2']} on {comp['metric']}: "
                f"effect size = {comp['effect_size']:.2f} ({comp['magnitude']})"
            )
            statistical_data['key_findings'].append(finding)
        
        logger.info("Parsed statistical data: %d comparisons, %d visualizations, %d power warnings",
                   len(statistical_data['comparisons']),
                   len(statistical_data['visualization_paths']),
                   len(statistical_data['power_warnings']))
        
        return statistical_data
    
    def _extract_key_findings(self, report: str) -> List[str]:
        """Extract key findings from statistical report (simple heuristic)."""
        findings = []
        
        # Look for bullet points or numbered lists
        for line in report.split('\n'):
            line = line.strip()
            if line.startswith('- ') or line.startswith('* '):
                findings.append(line[2:].strip())
            elif len(line) > 0 and line[0].isdigit() and '. ' in line:
                findings.append(line.split('. ', 1)[1].strip())
        
        # Limit to top 5 findings
        return findings[:5]
    
    def _generate_all_sections(self, context: SectionContext) -> Dict[str, str]:
        """
        Generate prose for all sections.
        
        For sections in config.sections (or all if None), generate full AI prose.
        For other sections, generate brief structural outlines.
        
        Args:
            context: SectionContext with experiment data
            
        Returns:
            Dictionary mapping section names to prose
        """
        sections = {}
        
        # Determine which sections get full prose
        if self.config.sections is None:
            # Default: all sections get full prose
            selected_sections = set(self.section_generators.keys())
        else:
            # Only specified sections get full prose
            selected_sections = set(self.config.sections)
        
        for section_name, generator in self.section_generators.items():
            logger.info("Generating section: %s", section_name)
            
            if section_name in selected_sections:
                # Generate full AI prose
                try:
                    prose = generator.generate(context)
                    
                    # T037-T039: Enhance sections with statistical content
                    if section_name == 'methodology':
                        prose = self._enhance_methodology_section(prose)
                    elif section_name == 'results':
                        prose = self._enhance_results_section(prose)
                    elif section_name == 'discussion':
                        prose = self._enhance_discussion_section(prose)
                    
                    sections[section_name] = prose
                    logger.info("  ✓ %s: %d words (full prose)", section_name, len(prose.split()))
                except Exception as e:
                    import traceback
                    logger.error("  ✗ %s: %s", section_name, str(e))
                    logger.debug("Full traceback: %s", traceback.format_exc())
                    sections[section_name] = f"<!-- ERROR generating {section_name}: {str(e)} -->"
            else:
                # Generate brief outline only
                outline = self._generate_section_outline(section_name, context)
                sections[section_name] = outline
                logger.info("  ✓ %s: %d words (outline only)", section_name, len(outline.split()))
        
        return sections
    
    def _generate_section_outline(self, section_name: str, context: SectionContext) -> str:
        """
        Generate a brief structural outline for a non-selected section.
        
        Args:
            section_name: Name of the section
            context: SectionContext with experiment data
            
        Returns:
            Brief outline text in LaTeX format (2-3 bullet points, <200 words)
        """
        # Section-specific outline templates (using LaTeX formatting)
        outlines = {
            "abstract": (
                "This paper presents an empirical comparison of multi-agent software "
                "development frameworks. Key findings and contributions are summarized."
            ),
            "introduction": (
                "\\textbf{Context and Motivation:}\n"
                "\\begin{itemize}\n"
                "\\item Multi-agent frameworks automate software development\n"
                "\\item Systematic comparison needed to guide adoption\n"
                "\\end{itemize}\n\n"
                "\\textbf{Research Questions:}\n"
                "\\begin{itemize}\n"
                f"\\item How do {', '.join(context.frameworks)} compare in efficiency and quality?\n"
                "\\item What are the practical trade-offs between frameworks?\n"
                "\\end{itemize}\n\n"
                "\\textbf{Contributions:}\n"
                "\\begin{itemize}\n"
                f"\\item Empirical evaluation across {context.num_runs} runs\n"
                "\\item Statistical analysis of performance differences\n"
                "\\end{itemize}"
            ),
            "related_work": (
                "\\textbf{Multi-Agent Development Frameworks:}\n"
                "\\begin{itemize}\n"
                f"\\item {', '.join(context.frameworks)}: Key capabilities and architectures\n"
                "\\end{itemize}\n\n"
                "\\textbf{Empirical Software Engineering:}\n"
                "\\begin{itemize}\n"
                "\\item Benchmark design and experimental methodology\n"
                "\\item Statistical testing for performance comparison\n"
                "\\end{itemize}"
            ),
            "methodology": (
                "\\textbf{Experimental Setup:}\n"
                "\\begin{itemize}\n"
                f"\\item Frameworks: {', '.join(context.frameworks)}\n"
                f"\\item Replications: {context.num_runs} runs per framework\n"
                "\\end{itemize}\n\n"
                "\\textbf{Metrics:}\n"
                "\\begin{itemize}\n"
                "\\item Efficiency: execution time, token usage, cost\n"
                "\\item Quality: test pass rate, code quality scores\n"
                "\\end{itemize}\n\n"
                "\\textbf{Statistical Analysis:}\n"
                "\\begin{itemize}\n"
                "\\item Mann-Whitney U tests for pairwise comparison\n"
                "\\item Kruskal-Wallis H test for overall differences\n"
                "\\end{itemize}"
            ),
            "results": (
                "\\textbf{Performance Summary:}\n"
                "\\begin{itemize}\n"
                f"\\item Data collected from {context.num_runs} runs per framework\n"
                "\\item Statistical tests reveal significant differences\n"
                "\\end{itemize}\n\n"
                "\\textbf{Key Findings:}\n"
                "\\begin{itemize}\n"
                + "\n".join(f"\\item {finding}" for finding in context.key_findings[:3])
                + "\n\\end{itemize}"
                if context.key_findings else 
                "\\begin{itemize}\n\\item Detailed results in figures and tables\n\\end{itemize}"
            ),
            "discussion": (
                "\\textbf{Interpretation:}\n"
                "\\begin{itemize}\n"
                "\\item Performance differences reflect architectural choices\n"
                "\\item Trade-offs between efficiency and quality\n"
                "\\end{itemize}\n\n"
                "\\textbf{Practical Implications:}\n"
                "\\begin{itemize}\n"
                "\\item Framework selection depends on use case priorities\n"
                "\\item Cost-benefit analysis for adoption decisions\n"
                "\\end{itemize}\n\n"
                "\\textbf{Limitations:}\n"
                "\\begin{itemize}\n"
                "\\item Benchmark scope and generalizability\n"
                "\\item Threats to validity\n"
                "\\end{itemize}"
            ),
            "conclusion": (
                "\\textbf{Summary:}\n"
                "\\begin{itemize}\n"
                f"\\item Empirical comparison of {len(context.frameworks)} frameworks\n"
                "\\item Statistical evidence of performance differences\n"
                "\\end{itemize}\n\n"
                "\\textbf{Future Work:}\n"
                "\\begin{itemize}\n"
                "\\item Extended benchmarks with larger codebases\n"
                "\\item Real-world deployment studies\n"
                "\\end{itemize}"
            )
        }
        
        return outlines.get(section_name, f"[{section_name.replace('_', ' ').title()} outline]")
    
    def _insert_citations(self, paper: PaperStructure) -> PaperStructure:
        """
        Insert citation placeholders in all sections.
        
        Args:
            paper: PaperStructure to process
            
        Returns:
            Updated PaperStructure with citation placeholders
        """
        # Process each section attribute
        sections_to_process = [
            'abstract', 'introduction', 'related_work',
            'methodology', 'results', 'discussion', 'conclusion'
        ]
        
        total_placeholders = 0
        for section_name in sections_to_process:
            section_text = getattr(paper, section_name, '')
            if section_text:
                processed_text = self.citation_handler.insert_placeholders(section_text)
                setattr(paper, section_name, processed_text)
                total_placeholders += self.citation_handler.count_placeholders(processed_text)
        
        logger.info("Inserted %d citation placeholders", total_placeholders)
        
        return paper
    
    def _convert_to_latex(self, paper: PaperStructure) -> Path:
        """
        Convert paper to LaTeX format.
        
        Args:
            paper: PaperStructure to convert
            
        Returns:
            Path to generated LaTeX file
        """
        # Copy ACM template to output directory
        self.template_bundle.copy_to_output(self.config.output_dir)
        
        # Build sections dict from paper attributes
        sections_dict = {
            'introduction': paper.introduction,
            'related_work': paper.related_work,
            'methodology': paper.methodology,
            'results': paper.results,
            'discussion': paper.discussion,
            'conclusion': paper.conclusion
        }
        
        # Build complete LaTeX document
        latex_content = self.document_formatter.format_latex_document(
            title=paper.title,
            authors=paper.authors,
            abstract=paper.abstract,
            sections=sections_dict,
            references=paper.references_template
        )
        
        # Write main.tex
        latex_file = self.config.output_dir / "main.tex"
        latex_file.write_text(latex_content)
        
        logger.info("LaTeX file written: %s", latex_file)
        
        return latex_file
    
    def _compile_to_pdf(self, latex_file: Path) -> Optional[Path]:
        """
        Compile LaTeX to PDF using pdflatex.
        
        Args:
            latex_file: Path to main.tex file
            
        Returns:
            Path to generated PDF, or None if pdflatex not available
            
        Raises:
            PdfCompilationError: If compilation fails
        """
        try:
            # Check if pdflatex is available
            result = subprocess.run(
                ['pdflatex', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode != 0:
                logger.warning("pdflatex not available, skipping PDF compilation")
                return None
                
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning("pdflatex not available, skipping PDF compilation")
            return None
        
        # Run pdflatex twice (for references)
        output_dir = latex_file.parent
        
        for i in range(2):
            logger.info("Running pdflatex (pass %d/2)...", i + 1)
            
            result = subprocess.run(
                ['pdflatex', '-interaction=nonstopmode', latex_file.name],
                cwd=output_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Check if PDF was actually created (more reliable than returncode)
            # pdflatex can return non-zero for warnings but still produce a valid PDF
            pdf_file_check = output_dir / f"{latex_file.stem}.pdf"
            
            if result.returncode != 0 and not pdf_file_check.exists():
                # Compilation truly failed - no PDF produced
                error_log = output_dir / f"{latex_file.stem}.log"
                error_msg = f"LaTeX compilation failed (pass {i + 1})"
                
                if error_log.exists():
                    # Extract key errors from log
                    log_content = error_log.read_text()
                    error_msg += f"\n\nSee log file: {error_log}"
                
                raise PdfCompilationError(
                    message=error_msg,
                    latex_log=result.stderr if result.stderr else ""
                )
            elif result.returncode != 0:
                # Non-zero return but PDF exists - just warnings
                logger.warning("pdflatex returned %d but PDF was created (likely just warnings)", result.returncode)
        
        pdf_file = output_dir / f"{latex_file.stem}.pdf"
        
        if pdf_file.exists():
            logger.info("PDF compiled successfully: %s", pdf_file)
            return pdf_file
        else:
            raise PdfCompilationError(
                message="PDF file not generated despite successful pdflatex run"
            )
    
    def _enhance_methodology_section(self, prose: str) -> str:
        """
        Enhance methodology section with statistical analysis description (T037).
        
        Adds "Statistical Analysis" subsection using methodology_text from
        statistical reports.
        
        Args:
            prose: Generated methodology prose
            
        Returns:
            Enhanced prose with statistical analysis subsection
        """
        if not self.statistical_data or not self.statistical_data.get('methodology_text'):
            logger.debug("No statistical methodology text available")
            return prose
        
        # Add Statistical Analysis subsection
        statistical_section = "\n\n\\subsection{Statistical Analysis}\n\n"
        statistical_section += self.statistical_data['methodology_text']
        statistical_section += "\n"
        
        # Append to existing prose
        enhanced = prose + statistical_section
        
        logger.info("Enhanced methodology with statistical analysis subsection")
        return enhanced
    
    def _enhance_results_section(self, prose: str) -> str:
        """
        Enhance results section with effect sizes and visualizations (T038).
        
        Includes effect sizes and p-values in comparisons, embeds statistical
        visualizations (box plot, forest plot) with captions.
        
        Args:
            prose: Generated results prose
            
        Returns:
            Enhanced prose with statistical results and visualizations
        """
        try:
            if not self.statistical_data:
                logger.debug("No statistical data available")
                return prose
            
            enhancements = []
            by_metric = {}  # Initialize here for later logging
            
            # Add statistical comparisons subsection
            if self.statistical_data.get('comparisons'):
                enhancements.append("\n\n\\subsection{Statistical Comparisons}\n\n")
                
                # Group comparisons by metric
                from collections import defaultdict
                by_metric = defaultdict(list)
                for comp in self.statistical_data['comparisons']:
                    metric = comp.get('metric')
                    if metric:  # Skip if metric is None
                        by_metric[metric].append(comp)
                
                for metric, comps in by_metric.items():
                    if not metric:  # Skip if metric is None
                        continue
                        
                    enhancements.append(f"\\textbf{{{metric}:}}\n")
                    enhancements.append("\\begin{itemize}\n")
                    
                    for comp in comps:
                        framework1 = comp.get('framework1')
                        framework2 = comp.get('framework2')
                        effect = comp.get('effect_size')
                        magnitude = comp.get('magnitude')
                        ci_lower = comp.get('ci_lower')
                        ci_upper = comp.get('ci_upper')
                        p_value = comp.get('p_value')
                        
                        # Convert None to defaults
                        if framework1 is None:
                            framework1 = 'Unknown'
                        if framework2 is None:
                            framework2 = 'Unknown'
                        if magnitude is None:
                            magnitude = 'unknown'
                        if ci_lower is None:
                            ci_lower = 0
                        if ci_upper is None:
                            ci_upper = 0
                        if p_value is None:
                            p_value = 1.0
                        
                        # Skip if effect size is None
                        if effect is None:
                            continue
                        
                        sig_marker = "$p < 0.05$" if p_value < 0.05 else "$p \\geq 0.05$"
                        
                        enhancements.append(
                            f"\\item {framework1} vs {framework2}: "
                            f"effect size = {effect:.3f} ({magnitude}, "
                            f"95\\% CI: [{ci_lower:.3f}, {ci_upper:.3f}]), {sig_marker}\n"
                        )
                    
                    enhancements.append("\\end{itemize}\n\n")
            
            # Embed visualizations
            if self.statistical_data.get('visualization_paths'):
                enhancements.append("\\subsection{Statistical Visualizations}\n\n")
                
                viz_paths = self.statistical_data['visualization_paths']
                
                # Box plot
                if 'box_plot' in viz_paths:
                    primary_metric = self.statistical_data.get('primary_metric')
                    if primary_metric is None:
                        primary_metric = 'metrics'
                    enhancements.append(
                        f"\\begin{{figure}}[htbp]\n"
                        f"\\centering\n"
                        f"\\includegraphics[width=0.8\\textwidth]{{{viz_paths['box_plot']}}}\n"
                        f"\\caption{{Box plot showing distribution of {primary_metric} across frameworks. "
                        f"Box shows median and quartiles, whiskers extend to 1.5$\\times$IQR, points are outliers.}}\n"
                        f"\\label{{fig:box_plot}}\n"
                        f"\\end{{figure}}\n\n"
                    )
                
                # Forest plot
                if 'forest_plot' in viz_paths:
                    primary_metric = self.statistical_data.get('primary_metric')
                    if primary_metric is None:
                        primary_metric = 'metrics'
                    enhancements.append(
                        f"\\begin{{figure}}[htbp]\n"
                        f"\\centering\n"
                        f"\\includegraphics[width=0.8\\textwidth]{{{viz_paths['forest_plot']}}}\n"
                        f"\\caption{{Forest plot showing effect sizes with 95\\% confidence intervals for {primary_metric}. "
                        f"Vertical line at 0 indicates no effect. Color indicates magnitude (green=small, orange=medium, red=large).}}\n"
                        f"\\label{{fig:forest_plot}}\n"
                        f"\\end{{figure}}\n\n"
                    )
        
            # Append enhancements to prose
            enhanced = prose + ''.join(enhancements)
            
            logger.info("Enhanced results with %d comparison groups and %d visualizations",
                       len(by_metric) if self.statistical_data.get('comparisons') else 0,
                       len(self.statistical_data.get('visualization_paths', {})))
            return enhanced
        except Exception as e:
            import traceback
            logger.warning("Could not enhance results section: %s", str(e))
            logger.warning("Full traceback:\n%s", traceback.format_exc())
            return prose
    
    def _enhance_discussion_section(self, prose: str) -> str:
        """
        Enhance discussion section with power analysis limitations (T039).
        
        Adds "Statistical Limitations" paragraph if power warnings exist,
        mentioning achieved power and sample size recommendations.
        
        Args:
            prose: Generated discussion prose
            
        Returns:
            Enhanced prose with statistical limitations
        """
        if not self.statistical_data or not self.statistical_data.get('power_warnings'):
            logger.debug("No power warnings to add to discussion")
            return prose
        
        # Add Statistical Limitations subsection
        limitations = "\n\n\\subsection{Statistical Limitations}\n\n"
        
        limitations += (
            "Our statistical analysis revealed some limitations regarding statistical power "
            "that should be considered when interpreting the results:\n\n"
            "\\begin{itemize}\n"
        )
        
        for warning in self.statistical_data['power_warnings']:
            limitations += f"\\item {warning}\n"
        
        limitations += "\\end{itemize}\n\n"
        limitations += (
            "These power limitations suggest that our current sample size may be insufficient "
            "to detect small to medium effect sizes with high confidence. Future work should "
            "consider increasing the number of experimental runs as recommended above to achieve "
            "adequate statistical power (target: 80\\%) for more definitive conclusions.\n"
        )
        
        # Append to existing prose
        enhanced = prose + limitations
        
        logger.info("Enhanced discussion with %d power warnings", 
                   len(self.statistical_data['power_warnings']))
        return enhanced

