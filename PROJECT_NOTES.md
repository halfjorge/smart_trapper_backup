# PROJECT NOTES - Smart Trapper (start here in a new chat)

Last updated: 2026-10-09 10:40 (handoff to a new chat for MEDIUM files) by Claude. Owner: Sara (The Half and Half, screen-print shop).

**New chat? Read section 0 (Next session) first, then the rest of this file, then `TRAP_RULES_NOTES.md` (the agreed trapping rules) and
`CHANGES_2026-10-06.md` (what was changed and why).** Sections 9-11 below cover git, how to make a
change, and how to test. `SMART_TRAPPER_HANDBOOK.md` and `SESSION_STATE.md` are older (March 2026).
They still describe the panel/bridge/engine layout correctly, but their status and branch notes are
out of date.

> SCOPE: this app is for poster / gig-print trapping. The fine-art separation tests (Welker,
> Van Loon, Huemer) were standalone experiments, NOT part of the app. Their notes and code are kept
> separately in `Desktop\Trap Examples\FINE_ART_NOTES.md` and `_FINE_ART_SEPS_CODE_claude.zip`. Don't mix them into app work.

---

## 0. NEXT SESSION STARTS HERE (handoff 2026-10-09)

**Status**
- EASY files (all solid Normal layers) are signed off; see section 5 and TEST_RESULTS.md.
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
- Key trap pullback (`keyTrapPullbackPx`): 1 default; Sara 1.
- Colour trap pullback (`colorTrapPullbackPx`): **keep 0 by default** (decided 2026-10-09). Use 2 only by
  choice on dot-heavy files (e.g. Byrne's calendar dots), where a sliver of trap peeking past small
  shapes would show. At 2 those spots keep only 1 px of overlap, against about 5 px of poster drift.
- Round traps (`trapShape` "round"): on by default; Sara on.
- Close key halo (`closeKeyHaloPx` 2 when ticked): off by default (rule 4).
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
