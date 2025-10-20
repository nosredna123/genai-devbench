# Verification Update Implementation Checklist

## Quick Start
```bash
# 1. Create feature branch
git checkout -b feature/efficient-verification

# 2. Follow this checklist in order
# 3. Test after each phase
# 4. Commit incrementally
```

## Phase 1: Data Model Updates ⏳
**Goal**: Add new tracking fields without breaking existing code

- [ ] Update `src/orchestrator/usage_reconciler.py`:
  - [ ] Add `execution` section to metrics dict
  - [ ] Add `token_coverage_rate` calculation
  - [ ] Track `steps_completed` separately from `steps_with_tokens`
  
- [ ] Update `src/orchestrator/experiment_orchestrator.py`:
  - [ ] Pass `steps_completed` to reconciler
  - [ ] Ensure all steps tracked (success + failed)

- [ ] Test:
  ```bash
  # Run reconciliation on test run
  ./runners/reconcile_usage.sh baes 23f46f6b-929e-429b-ba74-4b0d20abc1ed --min-age 0
  
  # Check metrics.json has new fields
  cat runs/baes/23f46f6b-929e-429b-ba74-4b0d20abc1ed/metrics.json | jq '.execution'
  ```

## Phase 2: Verification Logic Update ⏳
**Goal**: Replace strict rule with framework-aware verification

- [ ] Update `src/orchestrator/usage_reconciler.py`:
  - [ ] Add `_get_min_token_coverage(framework)` method
  - [ ] Modify `_check_verification_status()` to use new rules
  - [ ] Update status messages for clarity
  
- [ ] Test:
  ```bash
  # BAeS run with 50% coverage should be verified
  ./runners/reconcile_usage.sh baes 23f46f6b-929e-429b-ba74-4b0d20abc1ed --min-age 0
  # Expect: status=verified, message mentions "3/6 used LLM, 3/6 used templates"
  
  # Previous runs should still work
  ./runners/reconcile_usage.sh baes 6d5f179c-c3a6-404b-98be-ca536e72f01b --min-age 0
  ```

## Phase 3: Configuration Support ⏳
**Goal**: Make thresholds configurable per framework

- [ ] Update `config/experiment.yaml`:
  - [ ] Add `verification` section
  - [ ] Add framework-specific thresholds
  
- [ ] Update `src/orchestrator/usage_reconciler.py`:
  - [ ] Load config in `__init__`
  - [ ] Read thresholds from config in `_get_min_token_coverage()`
  - [ ] Add validation for config values
  
- [ ] Test:
  ```bash
  # Modify threshold in config to 0.4, verify it's respected
  # Modify to 1.0, verify BAeS run becomes warning
  ```

## Phase 4: Documentation Updates ⏳
**Goal**: Explain new verification model clearly

- [ ] Update `docs/VERIFICATION_RULES.md`:
  - [ ] Replace old rules with new multi-dimensional model
  - [ ] Add framework comparison section
  - [ ] Add efficiency vs completeness explanation
  
- [ ] Update `docs/quickstart.md`:
  - [ ] Update verification status interpretation
  - [ ] Add examples of each status
  
- [ ] Update `README.md`:
  - [ ] Update verification section if mentioned

## Phase 5: Migrate Existing Runs ⏳
**Goal**: Update all existing runs with new verification status

- [ ] Create `scripts/update_verification_status.py`:
  - [ ] Load runs_manifest.json
  - [ ] For each run with metrics.json:
    - [ ] Calculate new verification status
    - [ ] Update metrics.json
    - [ ] Update manifest entry
  - [ ] Backup manifest before changes
  
- [ ] Run migration:
  ```bash
  # Backup first!
  cp runs/runs_manifest.json runs/runs_manifest.json.pre-verification-update
  
  # Run migration
  python scripts/update_verification_status.py
  
  # Verify BAeS runs updated correctly
  grep -A 5 "23f46f6b" runs/runs_manifest.json
  ```

## Phase 6: Update Analysis & Reporting ⏳
**Goal**: Show efficiency metrics in reports

- [ ] Update `src/analysis/report_generator.py`:
  - [ ] Add efficiency analysis section
  - [ ] Show execution vs token metrics separately
  - [ ] Add cost-per-feature calculation
  
