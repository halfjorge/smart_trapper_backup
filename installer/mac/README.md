# Mac installer for the co-worker (2026-10-26, IN PROGRESS - not given to anyone yet)

What the co-worker gets: `SmartTrapper_Mac.zip` -> folder "Smart Trapper Installer" with
`Install Smart Trapper.command` (double-click), `Uninstall Smart Trapper.command`, `READ ME FIRST.txt`, `payload/`.

Install does: engine + helper -> `~/Library/Application Support/SmartTrapper/` (quarantine removed),
LaunchAgent `com.thehalfandhalf.smarttrapper.helper` (helper starts at login, restarts if it crashes),
`~/SmartTrapper/TrapJobs` + `status_logs` (NOT the Desktop: macOS guards the Desktop from background
programs), then the panel `payload/SmartTrapper.ccx` via Adobe's UnifiedPluginInstallerAgent (falls back to
opening it in Creative Cloud). No paid Apple developer account -> first launch needs System Settings >
Privacy & Security > "Open Anyway" once (READ ME FIRST explains).

Pieces:
- `SmartTrapperB1/helper/` - standalone helper (Rust, std + serde_json), same /health and /run answers as
  `UXP_Trapper/real_bridge.py` (tested identical: tools/ui_tests suite + same output files on 3 jobs).
  /health also sends `homeDir` so the panel can find ~/SmartTrapper on a Mac.
- Panel (main.js): `setUpFoldersForThisComputer()` - if the saved job folder doesn't exist (Sara's Windows
  path on a Mac) and the helper sends homeDir, use ~/SmartTrapper/TrapJobs. Sara's PC unchanged (her folder
  exists; the Python bridge sends no homeDir).
- Plugin = Sara's panel through `tools/dev/make_shared_copy.py` (co-worker copy), zipped as .ccx.
- `build_package.sh` assembles the zip; `.github/workflows/mac_package.yml` builds engine + helper for both
  Mac chip types on a GitHub Mac, assembles, installs, runs a real trap job, uninstalls, uploads the zip.

Still to do: Mac test on the co-worker's computer (link this chat from the Claude app there); confirm the
.ccx installs (a plain zip of the plugin folder - unverified); the user guide (paused, out of date).

## Shared Dropbox folder (added 2026-10-26 15:30)
- Panel: Setup > "Shared folder..." (both copies) - picked once, remembered with a UXP persistent token
  (`createPersistentToken` / `getEntryForPersistentToken`), saved as `sharedFolderToken` + `sharedFolderPath`.
- Reads only `presets.json` there (format = the real file, rules in shared_folder/README.md; tested against it).
  Missing / offline / broken -> built-in presets + note under Setup + "Presets: ..." line in the status;
  Run Trapper never fails because of it. Saved settings never changed by it.
- Installer looks for a "SmartTrapper Shared" folder under ~/Library/CloudStorage/*Dropbox* or ~/*Dropbox*
  and tells the co-worker which folder to pick. The installer and panel never WRITE to the shared folder.
- Tests: tools/ui_tests/shared_folder_test.js (18 checks, incl. the real shared presets.json).
