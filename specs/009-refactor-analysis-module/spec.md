# Feature Specification: Refactor Analysis Module Report Generator

**Feature Branch**: `009-refactor-analysis-module`  
**Created**: 2025-10-28  
**Status**: Draft  
**Scope**: Core refactoring - eliminate hardcoded metrics, implement dynamic config-driven reports with fail-fast validation  
**Follow-up Feature**: 010-paper-generation (camera-ready paper export with ACM format)  
**Input**: User description: "Refactor analysis module to update/fix final analysis report generator according to current codebase features and generated metrics"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Researcher Reviews Accurate Experiment Results (Priority: P1)

A researcher completes a multi-framework experiment run and needs to review statistically sound results that accurately reflect the metrics actually collected by the system, without misleading information about unmeasured capabilities.

**Why this priority**: This is the core value proposition - researchers must be able to trust the analysis reports to make informed decisions about framework capabilities. Inaccurate or misleading metrics undermine the entire research effort.

**Independent Test**: Can be fully tested by running a complete experiment with at least 2 frameworks, generating the statistical report, and verifying that: (1) all metrics shown have corresponding data in the metrics.json files, (2) no hardcoded metric lists exist, (3) excluded metrics are properly documented with reasons, and (4) the report sections match the experiment configuration.

**Acceptance Scenarios**:

1. **Given** an experiment has completed with multiple framework runs, **When** the statistical report is generated, **Then** only metrics with collected data values appear in analysis tables
2. **Given** some metrics defined in MetricsConfig have no data in any run, **When** the report is generated, **Then** those metrics appear only in the limitations section with their configured exclusion reasons
3. **Given** metrics have display formats defined in MetricsConfig, **When** values are displayed, **Then** formatting matches the MetricDefinition specifications exactly

---

### User Story 2 - Researcher Customizes Metric Display (Priority: P2)

A researcher wants metrics to be displayed with appropriate precision, units, and formatting based on their type (tokens, costs, rates, etc.) without manual post-processing.

**Why this priority**: Consistent, professional formatting improves report readability and reduces researcher effort in interpreting results.

**Independent Test**: Can be tested by adding a new metric to MetricsConfig with specific display_format, running an experiment, and verifying the generated report uses that exact formatting.

**Acceptance Scenarios**:

1. **Given** a researcher adds a new metric to MetricsConfig with display formatting, **When** the report is generated, **Then** the new metric automatically appears in appropriate tables if data exists, formatted correctly
2. **Given** different metrics have different display formats (currency, percentages, integers), **When** the report includes metric tables, **Then** values are formatted according to their MetricDefinition specifications
3. **Given** metrics are organized by category in MetricsConfig, **When** the report is generated, **Then** metrics are grouped logically by category in tables

---

### User Story 3 - System Prevents Invalid Metrics (Priority: P1)

The report generator must fail fast when encountering configuration mismatches or attempting to analyze metrics that don't exist in the collected data, preventing silent failures and misleading results.

**Why this priority**: Silent failures and fallback values create scientific validity issues. Researchers must be alerted immediately when configuration doesn't match reality.

**Independent Test**: Can be tested by deliberately creating config/data mismatches (e.g., referencing non-existent metrics, missing required config keys) and verifying the system raises clear, actionable errors before generating any output.

**Acceptance Scenarios**:

1. **Given** experiment.yaml references a metric not in MetricsConfig, **When** report generation starts, **Then** a clear validation error is raised with the missing metric name
2. **Given** collected run data is missing a required metric, **When** attempting aggregation, **Then** the system identifies which runs and metrics are missing
3. **Given** a section configuration is incomplete, **When** the report generator reads it, **Then** a descriptive error indicates the missing required field

---

### Edge Cases

