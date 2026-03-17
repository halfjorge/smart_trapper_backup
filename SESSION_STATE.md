# Smart Trapper Session State

Last updated: 2026-03-17 (America/New_York)  
Branch: `trapper_active`  
Repo root: `C:\Users\Valued Customer\Desktop\trapper`

## Purpose
This file is a concise resume point for a new Codex chat so it can immediately continue debugging and feature work.

## System Layout
- Legacy JSX pipeline:
  - `Phase2_Run_All.jsx`
  - `Phase2_Export.jsx`
  - `Phase2_Import.jsx`
- UXP pipeline:
  - Panel/UI and Photoshop logic: `UXP_Trapper/main.js`
  - Bridge service: `UXP_Trapper/real_bridge.py`
  - Engine: `SmartTrapperB1/engine/src/main.rs`

## Primary Workflow (UXP)
1. Start bridge:
   - `cd C:\Users\Valued Customer\Desktop\trapper\UXP_Trapper`
   - `python .\real_bridge.py`
2. In Photoshop panel:
   - optionally `Manual Progressive Knockout` first for non-knocked-out files
   - `Run Trapper`
   - `Prepare Import Structure`
   - `Build Import Plan`
   - `Import Traps`
3. Use `Save Status Snapshot` after major actions.

## Stable Defaults
- Job folder base:
  - `C:\Users\Valued Customer\Desktop\TrapJobs`
- Status logs:
  - `C:\Users\Valued Customer\Desktop\trapper\UXP_Trapper\status_logs`

## Current Status
- `Run Trapper` creates/refreshes hidden `__ORIGINAL_FLATTENED__` and excludes it from inference/grouping.
- `Prepare Import Structure` can build CLEAN layers successfully from `clean_masks/*.png` when the selected run folder matches the run.
- If `clean_masks/` is missing in the selected run folder, prepare falls back to in-document alpha-threshold CLEAN build.
- `Manual Progressive Knockout` now works and performs the manual top-down knockout sequence before trapping when needed.
- Current verified manual knockout success log:
  - `UXP_Trapper/status_logs/smart_trapper_status_2026-03-17T17-51-11-771Z.txt`
  - `Applied: true`
  - `Clears: 10`

## Important Failure Pattern
- If `Prepare Import Structure` shows:
  - `No source color metadata for ...`
  - `CLEAN built: 0`
- Then selected/bound job folder likely does not contain the matching `mask_colors.json` for that run.
- If `Prepare Import Structure` shows `CLEAN mask-alpha path fallback (...)`, the selected run folder is missing `clean_masks/` and prepare is using the older in-document CLEAN fallback.

## Logs That Matter
1. `UXP_Trapper/status_logs/smart_trapper_status_*.txt`
2. `UXP_Trapper/real_bridge_last_run.json`
3. `UXP_Trapper/real_bridge_service.log`
4. Run folder files:
   - `job.json`
   - `mask_colors.json`
   - `traps.json`
   - `trapper_bridge_log.txt`

## Branch and Commit Discipline
- Active branch for ongoing work: `trapper_active`
- Keep commits small and scoped.
- Commit after each verified bugfix.
- Include one status log path in commit note if fix is debug-related.

## Immediate Next Steps
1. Validate the separate `Manual Progressive Knockout` button across more files that are not already progressively knocked out.
2. Keep validating consistency of:
   - job folder binding
   - `mask_colors.json` and `clean_masks/` presence
   - edge-bias behavior at prepare/import stages
3. After stability lock, move feature parity from JSX into UXP in controlled increments.
