# PROJECT NOTES - Smart Trapper (start here in a new chat)

Last updated: 2026-10-26 15:30 (two sessions working - see the block at the top of section 0) by Claude (UI session). Owner: Sara (The Half and Half, screen-print shop).

**New chat? Read section 0 (Next session) first, then the rest of this file, then `TRAP_RULES_NOTES.md` (the agreed trapping rules) and
`CHANGES_2026-10-06.md` (what was changed and why).** Sections 9-11 below cover git, how to make a
change, and how to test. `SMART_TRAPPER_HANDBOOK.md` and `SESSION_STATE.md` are older (March 2026).
They still describe the panel/bridge/engine layout correctly, but their status and branch notes are
out of date.

> SCOPE: this app is for poster / gig-print trapping. The fine-art separation tests (Welker,
> Van Loon, Huemer) were standalone experiments, NOT part of the app. Their notes and code are kept
> separately in `Desktop\Trap Examples\FINE_ART_NOTES.md` and `_FINE_ART_SEPS_CODE_claude.zip`. Don't mix them into app work.

---

## 0. NEXT SESSION STARTS HERE (handoff 2026-10-26: UI / workflow, so someone else can use it)

### >>> TWO CLAUDE SESSIONS ARE WORKING ON THIS - READ BEFORE CHANGING ANYTHING (2026-10-26 15:30) <<<
Sara asked that the two sessions don't conflict. They can't message each other, so this block is the channel.
Edit only your own line here; fetch/pull first and re-check before every push or write to the PC.
- **UI / installer session** (session_01QbWcmNBwrQZqtLawTtBqCs): panel code (`UXP_Trapper/main.js`), the
  Mac installer, the standalone helper (`SmartTrapperB1/helper`), user guide (paused). Works on git branch
  **`mac_installer`** (NOT on Sara's PC yet - waiting for her OK and a test on the Mac). Does NOT write to the
  Dropbox folder "SmartTrapper Shared"; the panel/installer only READ `presets.json` there.
- **Shared-folder / settings session** (session_01MD548tCq1R9E4kh1AaC8Mr): fills "SmartTrapper Shared"
  (`presets.json`, `approved_runs/`, `recipes/`) with the past approved settings - DONE 2026-10-26 15:28
  (git copy: `shared_folder/`). Its README + files ARE the format (Sara 2026-10-27: follow the README's
  rules - add new files only; every delivery gets a recipe card and an approved_runs entry). The panel was
  adapted to read that presets.json (2026-10-27, tested on the real file); the earlier draft format in
  docs/shared_folder was retired. Please: no panel-code changes.
- **Both:** `trapper_2026_10` = exactly what is on Sara's PC. Only change it when Sara has OK'd something for
  her PC; `git fetch` + rebase first; add your notes under your own heading; never overwrite the PC copy of a
  file without checking it hasn't changed since you read it.
- Sara's Dropbox path (her PC): `C:\Users\Valued Customer\The Half and Half Dropbox\Ben Gunter\Shared\SmartTrapper Shared`
  (empty at 15:25 on 10-26, filled by the shared-folder session at 15:28). TrapJobs / masks / PSDs never go there.

**SHARED FOLDER RULES (Sara 2026-10-27, from shared_folder/README.md) - apply to every Claude chat:**
- `presets.json` = single source of truth; only Sara changes it. The panel only reads it.
- Add new files only; never rewrite another chat's files.
- No delivery without a recipe card and an approved_runs entry: every poster file Claude makes outside the
  app gets a card in `recipes/` (copy in that job's Trap Examples folder); every file Claude delivers gets an
  `approved_runs/` entry with verdict "DELIVERED" until Sara judges it. (Panel / installer software changes
  are not poster deliveries - they are logged in CHANGES / TEST_RESULTS as before.)

**Approve button + "use last approved settings" plan (build AFTER the installer, per Sara):**
- Approve button (Run Trapper's finish message / Status area): Approve / Reject + one-line note. Writes ONE
  NEW file `approved_runs/YYYY-MM-DD_<poster>_panel_<HHMMSS>_<APPROVED|REJECTED>.json` in the existing
  entries' format: date, file, job_type (type label), made_with "panel", job_folder, settings {ppi, trap_px,
  the 13 panel settings, inks[], key}, verdict, note, recorded_by "<name> (panel, <computer>)", plus
  fileType id and preset source. Never overwrites (adds -2, -3 ... if the name exists). Asks each person's
  name once (Setup). Folder not set / offline -> says so and offers to save the entry into the job folder.
- "Use last approved settings?": when Run Trapper starts (and when a document opens), look in approved_runs
  for the newest entry whose `file` matches this document (ignoring case, ".psd", " (1)") with a verdict
  starting APPROVED -> "This poster was approved on <date> with <type> (<note>). Use those settings?"
  [Use them] [Keep mine]. Read-only; nothing found / offline -> no prompt, one status line.

**Sara's goal now:** make the panel easy for ANOTHER person to use efficiently, without Sara's knowledge
of building and testing it. The backend (engine + trap rules) is in a good place; the work is UI and workflow.
Talk it through with Sara first and agree a plan before changing the panel.

**AGREED PLAN (Sara, 2026-10-26).** The other person is a co-worker in Sara's shop on a **Mac (macOS 26.5.1,
Photoshop 27.4.0)**, USING only (never building/testing). Four file types are right to start: Standard
poster, Geometric / flat shapes, Overlay / Multiply layers, Tonal / grayscale. Order:
1. DONE 2026-10-26: one-button **Run Trapper** (below).
2. DONE 2026-10-26: "What kind of file is this?" picker (below). NEXT after it: a check-only
   "Check file" button (plain warnings: names with spaces, empty/hidden layers, key/paper shown,
   overlay/tonal detection -> suggest a file type). Not started; agree with Sara first.
2b. DRAFT 2026-10-26: user guide PDF with pictures for every setting, `docs/user_guide/` (README there).
   Pictures = REAL engine on small test drawings, setting off vs on (Sara: "can you generate them?
   I don't want to run the trapper over and over"). Waiting for Sara's review; Mac install page is a
   placeholder until the package exists. To go in the install package. PAUSED 2026-10-26 15:09 (Sara: stop
   on the visual examples / pdf for now). The PDF in docs/user_guide still shows the OLD preset values -
   out of date; rebuild with the installed values before it goes anywhere.
3. Mac install for the co-worker (Sara 2026-10-26: co-worker has the Claude desktop app on this account,
   so this chat can be linked to the Mac to test the install there; NO paid Apple developer account ->
   one-time System Settings > Privacy & Security > "Open Anyway"; Sara will put the installer on the
   co-worker's Desktop; helper should start by itself at login): folders not hard-wired to Sara's PC (DEFAULT_JOB_FOLDER/LOG_FOLDER are
   `C:\Users\Valued Customer\...`; the folder pickers are hidden), packaged plugin (.ccx) instead of UXP
   Developer Tool, engine pre-built for Mac (no Rust), helper started by double-click, plain message when
   it isn't running. SHARE_README_WINDOWS_MAC.txt and build_smart_trapper_bundle.py are from the OLD JSX
   version - don't reuse them as they are.
4. Tidy labels / fold advanced settings away, one-page user guide.

**TWO VERSIONS (keep them separate and clean - Sara's condition):**
- ONE panel source in git: `UXP_Trapper/main.js` = **Sara's copy** (SHOW_INDIVIDUAL_STEPS = true).
- The **co-worker's ("shared") copy** is MADE from it by `tools/dev/make_shared_copy.py` (output
  `dist/SmartTrapper_Shared/`, not in git). Never edit the shared copy by hand. Every difference lives in
  that script's CHANGES list and in this table:

  | | Sara's copy | Co-worker's copy |
  |---|---|---|
  | Run Trapper (all four steps), Clean Colors, Cut Top Key | yes | yes |
  | "Individual steps (for testing)": Manual Progressive Knockout, Run Trapper (engine only), Prepare Import Structure, Import Traps | yes | hidden (`SHOW_INDIVIDUAL_STEPS = false`) |
  | Settings, file-type picker, checks, engine, helper | same | same |
- Same engine and helper for both. A print-output change always applies to both.

**One-button Run Trapper (panel only, 2026-10-26, Sara OK'd).** Button id `runAllBtn`, function
`runAllSteps()` in main.js. Runs Sara's order by calling the SAME step functions as the individual
buttons: Manual Progressive Knockout -> Run Trapper (engine; `runTrapper()`) -> Prepare Import Structure ->
Import Traps. Each step function now returns `{ ok, reason, ... }` (the individual buttons ignore it, so
they behave as before). Print output identical to clicking the four by hand.
- Knockout SKIPPED when Tonal inks is ticked (Sara: grayscale builds are not knocked out).
- Full STOPS before anything changes (Sara: "stop is good"): no document / under 3 visible layers; file
  already has COLOR__/CLEAN__/TRAP__ layers; helper not answering /health or engine missing; not RGB or not
  300 ppi; risky settings (settingsProblems); overlay layers found while "File has transparent / overlay
  layers" is off.
- Stops after a failed step (knockout error, engine not ok, 0 traps, prepare/import fatal) with which step,
  what was already done to the file, and "step back in History". Non-fatal problems (missing CLEAN layer,
  trap layer not imported, wrap failure) finish as "FINISHED - WITH WARNINGS" with a list. One alert only.
- The old engine-only button is labelled "Run Trapper (engine only)" in Sara's copy.
- Tested offline (TEST_RESULTS 2026-10-26 "One-button Run Trapper"): tools/ui_tests (stand-in Photoshop,
  real helper + engine), 18 situations + the 4 individual buttons, on both copies.
- Backup: versions\main_backup_2026-10-26_before_run_trapper_button.js. Sara: click Reload.

**"What kind of file is this?" picker (panel only, 2026-10-26, Sara confirmed the values).** Drop-down
`fileType` at the top of Run Settings; `FILE_TYPES` near the top of main.js. Picking a type only fills in
the existing settings; every box stays adjustable ("ADJUSTED from <type>" note lists the changes, "Put
back <type> settings" button). `fileType` is saved with the settings but NOT sent to the engine
(job.json built field by field; tested identical to ticking the boxes by hand).
**INSTALLED VALUES (Sara 2026-10-26 15:10 = the "DEFAULT SETTINGS / PRESETS" block below, bevel ON for
Geometric):**
| Type | Values (all others off) |
|---|---|
| Standard poster (illustrated / organic) | trap 5, Preflight cleanup ON, alpha 90, edge bias 1, key pullback 1, colour pullback 0, Round ON, Key traps follow visible ON, Smooth ON, Bevel ON (= Sara's MMJ_OBH27 run 2 without the overlay box) |
| Geometric / flat shapes | Standard but Round OFF, Key traps follow visible OFF (Smooth ON, Bevel ON) |
| Overlay / Multiply layers | Standard + File has transparent / overlay layers (= MMJ run 2 exactly) |
| Tonal / grayscale | Standard + Tonal inks (other boxes not used by the engine in tonal mode) |
| Custom | changes nothing |
- History: 14:40 Geometric had Bevel OFF (Obey corners); Sara then chose Bevel ON (15:10) after agreeing
  the presets in another session. Claude's note: on Obey the approved file had 134 bevelled corners squared
  back by hand - if geometric corners come out bevelled, untick Bevel.
- Caution: the new Standard rests on one poster (MMJ). The easy-file sign-off (TEST_RESULTS) was with
  smooth/bevel/follow-visible OFF. They only change traps under the key (nothing visible in register);
  known side effect of follow-visible = scattered single dots on diagonals (why Geometric has it off).
  Re-checking the Trap Examples with the new Standard is offered (needs the Trap Examples folder).
- Fresh install (no saved settings) starts on Standard poster - this is the co-worker's default. Saved
  settings are never replaced: the picker shows the type they match, else Custom (Sara at alpha 89 = Custom).
  DEFAULTS itself is unchanged (only used for empty boxes / very old saved settings).
- Run Trapper's finish message names the type ("Standard poster (adjusted)"); the overlay stop message
  says to pick Overlay / Multiply.
- Tests: tools/ui_tests/file_type_test.js (27 checks) on both copies; Run Trapper suite unchanged.
  Backup: versions\main_backup_2026-10-26_before_file_type_picker.js.

**What exists today (all on branch trapper_2026_10, live copy = Sara's Desktop\trapper):**
- Panel `UXP_Trapper/main.js` (UXP, loaded in UXP Developer Tool; panel change = Reload). Sections:
  Run Settings / Actions / Status.
  - Action buttons in use, in Sara's order: Clean Colors -> Manual Progressive Knockout -> (Cut Top Key From
    Colors) -> Run Trapper -> Prepare Import Structure -> Import Traps; Save Status Snapshot for debugging
    (writes UXP_Trapper\status_logs). Plus small/unlabelled buttons: refresh document, edit bridge URL,
    pick/clear job folder, pick/clear log folder, test bridge, save settings, export masks, import plan,
    create job, export config, "? Explain settings".
  - Settings: 9 tick boxes (fullDebug, preflightCleanup, roundTraps, closeKeyHalo, overlayLayers,
    smoothKeyTraps, bevelKeyCorners, keyTrapsFollowVisible, tonalInks) + 5 fields (alphaThreshold 90,
    edgeBiasPx 0, keyTrapPullbackPx 1, colorTrapPullbackPx 0, trapPx 5).
- Bridge `UXP_Trapper/real_bridge.py` (local service at http://127.0.0.1:8765) runs the engine.
- Engine `SmartTrapperB1/engine` (Rust; engine change = BUILD_AND_TEST_ENGINE.bat, then Reload).
  Cloud builds: vendored kit tools/dev/engine_build_kit_cloud.zip (crates.io blocked), see section 9/10.
- Sharing bits already in the repo: SmartTrapper_Share folder, SHARE_README_WINDOWS_MAC.txt,
  build_smart_trapper_bundle.py (not reviewed this session - check what they do before reusing).

**DEFAULT SETTINGS / PRESETS (agreed with Sara 2026-10-26, from MMJ_OBH27 runs 1 vs 2):**
Always: Preflight cleanup ON, Alpha threshold 90, Edge bias 1, Key trap pullback 1, Colour trap pullback 0,
Trap 5 px @300 ppi (10 @600), Close key halo OFF (only for files with white outlines round the key, Phish),
Tonal inks OFF. "File has overlay layers" ON whenever any layer is non-Normal or under 100% (panel can detect).
- Illustrated / organic (most posters) = Sara's MMJ run 2: Round ON, Key traps follow visible ON, Smooth ON,
  Bevel ON. (Run 2 vs run 1: Smooth/Bevel turned straight trap bands along the key into organic edges
  following the shapes - Sara: "much more organic at the key edge instead of those hard lines".)
- Geometric / hard-edged (Obey): Round OFF, Key traps follow visible OFF, Smooth ON, Bevel ON.
- Grayscale / textured layers (DMB Tour): Tonal inks ON (other boxes not used).
Parked idea (engine, needs Sara's OK): with overlay mode, split the key line where an overlay's key trap and
another colour's key trap overlap (MMJ: 116 frame trap + 3115 Darken trap made a green band under the key;
Smooth removed most of it). Watch: 232 u slivers at narrow key tips on MMJ (key-off view only).

**What a new user trips over (seen in this session):**
- Many steps whose ORDER matters; two knockout buttons can fail or remove art (the key must NOT cut inks
  on tonal files - now guarded when Tonal inks is on).
- Settings depend on the kind of file - a new user won't know them:
  geometric / flat (Obey): Round traps OFF, Key traps follow visible OFF, trap 5 @300;
  tonal / grayscale layers (DMB Tour): Tonal inks ON;
  overlay / multiply layers: File has overlay layers ON. -> good candidate for PRESETS.
- File problems the panel only finds by failing: a layer name with a trailing space (fixed 2026-10-21),
  a layer emptied by knockout (fixed 2026-10-21). -> good candidate for a PREFLIGHT CHECK with plain warnings.
- Setup needs UXP Developer Tool, the bridge running, and an engine build.
- Labels and help text are technical and long.

**Ideas to discuss with Sara (nothing built yet):** a short "what kind of file is this?" preset picker;
one guided "Run" that does the steps in order with checks between them; preflight warnings (names,
empty/hidden layers, which layer is key/paper, tonal-file detection); plain-language labels with
advanced settings tucked away; a one-page user guide; an install/share package.

**Offline tools from this session (not in the app):** tools/obey (joint mitre, bleed, PSD read/write),
tools/dmb_tour (tonal trapping prototype + PSD writer), tools/obey/layr_read_full.py (reads PSD/PSB layer
data from Photoshop PDFs). Delivered client files are listed in sections 0-prev*.

## 0-prev3. Update 2026-10-26 (Tonal inks added)

**NEW in the app: "Tonal inks (grayscale layers)" tick box, default OFF (Sara OK'd 2026-10-26).**
The DMB Fall Tour content-aware trapping is now in the engine (SmartTrapperB1/engine/src/tonal.rs, job.json
`tonalInks`) and the panel (tick box, sent to job.json, shown in the Settings log line).
- On: inks keep their tones (any alpha > 0 is ink); traps only under solid key line work (key 255, opened
  cross x2, 1 px back from non-solid key) + the soft line edge on the ink side (key >= 50%, within 2 px of the
  ink); 5 px square growth, all inks at once (line split mid-way); trap tone mirrored from inside the ink
  (ties: leftmost, then topmost); CLEAN = original tones; no ink-to-ink traps (agreed); halo/round/smooth/
  bevel/follow-visible/pullback not used. Panel: Progressive Knockout does not cut with the key; "Cut Top
  Key From Colors" is blocked while it's on. Panel import unchanged (soft transparency selection + fill keeps
  the tone) - CONFIRMED by Sara in Photoshop 2026-10-26 13:57 ("that looks good").
- Tests: DMB Tour job through the engine = the approved poster exactly (0 of 5,460,779 trap px differ, CLEAN
  tones identical). Box off: DMB Nash job old vs new engine IDENTICAL (22 files, --compare-jobs). cargo test 7/7.
- Sara: run BUILD_AND_TEST_ENGINE.bat, then Reload the panel. Backups: versions\engine_main_backup_2026-10-26_
  before_tonal_inks.rs, versions\main_backup_2026-10-26_before_tonal_inks.js.

## 0-prev2. Update 2026-10-21

**Panel fix 2026-10-21 (Manual Progressive Knockout):** Sara's run failed with "Destination clear failed
... result=-128" on grey green -> coat yello: grey green had been fully cut by the layers above it, so its
selection was empty and Photoshop cancels a clear with an empty selection (-128). main.js now skips a layer
with no pixels left (source or destination) and a pair whose selection is empty, with a line in the status
log; any other error still stops the run. No change to print output. Tested with a stand-in Photoshop
(old code reproduces -128, new code completes). Backup: versions\main_backup_2026-10-21_before_empty_layer_fix.js.
Waiting for Sara to reload the panel and re-run.

**Panel fix 2026-10-21 (trailing space in a layer name):** DMB Nash poster, layer "blue " (trailing space).
COLOR__ group names are trimmed ("COLOR__blue"), so CLEAN sync looked up "blue": no colour in
mask_colors.json ("blue "), no clean mask file, original layer not found/hidden -> no CLEAN__blue, original
blue left showing; 750,838 px of the engine's clean blue (98% under the key) missing = paper "outlines"
between blue and its key trap. main.js: inkKey()/resolveMaskName() - lookups also match ignoring spaces at
the start/end of a name; exact names still win first. Tested against Sara's mask_colors.json (7 checks).
Workaround without the fix: rename the layer without the trailing space.
Backup: versions\main_backup_2026-10-21_before_trailing_space_fix.js.

## 0-prev. Update 2026-10-20 10:15

**DMB Fall Tour 2026 (Trap Examples\DMB Tour) - content-aware tonal trapping, delivered for Sara's check:**
`DMB_Fall_tour_2026_trapped.zip` (layered PSD 5400 x 7200 @300: Background, CLEAN__/TRAP__<ink>_under_Key
per ink, Black/keyline, hidden marker). Method + numbers: tools/dmb_tour/README.md. Test crop approved first.
Offline only - nothing in the panel/engine.

## 0-obey. Update 2026-10-20 morning, Obey v2 + bleed

**Latest Obey files (Trap Examples\Obey), all offline - nothing in the panel/engine yet:**
- `Obey_roundtraps_off_MITRED_v2_600.zip` - Sara: "looks good". v2 = mitre pass with her "blue line"
  rule: at a joint the LOWER colour's trap band carries on under the key at the same angle to the key
  trap depth; the upper colour ends on its own edge (they overlap under the key by the band width).
  Mitre cutoff 25 deg between colour edge and key edge (was 45). 79 of 88 key joints mitred.
- `Obey_roundtraps_off_MITRED_v2_600_bleed_fixed.zip` - v2 + 0.25 in bleed (9900 x 12300 @ 600).
  Inside the trim identical to v2 except the 4 bottom rows (5,465 px of paper sliver filled - Sara
  asked). Flower texture: pure mirror at the trim; solid shapes (key stroke, yellow band) carried at
  their own angle; where a mirror would reflect a solid shape, plain blue background is used.
  Superseded: `..._v2_600_bleed.zip` (white line + obvious pattern seam at the bottom).
- NEXT: when Sara wants it, put the v2 joint rule into the engine behind a tick box ("Mitre key-trap
  joints", default OFF, Round traps OFF only). Bleed method also only offline (tools/obey).

## 0-prev. Update 2026-10-19 evening (Obey mitre pass v1 delivered) - superseded by the above

**Waiting for Sara's check:** `Trap Examples\Obey\Obey_roundtraps_off_MITRED_600.zip` (PSD, 9600 x 12000
@ 600 ppi, same 44 layers as her run minus the PDF's white "Layer 1", plus a HIDDEN magenta layer
"CHANGED PIXELS (mitre pass)" showing every changed pixel) and `Obey_mitre_before_after.png`.
Built offline from her `Obey_roundtraps_off.pdf` (square traps, 12 px under the key) by
tools/obey/mitre.py, modelled on her before/after screenshots of the top-left frame. Nothing in
her panel/engine code changed.
- What the pass does (only under the key; 11,354 px changed in total):
  1. 60 straight joints mitred: the trap zone under the key is split along the continuation of
     the two colours' shared edge, within 2 trap widths (24 px) of the joint. Each colour's trap
     ends on its own edge line; the overlap on the far side of the line is removed (as Sara did by hand).
  2. 28 shallow / curved / very short joints: NO line (that caused the flower-area wedges before).
     Solid overlap kept; only slivers/dots < 5 px wide on the other colour's side moved.
  3. Square corners: 561 px filled at 134 real corners (where the key wraps round a colour corner;
     these were bevelled by bevelKeyCorners). Not along curved edges.
  4. Loose dots of key trap cut off from their own colour removed (~30 px) when another colour
     already covers the spot; 28 px kept because removing them would leave bare key.
  5. Doubled ink cleared: the trapper's own output had 1,846 px in two layers of the same colour;
     now 0.
- Checks (tools/obey/mitre_check.py, psd_verify.py): every colour's separation unchanged outside
  the key (0 px); doubled ink 0; bare key pixels inside the trap band 122,713 -> 120,959 (fewer);
  trap lost away from joints only = removed dots; PSD read back with an independent reader:
  45 layers, 600 ppi, every layer pixel-identical to the fixed masks.
- Left alone on purpose: a few red pixels in the ART at the cream/red/key point near x2005 y1571
  (600 ppi) - their trap is legitimate; removing them would change the print.
- NEXT: Sara looks at the PSD. If approved, the rule goes into the engine behind a tick box
  ("Mitre key-trap joints", default OFF), applying only with Round traps OFF. Not started.
  Not done in this pass: carrying A-under-B trap bands on into the key (extend_bands.py, still
  untested) - Sara's screenshots didn't show it.

## 0a. Handoff 2026-10-19 (Obey) - superseded by 0 above

**Where we stopped (Obey poster, Trap Examples\Obey).** Geometric file, flat colours + key:
Yellow, Cream, Red, Light Blue, Blue, Dark blue, Key; paper "Cougar Natural 100#C".
- Sara re-ran the panel herself (status snapshot `UXP_Trapper\status_logs\smart_trapper_status_2026-10-19T19-42-52-582Z.txt`):
  colours merged, **300 ppi, 4800 x 6000, trapPx 5, Round traps OFF, Key traps follow visible
  colour OFF**, keyTrapPullbackPx 1, smoothKeyTraps + bevelKeyCorners on. She says this is better
  than her morning run (600 ppi, trapPx 10, round ON, follow-visible ON).
- Why round OFF is better on geometric art: round traps grow as a circle, so trap ends get rounded
  caps that bulge past corners (bumps/blobs at joints), and round also drops trap pixels closer to
  open area than to their own colour, which shaves corners (trap "stopping short"). Square traps
  fill corners. Follow-visible OFF removes the nearest-colour split under the key that caused the
  scattered tie dots and the light blue cut off by the blue.
- What she still fixes by hand (screenshot of the key frame with red/cream and blue/cream stripes):
  every joint where a stripe edge runs into the key: the square trap leaves a small stair-step /
  dot at the joint; she makes a clean mitre (trap line ends on the continuation of the stripe's
  own edge) and the inside frame corner a crisp square.
- **NEXT STEP:** Sara will save her new square-trap run (layered, PDF with a white top layer is
  fine) into `Trap Examples\Obey`. Claude rebuilds the layers from it (PDF -> Layr block -> PSB,
  tools/obey/pdf2psb.py + bin2psb.py), runs ONE joint-mitre cleanup pass over the whole file on
  top of the square traps, and sends a 72 dpi preview PSD (full pixel size is fine) for her to
  check. Nothing goes into her code until she approves (behind a tick box, default off).

**Lessons from today's Obey what-ifs (all offline, none in the engine):**
- Joint fix v1 (tools/obey/joint_fix.py): re-split the trap zone at joints along the A|B edge line.
  Problems Sara found in the 600 ppi file: (1) it copied CLEAN pixels into TRAP layers of the same
  colour -> "doubled ink" lines that show darker in her multiply preview; (2) at shallow/curvy
  joints (the flower pattern) the line handed long wedges of trap to the wrong colour (light blue
  trap cut off by the blue). Fixed in the current script: no doubling (tidy.py), line only when the
  edge enters the key within 45 deg, re-split only within ~1.5 x trap of the joint. Not yet
  re-delivered to her (her latest files still have the v1 problems).
- Sara's two hand examples (light blue stems, yellow/cream at the key): where a trap band between
  two colours (A under B) meets the key, the band should carry straight on under the key to the key
  trap depth. Draft script tools/obey/extend_bands.py (UNTESTED, never run). Stray-dot cleanup
  draft tools/obey/specks.py (UNTESTED).
- Bleed: tools/obey/bleed.py + add_bleed_psd.py add 0.25 in (150 px @600) content-aware bleed to
  every layer through one position map (straight edges carried at their angle, curvy pattern
  mirrored). Sara's issues were inside the print area, not the bleed.
- Delivered so far (Trap Examples\Obey): Obey_joint_fix_test.zip, Obey_joint_fix_600.zip,
  Obey_joint_fix_600_bleed.zip - all built with joint fix v1 (superseded).

## 0b. Previous handoff (2026-10-09)

**Status**
- EASY files (all solid Normal layers) are signed off; see section 5 and TEST_RESULTS.md.
- MEDIUM 2026-10-09:
  - Rule 3 is BUILT behind the panel tick box "File has transparent / overlay layers" (setting
    `overlayLayers`, job.json `overlayMode`, default off). Sara wants overlay rules kept separate
    from solid-file behaviour.
  - Simulated results: Mempho and Helton have 0 solid-area change. Easy files are identical with
    the box on or off.
  - DONE 2026-10-12: Sara ran Mempho and Helton in Photoshop with the box ticked. Both have 0
    solid-area change vs the client, the COLOR__ groups were set to Multiply / Darken, and the
    numbers match the simulation exactly (TEST_RESULTS.md). MEDIUM is signed off pending Sara's
    visual check.
  - 2026-10-12 panel fix: the 2 s banner timer had started scanning layers, which stopped the
    number boxes taking typing. The scan is now cached per document and the timer pauses while
    typing.
  - Next: HARD (DMB Ocean, gray/gradient layers, rule 7).
  - 2026-10-12: Wilco (Trap Examples\wilco) was a messy client file. Claude rebuilt it into the
    standard before structure with tools/arrange (see its README): 6 inks, darkest on top, green
    Background used as paper. Output is Trap Examples\wilco\Wilco_before_arranged.zip.
    Open question for Sara: is the green paper stock, or a printed green flood?
  - The group blend mode is set through the UXP DOM (`group.blendMode = orig.blendMode`), which
    is untested in Photoshop. The status log says what it set.
- The next job is **MEDIUM files**: solid Normal layers plus overlay layers (Multiply / Darken, or
  under 100% opacity/fill). The test files are **Mempho** and **Helton** in
  `Desktop\Trap Examples` (before.psd = client file, after.psd = Sara's hand trapping, notes.txt).
- After that comes HARD (DMB Ocean, gray/gradient layers, rule 7).

**Goal for medium files.** Implement rule 3 from TRAP_RULES_NOTES.md and prove it on Mempho and
Helton:
- An overlay layer is any non-Normal blend mode, or opacity/fill under 100%. Darken counts.
- Colours UNDER an overlay are not knocked out and get no trap under it. The overprint is part of
  the art (yellow under blue Multiply = green).
- Overlays overlapping each other outside the key are kept.
- Overlays ARE knocked out under the opaque key, with the normal 5 px trap.
- Rule #1 still applies: with all layers on, the result must look like the client file, which
  means comparing a blend-aware composite (Multiply/Darken), not just "top colour wins".
- Mempho note: today's trapper would visibly change about 3% of that print.

**What Claude found in the code but has not fixed yet.** Verify each before changing it:
1. **Manual Progressive Knockout** (`applyProgressiveKnockoutInPhotoshop`, main.js about line 1325)
   uses EVERY visible non-group layer as a cutter, overlays included. That breaks rule 3, because
   it cuts colours out from under Multiply/Darken layers. Overlays must not cut. They still get
   cut by the key, and by opaque layers above them.
2. **`detectBlendLikeLayers`** (main.js about line 2734) has an operator-precedence bug. As
   written it means `(blend != normal && opacity != 100) || fill != 100`, so a Multiply layer at
   100% opacity is NOT detected. Intended: `blend != normal || opacity != 100 || fill != 100`.
   Check where it's used before fixing.
3. **Engine** (SmartTrapperB1/engine/src/main.rs): `job.json` already carries `blendMode`,
   `opacity` and `fillOpacity` per colour, but the engine ignores them.
   - It traps every lower colour under every upper colour, overlays included.
   - In the round-trap / pullback "hidden" mask it treats an overlay above as hiding what's below.
   - Needed: skip trap pairs whose TARGET (upper) is an overlay; don't count overlays as "hidden"
     cover; overlay SOURCES still trap under opaque colours above and under the key.
4. **Prepare Import / Import Traps** (`buildCleanLayerInGroup` about line 1868, `importTraps` about
   line 3139): check whether the CLEAN__ and TRAP__ layers get the overlay's blend mode and opacity
   (or sit in a group that has it). If a Multiply colour's CLEAN layer comes in as Normal, the
   print changes. CONFIRMED 2026-10-09: they come in as Normal (see step 2 below).
5. **The test harness** (`tools/example_checks/easy_check.py`) assumes every layer is opaque
   ("top colour wins"). For medium files it needs a blend-aware composite:
   - Multiply: result = below * colour / 255.
   - Darken: min(below, colour).
   - Respect opacity.
   - Then compare client vs trapped composite (e.g. count pixels that differ by more than a few
     levels). Layer blend modes come from extract.py's meta.json (third field, e.g.
     BlendMode.MULTIPLY).

**Suggested order**
1. Stage and extract Mempho and Helton:
   - Copy before.psd, after.psd and notes.txt from the device. Helton's files are about 320 MB
     each, so stage them one per call.
   - Run `tools/example_checks/extract.py`.
2. Make a blend-aware easy_check (or `--blend` mode) and measure today's trapper vs Sara's hand file
   on both. This confirms the about 3% Mempho problem before changing anything.
   DONE 2026-10-09: `tools/example_checks/medium_check.py`. The baseline is in TEST_RESULTS.md.
   - MPK + engine changes the solid areas: Mempho 2.18%, Helton 3.45% (hand files 0.09% / 0.05%).
   - All of that comes from MPK cutting colours out from under the overlays.
   - Code check: `detectBlendLikeLayers` is only used for the panel's summary text.
   - Prepare Import: CONFIRMED by Sara 2026-10-09. After Prepare Import the overlay's CLEAN__ layer
     is Normal, not Multiply.
     - Cause: `createLayerAboveCurrent` makes a plain new layer (Normal, 100%) for CLEAN__
       (main.js about line 1928) and for every TRAP__ layer (about lines 3259 and 3314).
       Nothing copies the blend mode or opacity from the original layer.
     - Fix: give CLEAN__ and TRAP__ the original layer's blend mode, opacity and fill.
     - Baseline cost of the bug: about 2.5% of Mempho and 3.6% of Helton change from this alone.
3. Engine rule-3 changes (item 3). Keep older job.json files working, then cargo test.
4. Panel: MPK skips overlays as cutters (item 1), fix item 2, confirm item 4 with Sara.
5. Re-measure, add a dated section to TEST_RESULTS.md, update CHANGES / TRAP_RULES / this file,
   commit and push.
6. Ask Sara to run both files in Photoshop. She says "read latest", and Claude reads the newest
   `Desktop\TrapJobs\<doc>__UXP__<time>` folder and `trapper\UXP_Trapper\status_logs\` (see the
   Working with Sara notes below).

**Sara's current settings** (her last runs, 2026-10-09):
- Trap width 5
- Preflight cleanup on
- Alpha threshold 89-90
- Edge bias 1 (the engine raises 0-1 to 1)
- Key trap pullback 1
- Colour trap pullback 0 (2 only by choice on dot-heavy files)
- Round traps on
- Close key halo off (on only for halo files like Phish)

**Poster registration drift is about 5 px at 300 ppi.** That's why traps are 5 px. The "2 px"
figure was from the fine-art tests and does not apply here.

**Working with Sara (how this chat ran)**
- **Who she is:** a screen-print shop owner, not a coder. Use plain language and short answers. Ask
  before engine changes that would change how a file prints; otherwise build, test, and report
  numbers.
- **Her computer:** this chat was linked to it. `Desktop\trapper` is the LIVE app folder that
  Photoshop loads. Also linked: `Desktop\Trap Examples` and `Desktop\TrapJobs`.
- **Delivering a change:**
  1. Back up the old file to `_BACKUP_2026-10-06_before_claude\...\<name>_before_<change>.<ext>`.
  2. Write the new file into `Desktop\trapper`.
  3. Commit the same change to git and push it.
  4. Tell Sara exactly what to do: "Reload" for a panel-only change, or "run
     BUILD_AND_TEST_ENGINE.bat, then Reload" for an engine change.
- **Git:**
  - Clone `halfjorge/smart_trapper_backup` and work on branch `trapper_2026_10`. Push access works.
  - The repo stores LF line endings (`tools/dev/lf.py`). The PC's main.js has mixed CRLF/LF. When
    editing a PC copy, keep its line endings (`tools/dev/keepeol.py`) so diffs stay small.
- **The cloud workspace is wiped between chats.** Nothing from this chat's `/home/claude` survives.
  Re-clone the repo.
  - **Building the engine in the cloud:** crates.io is BLOCKED there (tested 2026-10-09), so use the
    vendored kit `tools/dev/engine_build_kit_cloud.zip`. It holds the dependency sources plus
    `build_new/` with a Cargo.toml pointing at them.
  - Steps:
    1. Unzip it to a scratch folder.
    2. Copy `SmartTrapperB1/engine/src/*.rs` into `build_new/src/`.
    3. Run `cargo build --release --offline` and `cargo test --release --offline` (5 tests).
    4. Copy edited .rs files back into the repo.
  - On Sara's PC, BUILD_AND_TEST_ENGINE.bat builds the normal way with internet.
  - Verified 2026-10-09: the kit builds today's engine, and all tests pass.
- **Checking Sara's own runs:**
  - `tools/example_checks/runcheck.py` measures a real TrapJobs run folder against the client file.
  - For opaque files, `easy_check.py --set key=value` simulates other settings.
- **Keep the docs current with every change.** That means CHANGES_2026-10-06.md (plain language for
  Sara), TRAP_RULES_NOTES.md (rules BUILT/DECIDED), TEST_RESULTS.md (numbers), and this file.

**Things that went wrong today (so they don't repeat)**
- **Scrolling changed settings:** the mouse wheel over a number box changed its value (Edge bias -1,
  so 0 traps). Fixed: the boxes are now text boxes, and the red banner warns about risky settings.
- **No-overlap joins:** the round-trap corner rule and colour pullback could leave colours meeting
  with no overlap. Fixed: always keep the first 1 px of trap.
- **Untrapped key lines:** Edge bias 0 left the key lines untrapped. Fixed: minimum 1 px of key-edge
  growth.
- **Byrne's after file:** `Trap Examples\Byrne\after.tif` is an earlier TRAPPER output, not Sara's
  hand trapping.

---

## 1. What the app does

A Photoshop trapping tool for spot-colour poster files.

- **Input PSD:** top layer = key (whatever its name), bottom layer = blank paper, colour layers in
  between. Colour order is set by hand before running; the trapper never reorders.
- **Panel (UXP):** `UXP_Trapper\main.js`. The buttons:
  - Manual Progressive Knockout (optional, operator's choice)
  - Cut Top Key From Colors (optional)
  - Clean Colors (optional)
  - Run Trapper
  - Prepare Import Structure
  - Import Traps
- **Bridge:** `UXP_Trapper\real_bridge.py`, a local HTTP service. Start it with
  `python .\real_bridge.py`.
- **Engine (Rust):** `SmartTrapperB1\engine\src\main.rs` and `fast.rs`.
  - Rebuild with `BUILD_AND_TEST_ENGINE.bat`, then click Reload on the panel.
  - The engine reads the exported masks plus job.json, then writes:
    - `traps\*.png` and `traps.json`
    - `clean_masks\` (threshold cleanup)
    - `mask_colors.json`
- **Output:** each colour sits in a `COLOR__<ink>` group, which holds:
  - `CLEAN__<ink>`: the cleaned solid layer
  - `TRAP__<ink>_under_<colour above>`: the trap layers
- **Job folders:** `Desktop\TrapJobs\` (a fresh subfolder for every run).
- **Backups:**
  - `_BACKUP_2026-10-06_before_claude\` holds the files from before Claude's changes.
  - `RESTORE_PREVIOUS_VERSION.bat` undoes those changes.
- The old JSX scripts (`Phase2_*.jsx`), `Trapper_CEP_Panel`, `trapper OLD` and `versions\` are
  legacy. The UXP panel is the current app.
- Git / GitHub: see section 9.

**Panel settings.** For each one: the job.json field, the code default (what a fresh install gets),
and what Sara used on her last run (Oct 7).
- Trap width (`tolerance` / CLI arg): 5 px default; Sara 5.
- Preflight cleanup (`preflightCleanup`): off by default; Sara on. It turns on the threshold and
  edge bias below.
- Alpha threshold (`alphaThreshold`): 8 by default; Sara 89-90, about 35% opacity counts as ink.
- Edge bias (`edgeBiasPx`): 0 by default; Sara 1. It grows colours back only where the key covers
  them. The engine treats 0-1 as 1 (minimum, since 2026-10-09), so colours always touch the key.
- Key trap pullback (`keyTrapPullbackPx`): 1 default; Sara 1. Since 2026-10-13 the trap is kept back
  only from open area beside the key (paper / uncovered lower colour), never from its own colour's
  side, so 2+ no longer opens a white ring between a colour and its trap.
- Colour trap pullback (`colorTrapPullbackPx`): **keep 0 by default** (decided 2026-10-09). Use 2 only by
  choice on dot-heavy files (e.g. Byrne's calendar dots), where a sliver of trap peeking past small
  shapes would show. At 2 those spots keep only 1 px of overlap, against about 5 px of poster drift.
- Round traps (`trapShape` "round"): on by default; Sara on.
- Close key halo (`closeKeyHaloPx` 2 when ticked): off by default (rule 4). Never fills with an overlay
  colour (2026-10-14). Leave it off on art with thin paper strokes beside the key (Baltimore).
- File has transparent / overlay layers (`overlayMode`): off by default (rule 3, added 2026-10-09).
  Tick it only for files with Multiply/Darken or under-100% layers. When off, everything works as
  before. The red banner names any overlay layers it finds while the box is off.
- Smooth traps under the key (`smoothKeyTraps`): off by default (added 2026-10-12). Trims thin
  "fingers" of trap under the key (bits under about 5 px wide). Every colour keeps a 1-2 px ring of
  overlap. Works on any file.
- Bevel trap corners next to paper (`bevelKeyCorners`): off by default (added 2026-10-12). Cuts the
  square end of a trap under the key into a bevel where bare paper is beside it (Frankenstein
  letter strokes). Traps across thin key lines are left alone.
- Key traps follow the colour you see (`keyTrapsFollowVisible`): off by default (added 2026-10-13).
  Under the key, the colour seen next to the key edge goes on top in the trap zone; later colours
  are taken out there (Peteschaw olive under a thin blue line). Any colour, any file.
- Test runs should use Sara's values.
- Missing fields in older job.json files fall back to the old behaviour.

## 2. Shop setup (applies to everything)

- **Prints:** posters on uncoated and coated paper, waterbased and UV inks, no white underbase.
  Press files are set up 2-up.
- **Ink:** transparent inks. Colours are matched by eye on a calibrated monitor.
- **Screens and output:**
  - Up to about 13 screens.
  - Grey / gradient layers are dithered in the RIP: Xerio RIP 4, 128 micron stochastic (FM) dither.
  - Dithering loses fine detail and subtle tone, so solid ink is preferred wherever possible.
- **Registration (posters / graphic seps):** allow for about 5 px of drift at 300 ppi. That's why the
  standard trap is 5 px. (The "2 px window" from the fine-art tests applies to fine art only, not to
  this app.)
- **Standard trap:** 5 px at 300 ppi. Hand-made "5 px" traps usually measure about 6 px.
- **Files must be RGB at 300 ppi.** The panel shows a red banner if they aren't.
- **No press tests are possible.** All checking is done by simulation and comparison with
  hand-trapped examples.

## 3. Sara's working preferences

- **Rule #1:** with all layers on, the trapped file must look like the client file. The only
  exceptions are deliberate fixes:
  - cleaning fuzz into solid ink
  - closing halos caused by artist error
- **No butt registration.** Wherever two inks meet outside the key, there must be an overlap.
- **Run Trapper never cuts anything out.** Knockouts are the operator's choice, made with the panel
  buttons before trapping.
- **Grey values are never changed where they show.**
- **Ask before changing the engine** when a before/after example differs in a way that isn't
  explained.
- Use her own examples as "this is what we did", not as the gold standard. If there's a better way,
  propose it.
- Plain-language explanations; no jargon.
- Don't rush, but don't burn compute.

## 4. File types (Sara's categories) - the current goal

| Type | What's in it | Examples in `Desktop\Trap Examples` |
|---|---|---|
| EASY | All layers 100% solid, Normal blend | DMB, DMB Methane, Phish, BTS (Sara's list); probably also Byrne, Vista, Phish Jackson (confirm with Sara) |
| MEDIUM | Solid Normal layers plus solid overlay layers (Multiply / Darken, or under 100% opacity) | Mempho, Helton |
| HARD | Mix of solid, solid+gray/gradient, overlays, and overlays with gray | DMB Ocean |

Notes:
- DMB Bourbon is excluded (Sara is unsure of its discrepancies).
- Smashing Pumpkins Jacksonville was made press-ready with a script (`make_sp_press.py`).

How each type should be handled is in `TRAP_RULES_NOTES.md`:
- overlays: rule 3
- gray layers: rule 7
- cleanup order: rule 6

## 5. Where it stands (2026-10-09)

**Built and working:**
- Engine about 4x faster, with output identical to the old engine.
- The engine writes `mask_colors.json` itself; this cut a 5 min run to about 1 min.
- Fresh job folder per run.
- Settings are saved and there's an "Explain settings" button.
- Layer-name fix for names containing `/ : " * ? < > |`.
- Clean Colors button.
- Colour trap pullback setting (rule 10).
- Round traps that follow their own colour (default ON).
- Red file-check banner for files that aren't RGB at 300 ppi. It also shows "CHECK SETTINGS" for
  risky values (Edge bias below 0, Trap width 0, pullback not smaller than Trap width), and
  "LAST RUN MADE 0 TRAPS" after a run with no traps.
- Number boxes are text boxes, so the mouse wheel can't change them by accident. Values are checked
  when you leave the box.
- Trap layers renamed `_under_`.
- **Defaults:** round traps ON, colour trap pullback 0.

**Easy files: re-checked 2026-10-09 on the current engine with Sara's settings. All pass.**
Details are in `TEST_RESULTS.md`. Files: DMB, Methane, Phish, BTS, plus Byrne and Phish Jackson
(neither has a hand file).
- Nothing changes with all layers on except deliberate fixes (soft edges made solid, key halo).
  No ink is lost and no colour is swapped.
- Butt joins: 0 in every file, after the 1 px minimum-overlap fix to round traps.
- Close key halo is right for Phish (it matches the hand file) and wrong for BTS and Methane, so
  it stays off by default.
- Rule 6, colour-to-colour hairlines: on hold (Sara's decision).
- Alpha threshold: Sara uses 89. Methane's hand work rounded up from about 12-15%. Still a per-job
  setting; no change.
- Full-bleed edge issue: not seen in these files (no butt px within 3 px of the canvas edge).
- Not covered: Vista (no before/after pair), Smashing Pumpkins, DMB Bourbon (excluded).

**Medium and hard files:** the rules are written (3 and 7) but not yet built or verified in the
engine.

**Other known issues:**
- Full-bleed art (touching the canvas edge) sometimes traps differently from art with a border.
  Suspect the engine treats the canvas edge as "no ink".
- Possible future panel tool: backing / flat fill under fine hatching (BTS).

## 6. Plan (agreed 2026-10-09)

Goal: work through easy, then medium, then hard examples and make the engine handle all three.

1. **Finish EASY.** DONE 2026-10-09 (see TEST_RESULTS.md). The original plan was:
   - DONE: the Close key halo option. The colour-to-colour hairline fix is on hold.
   - Re-run every easy example on the current engine with the default settings: DMB, Methane,
     Phish, Phish Jackson, BTS, Byrne, Vista.
   - Report three things for each example:
     - Does it look the same as the client file with all layers on?
     - Are there any butt joins left outside the key?
     - How close are the traps to Sara's?
   - Sign off when all pass.
2. **MEDIUM** (Mempho, Helton), rule 3.
   - Overlay layers (any non-Normal blend, or under 100% opacity/fill) are not knocked out or
     trapped under each other or under colours.
   - Overlays ARE cut back under the opaque key with a 5 px trap.
   - Have the trapper report the file type when it runs.
3. **HARD** (DMB Ocean), rule 7.
   - Gray layers are only cut under fully solid ink above them; the trap band keeps the original
     gray values.
   - Layers under semi-transparent ink are kept.
   - Never progressively knock out gray-heavy files.
4. Later:
   - the full-bleed edge issue
   - a backing tool
   - a press preview for posters: 2 px shift shows paper? thin lines or type lost after 128 um
     dither? Write this fresh for the app.

## 7. What was tried / decided (app only)

- **Kept:**
  - the faster engine
  - engine-side mask colours
  - round traps with the corner rule (verified to 1 px in 4.6 M against an exact reference)
  - the file-check banner
  - Clean Colors
  - layer-name fix
  - `_under_` naming
- **Pullback 2:** built, but Sara chose 0 as the default. On Byrne, 0 leaves 6,871 trap px touching
  an open edge, mostly 1 px specks at small gray dots. Revisit if they show on press.
- **Rejected:**
  - Run Trapper doing knockouts automatically. Cutting is the operator's choice (rule 8).
  - Progressive knockout on gray-heavy files. It visibly changed about 17% of Ocean.
- **Left out for now:** automatic backing fills (BTS), and closing halos without asking (it's an
  on/off option instead).

## 8. Claude's test scripts (also in git: tools/example_checks, tools/dev)

`tools\example_checks\` (in git) holds the Python scripts used to compare engine output with the
hand-trapped "after" files. The same scripts are also in `_claude_test_scripts.zip`. They are reference only, not part of the app. Paths inside them
point to Claude's old cloud workspace (`/home/claude/...`), so adjust them before reuse. See the
README inside the zip.

## 9. Git and GitHub

- **GitHub repo:** `halfjorge/smart_trapper_backup`. Claude has been able to push to it since
  2026-10-09.
- **Current work branch: `trapper_2026_10`.** It has everything up to now, one commit per step:
  1. Snapshot of the PC as of 2026-10-06, before Claude: the March-September work that was never
     pushed (PC branch `experimental_2026_04_02_robust_trapper`).
  2. The Oct 6-7 changes (faster engine, Clean Colors, round traps, pullback, file check).
  3. Close key halo.
  4. These docs and `tools/example_checks/`.
- **Other branches:**
  - `trapper_active` is the old March state.
  - `main` is older still.
  - Nothing has been merged. Merge `trapper_2026_10` into `trapper_active` once the easy files are
    signed off.
- **How changes reach Sara's PC:** Claude writes the changed files straight into
  `Desktop\trapper` (the live folder Photoshop loads), then commits the same change to
  `trapper_2026_10` and pushes it.
  - The PC's own git checkout has not been switched to the new branch, so `git status` on the PC
    shows the files as changed. That's expected.
  - To line the PC up later (ask Claude to walk through it), the content is already the same:
    ```
    git stash
    git fetch origin
    git checkout -B trapper_2026_10 origin/trapper_2026_10
    git stash drop
    ```
- **Line endings:** the repo stores LF. Windows git converts files to CRLF on the PC, which is fine.
- **Commit messages** say what changed, why, and how it was tested.

## 10. How to make a change (for the next agent or person)

1. Read sections 4-6 and `TRAP_RULES_NOTES.md`. If an example disagrees with the rules, ask Sara
   before changing the engine.
2. Back up every file you're about to change into `_BACKUP_2026-10-06_before_claude\` as
   `<name>_before_<change>.<ext>` (Sara restores with these).
3. **Engine:** edit `SmartTrapperB1\engine\src\main.rs` / `fast.rs`.
   - New job.json fields need `#[serde(default)]`, so older job folders keep working.
   - Run `cargo test` (5 unit tests in fast.rs).
   - On the PC, `BUILD_AND_TEST_ENGINE.bat` builds the engine and runs a regression job.
4. **Panel:** edit `UXP_Trapper\main.js`. A new setting has to be wired in all of these places
   (search for `roundTraps` or `closeKeyHalo` as a model):
   - `DEFAULTS`
   - the HTML block (setting box plus help text)
   - the element-id list
   - `getSettings`
   - `applySettings`
   - the job.json builder
   - the status-log "Settings:" line
   - the persist-on-change list

   Then run `node --check main.js`. After a panel change, Sara clicks Reload; after an engine
   change, she runs the .bat first.
   - Step functions (`runManualProgressiveKnockout`, `runTrapper`, `prepareImportStructure`,
     `importTraps`) must keep returning `{ ok, reason }`: the one-button Run Trapper relies on it.
   - Anything that should differ in the co-worker's copy goes in `tools/dev/make_shared_copy.py`
     (and the TWO VERSIONS table in section 0), never as a hand edit to a copy.
   - Panel tests without Photoshop: `tools/ui_tests/` (README there).
5. **Test** against the Trap Examples (section 11). Report what changed with all layers on, and
   any new butt joins.
6. **Update the docs** (and add a dated section to `TEST_RESULTS.md` for any test run):
   - `CHANGES_2026-10-06.md`: a new dated section, in plain language for Sara.
   - `TRAP_RULES_NOTES.md`: mark rules BUILT or DECIDED.
   - This file: sections 5-7.
7. **Copy and commit:** copy the files to the PC, then commit and push to `trapper_2026_10`.

## 11. How to test against the examples

- **The examples:** `Desktop\Trap Examples\<job>\before.psd` (client file) and `after.psd` (Sara's
  hand trapping), plus `notes.txt`.
  - The after files are often a 2-up press layout cropped back. Phish has a +150 px border offset.
- **Extract layers:** `tools/example_checks/extract.py <psd> <outdir>` writes every top-level layer
  as RGBA `.npy`. It needs psd-tools; a layered TIFF uses `tifflayers.py`.
- **Run the real engine on an example:**
  - `easy_check.py <job>` is the standard check, and the one behind TEST_RESULTS.md.
    - It aligns the after file and matches its layers by colour.
    - It runs MPK and then the engine with Sara's settings.
    - It reports visible change, butt px, trap at open edge, trap width, and agreement with the
      hand file.
    - Options: `--halo 0,2`, `--shape square`, `--no-mpk`.
  - `halo_test.py <job> <offset> <trapPx> <halo list>` is the newest and cleanest. It builds a job
    folder with the panel's default settings and real soft alpha, runs Manual Progressive Knockout,
    runs the engine, and compares with the hand file.
  - `sim.py` is the older version of the same (binary masks).
- **What to report:**
  - **Visible change vs the client file**, outside the key, with all layers on. It should be 0
    except deliberate fixes.
  - **Paper left where the hand file has colour.**
  - **Trap px that touch an open edge**, i.e. butt joins (`byrne_engine.py`).
- All scripts use paths from Claude's cloud workspace (`/home/claude/ex/...`), so adjust them before
  running elsewhere.