- What happens when a framework has zero completed runs? (validation should prevent report generation)
- How does the system handle metrics defined in config but with no collected values in any run? (appear in limitations section with status/reason from config)
- What if experiment.yaml is missing the metrics section entirely? (should fail with clear error)
- How are metrics appearing in run data but NOT defined in MetricsConfig handled? (fail-fast validation error)
- What happens when stopping rule metrics don't have collected data? (validation error)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST read all metric definitions from a single unified metrics section in MetricsConfig (no separate reliable_metrics, derived_metrics, excluded_metrics subsections)
- **FR-002**: System MUST auto-discover which metrics have data by examining collected run files (dynamic partitioning at report generation time)
- **FR-003**: System MUST only include metrics with actual collected values in analysis tables
- **FR-004**: System MUST generate limitations section dynamically listing metrics from MetricsConfig that have no collected data, using their configured status/reason fields
- **FR-005**: System MUST fail with descriptive errors when required configuration keys are missing (no silent fallbacks)
- **FR-006**: System MUST format metric values using MetricDefinition.format_value() for consistency
- **FR-007**: System MUST organize metrics by category as defined in MetricsConfig
- **FR-008**: System MUST generate metric definition tables using _generate_metric_table_from_config() for all metrics
- **FR-009**: System MUST include data source information for each metric in definition tables
- **FR-010**: System MUST separate metrics with data from metrics without data in distinct report sections based on actual run contents
- **FR-011**: System MUST document why each metric without data is not available using status/reason fields from MetricsConfig
- **FR-012**: System MUST validate framework configuration completeness before accessing framework metadata
- **FR-013**: System MUST use strict configuration validation helpers (_require_config_value, _require_nested_config) instead of permissive .get() calls
- **FR-014**: System MUST aggregate only metrics marked with aggregation != 'none' in MetricsConfig
- **FR-015**: System MUST abort report generation and list all unknown metrics if any metric in run data does not exist in current MetricsConfig (fail-fast validation)
- **FR-016**: System MUST generate all standard report sections (executive summary, metrics tables, statistical tests, cost analysis, limitations) for every report

### Key Entities

- **MetricsConfig**: Central source of truth for all metric definitions with display metadata (formatting, units, categories, descriptions). Contains a single unified metrics section; partitioning into "with data" vs "without data" happens dynamically at report generation time based on actual run contents.
- **MetricDefinition**: Individual metric with name, description, unit, category, formatting, ideal_direction, and optional status/reason fields for documentation
- **ReportSection**: Standard report component (executive summary, cost analysis, limitations, etc.) - all sections are always generated
- **FrameworkMetadata**: Framework identification information (full name, organization, description)
- **AggregateStatistics**: Computed summary statistics (mean, median, CI) for a specific metric across runs

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero metric identifiers appear as string literals or hardcoded lists in report_generator.py (100% dynamic loading from MetricsConfig)
- **SC-002**: All report sections, metric tables, and exclusion lists are generated from configuration files without code changes
- **SC-003**: 100% of required configuration keys are validated with _require_config_value() before use
- **SC-004**: All configuration validation errors include the missing key name, context, and suggested fix
- **SC-005**: Report generation fails with clear error listing any metrics found in run data but missing from current MetricsConfig (strict schema validation)
- **SC-006**: All metric values formatted using MetricDefinition.format_value() match the display_format specification
- **SC-007**: Limitations section automatically updates based on which metrics lack data (no manual documentation sync required)
- **SC-008**: Every generated report contains all standard sections in consistent order (executive summary, foundational concepts, metrics tables, statistical analysis, cost breakdown, limitations)
- **SC-009**: Adding a new metric to MetricsConfig makes it immediately available in reports if data exists, without code changes

## Clarifications

### Session 2025-10-28 - Scope Definition

- Q: When the report generator encounters metrics in historical run data that no longer exist in the current MetricsConfig (e.g., a metric was renamed or removed), how should the system handle this? → A: Fail hard - Abort report generation with error listing missing metrics
- Q: The current report_generator.py contains hardcoded metric lists like `RELIABLE_METRICS = {'TOK_IN', 'TOK_OUT', ...}`. During refactoring, how should we handle the transition? → A: Remove immediately - Delete all hardcoded lists, use MetricsConfig exclusively from start
- Q: Should report sections be configurable (enable/disable via experiment.yaml) or always generate full reports? → A: Always generate full reports - Section configuration is overengineering; complete reports ensure consistency and scientific rigor
- Q: Should metrics be pre-categorized in config as "measured" vs "unmeasured", or should this be auto-discovered from run data? → A: Auto-discover - Single unified metrics section in config, partition dynamically based on which metrics have data at report generation time

### Session 2025-10-28 - Feature Split Decision

