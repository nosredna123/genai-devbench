#!/usr/bin/env python3
"""
Phase 9 End-to-End Integration Test

Tests the complete statistical analysis and paper integration pipeline
with synthetic experiment data.
"""

import sys
import json
import yaml
import tempfile
from pathlib import Path

from src.paper_generation.experiment_analyzer import ExperimentAnalyzer
from src.paper_generation.paper_generator import PaperGenerator
from src.paper_generation.models import PaperConfig


def create_test_experiment(exp_dir: Path):
    """Create a complete test experiment directory with synthetic data."""
    
    # Framework configurations
    frameworks_data = {
        'baseline': {
            'runs': [
                {'execution_time': 10.0, 'api_calls': 15, 'tokens_total': 1000, 'cost': 0.01},
                {'execution_time': 10.2, 'api_calls': 15, 'tokens_total': 1020, 'cost': 0.01},
                {'execution_time': 10.1, 'api_calls': 16, 'tokens_total': 1100, 'cost': 0.011},
                {'execution_time': 10.4, 'api_calls': 15, 'tokens_total': 980, 'cost': 0.01},
                {'execution_time': 10.3, 'api_calls': 16, 'tokens_total': 1050, 'cost': 0.011},
            ]
        },
        'optimized': {
            'runs': [
                {'execution_time': 5.0, 'api_calls': 8, 'tokens_total': 500, 'cost': 0.005},
                {'execution_time': 5.2, 'api_calls': 8, 'tokens_total': 520, 'cost': 0.005},
                {'execution_time': 5.0, 'api_calls': 9, 'tokens_total': 550, 'cost': 0.0055},
                {'execution_time': 5.1, 'api_calls': 8, 'tokens_total': 490, 'cost': 0.005},
                {'execution_time': 5.2, 'api_calls': 9, 'tokens_total': 530, 'cost': 0.0055},
            ]
        }
    }
    
    # Create runs directory structure
    runs_dir = exp_dir / 'runs'
    for framework, data in frameworks_data.items():
        fw_dir = runs_dir / framework
        fw_dir.mkdir(parents=True)
        
        for i, run in enumerate(data['runs']):
            run_id = f'run_{i+1:03d}'
            run_dir = fw_dir / run_id
            run_dir.mkdir()
            
            # Create metrics.json with verification
            metrics = {
                'duration_total': run['execution_time'],
                'api_calls_total': run['api_calls'],
                'tokens_total': run['tokens_total'],
                'tokens_in': int(run['tokens_total'] * 0.7),
                'tokens_out': int(run['tokens_total'] * 0.3),
                'cached_tokens': 0,
                'cost_total': run['cost'],
                'usage_api_reconciliation': {
                    'verification_status': 'verified'
                }
            }
            
            with open(run_dir / 'metrics.json', 'w') as f:
                json.dump(metrics, f, indent=2)
    
    # Create config.yaml
    config_content = {
        'model': 'gpt-4o-mini',
        'pricing': {
            'models': {
                'gpt-4o-mini': {
                    'input': 0.00001,
                    'output': 0.00003
                }
            }
        }
    }
    
    with open(exp_dir / 'config.yaml', 'w') as f:
        yaml.dump(config_content, f)
    
    # Create experiment.yaml in config directory
    config_dir = exp_dir / 'config'
    config_dir.mkdir(exist_ok=True)
    
    exp_config = {
        'frameworks': ['baseline', 'optimized'],
        'num_runs': 5,
        'experiment_name': 'Test Statistical Integration'
    }
    
    with open(config_dir / 'experiment.yaml', 'w') as f:
        yaml.dump(exp_config, f)


