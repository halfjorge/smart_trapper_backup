# Shared folder format -> see `shared_folder/README.md`

**Superseded (2026-10-27).** The rules and formats for the Dropbox folder "SmartTrapper Shared" are the ones in
`shared_folder/README.md` and the real files next to it (`presets.json`, `approved_runs/*.json`, `recipes/*.md`).
The copy in git (`shared_folder/`) mirrors the Dropbox folder. An earlier draft format that lived here was
retired so there is only one rule book. (The old example file is now a test fixture:
`tools/ui_tests/fixtures/presets_test.json` - not a preset, ignore it.)

What the panel does with the folder (panel = reader, apart from the future approve button):
- `presets.json`: READ only. The panel understands its format (`types` keyed by id, each with `label`,
  `values`, optional `example`/`note`; `version`, `agreed_with`). Tested against the real file 2026-10-27:
  read cleanly, values identical to the panel's built-in presets.
- Folder not set / Dropbox offline / file missing or broken -> built-in presets, a note under Setup and in the
  status; Run Trapper never fails because of it.
- `approved_runs/`: the future approve button will ADD one new file per judged run in the same format as the
  existing entries (see PROJECT_NOTES "Approve button plan"). It never edits or deletes existing files.
