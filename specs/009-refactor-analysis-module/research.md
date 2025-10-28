# Research: Configuration Patterns & Validation Strategies

**Feature**: 009-refactor-analysis-module  
**Phase**: 0 (Outline & Research)  
**Date**: 2025-10-28

## Research Questions

### 1. How to implement auto-discovery of metrics from run data?

**Decision**: Scan metrics.json files at report generation time

**Rationale**:
- Run data schema has `aggregate_metrics` dictionary with all collected metrics
- Simple set intersection: `metrics_in_config ∩ metrics_in_data = metrics_with_data`
- Metrics in data but not in config → fail-fast validation error
- Metrics in config but not in data → appear in limitations section

**Implementation Pattern**:
```python
def _discover_metrics_with_data(run_files: List[Path], metrics_config: MetricsConfig) -> Set[str]:
    """Auto-discover which metrics have collected data."""
    all_data_metrics = set()
    
    for run_file in run_files:
        with open(run_file) as f:
            run_data = json.load(f)
            all_data_metrics.update(run_data.get('aggregate_metrics', {}).keys())
    
    # Validate: all data metrics must be in config
    config_metrics = set(metrics_config.get_all_metrics().keys())
    unknown_metrics = all_data_metrics - config_metrics
    
    if unknown_metrics:
        raise MetricsValidationError(
            f"Unknown metrics found in run data: {unknown_metrics}. "
            f"Add to experiment.yaml metrics section or remove from data."
        )
    
    return all_data_metrics & config_metrics  # Metrics both configured and collected
```

**Alternatives Considered**:
- Pre-categorization in config (rejected: requires manual maintenance, violates DRY)
- Heuristic guessing (rejected: not scientific, error-prone)

---

### 2. What's the best pattern for fail-fast config validation?

**Decision**: Implement strict helper functions `_require_config_value()` and `_require_nested_config()`

**Rationale**:
- Constitution principle XIII: "Fail-Fast Philosophy - No fallback mechanisms"
- Clear error messages better than silent None propagation
- Easier debugging (errors point to exact missing key)
- Forces config completeness (no hidden requirements)

**Implementation Pattern**:
```python
def _require_config_value(config: Dict, key: str, context: str) -> Any:
    """
    Get required config value with fail-fast validation.
    
    Args:
        config: Configuration dictionary
        key: Required key name
        context: Human-readable context for error message
        
    Returns:
        Config value
        
    Raises:
        ConfigValidationError: If key missing with actionable error message
    """
    if key not in config:
        raise ConfigValidationError(
            f"Missing required config key '{key}' in {context}.\n"
            f"Expected keys: {list(config.keys())}\n"
            f"Add '{key}' to your experiment.yaml under {context}."
        )
    
    value = config[key]
    if value is None:
        raise ConfigValidationError(
            f"Config key '{key}' in {context} cannot be null.\n"
            f"Provide a valid value for '{key}'."
        )
    
    return value

def _require_nested_config(config: Dict, path: List[str]) -> Any:
    """Get nested config value with path-aware error messages."""
    current = config
    for i, key in enumerate(path):
        partial_path = '.'.join(path[:i+1])
        if not isinstance(current, dict):
            raise ConfigValidationError(
                f"Invalid config structure at '{partial_path}'. "
                f"Expected dict, got {type(current).__name__}."
            )
        current = _require_config_value(current, key, partial_path)
    return current
```

**Alternatives Considered**:
- `.get(key, default)` with fallbacks (rejected: violates fail-fast principle)
- Try/except KeyError (rejected: generic errors, poor user experience)
- Pydantic validation models (rejected: adds dependency, overkill for simple validation)

---

### 3. How to handle the config format migration?

**Decision**: Provide migration script + comprehensive documentation, no backward compatibility

**Rationale**:
- Constitution principle XII: "No Backward Compatibility Burden"
- One-time migration acceptable for improved architecture
- Clear migration guide reduces friction
- Breaking change is well-justified (eliminates hardcoded values)

**Migration Strategy**:
1. **Documentation**: Create `docs/CONFIG_MIGRATION_GUIDE.md` with before/after examples
2. **Validation**: New code validates config format, provides clear error on old format
3. **Detection**: Check for old subsections (`reliable_metrics`, `derived_metrics`, `excluded_metrics`)
4. **Error Message**: Point users to migration guide if old format detected

**Implementation Pattern**:
```python
def _detect_old_config_format(config: Dict) -> bool:
    """Detect if config uses old 3-subsection format."""
    metrics_section = config.get('metrics', {})
    old_keys = {'reliable_metrics', 'derived_metrics', 'excluded_metrics'}
    return bool(old_keys & set(metrics_section.keys()))

def _validate_config_format(config: Dict) -> None:
    """Validate config uses new unified format."""
    if _detect_old_config_format(config):
        raise ConfigMigrationError(
            "Detected old config format with reliable_metrics/derived_metrics/excluded_metrics subsections.\n"
            "Please migrate to new unified format. See docs/CONFIG_MIGRATION_GUIDE.md\n\n"
            "Quick migration:\n"
            "  OLD: metrics:\n"
            "         reliable_metrics:\n"
            "           TOK_IN: {...}\n"
            "  NEW: metrics:\n"
            "         TOK_IN: {...}\n"
        )
```