- [ ] Generate new report:
  ```bash
  ./runners/analyze_results.sh
  
  # Check efficiency section exists
  cat analysis_output/report.md | grep -A 20 "Efficiency Analysis"
  ```

## Testing Checklist ⏳

### Unit Tests
- [ ] Write `tests/unit/test_verification_logic.py`:
  - [ ] `test_baes_with_50_percent_coverage_is_verified()`
  - [ ] `test_chatdev_with_50_percent_coverage_is_warning()`
  - [ ] `test_execution_incomplete_is_failed()`
  - [ ] `test_data_unstable_is_warning()`
  - [ ] `test_first_attempt_is_pending()`

- [ ] Run tests:
  ```bash
  pytest tests/unit/test_verification_logic.py -v
  ```

### Integration Tests
- [ ] Run full BAeS experiment:
  ```bash
  ./runners/run_experiment.sh --framework baes --runs 1
  ```
  - [ ] Verify new run has correct verification status
  - [ ] Check metrics.json has all new fields
  
- [ ] Run reconciliation on all frameworks:
  ```bash
  # Find recent runs for each framework
  ./runners/reconcile_usage.sh baes <run_id> --min-age 0
  ./runners/reconcile_usage.sh chatdev <run_id> --min-age 0
  ./runners/reconcile_usage.sh ghspec <run_id> --min-age 0
  ```

### Manual Verification
- [ ] Check BAeS run `23f46f6b-929e-429b-ba74-4b0d20abc1ed`:
  - [ ] Status should be `verified`
  - [ ] Message should mention "3/6 used LLM, 3/6 used templates"
  - [ ] `token_coverage_rate` should be 0.5
  
- [ ] Check a ChatDev run with 100% coverage:
  - [ ] Status should still be `verified`
  - [ ] Message should mention "complete token coverage"

## Pre-Merge Checklist ⏳

- [ ] All phases completed
- [ ] All tests passing
- [ ] Documentation updated
- [ ] No regressions in existing runs
- [ ] Code reviewed (self or peer)
- [ ] Commit messages are clear

## Merge & Deploy ⏳

- [ ] Final test run:
  ```bash
  # Run full test suite
  pytest tests/ -v
  
  # Run integration test
  ./run_tests.sh
  ```

- [ ] Merge to main:
  ```bash
  git checkout main
  git merge feature/efficient-verification
  git push origin main
  ```

- [ ] Post-merge verification:
  ```bash
  # Re-reconcile all runs
  python scripts/update_verification_status.py
  
  # Generate new analysis
  ./runners/analyze_results.sh
  
  # Compare with old report
  diff analysis_output/report.md analysis_output/report.md.old
  ```

## Rollback Plan (If Needed) ⏳

If something goes wrong:

```bash
# 1. Restore manifest backup
cp runs/runs_manifest.json.pre-verification-update runs/runs_manifest.json

# 2. Revert code changes
git revert HEAD

# 3. Verify old system works
./runners/reconcile_usage.sh baes <test_run_id>
```

## Post-Deployment Monitoring ⏳

Monitor for 1 week after deployment:

- [ ] Day 1: Check all new runs get correct verification status
- [ ] Day 3: Review verification rate across frameworks
- [ ] Day 7: Compare analysis reports (before/after)
- [ ] Ongoing: Document any edge cases discovered

## Success Criteria ✓

The update is successful when:

- ✓ BAeS runs with 50%+ token coverage are marked as `verified`
- ✓ Framework efficiency is highlighted in analysis reports
- ✓ All existing verified runs remain verified (no false negatives)
- ✓ Team understands the new verification model
- ✓ Documentation clearly explains efficiency vs completeness

## Notes

**Estimated Time**: 10-12 hours total
- Phase 1: 2-3 hours
- Phase 2: 3-4 hours  
- Phase 3: 2 hours
- Phase 4: 1-2 hours
- Phase 5: 1 hour + runtime
- Phase 6: 2-3 hours

**Key Files to Modify**:
1. `src/orchestrator/usage_reconciler.py` (main changes)
2. `config/experiment.yaml` (add verification config)
3. `docs/VERIFICATION_RULES.md` (update documentation)
4. `src/analysis/report_generator.py` (show efficiency metrics)

**Key Insight**:
Zero-token steps are NOT a bug - they're a FEATURE showing framework efficiency. Treat accordingly! 🎯
