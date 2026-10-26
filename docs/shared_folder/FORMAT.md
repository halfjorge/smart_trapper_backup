# "SmartTrapper Shared" (Dropbox) - what goes in it and in what format

Sara's PC: `C:\Users\Valued Customer\The Half and Half Dropbox\Ben Gunter\Shared\SmartTrapper Shared`
(the Mac has its own Dropbox path - each person picks the folder once in the panel: Setup > "Shared folder...").

Small text files only. NOT here: TrapJobs job folders, masks, PSDs.

## presets.json  (Sara changes it; the panel only READS it)
Single source of truth for the file types. Example with the agreed values: `presets.example.json` (this folder).
- `always`: settings for every type. `types`: list of `{id, label, help, settings}`; a type's `settings`
  override `always`.
- ids the panel knows: `standard` (also accepts "illustrated"/"organic"), `geometric`, `overlay`, `tonal`.
  If `overlay` is missing the panel makes it = standard + overlayLayers.
- setting names = the panel's: preflightCleanup, alphaThreshold, edgeBiasPx, keyTrapPullbackPx,
  colorTrapPullbackPx, trapPx, roundTraps, closeKeyHalo, overlayLayers, smoothKeyTraps, bevelKeyCorners,
  keyTrapsFollowVisible, tonalInks (job.json names trapShape / closeKeyHaloPx / overlayMode also understood).
  Booleans = true/false; numbers in range (alpha 0-255, trap 1-50 ...). Anything else is ignored and listed
  under the picker.
- If the folder isn't set, Dropbox is offline, or the file is missing/broken: the panel uses its built-in
  presets (same agreed values), says so under Setup and in the status, and Run Trapper still works.
- Saved settings on each computer are never changed by it; if a preset differs from someone's boxes the
  picker shows "ADJUSTED from ...". A brand-new install starts on the file's Standard values.

## approved_runs/  (one file per entry - nobody ever edits a shared file, so no Dropbox "conflicted copy")
File name: `YYYY-MM-DD_HHMMSS_<who>_<psd name without .psd>.json` (who = sara / <co-worker's first name>).
```json
{
  "schema": "smart-trapper-run/1",
  "date": "2026-10-26T14:48:21-04:00",
  "who": "Sara",
  "file": "MMJ_OBH27_poster.psd",
  "jobType": "overlay",
  "presetSource": "shared presets.json (updated 2026-10-26 by Sara)",
  "verdict": "approved",
  "note": "One line: what was good / what was wrong.",
  "settings": { "preflightCleanup": true, "alphaThreshold": 90, "edgeBiasPx": 1, "keyTrapPullbackPx": 1,
                "colorTrapPullbackPx": 0, "trapPx": 5, "roundTraps": true, "closeKeyHalo": false,
                "overlayLayers": true, "smoothKeyTraps": true, "bevelKeyCorners": true,
                "keyTrapsFollowVisible": true, "tonalInks": false },
  "resolution": 300,
  "trapCount": 0,
  "statusLog": "smart_trapper_status_2026-10-26T18-48-21-701Z.txt (optional)"
}
```
`verdict`: "approved" or "rejected". The panel's approve button (later) will write exactly this.

## recipes/
Plain-language notes on how special jobs were made: one `.md` or `.txt` per job, e.g.
`2026-10-20_DMB_Fall_Tour_tonal.md`. Free text; start with the file name, job type and settings used.
