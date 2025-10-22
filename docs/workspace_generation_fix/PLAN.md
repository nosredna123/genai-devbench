# Workspace Generation Fix Plan

## Problem Statement

Two of the three frameworks (ChatDev and GHSpec) are failing to generate managed system artifacts in the workspace directory, while BAeS is working correctly after recent fixes.

### Current Status
- ✅ **BAeS**: Successfully generates artifacts in `workspace/managed_system/`
- ❌ **ChatDev**: Fails with `ModuleNotFoundError: No module named 'easydict'`
- ❌ **GHSpec**: Fails to generate Python files in workspace

## Root Causes Identified

### ChatDev Issues
1. **Missing dependency**: `easydict` module not installed in virtual environment
2. **Workspace structure**: Need to verify output directory mapping
3. **Validation compatibility**: May need similar fixes as BAeS adapter

### GHSpec Issues
1. **Output location**: Framework may be generating files in different location
2. **Execution errors**: Need to check adapter logs for actual failure cause
3. **Validation compatibility**: May need similar fixes as BAeS adapter

## Success Criteria

All three frameworks must:
1. ✅ Execute without errors
2. ✅ Generate Python files in the correct workspace directory
3. ✅ Pass validation phase
4. ✅ Work consistently across 2 runs

## Implementation Strategy

### Phase 1: ChatDev Fix (Priority 1)
1. **Investigate**: Check adapter logs and execution flow
2. **Fix dependencies**: Add missing `easydict` to requirements
3. **Fix workspace**: Ensure output maps to correct directory
4. **Test**: Run 2-experiment test with all frameworks
5. **Document**: Record changes and lessons learned

### Phase 2: GHSpec Fix (Priority 2)
1. **Investigate**: Analyze execution logs and workspace output
2. **Fix workspace mapping**: Correct output directory configuration
3. **Fix validation**: Ensure adapter validates correctly
4. **Test**: Run 2-experiment test with all frameworks
5. **Document**: Record changes and lessons learned

### Phase 3: DRY Refactoring
1. **Analyze**: Identify common patterns across all three adapters
2. **Extract**: Move shared validation/workspace logic to base adapter
3. **Refactor**: Update all adapters to use shared code
4. **Test**: Verify all frameworks still work
5. **Document**: Update architecture documentation

### Phase 4: Directory Renaming (User-Friendly Structure)
1. **Analyze**: Review current directory naming scheme
2. **Propose**: Create user-friendly naming conventions
3. **Design**: Plan migration strategy preserving backward compatibility
4. **Implement**: Update code to use new directory names
5. **Test**: Verify all frameworks work with new structure
6. **Document**: Update all documentation and examples

**Current Structure:**
```
runs/<framework>/<run-id>/
├── workspace/                    # Contains generated code
│   ├── managed_system/           # Generated application (DO NOT RENAME - contains actual codebase)
│   └── database/                 # Database files (BAeS specific)
├── logs/                         # Execution logs
├── metadata.json                 # Run metadata
├── metrics.json                  # Quality metrics
└── run.tar.gz                    # Archived run
```

**Proposed Improvements:**
- Keep `managed_system/` as-is (contains actual generated codebase)
- Consider renaming `workspace/` to `generated_artifacts/` or `output/` for clarity
- Consider renaming `database/` to `db_files/` or keeping as-is
- Add clear README.md in each run directory explaining structure
- Maintain backward compatibility with existing experiments

**Note:** The `managed_system/` directory must remain unchanged as it contains the actual generated application code structure.

## Testing Protocol

For each framework fix, create a test experiment with:
```yaml
model: gpt-4o-mini
frameworks: baes, chatdev, ghspec
max_runs: 2
```

Validation checklist per framework:
- [ ] No execution errors in logs
- [ ] Python files exist in `workspace/` or `workspace/managed_system/`
- [ ] Validation phase passes
- [ ] Archive phase completes
- [ ] Both runs succeed consistently

## File Structure

```
docs/workspace_generation_fix/
├── PLAN.md (this file)
├── INVESTIGATION.md (findings and analysis)
├── CHATDEV_FIX.md (ChatDev-specific changes)
├── GHSPEC_FIX.md (GHSpec-specific changes)
├── DRY_REFACTORING.md (shared code extraction)
└── COMPLETION_SUMMARY.md (final results)
```

## Timeline

1. **Investigation**: 30 minutes
2. **ChatDev Fix**: 1-2 hours
3. **GHSpec Fix**: 1-2 hours
4. **DRY Refactoring**: 1 hour
5. **Directory Renaming**: 1-2 hours
6. **Final Testing**: 30 minutes

**Total Estimated Time**: 5-8 hours

## Next Steps

1. Read the SpecKit planning prompt to ensure compliance
2. Start Phase 1: ChatDev investigation and fix
3. Document all findings in INVESTIGATION.md
4. Implement fixes following DRY principles
5. Test thoroughly with 2-run experiments