- Q: Should paper generation (camera-ready ACM format, Pandoc conversion, comprehensive prose) be included in this refactoring? → A: Split into separate feature 010-paper-generation - This feature focuses on core technical refactoring, paper generation adds later
- **Rationale**: Core refactoring (removing hardcoded metrics, config-driven design, validation) is substantial standalone work (1-2 weeks). Paper generation with ACM templates, figure export, and AI prose generation is separate value stream (2-3 weeks). Splitting enables faster delivery of core improvements.

## Assumptions

- The MetricsConfig singleton is properly initialized before report generation begins
- All experiment runs have completed metrics.json files with consistent structure (validated by schema)
- The _generate_metric_table_from_config() helper function exists and handles all metrics
- The UsageReconciler has already populated aggregate_metrics with token data before report generation
- **Configuration Simplification**: MetricsConfig contains a single unified `metrics` section (not separate reliable/derived/excluded subsections). Metrics are auto-partitioned into "with data" vs "without data" at report generation time by examining actual run files.
- **Metadata Fields**: Each metric definition includes optional `status` (e.g., "not_implemented") and `reason` fields for documentation purposes, used when generating limitations sections.

## Dependencies

- **MetricsConfig API**: Must support get_all_metrics(), get_metric(), get_metrics_by_category() - no separate methods for "measured" vs "unmeasured" (partitioning happens at report generation)
- **Experiment Configuration**: Must have single unified metrics section with all metric definitions including display metadata (format, unit, category) and optional status/reason fields
- **Run Data Schema**: metrics.json files must contain aggregate_metrics dictionary with metric values actually collected during the run

## Non-Goals

- **Paper Generation Features**: Camera-ready paper export, ACM LaTeX format, Pandoc conversion, comprehensive AI-generated prose (deferred to Feature 010-paper-generation)
- **Figure Export Tools**: Standalone figure generation CLI, PDF/PNG export for publications (deferred to Feature 010)
- **Reproducibility Packaging**: Docker support, frozen dependencies, enhanced reproduction guides (deferred to Feature 010)
- Changing the statistical test implementations (Kruskal-Wallis, Cliff's Delta, etc.)
- Modifying the metrics collection process or MetricsCollector behavior
- Implementing real-time report generation during experiment execution
- Creating interactive or HTML report formats (Markdown statistical reports only in this feature)
- Refactoring the visualization generation code (separate concern)
- Maintaining backward compatibility with old config format (reliable_metrics/derived_metrics/excluded_metrics subsections) - this is a breaking config change

## Technical Constraints

- Must maintain Python 3.11+ compatibility
- Must preserve existing report structure and section ordering for consistency
- Must not duplicate metric definitions across multiple configuration sources
- Performance: Report generation should complete within 30 seconds for 50 runs across 3 frameworks

## Configuration Migration

### Old Format (Current - To Be Replaced):
```yaml
metrics:
  reliable_metrics:
    TOK_IN:
      name: "Input Tokens"
      display_format: "{:,.0f}"
      # ...
  derived_metrics:
    COST_USD:
      # ...
  excluded_metrics:
    AUTR:
      name: "Autonomy Rate"
      reason: "HITL detection not implemented"
      status: "not_measured"
```

### New Format (Simplified):
```yaml
metrics:
  TOK_IN:
    name: "Input Tokens"
    display_format: "{:,.0f}"
    unit: "tokens"
    category: "efficiency"
    ideal_direction: "minimize"
    data_source: "openai_usage_api"
    aggregation: "sum"
    # No status field = implemented
  
  COST_USD:
    name: "Total Cost"
    display_format: "${:.4f}"
    unit: "USD"
    category: "cost"
    # Derived via calculation field
    calculation:
      formula: "(TOK_IN - CACHED) * price..."
  
  AUTR:
    name: "Autonomy Rate"
    display_format: "{:.2f}"
    unit: "rate"
    category: "interaction"
    status: "not_implemented"  # Documentation only
    reason: "Requires HITL detection implementation"
```

### Migration Logic:
- **Report generator**: Auto-discovers which metrics have data (no need to check subsections)
- **Limitations section**: Shows metrics with `status: "not_implemented"` OR metrics with no data in runs
- **Breaking change**: Old config files must be updated (one-time migration)
