# Smart Trapper Handbook

Last updated: 2026-03-17  
Repository root: `C:\Users\Valued Customer\Desktop\trapper`  
Primary branch: `trapper_active`

## 1) Project Purpose
Smart Trapper is a Photoshop-focused separation/trapping workflow for print art with multiple spot/process color layers plus key and paper.

Business goals:
- Remove manual repetitive prep.
- Generate reliable trap geometry per source/target color pair.
- Preserve visual integrity under registration variance.
- Keep debugging fast with actionable logs.

Technical goals:
- Reach functional parity between legacy JSX and new UXP panel flow.
- Stabilize cross-file behavior (8-bit, 16-bit, varied dimensions/resolution).
- Make troubleshooting deterministic (logs + reproducible steps).

## 2) Components

### Legacy JSX (reference implementation)
- `Phase2_Run_All.jsx`
- `Phase2_Export.jsx`
- `Phase2_Import.jsx`
- `Phase2_Create_Spot_Channels.jsx`

Role:
- Existing mature Photoshop scripting path.
- Source of truth for many edge-case behaviors and workflow expectations.

### UXP Panel (current migration target)
- `UXP_Trapper/main.js`

Role:
- In-Photoshop control surface.
- Orchestrates export -> bridge run -> import actions.
- Stores settings and produces status snapshots.
- Creates a hidden original flattened snapshot layer.
- Supports a separate manual progressive knockout action before trapping.

### Bridge
- `UXP_Trapper/real_bridge.py`

Role:
- Local HTTP service between panel and Rust engine.
- Handles `/health` and `/run`.
- Writes run metadata and bridge logs.

### Engine
- `SmartTrapperB1/engine/src/main.rs`

Role:
- Reads job inputs/masks.
- Generates trap outputs (`traps.json`, trap PNGs, clean masks).

## 3) Data / File Flow

1. Panel exports masks and metadata into run folder (timestamped job subfolder).
2. Bridge launches engine against that run folder.
3. Engine writes outputs:
   - `traps.json`
   - `clean_masks/*.png` (if cleanup path enabled)
   - `traps/*.png`
4. Panel imports clean layers and traps back into active PSD.

Important run artifacts:
- `job.json`
- `mask_colors.json`
- `traps.json`
- `trapper_bridge_log.txt`
- `uxp_job_request.json`
- hidden PSD reference layer: `__ORIGINAL_FLATTENED__`

## 4) Layer Model Expectations

Expected top-level input model:
- Top: key layer
- Middle: visible color art layers
- Bottom: paper layer

Expected import structure:
- `COLOR__<ink>` groups for each color
- `CLEAN__<ink>` layer inside each color group
- `TRAP__<source>_over_<target>` layers in source group
- Original source layer usually hidden once CLEAN exists

## 5) Core UXP Actions

### Run Trapper
- Creates or refreshes hidden `__ORIGINAL_FLATTENED__` at the top of the stack.
- Exports masks and metadata.
- Calls bridge `/run`.
- Rebinds selected run folder when bridge returns job path.
- Verifies `mask_colors.json` presence.

### Manual Progressive Knockout
- Separate UXP action button.
- Mimics manual Photoshop prep:
  - ctrl-click top visible art layer
  - delete that selection out of each lower visible art layer except paper
  - repeat top-down until all non-paper layers are progressively knocked out
- Use this on files that are not already progressively knocked out before running `Run Trapper`.

### Prepare Import Structure
- Wraps eligible layers into `COLOR__` groups.
- Builds CLEAN layers from engine-produced clean masks.
- Applies threshold/edge-bias behavior depending on path.

### Build Import Plan
- Validates traps against current document/groups and run folder assets.
- Reports missing groups, base layers, or trap PNGs.

### Import Traps
- Imports trap PNGs into source groups.
- Fills with source color metadata.
- Attempts cleanup/hide of original layers where appropriate.

## 6) Known Sensitive Areas

1. Folder binding state
- `currentJobFolderEntry` can go stale across sessions/reloads if not rebound from stored path.
- Symptom: CLEAN build skips all colors due to missing `mask_colors.json`.

2. Index assumptions
- Any synthetic top layer (like `__ORIGINAL_FLATTENED__`) can break positional assumptions if not excluded.

3. Placement reliability
- Layer placement via place/open/duplicate paths can shift if not normalized.
- Clean/trap import must remain canvas-coordinate stable.

4. Edge bias behavior
- Must only help shared-color boundaries and avoid introducing visible artifacts at paper edges.
- Requires strict verification against output examples.

5. Input prep state
- Some files are already progressively knocked out.
- Some files are stacked with overlaps intact.
- These states behave differently; use `Manual Progressive Knockout` on the latter before trapping.

## 7) Recent Work Themes (Migration Timeline)

- Built and stabilized UXP panel layout/workflow.
- Added robust status snapshots and bridge telemetry.
- Added folder defaults (job base + log folder).
- Added completion alerts for long-running actions.
- Added flattened snapshot layer behavior for debugging/reference.
- Added working manual progressive knockout action in UXP, separate from normal `Run Trapper`.
- Iteratively fixed:
  - trap/clean placement drift
  - smart object/layer effect import artifacts
  - color fill mismatches
  - inconsistent CLEAN creation caused by metadata/folder-state issues

## 8) Logging and Debugging Practice

Primary log first:
- `UXP_Trapper/status_logs/smart_trapper_status_*.txt`

Then correlate with:
- `UXP_Trapper/real_bridge_last_run.json`
- `UXP_Trapper/real_bridge_service.log`
- run folder (`job.json`, `mask_colors.json`, `traps.json`, `trapper_bridge_log.txt`)

Minimum reproducibility packet:
1. exact settings used (alpha threshold, edge bias, trap width, mode)
2. whether `Manual Progressive Knockout` was run first
3. latest status snapshot
4. latest bridge run snapshot
5. screenshot of resulting layer stack and artifact region

## 9) Operational Commands

Start bridge:
```powershell
cd C:\Users\Valued Customer\Desktop\trapper\UXP_Trapper
python .\real_bridge.py
```

Engine build:
```powershell
cd C:\Users\Valued Customer\Desktop\trapper\SmartTrapperB1\engine
cargo build --release
```

## 10) Branch Workflow

- Main working branch: `trapper_active`
- Keep one bugfix per commit whenever practical.
- Commit only after status-log verified behavior.
- Avoid mixing UI polish, engine math, and placement changes in one commit.

## 11) Current Working Rule Set

When behavior is unstable:
1. Reproduce with one document and fixed settings.
2. Capture fresh status snapshot.
3. Identify whether failure is:
   - panel state / folder binding,
   - bridge run,
   - engine output,
   - Photoshop import/apply step.
4. Patch smallest possible layer.
5. Re-test same file/settings before broadening scope.

## 12) Next Priorities

1. Lock reliability of CLEAN and TRAP placement across varied files.
2. Validate manual progressive knockout across more non-knocked-out files.
3. Lock edge-bias behavior so it improves gaps without introducing paper-edge artifacts.
4. Continue JSX parity feature-by-feature only after each behavior is stable.
