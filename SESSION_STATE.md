# Smart Trapper Session State

Last updated: 2026-03-12 (America/New_York)  
Branch: `testing2_26_26`  
Repo root: `C:\Users\Valued Customer\Desktop\trapper`

## What This File Is For
This file is the handoff/source-of-truth so a new chat can resume quickly even if thread history is lost.

## Current Architecture
- Photoshop UI: UXP panel (`UXP_Trapper/main.js`)
- Local bridge service: Python HTTP server (`UXP_Trapper/real_bridge.py`)
- Trap engine: Rust binary (`SmartTrapperB1/engine/target/release/smart_trapper_b1.exe`)
- Art workflow: Export masks -> run engine -> prepare import structure -> build import plan -> import traps

## Current Known Good Workflow
1. Start bridge in PowerShell:
   - `cd C:\Users\Valued Customer\Desktop\trapper\UXP_Trapper`
   - `python .\real_bridge.py`
2. In Photoshop UXP panel:
   - `Run Trapper`
   - `Prepare Import Structure`
   - `Build Import Plan`
   - `Import Traps`
3. Use `Save Status Snapshot` after each phase when troubleshooting.

## Persistent Paths (defaults in panel)
- Job folder base:
  - `C:\Users\Valued Customer\Desktop\TrapJobs`
- Status snapshot folder:
  - `C:\Users\Valued Customer\Desktop\trapper\UXP_Trapper\status_logs`

## Recent Stability Work
- Added bridge telemetry in `real_bridge.py`:
  - `sessionId`, `pid`, `startedAt`, `uptimeSec`, `requestCount` on `/health`
  - per-request `requestId` for `/run`
  - append-only service log:
    - `UXP_Trapper/real_bridge_service.log`
  - richer run snapshot metadata in:
    - `UXP_Trapper/real_bridge_last_run.json`
- Panel now logs bridge health preflight and run HTTP status in `main.js` before/after `Run Trapper`.

## Active Problem Areas
- Intermittent behavior can look like placement drift or phase inconsistency until bridge is restarted.
- Clean/trap coordinate regressions have historically correlated with:
  - stale bridge process/session
  - DPI normalization experiments
  - edge-bias-related clean mask generation shifts

## Logs to Collect for Any Bug Report
1. Latest panel status snapshot:
   - `UXP_Trapper/status_logs/smart_trapper_status_*.txt`
2. Bridge per-run snapshot:
   - `UXP_Trapper/real_bridge_last_run.json`
3. Bridge service timeline:
   - `UXP_Trapper/real_bridge_service.log`
4. Job folder artifacts:
   - `trapper_bridge_log.txt`
   - `job.json`
   - `mask_colors.json`
   - `traps.json`

## Debug Checklist (Fast)
1. Confirm `/health` includes `sessionId`, `pid`, `uptimeSec`.
2. Confirm status snapshot shows bridge health preflight before run payload.
3. Confirm run response includes `requestId`, `sessionId`, `engineMs`, `bridgeTotalMs`.
4. Confirm selected job folder is the exact current run folder (timestamped subfolder).

## Commit Discipline (for robust history)
- Commit small checkpoints with focused scope and message.
- Prefer one commit per bugfix:
  - `uxp: add bridge session telemetry`
  - `uxp: fix clean import coordinate guard`
  - `engine: write PNG DPI metadata`
- Always attach at least one status snapshot path in commit notes (or PR body) when bug-related.

## Next Recommended Step
- Reproduce one intermittent run and capture:
  - latest status snapshot
  - `real_bridge_last_run.json`
  - tail of `real_bridge_service.log`
- Then compare `sessionId/requestId` between health + run to confirm single bridge instance continuity.