**Alternatives Considered**:
- Automatic migration (rejected: risky, hides changes from users)
- Dual support for both formats (rejected: complexity, violates principle XII)
- Gradual deprecation (rejected: delays benefits, increases maintenance burden)

---

### 4. Best practices for MetricsConfig API simplification?

**Decision**: Replace category-specific getters with unified `get_all_metrics()` and filtering

**Rationale**:
- Single source of truth (all metrics in one section)
- Filtering happens at report generation time based on actual data
- Simpler API surface (fewer methods to maintain)
- More flexible (can filter by any attribute, not just category)

**New API Design**:
```python
class MetricsConfig:
    def get_all_metrics(self) -> Dict[str, MetricDefinition]:
        """Get all metric definitions."""
        return self._metrics.copy()
    
    def get_metric(self, key: str) -> Optional[MetricDefinition]:
        """Get specific metric definition."""
        return self._metrics.get(key)
    
    def get_metrics_by_category(self, category: str) -> Dict[str, MetricDefinition]:
        """Filter metrics by category."""
        return {
            key: metric for key, metric in self._metrics.items()
            if metric.category == category
        }
    
    def get_metrics_by_filter(self, **filters) -> Dict[str, MetricDefinition]:
        """Flexible filtering by any attribute."""
        results = {}
        for key, metric in self._metrics.items():
            if all(getattr(metric, k, None) == v for k, v in filters.items()):
                results[key] = metric
        return results
```

**Removed Methods**:
- `get_reliable_metrics()` - replaced by auto-discovery
- `get_derived_metrics()` - replaced by filtering
- `get_excluded_metrics()` - replaced by auto-discovery (metrics without data)

**Alternatives Considered**:
- Keep separate methods, make them filter-based (rejected: API bloat)
- Use query language (rejected: overkill for simple filtering)

---

### 5. How to generate limitations section dynamically?

**Decision**: Compare configured metrics against metrics with data, document missing ones

**Rationale**:
- Scientific transparency requires documenting what wasn't measured
- Auto-generated from ground truth (run data) prevents staleness
- Uses status/reason fields from config for explanations

**Implementation Pattern**:
```python
def _generate_limitations_section(
    metrics_config: MetricsConfig,
    metrics_with_data: Set[str]
) -> List[str]:
    """
    Generate limitations section listing unmeasured metrics.
    
    Args:
        metrics_config: Metrics configuration
        metrics_with_data: Set of metric keys that have collected data
        
    Returns:
        List of markdown lines for limitations section
    """
    lines = ["## Limitations\n\n"]
    
    all_metrics = metrics_config.get_all_metrics()
    unmeasured = set(all_metrics.keys()) - metrics_with_data
    
    if not unmeasured:
        lines.append("**No measurement limitations detected.** All configured metrics have collected data.\n\n")
        return lines
    
    lines.append("**Unmeasured Metrics**: The following metrics are defined but have no collected data:\n\n")
    
    for metric_key in sorted(unmeasured):
        metric = all_metrics[metric_key]
        status = getattr(metric, 'status', 'not_measured')
        reason = getattr(metric, 'reason', 'No data collected')
        
        lines.append(f"- **{metric.name}** (`{metric_key}`): {reason}\n")
    
    return lines
```

**Alternatives Considered**:
- Manual documentation (rejected: gets stale, violates DRY)
- Hardcoded exclusion lists (rejected: exactly what we're removing)

---

## Technology Stack Summary

- **Python 3.11+**: Target language, already in use
- **PyYAML**: Config parsing, already in requirements.txt
- **pytest**: Testing framework, already in requirements.txt
- **pathlib**: File path handling, Python stdlib
- **dataclasses**: MetricDefinition structure, Python stdlib
- **typing**: Type hints, Python stdlib

**No new dependencies required.**

---

## Risk Mitigation

### Risk 1: Breaking existing experiments

**Mitigation**:
- Comprehensive migration guide
- Clear error messages pointing to docs
- Test with existing experiment data
- Version spec file format change in docs

### Risk 2: Performance degradation from file scanning

**Mitigation**:
- Scan only once at report generation start
- Cache discovered metrics
- Performance requirement: <30s for 50 runs
- Current implementation likely faster (no redundant iterations)

### Risk 3: Incomplete validation coverage

**Mitigation**:
- Unit tests for all validation helpers
- Integration tests with malformed configs
- Test all edge cases from spec

---

## Implementation Sequence

1. **Phase 1A**: Update MetricsConfig API (remove subsection methods, add unified interface)
2. **Phase 1B**: Implement validation helpers (_require_config_value, _require_nested_config)
3. **Phase 1C**: Implement auto-discovery logic
4. **Phase 2A**: Refactor report_generator.py (remove hardcoded lists)
5. **Phase 2B**: Update all .get() calls to use validation helpers
6. **Phase 2C**: Implement dynamic limitations section
7. **Phase 3**: Migrate config/experiment.yaml to new format
8. **Phase 4**: Write migration guide
9. **Phase 5**: Comprehensive testing

---

## References

- Feature Spec: `/specs/009-refactor-analysis-module/spec.md`
- BAEs Constitution: `.specify/memory/constitution.md` (principles XII, XIII)
- Current Implementation: `src/analysis/report_generator.py` (lines 609, 2148, 2758)
- Current MetricsConfig: `src/utils/metrics_config.py`