def validate_output(output_dir: Path):
    """Validate that all expected outputs were generated."""
    
    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    
    results = {
        'files_created': [],
        'files_missing': [],
        'validation_checks': []
    }
    
    # Check basic files
    print("\n1. Basic Output Files:")
    basic_files = [
        'metrics.json',
        'statistical_report.md',
    ]
    
    for filename in basic_files:
        file_path = output_dir / filename
        if file_path.exists():
            size = file_path.stat().st_size
            print(f"   ✅ {filename} ({size:,} bytes)")
            results['files_created'].append(filename)
        else:
            print(f"   ❌ {filename} MISSING")
            results['files_missing'].append(filename)
    
    # Check T034/T035 statistical reports
    print("\n2. Statistical Reports (T034/T035):")
    report_files = [
        ('statistical_report_summary.md', 'T034'),
        ('statistical_report_full.md', 'T035'),
    ]
    
    for filename, task in report_files:
        file_path = output_dir / filename
        if file_path.exists():
            size = file_path.stat().st_size
            lines = len(file_path.read_text().split('\n'))
            print(f"   ✅ {filename} ({task}): {size:,} bytes, {lines} lines")
            results['files_created'].append(filename)
        else:
            print(f"   ❌ {filename} ({task}) MISSING")
            results['files_missing'].append(filename)
    
    # Check visualizations
    print("\n3. Statistical Visualizations:")
    viz_dir = output_dir / 'figures' / 'statistical'
    if viz_dir.exists():
        viz_files = list(viz_dir.glob('*.svg'))
        print(f"   ✅ figures/statistical/ directory created")
        print(f"   ✅ {len(viz_files)} SVG files generated:")
        
        viz_types = set()
        for vf in sorted(viz_files):
            print(f"      - {vf.name}")
            if 'box_plot' in vf.name:
                viz_types.add('box')
            elif 'forest_plot' in vf.name:
                viz_types.add('forest')
            elif 'violin_plot' in vf.name:
                viz_types.add('violin')
            elif 'qq_plot' in vf.name:
                viz_types.add('qq')
        
        expected_types = {'box', 'forest', 'violin', 'qq'}
        if viz_types == expected_types:
            print(f"   ✅ All visualization types generated: {', '.join(sorted(viz_types))}")
        else:
            missing = expected_types - viz_types
            print(f"   ⚠️  Missing visualization types: {', '.join(missing)}")
        
        results['files_created'].append(f'figures/statistical/*.svg ({len(viz_files)} files)')
    else:
        print(f"   ❌ figures/statistical/ directory MISSING")
        results['files_missing'].append('figures/statistical/')
    
    # Validate summary report structure (T034)
    print("\n4. Summary Report Structure (T034):")
    summary_file = output_dir / 'statistical_report_summary.md'
    if summary_file.exists():
        content = summary_file.read_text()
        checks = {
            'Quick Start Guide': '🚀' in content or 'Quick Start' in content,
            'Executive Summary': 'Executive Summary' in content,
            'Key Findings': '📊' in content or 'Key Findings' in content,
            'Effect sizes with CIs': '95% CI' in content or 'confidence interval' in content.lower(),
            'Visualizations embedded': '.svg)' in content or 'figures/' in content,
            'Line count <300': len(content.split('\n')) < 300,
        }
        
        for check, passed in checks.items():
            status = '✅' if passed else '❌'
            print(f"   {status} {check}")
            results['validation_checks'].append((f'Summary: {check}', passed))
    
    # Validate full report structure (T035)
    print("\n5. Full Report Structure (T035):")
    full_file = output_dir / 'statistical_report_full.md'
    if full_file.exists():
        content = full_file.read_text()
        line_count = len(content.split('\n'))
        
        checks = {
            'Table of Contents': 'Table of Contents' in content,
            'Descriptive Statistics': 'Descriptive Statistics' in content,
            'Skewness & Kurtosis': 'Skewness' in content and 'Kurtosis' in content,
            'Normality Assessment': 'Normality Assessment' in content or 'Shapiro-Wilk' in content,
            'Assumption Validation': 'Assumption Validation' in content or 'Levene' in content,
            'Statistical Comparisons': 'Statistical Comparisons' in content,
            'Power Analysis': 'Power Analysis' in content,
            'Methodology section': 'Statistical Methodology' in content or 'Methodology' in content,
            'Reproducibility metadata': 'scipy_version' in content or 'Reproducibility' in content,
            'Glossary': 'Glossary' in content,
            'Line count 800-1200': 800 <= line_count <= 1200,
        }
        
        for check, passed in checks.items():
            status = '✅' if passed else '⚠️ ' if 'Line count' in check else '❌'
            print(f"   {status} {check}")
            if 'Line count' in check:
                print(f"      (Actual: {line_count} lines)")
            results['validation_checks'].append((f'Full: {check}', passed))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    total_checks = len(results['validation_checks'])
    passed_checks = sum(1 for _, passed in results['validation_checks'] if passed)
    
    print(f"\nFiles Created: {len(results['files_created'])}")
    print(f"Files Missing: {len(results['files_missing'])}")
    print(f"Validation Checks: {passed_checks}/{total_checks} passed")
    
    if results['files_missing']:
        print(f"\n⚠️  Missing files: {', '.join(results['files_missing'])}")
    
    success = len(results['files_missing']) == 0 and passed_checks == total_checks
    
    return success, results


