"""
PaperGenerator: Main orchestrator for camera-ready paper generation.

Coordinates the entire pipeline: experiment data loading, section generation,
figure export, citation placeholder insertion, LaTeX conversion, and PDF compilation.
"""

import json
import yaml
import time
from pathlib import Path
from typing import Dict, List, Optional
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
        
        # Step 1: Load experiment data
        logger.info("Step 1: Loading experiment data...")
        context = self._load_experiment_data()
        
        # Validate metrics_filter if specified (after data loaded)
        if self.config.metrics_filter is not None:
            # Extract all unique metric names from loaded data
            available_metrics = set()
            for framework_metrics in context.metrics.values():
                available_metrics.update(framework_metrics.keys())
            self.config.validate_metrics_filter(available_metrics)
        
        # If figures-only mode, skip prose generation and LaTeX compilation
        if self.config.figures_only:
            logger.info("Step 2: Exporting figures (figures-only mode)...")
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
        
        # Step 2: Generate all sections
        logger.info("Step 2: Generating sections...")
        sections = self._generate_all_sections(context)
        
        # Step 3: Export figures
        logger.info("Step 3: Exporting figures...")
        figures = self.figure_exporter.export_figures(context)
        
        # Step 4: Assemble paper structure
        logger.info("Step 4: Assembling paper structure...")
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
        
        # Step 5: Insert citation placeholders
        logger.info("Step 5: Inserting citation placeholders...")
        paper_structure = self._insert_citations(paper_structure)
        
        # Step 6: Convert to LaTeX
        logger.info("Step 6: Converting to LaTeX...")
        latex_file = self._convert_to_latex(paper_structure)
        
        # Step 7: Compile to PDF (if not skipped)
        pdf_file = None
        if not self.config.skip_latex:
            logger.info("Step 7: Compiling to PDF...")
            pdf_file = self._compile_to_pdf(latex_file)
        else:
            logger.info("Step 7: Skipped PDF compilation (skip_latex=True)")
        
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
        
        # Step 8: Enhance experiment README with reproduction instructions
        logger.info("Step 8: Enhancing experiment README...")
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
        
        # Check for analysis subdirectory
        analysis_dir = exp_dir / "analysis"
        if not analysis_dir.exists():
            raise ExperimentDataError(
                message=f"Experiment directory missing 'analysis/' subdirectory: {exp_dir}\n"
                       f"Expected: {analysis_dir}"
            )
        
        logger.debug("Experiment directory validated: %s", exp_dir)
    
    def _load_experiment_data(self) -> SectionContext:
        """
        Load experiment data from directory.
        
        Returns:
            SectionContext with loaded data
            
        Raises:
            ExperimentDataError: If required files missing or invalid
        """
        exp_dir = self.config.experiment_dir
        
        try:
            # Load config/experiment.yaml
            config_file = exp_dir / "config" / "experiment.yaml"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    exp_config = yaml.safe_load(f)
                frameworks = exp_config.get('frameworks', [])
                num_runs = exp_config.get('num_runs', 50)
            else:
                logger.warning("experiment.yaml not found, using defaults")
                frameworks = []
                num_runs = 50
            
            # Load analysis/metrics.json
            metrics_file = exp_dir / "analysis" / "metrics.json"
            if not metrics_file.exists():
                raise ExperimentDataError(
                    message=f"Required file not found: {metrics_file}"
                )
            
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
            
            metrics = metrics_data.get('metrics', {})
            statistical_results = metrics_data.get('statistical_tests', {})
            
            # If frameworks not in config, extract from metrics
            if not frameworks:
                frameworks = list(metrics.keys())
            
            # Load analysis/statistical_report.md (if exists)
            report_file = exp_dir / "analysis" / "statistical_report.md"
            if report_file.exists():
                statistical_report = report_file.read_text()
                # Extract key findings from report (simple heuristic)
                key_findings = self._extract_key_findings(statistical_report)
            else:
                statistical_report = ""
                key_findings = []
            
            # Create context
            context = SectionContext(
                section_name="",  # Will be set by each generator
                experiment_summary=f"Empirical comparison of {len(frameworks)} multi-agent frameworks for software development",
                frameworks=frameworks,
                num_runs=num_runs,
                metrics=metrics,
                statistical_results=statistical_results,
                key_findings=key_findings
            )
            
            logger.info("Loaded experiment data: %d frameworks, %d runs", 
                       len(frameworks), num_runs)
            
            return context
            
        except Exception as e:
            raise ExperimentDataError(
                message=f"Failed to load experiment data: {str(e)}"
            ) from e
    
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
                    sections[section_name] = prose
                    logger.info("  ✓ %s: %d words (full prose)", section_name, len(prose.split()))
                except Exception as e:
                    logger.error("  ✗ %s: %s", section_name, str(e))
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
            
            if result.returncode != 0:
                # Compilation failed
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
        
        pdf_file = output_dir / f"{latex_file.stem}.pdf"
        
        if pdf_file.exists():
            logger.info("PDF compiled successfully: %s", pdf_file)
            return pdf_file
        else:
            raise PdfCompilationError(
                message="PDF file not generated despite successful pdflatex run"
            )
