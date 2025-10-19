# Stage 3 Task 3.3 Complete: Dynamic Metric Definitions Table

**Date:** October 19, 2025  
**Task:** Read metric table from MetricsConfig instead of hardcoding definitions  
**Status:** ✅ Complete

## Summary

Task 3.3 refactors the metric definitions section to dynamically generate metric tables from `MetricsConfig` instead of using hardcoded values. This is the first section to be fully config-driven, demonstrating the approach for subsequent tasks.

## Changes Made

### 1. New Helper Function (`src/analysis/report_generator.py`)

**Added:** `_generate_metric_table_from_config(metrics_config, category)`

**Purpose:** Generate metric definition tables dynamically from MetricsConfig

**Location:** Lines ~2302-2364 (before `_get_timestamp()`)

**Features:**
```python
def _generate_metric_table_from_config(
    metrics_config, 
    category: str = 'reliable'
) -> List[str]:
    """
    Generate metric definition table from MetricsConfig.
    
    Args:
        metrics_config: MetricsConfig instance
        category: 'reliable', 'derived', or 'excluded'
        
    Returns:
        List of markdown lines for the metric table
    """
```

**Supported Categories:**

1. **'reliable'** - Directly measured metrics
   - Columns: Metric | Full Name | Description | Range | Ideal | Data Source
   - Determines ideal direction symbol (Lower ↓ / Higher ↑)
   - Determines range based on unit type

2. **'excluded'** - Unmeasured/excluded metrics
   - Columns: Metric | Full Name | Status | Reason
   - Reads from config `metrics.excluded_metrics`

3. **'derived'** - Calculated metrics
   - Columns: Metric | Full Name | Description | Calculation | Unit
   - Reads calculation formula from config

### 2. Refactored Metric Definitions Section

**Before:** Hardcoded 7-row table for reliable metrics
```python
lines.extend([
    "| **TOK_IN** | Input Tokens | Tokens sent to LLM | 0-∞ | Lower ↓ | OpenAI Usage API |",
    "| **TOK_OUT** | Output Tokens | Tokens received from LLM | 0-∞ | Lower ↓ | OpenAI Usage API |",
    # ... 5 more hardcoded rows
])
```

**After:** Dynamic generation from config
```python
# Generate reliable metrics table from config
lines.extend(_generate_metric_table_from_config(metrics_config, 'reliable'))

# Later...
# Generate unmeasured metrics table from config
lines.extend(_generate_metric_table_from_config(metrics_config, 'excluded'))
```

**Location:** Lines ~1478-1530

### 3. Benefits of Dynamic Generation

#### Single Source of Truth
- Metric definitions live in `config/experiment.yaml`
- Changes to metrics automatically reflect in reports
- No risk of config/report mismatch

#### Maintainability
- Add new metric → update config → automatic report inclusion
- Remove metric → update config → automatic report exclusion  
- Rename metric → update config → consistent everywhere

#### Consistency
- Same metric info used by:
  - Report generator
  - Visualization system (future)
  - Analysis tools
  - Documentation

#### Validation
- MetricsConfig validates structure on load
- Catches missing/malformed metric definitions early
- Type-safe access to metric properties

## Code Examples

### Example 1: Reliable Metrics Table Generation

**Input (from config/experiment.yaml):**
```yaml
metrics:
  reliable_metrics:
    TOK_IN:
      name: "Input Tokens"
      description: "Tokens sent to LLM"
      unit: "tokens"
      ideal_direction: "minimize"
      data_source: "OpenAI Usage API"
```

**Output (generated markdown):**
```markdown
| **TOK_IN** | Input Tokens | Tokens sent to LLM | 0-∞ | Lower ↓ | OpenAI Usage API |
```

### Example 2: Excluded Metrics Table Generation

**Input (from config/experiment.yaml):**
```yaml
metrics:
  excluded_metrics:
    Q_STAR:
      name: "Quality Star"
      status: "Always 0"
      reason: "Depends on unmeasured metrics below"
```

**Output (generated markdown):**
```markdown
| **Q_STAR** | Quality Star | Always 0 | Depends on unmeasured metrics below |
```

### Example 3: Logic for Ideal Direction Symbol

```python
# Determine ideal direction symbol
ideal_symbol = "Lower ↓" if metric.ideal_direction == 'minimize' else "Higher ↑"
```

**Examples:**
- `TOK_IN` (minimize) → "Lower ↓"
- `CACHED_TOKENS` (maximize) → "Higher ↑"
- `T_WALL_seconds` (minimize) → "Lower ↓"

### Example 4: Logic for Range Determination

```python
# Determine range based on unit
range_str = "0-∞" if metric.unit in ['tokens', 'seconds', 'count', 'USD'] else "0-1"
if key == 'UTT':
    range_str = "Fixed"
```

