# Smart Trapper UXP

This is the start of a real UXP rewrite track for the trapper workflow. It does not replace the current `.jsx` pipeline.

## What works now

- Photoshop panel UI
- Persistent run settings
- Active-document inspection
- Startup-equivalent controls in one panel
- Job folder skeleton creation from the active Photoshop document
- `job.json` generation in the same structure as the current JSX export
- Initial mask export into `masks/` from the active Photoshop document
- First-pass import planning from `traps.json` against the active Photoshop document
- Bridge health check and run payload generation
- Settings snapshot export
- Optional mock bridge for local panel testing
- Hidden `__ORIGINAL_FLATTENED__` snapshot layer on `Run Trapper`
- Separate `Manual Progressive Knockout` action that mimics top-down manual knockout before trapping

## What is not wired yet

- Full Photoshop-side export/import parity with `Phase2_Export.jsx` and `Phase2_Import.jsx`
- End-to-end trap run from the panel
- External Rust engine invocation through a real companion bridge

## Files

- `manifest.json`
- `index.html`
- `styles.css`
- `main.js`
- `BRIDGE_CONTRACT.md`
- `mock_bridge.py`

## Load in UXP Developer Tool

1. Open Adobe UXP Developer Tool.
2. Add this plugin folder: `UXP_Trapper`
3. Load it into Photoshop.
4. Open the panel from the Plugins menu.

## Optional: run the mock bridge

From this folder:

```powershell
python .\mock_bridge.py
```

Then in the UXP panel:

- `Test Bridge` should return a health response
- `Run Trapper` should POST the current panel payload to the mock bridge

The latest payload is written to:

- `UXP_Trapper/mock_bridge_last_run.json`

## Current UXP export flow

The panel can now do the first real export-side pass from the active Photoshop document:

1. Open a PSD with your normal top-level stack:
   - top layer = key
   - visible color layers in the middle
   - bottom layer = paper
2. Either:
   - click `Create Job Folder Skeleton`, or
   - click `Select Job Folder` and choose a base folder such as `TrapJobs`
3. Either:
   - click `Export Masks To Job Folder`, or
   - click `Run Trapper` to export masks and immediately call the real bridge

Optional prep step for overlapping files:

- Click `Manual Progressive Knockout` first if the file is not already knocked out top-to-bottom.
- This performs the same workflow as:
  - ctrl-click top layer
  - delete that selection from each lower visible art layer except paper
  - repeat down the stack

If the selected folder is a base folder rather than an existing job folder, the panel now creates a timestamped job subfolder automatically before export/run.

That currently writes:

- `job.json`
- `uxp_job_request.json`
- `masks/*.png`
- `traps/`

Important limitation:

- this first UXP export pass writes isolated layer PNGs directly to `masks/`
- cleanup parity and key-cut parity are not yet ported from the JSX pipeline
- trap import back into Photoshop is not yet ported
- manual knockout is separate from `Run Trapper`; it mutates the open PSD before export just like a manual prep step would

## Current UXP import-side planning flow

The panel can now inspect a completed trap job and build an import plan against the open PSD:

1. Open the target PSD in Photoshop
2. Make sure the panel is pointing at a completed job folder that contains:
   - `traps.json`
   - `traps/`
3. If needed, click `Prepare Import Structure` to wrap visible top-level color layers into `COLOR__...` groups
4. Click `Build Import Plan`

That currently reports:

- total traps in `traps.json`
- whether each `COLOR__<source>` group exists in the PSD
- whether each source base layer exists
- whether each trap PNG exists in the selected job folder
- how many traps are ready to import

Important limitation:

- this is a planning pass only
- it does not yet create `TRAP__...` layers in Photoshop
- `Prepare Import Structure` is the first real UXP import-side mutation step
- actual trap PNG import and `TRAP__...` layer creation are not yet ported

## Real bridge: run the Rust engine on an existing job folder

From this folder:

```powershell
python .\real_bridge.py
```

Then in the panel:

1. Set the bridge URL to `http://127.0.0.1:8765`
2. Click `Select Job Folder` if you are using:
   - an existing exported job folder, or
   - a base folder where the panel should create a timestamped job subfolder
   - or create a new one with `Create Job Folder Skeleton`
3. Click `Run Trapper`

The bridge will:

- validate the engine path
- validate the selected job folder
- run the existing Rust engine
- write a bridge log into that job folder as `trapper_bridge_log.txt`

Latest received payload:

- `UXP_Trapper/real_bridge_last_run.json`

You can also use the real bridge against a UXP-created job folder after `Export Masks To Job Folder`, as long as the generated `masks/*.png` set is acceptable for the current file.

## Design choice

This plugin is built around a local bridge architecture. That is the practical way to preserve your existing Rust engine while moving the Photoshop UI to UXP.
