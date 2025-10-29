#!/usr/bin/env python3
"""
Export Publication Figures from Experiment Results

This script exports high-quality figures (PDF vector + PNG 300 DPI) from
completed experiment results without regenerating the entire paper.

Usage:
    python scripts/export_figures.py /path/to/experiment
    python scripts/export_figures.py /path/to/experiment --output-dir ./figures
    python scripts/export_figures.py /path/to/experiment --formats pdf png --dpi 600
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from paper_generation.figure_exporter import FigureExporter
from paper_generation.models import PaperConfig
from paper_generation.exceptions import (
    FigureExportError,
    DependencyMissingError,
    ConfigValidationError
)


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Export publication-quality figures from experiment data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export figures to default output directory
  python scripts/export_figures.py experiments/my_experiment

  # Specify custom output directory
  python scripts/export_figures.py experiments/my_experiment --output-dir ./figures_output

  # Export with higher DPI
  python scripts/export_figures.py experiments/my_experiment --dpi 600

  # Export only PNG format
  python scripts/export_figures.py experiments/my_experiment --formats png
        """
    )
    
    parser.add_argument(
        'experiment_dir',
        type=Path,
        help='Path to experiment directory containing analysis/metrics.json'
    )
    
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=None,
        help='Output directory for exported figures (default: experiment_dir/paper_output)'
    )
    
    parser.add_argument(
        '--formats',
        nargs='+',
        choices=['pdf', 'png'],
        default=['pdf', 'png'],
        help='Output formats (default: both pdf and png)'
    )
    
    parser.add_argument(
        '--dpi',
        type=int,
        default=300,
        help='DPI for exported figures (default: 300, minimum: 300)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main():
    """Main entry point for figure export CLI."""
    args = parse_args()
    setup_logging(args.verbose)
    
    logger = logging.getLogger(__name__)
    
    try:
        # Validate experiment directory
        if not args.experiment_dir.exists():
            logger.error(f"Experiment directory not found: {args.experiment_dir}")
            return 1
        
        # Set output directory
        output_dir = args.output_dir or (args.experiment_dir / "paper_output")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate DPI
        if args.dpi < 300:
            logger.warning(f"DPI {args.dpi} is below recommended minimum of 300")
        
        logger.info(f"Exporting figures from: {args.experiment_dir}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Formats: {', '.join(args.formats)}")
        logger.info(f"DPI: {args.dpi}")
        
        # Create config
        config = PaperConfig(
            experiment_dir=args.experiment_dir,
            output_dir=output_dir,
            skip_latex=True,
            figures_only=True
        )
        
        # Create exporter
        exporter = FigureExporter(config)
        
        # Load data and export figures
        logger.info("Loading experiment data...")
        context = exporter.load_experiment_data()
        
        logger.info(f"Found {len(context.frameworks)} frameworks")
        logger.info(f"Generating figures...")
        
        figures = exporter.export_figures(context)
        
        # Display results
        print(f"\n✅ Successfully exported {len(figures)} figures:\n")
        
        for i, fig in enumerate(figures, 1):
            print(f"{i}. {fig.pdf_path.name}")
            if 'pdf' in args.formats:
                print(f"   PDF: {fig.pdf_path}")
            if 'png' in args.formats:
                print(f"   PNG: {fig.png_path}")
            print(f"   Caption: {fig.caption[:80]}...")
            print()
        
        print(f"Figures saved to: {output_dir / 'figures'}")
        
        return 0
        
    except DependencyMissingError as e:
        logger.error(f"Missing dependency: {e}")
        return 1
    
    except ConfigValidationError as e:
        logger.error(f"Configuration error: {e}")
        return 1
    
    except FigureExportError as e:
        logger.error(f"Figure export failed: {e}")
        return 1
    
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