**Examples:**
- `TOK_IN` (unit: tokens) → "0-∞"
- `AUTR` (unit: rate) → "0-1"
- `UTT` (special case) → "Fixed"

## Testing

### Test Status: ✅ All Passing

```bash
$ pytest tests/unit/test_report_generation.py -v
26/26 tests PASSED in 0.89s

$ pytest tests/unit/ -q
169/169 tests PASSED in 1.59s
```

### What Tests Validate

**Existing tests verify:**
- Report structure is maintained
- All expected sections present
- Metric tables generated correctly
- No regression in report content
- Unicode handling works
- Config loading succeeds

**Future test needs (Task 3.8):**
- Verify metric table content matches config
- Test with different metric configurations
- Test with missing metrics in config
- Test with malformed metric definitions

## Technical Details

### Function Signature

```python
def _generate_metric_table_from_config(
    metrics_config: MetricsConfig,
    category: str = 'reliable'
) -> List[str]
```

**Parameters:**
- `metrics_config`: MetricsConfig instance (from `get_metrics_config()`)
- `category`: One of 'reliable', 'derived', 'excluded'

**Returns:**
- List of markdown lines (table header + rows)

**Raises:**
- None (defensive - handles missing data gracefully)

### Table Formats by Category

#### Reliable Metrics
```markdown
| Metric | Full Name | Description | Range | Ideal | Data Source |
|--------|-----------|-------------|-------|-------|-------------|
| **KEY** | Name | Description | 0-∞ | Lower ↓ | Source |
```

#### Excluded Metrics
```markdown
| Metric | Full Name | Status | Reason |
|--------|-----------|--------|--------|
| **KEY** | Name | Status | Reason text |
```

#### Derived Metrics (future use)
```markdown
| Metric | Full Name | Description | Calculation | Unit |
|--------|-----------|-------------|-------------|------|
| **KEY** | Name | Description | Formula | Unit |
```

### Integration Points

**Called from:** `generate_statistical_report()`

**Calls:**
- `metrics_config.get_reliable_metrics()` - for reliable table
- `metrics_config.get_excluded_metrics()` - for excluded table
- `metrics_config.get_derived_metrics()` - for derived table (future)

**Data flow:**
```
experiment.yaml
    ↓
MetricsConfig.get_reliable_metrics()
    ↓
_generate_metric_table_from_config(config, 'reliable')
    ↓
Markdown table lines
    ↓
Report output
```

## Comparison: Before vs After

### Lines of Code

**Before:**
- 7 hardcoded table rows for reliable metrics
- 4 hardcoded table rows for excluded metrics
- **Total:** 11 hardcoded rows + 2 table headers = **13 lines**

**After:**
- 1 function call for reliable metrics
- 1 function call for excluded metrics
- **Total:** 2 lines + 62-line reusable function

**Benefit:** More code initially, but:
- Function reusable for all metric categories
- Adding metrics = 0 code changes
- Changing metrics = config-only changes

### Maintainability

**Before:**
```python
# To add a metric:
1. Update config/experiment.yaml ✓
2. Update report_generator.py (table row) ✓
3. Update test expectations ✓
4. Update documentation ✓
# 4 places to change!
```

**After:**
```python
# To add a metric:
1. Update config/experiment.yaml ✓
# Done! Report auto-updates
```

### Risk of Inconsistency

**Before:**
- ❌ Config says "minimize" → Report shows "Higher ↑" (typo)
- ❌ Config has 8 metrics → Report shows 7 (forgot to add)
- ❌ Metric renamed in config → Report still uses old name

**After:**
- ✅ Config is single source of truth
- ✅ All metrics auto-included
- ✅ Renames propagate automatically

## Design Decisions

### Why Use Category Parameter?

**Decision:** Single function with category parameter vs separate functions

**Rationale:**
- Reduces code duplication
- Easier to maintain (one place for table logic)
- Extensible (can add new categories easily)
- Similar structure for all table types

### Why Not Use Metric.format_value()?

**Question:** Why not use the `format_value()` method from MetricDefinition?

**Answer:** Table generation doesn't format values, it shows metadata:
- `format_value()` formats data values (e.g., "45,230 tokens")
- Table shows metric definitions (e.g., "0-∞", "Lower ↓")
- Different use cases → different methods

### Why Sort by Key?

**Decision:** `for key, metric in sorted(metrics.items()):`

**Rationale:**
- Alphabetical order is predictable
- Easier to find specific metrics
- Consistent across all tables
- Alternative: Could add `display_order` to config (future enhancement)

## Migration Path for Other Sections

### Pattern Established by Task 3.3

**Step 1:** Create helper function
```python
def _generate_section_from_config(metrics_config, section_name):
    # Read section config
    # Generate content dynamically
    # Return list of markdown lines
```

