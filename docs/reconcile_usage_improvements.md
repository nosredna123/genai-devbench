# Reconcile Usage Script Improvements

## Overview
Enhanced the `reconcile_usage.sh` script to provide better visibility into the reconciliation status of all experiment runs, making it much easier for users to understand what's happening with their data verification.

## Changes Made

### 1. Added `--verbose` Flag
A new `--verbose` flag can be used with `--list` to show comprehensive information about ALL runs in the system, not just pending ones.

**Usage:**
```bash
./runners/reconcile_usage.sh --list --verbose
```

### 2. Enhanced Information Display

#### Normal Mode (`--list`)
- Shows only runs that need reconciliation (>30 min old, not yet verified)
- Clear messaging when no runs need attention
- Helpful tip pointing users to verbose mode for more details
- **Example output:**
  ```
  Found 1 runs pending verification:
  
    ⏳ baes/0a7e4445-ddf2-4e34-98c6-486690697fe5
      Status: pending (attempt 0)
      Age: 0.9 hours
      Message: Not yet reconciled
  
  💡 Tip: Use '--list --verbose' to see ALL runs and their status
  ```

#### Verbose Mode (`--list --verbose`)
Provides a comprehensive overview categorized by status:

**Summary Section:**
- Total runs count
- Breakdown by category:
  - ✅ Verified (fully confirmed)
  - ⏳ Pending verification (ready to reconcile)
  - 🕐 Too recent (<30 min, waiting for API data)
  - ❓ No reconciliation data (never attempted)

**Detailed Sections:**

1. **Verified Runs:**
   - Shows successfully verified runs
   - Displays token counts (input/output)
   - Shows age and verification message
   - Sorted by most recent first

2. **Pending Verification:**
   - Runs ready for reconciliation (>30 min old)
   - Shows current status and attempt count
   - Displays token counts
   - Shows age and status message

3. **Too Recent for Reconciliation:**
   - Runs that haven't reached the 30-minute threshold
   - Shows exactly how many more minutes to wait
   - Helpful for understanding when runs will be ready
   - **Example:**
     ```
     🕐 chatdev/aa0e24f6...
       Tokens: 237,487 in / 84,634 out
       Age: 28.9 minutes (wait 1.1 more)
     ```

4. **No Reconciliation Data:**
   - Runs that have never been reconciled
   - May indicate runs with zero tokens or issues

### 3. Improved User Experience

#### Better Context
Users now understand why certain runs aren't listed:
- Too recent (need to wait for OpenAI API propagation)
- Already verified (no action needed)
- Outside the reconciliation window

#### Actionable Information
- Shows exact wait times for recent runs
- Clear status progression indicators
- Token counts visible in all modes
- Shortened run IDs for readability (first 8 chars)

#### Visual Clarity
- Status emojis for quick scanning:
  - ✅ Verified
  - ⏳ Pending
  - 🕐 Too recent / Data not available
  - ⚠️ Warning
  - ❓ Unknown/No data
- Section headers with clear categorization
- Consistent formatting across sections

### 4. Updated Help Documentation

Added `--verbose` flag documentation and example to the help text:
```bash
./runners/reconcile_usage.sh --help
```

## Use Cases

### Quick Check (Normal Mode)
When you just want to know "what needs my attention right now?":
```bash
./runners/reconcile_usage.sh --list
```

### Full System Status (Verbose Mode)
When you want to understand the complete state of all runs:
```bash
./runners/reconcile_usage.sh --list --verbose
```

Perfect for:
- Understanding why certain runs aren't being reconciled
- Checking if all runs completed successfully
- Planning when to run reconciliation
- Debugging reconciliation issues
- Getting a complete overview of the experiment batch

## Example Scenarios

### Scenario 1: Just finished experiment batch
```bash
$ ./runners/reconcile_usage.sh --list --verbose

📊 SUMMARY: 13 total runs
   ✅ Verified: 3
   ⏳ Pending verification: 0
   🕐 Too recent (<30 min): 9
   ❓ No reconciliation data: 1
```
**Interpretation:** Most runs are too recent. Wait ~30 minutes and they'll be ready.

### Scenario 2: Some runs ready for reconciliation
```bash
$ ./runners/reconcile_usage.sh --list

Found 8 runs pending verification:
  ⏳ baes/c3c8cc0d... (attempt 1, 2.3 hours old)
  ...
```
**Interpretation:** 8 runs are ready. Run without `--list` to reconcile them.

### Scenario 3: Everything up to date
```bash
$ ./runners/reconcile_usage.sh --list

✅ No runs need reconciliation right now!

Possible reasons:
  • Too recent (< 30 minutes old)
  • Already verified (double-check complete)
  • Too old (> 24 hours)

💡 Tip: Use '--list --verbose' to see ALL runs with their status
```
**Interpretation:** System is healthy, all runs processed.

## Technical Details

### Age Calculation
- Based on `metrics.json` file modification time
- 30-minute minimum age ensures OpenAI Usage API data availability
- Clear countdown shown for runs approaching the threshold

### Status Categories
1. **verified**: Double-checked and confirmed stable
2. **pending**: First reconciliation done, awaiting verification
3. **data_not_available**: API data not yet available
4. **warning**: Inconsistencies detected
5. **unknown**: No reconciliation attempted

### Performance
- Efficient scanning using existing manifest
- No API calls made in list mode
- Fast execution even with many runs

## Benefits

1. **Transparency**: Users see exactly what's happening
2. **Confidence**: Clear indication of data verification status
3. **Efficiency**: Know when to run reconciliation
4. **Debugging**: Easy identification of issues
5. **Planning**: Understand timing requirements

## Future Enhancements

Potential improvements:
- Add filtering by framework in verbose mode
- Export to JSON/CSV for analysis
- Show reconciliation history timeline
- Add color coding (if terminal supports it)
- Include estimated completion time for batches
