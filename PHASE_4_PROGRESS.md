# Phase 4: User Story 2 - Customization Features

## Progress Summary

### Completed Tasks

#### T041: Create integration tests for section selection ✅
- **File Created**: `tests/paper_generation/test_customization_sections.py`
- **Test Methods** (4 total):
  1. `test_sections_flag_filters_correctly` - Validates `--sections` flag filters correctly
  2. `test_outline_generation_for_nonselected_sections` - Validates non-selected sections get outlines
  3. `test_all_sections_selected_equals_default_behavior` - Validates explicit all = default (PASSING)
  4. `test_invalid_section_names_rejected` - Validates error handling
- **Test Results**: 3 failing, 1 passing (as expected - TDD approach, no implementation yet)
- **Status**: ✅ COMPLETE

#### T042: Create integration tests for metric filtering ✅
- **File Created**: `tests/paper_generation/test_customization_metrics.py`
- **Test Methods** (4 total):
  1. `test_metrics_filter_affects_tables_and_prose` - Validates filtering affects both tables and prose
  2. `test_filtered_metrics_exclude_others` - Validates excluded metrics are minimized
  3. `test_no_metrics_filter_includes_all_metrics` - Validates default includes all
  4. `test_invalid_metric_names_rejected` - Validates error handling
- **Test Results**: Not yet run (will fail - no implementation)
- **Status**: ✅ COMPLETE

#### T043: Create integration tests for prose levels ✅
- **File Created**: `tests/paper_generation/test_customization_prose.py`
- **Test Methods** (5 total):
  1. `test_minimal_prose_shorter_than_standard` - Validates minimal is ≥30% shorter
  2. `test_minimal_avoids_causal_claims` - Validates minimal avoids causal language
  3. `test_comprehensive_more_detailed_than_standard` - Validates comprehensive is ≥20% longer
  4. `test_standard_is_default_prose_level` - Validates default behavior
  5. `test_invalid_prose_level_rejected` - Validates error handling
- **Test Results**: Not yet run (will fail - no implementation)
- **Status**: ✅ COMPLETE

### In Progress Tasks

None currently.

### Remaining Tasks (8 tasks)

#### Implementation Tasks (5 tasks)
- **T044**: Extend `PaperConfig` with section selection and prose level
- **T045**: Extend `PaperGenerator` to respect config sections (skip/outline logic)
- **T046**: Extend `ProseEngine` with prose level parameter
- **T047**: Implement metric filtering in `ResultsGenerator`
- **T048**: Extend CLI to parse new flags

#### Unit Test Tasks (3 tasks)
- **T049**: Unit tests for section filtering logic
- **T050**: Unit tests for prose level variations
- **T051**: Unit tests for metric filtering

## Test Files Summary

| File | Tests | Purpose | Status |
|------|-------|---------|--------|
| `test_customization_sections.py` | 4 | Section selection via `--sections` | ✅ Created, 3 failing |
| `test_customization_metrics.py` | 4 | Metric filtering via `--metrics-filter` | ✅ Created, not run |
| `test_customization_prose.py` | 5 | Prose levels via `--prose-level` | ✅ Created, not run |

## Implementation Plan

### Next Steps (T044-T048)

1. **T044: Extend PaperConfig**
   - Add `sections: Optional[List[str]]` field
   - Add `metrics_filter: Optional[List[str]]` field
   - Add `prose_level: ProseLevel` enum field (minimal/standard/comprehensive)
   - Add validation for section names against allowed list
   - Add validation for metric names against available metrics

2. **T045: Extend PaperGenerator**
   - Modify section generation loop to check `config.sections`
   - If section not in selected list:
     * Generate brief outline (2-3 bullet points, <200 words)
     * Skip AI prose generation
   - If section in selected list:
     * Generate full AI prose as normal

3. **T046: Extend ProseEngine**
   - Add `prose_level` parameter to prose generation
   - Adjust prompts based on level:
     * **Minimal**: Shorter targets, avoid causal claims, stick to observations
     * **Standard**: Current default behavior
     * **Comprehensive**: Longer targets, more detail, deeper analysis

4. **T047: Implement Metric Filtering**
   - Modify `ResultsGenerator` to accept `metrics_filter`
   - Filter statistical tables to only include selected metrics
   - Filter prose generation context to only discuss selected metrics

5. **T048: Extend CLI**
   - Add `--sections` argument (comma-separated list)
   - Add `--metrics-filter` argument (comma-separated list)
   - Add `--prose-level` argument (choices: minimal/standard/comprehensive)
   - Pass parsed values to `PaperConfig`

## Test Failure Analysis

### T041 Test Failures (Expected)

**Failure 1: `test_sections_flag_filters_correctly`**
```
AssertionError: Introduction should be outline only, got 475 words
```
- **Cause**: `--sections` flag is parsed but ignored by PaperGenerator
- **Fix needed**: T045 (implement section filtering logic)

**Failure 2: `test_outline_generation_for_nonselected_sections`**
```
AssertionError: Results should have full prose, got 266 words
```
- **Cause**: All sections get full prose regardless of selection
- **Fix needed**: T045 (implement section filtering logic)

**Failure 3: `test_invalid_section_names_rejected`**
```
assert 0 != 0 (returncode should be non-zero)
```
- **Cause**: Invalid section names silently ignored
- **Fix needed**: T044 (add section name validation in PaperConfig)

**Pass: `test_all_sections_selected_equals_default_behavior`**
- This test passes because both cases generate all sections (default behavior)
- Will continue passing after implementation

## Phase 4 Completion Criteria

- [ ] All 11 tasks complete (T041-T051)
- [ ] All integration tests passing (13 tests across 3 files)
- [ ] All unit tests passing (T049-T051)
- [ ] Manual validation:
  - [ ] `--sections=methodology,results` generates only those with full prose
  - [ ] `--metrics-filter=execution_time,cost` limits tables and prose
  - [ ] `--prose-level=minimal` produces shorter, observation-focused text
  - [ ] `--prose-level=comprehensive` produces longer, detailed text
  - [ ] Invalid inputs rejected with helpful error messages

## Progress Metrics

- **Tasks Complete**: 3/11 (27%)
- **Integration Tests Written**: 13/13 (100%)
- **Implementation Tasks**: 0/5 (0%)
- **Unit Tests**: 0/3 (0%)
- **Overall Phase 4**: 3/11 (27%)

## Timeline

- **Phase 4 Started**: 2025-10-28
- **Tests Created**: 2025-10-28 (T041-T043)
- **Implementation Start**: TBD (T044-T048)
- **Unit Tests**: TBD (T049-T051)
- **Phase 4 Complete**: TBD

## Notes

- Following TDD approach strictly: tests first, then implementation
- All tests expected to fail until implementation tasks complete
- Test quality is high - comprehensive coverage of edge cases
- Ready to proceed with implementation (T044-T048)
