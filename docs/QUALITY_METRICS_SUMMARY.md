# Quality Metrics: Why They Show Zero

## TL;DR

**All frameworks show CRUDe=0, ESR=0, MC=0, Q_star=0 because the generated applications are never executed during experiments.**

This is **expected behavior** - the experiment framework measures **code generation efficiency** (tokens, time, automation), not **runtime quality**.

---

## The Problem

```
⚠️ Data Quality Alerts

- All frameworks show zero for `CRUDe` - verify metric calculation
- All frameworks show zero for `ESR` - verify metric calculation  
- All frameworks show zero for `MC` - verify metric calculation
- All frameworks show zero for `Q_star` - verify metric calculation
```

## The Root Cause

The validation code attempts to test CRUD endpoints by making HTTP requests:

```python
# src/orchestrator/validator.py
def test_crud_endpoints(self) -> Tuple[int, float]:
    for entity in ['students', 'courses', 'teachers']:
        response = requests.post(
            f"{self.api_base_url}/{entity}",  # e.g., http://localhost:8100/students
            json=test_data[entity],
            timeout=10
        )
```

**But the servers are never started**, so all requests fail:

```json
{
  "level": "WARNING",
  "message": "GET /courses failed: Connection refused",
  "run_id": "66768e5b-597d-4294-9617-0f9e7d903dfd"
}
```

Result: `0/12 operations succeeded` → CRUDe=0, ESR=0.0

---

## Why This Happens

**Configuration** (`config/experiment.yaml`):
```yaml
baes:
  auto_restart_servers: false  # ← Deliberately disabled
```

**Documented as expected** (`docs/baes/JSON_PARSING_FIX_VALIDATION.md`):
> ### Issue 2: CRUD Validation Fails (Expected)
> **Status**: ⚠️ **EXPECTED BEHAVIOR**  
> **Reason**: Servers not started during experiment

---

## Design Rationale

The experiment framework **intentionally does not start generated applications** because:

1. **Scope**: Measures LLM efficiency (tokens, time), not code quality
2. **Complexity**: Each framework generates different project structures
3. **Overhead**: Server startup would add 30-60 seconds per run
4. **Conflicts**: Parallel runs would require dynamic port allocation
5. **Reliability**: Dependency issues could cause false negatives

**What's measured**:
- ✅ Token consumption (cost)
- ✅ Execution time (speed)
- ✅ Test automation (AUTR = 1.0 for all)
- ✅ Human interventions (HIT = 0 for all)

**What's NOT measured**:
- ❌ Whether generated code actually works
- ❌ CRUD endpoint completeness
- ❌ API response correctness
- ❌ Application quality

---

## Impact on Report

### Current Statistics (Meaningless)

```
Kruskal-Wallis H-Test for CRUDe: p=1.0000 (no significant difference)
```

**Interpretation**: "No evidence of differences" is **technically correct** but misleading - all values are identically zero, so there's no variance to compare.

### Current Visualizations (Misleading)

Radar chart shows all frameworks with "0" quality scores, which could be misinterpreted as:
- "All frameworks fail quality tests" ❌ (wrong - tests not run)
- "All frameworks are equally bad" ❌ (wrong - not measured)

**Correct interpretation**: Quality metrics were not measured.

---

## What Should Be Done

### Immediate Fix (Recommended)

Update report generation to:
1. Mark quality metrics as "Not Measured"
2. Remove quality metrics from statistical tests
3. Add prominent disclaimer in Executive Summary
4. Update visualizations to exclude unmeasured metrics

### Future Enhancement (Optional)

Implement runtime validation as a **separate study**:
- Start generated applications in isolated environments
- Run CRUD validation against live servers
- Collect quality metrics post-hoc
- Compare frameworks on output quality vs generation efficiency

**Estimated effort**: 20-40 hours of development

---

## References

- **Investigation Report**: `docs/QUALITY_METRICS_INVESTIGATION.md`
- **Validation Code**: `src/orchestrator/validator.py`
- **Metrics Collector**: `src/orchestrator/metrics_collector.py`
- **Original Documentation**: `docs/baes/JSON_PARSING_FIX_VALIDATION.md`

---

**Date**: October 16, 2025  
**Status**: ✅ Root cause identified  
**Action Required**: Update report generation (see Phase 1 in investigation report)