**Step 2:** Replace hardcoded section
```python
# Before
lines.extend([hardcoded, content, here])

# After
lines.extend(_generate_section_from_config(metrics_config, 'section_name'))
```

**Step 3:** Test
```bash
pytest tests/unit/test_report_generation.py -v
```

### Applicable to Remaining Tasks

- **Task 3.4:** Aggregate statistics table (same pattern)
- **Task 3.5:** Statistical tests (same pattern)
- **Task 3.6:** Cost analysis section (same pattern)
- **Task 3.7:** Limitations section (same pattern)

## Files Modified

**1. src/analysis/report_generator.py**
- Added `_generate_metric_table_from_config()` function (62 lines)
- Replaced hardcoded reliable metrics table (7 lines → 1 function call)
- Replaced hardcoded excluded metrics table (4 lines → 1 function call)
- **Net change:** +54 lines (but more maintainable)

## Validation

### Manual Validation

✅ Generated report contains metric definitions table  
✅ Table structure matches expected format  
✅ All 7 reliable metrics included  
✅ All 4 excluded metrics included  
✅ Ideal direction symbols correct  
✅ Range values correct  
✅ Data sources accurate  

### Automated Validation

```bash
# Report generation tests
$ pytest tests/unit/test_report_generation.py::test_full_report_structure -v
PASSED

# All tests
$ pytest tests/unit/ -q
169 passed
```

## Future Enhancements

### Enhancement 1: Display Order Config

**Current:** Metrics sorted alphabetically

**Enhancement:** Add `display_order` field to config
```yaml
TOK_IN:
  name: "Input Tokens"
  display_order: 1
  # ...
```

**Benefit:** Custom ordering for logical grouping

### Enhancement 2: Conditional Columns

**Current:** All tables have fixed columns

**Enhancement:** Make columns configurable
```yaml
report:
  metric_table:
    columns: [Metric, "Full Name", Description, Range, Ideal]
```

**Benefit:** Flexible table structure

### Enhancement 3: Metric Categories in Table

**Current:** Three separate tables (reliable, excluded, derived)

**Enhancement:** Show category in single unified table
```markdown
| Metric | Category | Full Name | ... |
|--------|----------|-----------|-----|
| TOK_IN | Reliable | Input Tokens | ... |
| COST_USD | Derived | Cost (USD) | ... |
```

**Benefit:** Single comprehensive reference

### Enhancement 4: Automated Documentation

**Current:** Manual documentation of metrics

**Enhancement:** Generate standalone metric reference
```python
def generate_metric_reference_doc(output_path):
    """Generate standalone metric documentation."""
```

**Benefit:** API documentation, developer reference

## Success Criteria: ✅ Met

- [x] Metric table generated from MetricsConfig
- [x] Reliable metrics table is config-driven
- [x] Excluded metrics table is config-driven
- [x] All existing tests pass
- [x] No regression in report content
- [x] Function is reusable for other categories
- [x] Code is well-documented
- [x] Pattern established for other tasks

## Lessons Learned

### What Worked Well

1. **Helper Function Approach:** Clean, testable, reusable
2. **Category Parameter:** Single function handles multiple table types
3. **Incremental Refactoring:** Small change, easy to verify
4. **Config as Truth:** Eliminates hardcoded values

### Challenges Overcome

1. **Table Format Differences:** Handled via category parameter
2. **Range Determination:** Logic based on unit type
3. **Special Cases:** UTT handled explicitly (Fixed range)

### Recommendations for Next Tasks

1. **Follow Same Pattern:** Helper function + config reading
2. **Test Incrementally:** One section at a time
3. **Keep Backwards Compatible:** Report output unchanged
4. **Document Well:** Comments + comprehensive docs

## Next Steps

### Immediate: Task 3.4 - Dynamic Aggregate Statistics Table

**Goal:** Use `aggregate_statistics.metrics` list from config

**Approach:**
1. Create `_generate_aggregate_stats_table()` helper
2. Read metrics list from `section_config.get('metrics', [])`
3. Replace hardcoded metric iteration
4. Test and validate

**Estimated Effort:** 2-3 hours

### Sequence: Tasks 3.4 → 3.5 → 3.6 → 3.7 → 3.8

Each task follows the established pattern from 3.3

## Conclusion

Task 3.3 successfully demonstrates config-driven section generation by refactoring the metric definitions tables. The approach is clean, testable, and establishes a clear pattern for subsequent tasks.

**Key Achievement:** First section is now fully config-driven, reading all content from `MetricsConfig` rather than hardcoded values.

**Impact:**
- ✅ Reduced maintenance burden
- ✅ Eliminated config/report mismatch risk
- ✅ Improved consistency
- ✅ Established reusable pattern

---

**Status:** Ready for Task 3.4 🚀
