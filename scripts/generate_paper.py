#!/usr/bin/env python3
"""
generate_paper.py: CLI for generating camera-ready papers from experiment results.

Usage:
    python scripts/generate_paper.py <experiment_dir> [options]
    
Example:
    python scripts/generate_paper.py experiments/my_experiment --output-dir papers/draft1
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    project_root = Path(__file__).parent.parent
    env_file = project_root / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        logging.debug(f"Loaded environment variables from {env_file}")
except ImportError:
    # python-dotenv not installed, environment variables must be set manually
    pass

from src.paper_generation.paper_generator import PaperGenerator
from src.paper_generation.models import PaperConfig
from src.paper_generation.exceptions import PaperGenerationError


def setup_logging(verbose: bool = False):
    """Configure logging for CLI."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Generate camera-ready paper from experiment results',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Basic usage
  python scripts/generate_paper.py experiments/chatdev_vs_metagpt
  
  # Custom output directory
  python scripts/generate_paper.py experiments/my_exp --output-dir papers/draft1
  
  # Skip LaTeX/PDF compilation (faster, for drafts)
  python scripts/generate_paper.py experiments/my_exp --skip-latex
  
  # Export only figures (no paper text)
  python scripts/generate_paper.py experiments/my_exp --figures-only
  
  # Use different AI model
  python scripts/generate_paper.py experiments/my_exp --model gpt-4
  
  # Minimal prose level (less interpretation)
  python scripts/generate_paper.py experiments/my_exp --prose-level minimal
        '''
    )
    
    # Required arguments
    parser.add_argument(
        'experiment_dir',
        type=Path,
        help='Path to experiment directory (must contain analysis/ subdirectory)'
    )
    
    # Optional arguments
    parser.add_argument(
        '--output-dir',
        type=Path,
        help='Output directory for generated paper (default: experiment_dir/paper)'
    )
    
    parser.add_argument(
        '--sections',
        type=str,
        help='Comma-separated list of sections to generate (default: all). '
             'Valid: abstract,introduction,related_work,methodology,results,discussion,conclusion'
    )
    
    parser.add_argument(
        '--metrics-filter',
        type=str,
        help='Comma-separated list of metrics to include in results (default: all). '
             'Example: execution_time,total_cost_usd,test_pass_rate'
    )
    
    parser.add_argument(
        '--prose-level',
        choices=['minimal', 'standard', 'comprehensive'],
        default='standard',
        help='Level of prose detail (default: standard)'
    )
    
    parser.add_argument(
        '--skip-latex',
        action='store_true',
        help='Skip LaTeX conversion and PDF compilation (faster for drafts)'
    )
    
    parser.add_argument(
        '--figures-only',
        action='store_true',
        help='Export only figures without generating paper text (fast figure regeneration)'
    )
    
    parser.add_argument(
        '--model',
        default='gpt-3.5-turbo',
        help='OpenAI model to use for prose generation (default: gpt-3.5-turbo)'
    )
    
    parser.add_argument(
        '--temperature',
        type=float,
        default=0.7,
        help='Temperature for AI generation (0.0-1.0, default: 0.7)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main():
    """Main CLI entry point."""
    args = parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    # Validate experiment directory
    if not args.experiment_dir.exists():
        logger.error("Experiment directory not found: %s", args.experiment_dir)
        return 1
    
    # Set output directory
    output_dir = args.output_dir if args.output_dir else args.experiment_dir / "paper"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Parse sections filter if provided
    sections_filter = None
    if args.sections:
        sections_filter = [s.strip() for s in args.sections.split(',')]
        logger.info("Generating only sections: %s", ', '.join(sections_filter))
    
    # Parse metrics filter if provided
    metrics_filter = None
    if args.metrics_filter:
        metrics_filter = [m.strip() for m in args.metrics_filter.split(',')]
        logger.info("Filtering to metrics: %s", ', '.join(metrics_filter))
    
    try:
        # Create configuration
        config = PaperConfig(
            experiment_dir=args.experiment_dir,
            output_dir=output_dir,
            sections=sections_filter,
            metrics_filter=metrics_filter,
            model=args.model,
            temperature=args.temperature,
            prose_level=args.prose_level,
            skip_latex=args.skip_latex,
            figures_only=args.figures_only
        )
        
        logger.info("Configuration:")
        logger.info("  Experiment: %s", config.experiment_dir)
        logger.info("  Output: %s", config.output_dir)
        logger.info("  Model: %s", config.model)
        logger.info("  Prose level: %s", config.prose_level)
        logger.info("  Skip LaTeX: %s", config.skip_latex)
        logger.info("  Figures only: %s", config.figures_only)
        
        # Create generator
        generator = PaperGenerator(config)
        
        # Generate paper
        logger.info("")
        logger.info("Starting paper generation...")
        logger.info("")
        
        result = generator.generate()
        
        # Display results
        print("\n" + "=" * 80)
        if result.figures_generated > 0 and result.total_word_count == 0:
            # Figures-only mode
            print("✅ Figure export complete!")
            print("=" * 80)
            print(f"Figures generated: {result.figures_generated}")
            print(f"Export time:       {result.generation_time_seconds:.1f} seconds")
            print(f"Output directory:  {config.output_dir / 'figures'}")
            print("\nExported figures:")
            for fig_path in result.figure_paths:
                print(f"  - {fig_path.name}")
        else:
            # Full paper generation mode
            print("✅ Paper generation complete!")
            print("=" * 80)
            print(f"Total words:     {result.total_word_count:,}")
            print(f"Total tokens:    {result.ai_tokens_used:,}")
            print(f"Generation time: {result.generation_time_seconds:.1f} seconds")
            print(f"Figure count:    {len(result.figure_paths)}")
            
            if result.latex_path:
                print(f"LaTeX file:      {result.latex_path}")
            
            if result.pdf_path:
                print(f"PDF file:        {result.pdf_path}")
                print("\n⚠️  IMPORTANT: Review AI-generated content and fill citation placeholders!")
            else:
                print("\n⚠️  PDF not generated (pdflatex not available or --skip-latex used)")
                if result.latex_path:
                    print(f"   Compile manually: cd {result.latex_path.parent} && pdflatex {result.latex_path.name}")
        
        print("=" * 80)
        print("")
        
        return 0
        
    except PaperGenerationError as e:
        logger.error("Paper generation failed: %s", str(e))
        print(f"\n❌ Error: {str(e)}", file=sys.stderr)
        return 1
    
    except KeyboardInterrupt:
        logger.warning("Generation interrupted by user")
        print("\n⚠️  Generation interrupted", file=sys.stderr)
        return 130
    
    except Exception as e:
        logger.exception("Unexpected error during generation")
        print(f"\n❌ Unexpected error: {str(e)}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