def main():
    """Run end-to-end integration test."""
    
    print("=" * 80)
    print("PHASE 9 END-TO-END INTEGRATION TEST")
    print("=" * 80)
    print()
    print("This test validates the complete pipeline:")
    print("  - T033: ExperimentAnalyzer with statistical analysis")
    print("  - T034: Summary report generation")
    print("  - T035: Full report generation")
    print("  - Visualization generation (Phases 6-7)")
    print("  - Statistical analysis (Phases 3-5, 8)")
    print()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        exp_dir = Path(tmpdir) / 'test_experiment'
        exp_dir.mkdir()
        output_dir = Path(tmpdir) / 'test_output'
        output_dir.mkdir()
        
        print(f"Test Directories:")
        print(f"  Experiment: {exp_dir}")
        print(f"  Output: {output_dir}")
        print()
        
        # Step 1: Create test data
        print("Step 1: Creating synthetic experiment data...")
        try:
            create_test_experiment(exp_dir)
            print("  ✅ Experiment data created (2 frameworks, 5 runs each)")
        except Exception as e:
            print(f"  ❌ Failed to create experiment: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        # Step 2: Run experiment analysis
        print("\nStep 2: Running ExperimentAnalyzer.analyze() (T033)...")
        try:
            analyzer = ExperimentAnalyzer(exp_dir, output_dir)
            frameworks_data = analyzer.analyze()
            print(f"  ✅ Analysis complete: {len(frameworks_data)} frameworks")
            print(f"     - Statistical analysis performed")
            print(f"     - Visualizations generated")
            print(f"     - Statistical reports created")
        except Exception as e:
            print(f"  ❌ Analysis failed: {e}")
            import traceback
            traceback.print_exc()
            return 1
        
        # Step 3: Validate outputs
        print("\nStep 3: Validating outputs...")
        success, results = validate_output(output_dir)
        
        # Step 4: Test paper integration (T036 parsing only)
        print("\n" + "=" * 80)
        print("PAPER INTEGRATION TEST (T036)")
        print("=" * 80)
        
        try:
            # Create minimal paper config
            config = PaperConfig(
                experiment_dir=exp_dir,
                output_dir=output_dir,
                skip_latex=True,  # Skip LaTeX compilation for this test
                figures_only=True  # Only test data loading, not paper generation
            )
            
            print("\nTesting PaperGenerator._parse_statistical_reports()...")
            generator = PaperGenerator(config)
            
            # The parsing happens in _load_analyzed_data which was already called
            # during initialization, so we can check the results
            if hasattr(generator, 'statistical_data'):
                stat_data = generator.statistical_data
                print(f"  ✅ Statistical data parsed:")
                print(f"     - Comparisons: {len(stat_data.get('comparisons', []))}")
                print(f"     - Visualizations: {len(stat_data.get('visualization_paths', {}))}")
                print(f"     - Power warnings: {len(stat_data.get('power_warnings', []))}")
                print(f"     - Primary metric: {stat_data.get('primary_metric', 'N/A')}")
                print(f"     - Methodology text: {len(stat_data.get('methodology_text', ''))} chars")
                
                # Show sample comparison
                if stat_data.get('comparisons'):
                    comp = stat_data['comparisons'][0]
                    print(f"\n  Sample comparison:")
                    print(f"     {comp.get('framework1')} vs {comp.get('framework2')}")
                    print(f"     Effect size: {comp.get('effect_size', 0):.3f}")
                    print(f"     Magnitude: {comp.get('magnitude', 'unknown')}")
                    print(f"     P-value: {comp.get('p_value', 1.0):.4f}")
            else:
                print(f"  ⚠️  statistical_data attribute not found")
        
        except Exception as e:
            print(f"  ❌ Paper integration test failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Final result
        print("\n" + "=" * 80)
        if success:
            print("✅ PHASE 9 INTEGRATION TEST: PASSED")
        else:
            print("⚠️  PHASE 9 INTEGRATION TEST: ISSUES DETECTED")
        print("=" * 80)
        
        return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
